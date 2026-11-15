import atexit
import time
import json
import base64
import threading
import datetime
from pathlib import Path
import tinytuya

TUYA_CONFIG_FILE = Path("/opt/domoskiosk/tuya_config.json")
def _load_tuya_credentials():
    cfg = {}
    if TUYA_CONFIG_FILE.exists():
        try:
            cfg = json.loads(TUYA_CONFIG_FILE.read_text())
        except Exception:
            pass
    import os
    region = os.environ.get("TUYA_API_REGION") or cfg.get("region", "eu")
    key = os.environ.get("TUYA_API_KEY") or cfg.get("api_key", "YOUR_TUYA_API_KEY")
    secret = os.environ.get("TUYA_API_SECRET") or cfg.get("api_secret", "YOUR_TUYA_API_SECRET")
    return region, key, secret

API_REGION, API_KEY, API_SECRET = _load_tuya_credentials()

CACHE_FILE = Path("/tmp/domos_live_devices.json")
ALL_DEVICES_CACHE = Path("/tmp/domos_all_cloud_devices.json")

# Core recognized device IDs
CAMERA_REGISTRY = {
    "bf77eed8534deaf66f2xpj": {
        "id": "bf77eed8534deaf66f2xpj",
        "name": "Videoportero Exterior",
        "location": "Entrada / Cancel",
        "category": "camera",
        "type": "doorbell",
        "icon": "videocam"
    },
    "bfce70c5e1e7475542tezv": {
        "id": "bfce70c5e1e7475542tezv",
        "name": "Cámara Pasillo",
        "location": "Pasillo Principal",
        "category": "camera",
        "type": "camera",
        "icon": "camera_indoor"
    },
    "bf88224fd128fceb4b5vd4": {
        "id": "bf88224fd128fceb4b5vd4",
        "name": "Cámara Sótano (Impresora 3D)",
        "location": "Sótano / Impresora 3D",
        "category": "camera",
        "type": "camera",
        "icon": "camera_indoor"
    },
    "bf7b5ccc66a5c47cbfdkew": {
        "id": "bf7b5ccc66a5c47cbfdkew",
        "name": "Cámara Salita",
        "location": "Salita",
        "category": "camera",
        "type": "camera",
        "icon": "camera_indoor"
    },
    "bf4c6936a402c805cfjjae": {
        "id": "bf4c6936a402c805cfjjae",
        "name": "Cámara Salón",
        "location": "Salón",
        "category": "camera",
        "type": "camera",
        "icon": "camera_indoor"
    }
}

DEVICE_REGISTRY = {
    "bf9abfe1a19f35a05ceej0": {
        "id": "bf9abfe1a19f35a05ceej0",
        "name": "Luz Cocina 1",
        "category": "light",
        "icon": "lightbulb",
        "type": "switch",
        "code": "switch_1"
    },
    "bf873ba4935f6abf954qsp": {
        "id": "bf873ba4935f6abf954qsp",
        "name": "Luz Cocina 2",
        "category": "light",
        "icon": "lightbulb",
        "type": "switch",
        "code": "switch_1"
    },
    "bf3aa35b1531ceffbezyrx": {
        "id": "bf3aa35b1531ceffbezyrx",
        "name": "Luz Jardín",
        "category": "light",
        "icon": "park",
        "type": "switch",
        "code": "switch_1"
    },
    "bf642a5115857811a7nihe": {
        "id": "bf642a5115857811a7nihe",
        "name": "Led Habitación 1",
        "category": "light",
        "icon": "flare",
        "type": "switch",
        "code": "switch_1"
    },
    "bf7e0ce372966aa35dcte8": {
        "id": "bf7e0ce372966aa35dcte8",
        "name": "Led Habitación 2",
        "category": "light",
        "icon": "flare",
        "type": "switch",
        "code": "switch_1"
    },
    "bf9cba82aabe945f4fc8q9": {
        "id": "bf9cba82aabe945f4fc8q9",
        "name": "Higrómetro Salón",
        "category": "climate",
        "icon": "thermostat",
        "type": "sensor"
    },
    "bf2d1d67a6677da71c58y5": {
        "id": "bf2d1d67a6677da71c58y5",
        "name": "Higrómetro Dormitorio",
        "category": "climate",
        "icon": "thermostat",
        "type": "sensor"
    },
    "bf3aa055b420138596m0cs": {
        "id": "bf3aa055b420138596m0cs",
        "name": "Sensor Aire Sótano",
        "category": "climate",
        "icon": "air",
        "type": "air_sensor"
    },
    "bfe037c461c9c61da3pesr": {
        "id": "bfe037c461c9c61da3pesr",
        "name": "Paneles Solares",
        "category": "solar",
        "icon": "solar_power",
        "type": "energy"
    },
    "bf6288vqvhibntur": {
        "id": "bf6288vqvhibntur",
        "name": "Batería Smart 20V",
        "category": "battery",
        "icon": "battery_charging_full",
        "type": "battery"
    },
    "bfe3804040d12a2822hzmp": {
        "id": "bfe3804040d12a2822hzmp",
        "name": "Impresora 3D",
        "category": "plug",
        "icon": "print",
        "type": "switch",
        "code": "switch_1"
    },
    "bf75842d28c31e9943g0wz": {
        "id": "bf75842d28c31e9943g0wz",
        "name": "Termo Eléctrico",
        "category": "plug",
        "icon": "water_drop",
        "type": "switch",
        "code": "switch_1"
    },
    "1728645494b97e138251": {
        "id": "1728645494b97e138251",
        "name": "Secatoallas",
        "category": "plug",
        "icon": "hot_tub",
        "type": "switch",
        "code": "switch_1"
    },
    "64326051e8db8480acc0": {
        "id": "64326051e8db8480acc0",
        "name": "Alarma Hogar",
        "category": "security",
        "icon": "shield",
        "type": "alarm"
    },
    "bf216abd6b1934fa11rl63": {
        "id": "bf216abd6b1934fa11rl63",
        "name": "Puerta Principal",
        "category": "security",
        "icon": "door_front",
        "type": "door"
    },
    "bf20349qicjyoh2g": {
        "id": "bf20349qicjyoh2g",
        "name": "Cerradura",
        "category": "security",
        "icon": "lock",
        "type": "lock"
    },
    "bf452117db5ebe4eadwctr": {
        "id": "bf452117db5ebe4eadwctr",
        "name": "Sensor patio",
        "category": "security",
        "icon": "motion_photos_on",
        "type": "motion"
    },
    "607584008c4f0049de61": {
        "id": "607584008c4f0049de61",
        "name": "Aire acondicionado",
        "category": "ac",
        "icon": "ac_unit",
        "type": "ac",
        "code": "switch"
    },
    "215081148c4f0047898d": {
        "id": "215081148c4f0047898d",
        "name": "Aire del Pueblo",
        "category": "ac",
        "icon": "ac_unit",
        "type": "ac",
        "code": "switch"
    },
    "bf221ae9a7e021a4374abl": {
        "id": "bf221ae9a7e021a4374abl",
        "name": "TV Salón",
        "category": "ir",
        "icon": "tv",
        "type": "infrared_tv"
    },
    "bf9b0283af185020bd8evy": {
        "id": "bf9b0283af185020bd8evy",
        "name": "TV",
        "category": "ir",
        "icon": "tv",
        "type": "infrared_tv"
    },
    "bffaf4f9e3e652a793t9n0": {
        "id": "bffaf4f9e3e652a793t9n0",
        "name": "Luz IR",
        "category": "ir",
        "icon": "lightbulb",
        "type": "infrared_light"
    }
}

class TuyaService:
    def __init__(self):
        try:
            self.cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        except Exception as e:
            print(f"[TuyaService] Deferred cloud init (network not ready): {e}", flush=True)
            self.cloud = None
        self.states = {}
        self.all_cloud_devices = []
        self.last_update = 0
        self._load_cache()
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _load_cache(self):
        if CACHE_FILE.exists():
            try:
                self.states = json.loads(CACHE_FILE.read_text())
            except Exception:
                self.states = {}
        if ALL_DEVICES_CACHE.exists():
            try:
                self.all_cloud_devices = json.loads(ALL_DEVICES_CACHE.read_text())
            except Exception:
                self.all_cloud_devices = []
        try:
            Path("/tmp/domos_tuya_states.json").write_text(json.dumps(self.states))
        except Exception:
            pass
        atexit.register(lambda: self._save_cache(persist_disk=True))

    def _save_cache(self, persist_disk: bool = True):
        try:
            Path("/tmp/domos_tuya_states.json").write_text(json.dumps(self.states))
            if persist_disk:
                CACHE_FILE.write_text(json.dumps(self.states, indent=2))
                ALL_DEVICES_CACHE.write_text(json.dumps(self.all_cloud_devices, indent=2))
        except Exception:
            pass

    def sync_cloud_devices(self):
        """Auto-discovers newly paired devices from the user's Tuya/Smart Life accounts."""
        try:
            devs = self.cloud.getdevices()
            if isinstance(devs, list) and len(devs) > 0:
                self.all_cloud_devices = devs
                for d in devs:
                    dev_id = d.get("id")
                    if not dev_id or dev_id in DEVICE_REGISTRY or dev_id in CAMERA_REGISTRY:
                        continue
                    name = d.get("name", "Dispositivo Tuya")
                    cat = d.get("category", "")
                    
                    # Auto-classify new devices
                    if cat in ["tdq", "dj", "cl"]:
                        DEVICE_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "category": "light", "icon": "lightbulb", "type": "switch", "code": "switch_1"
                        }
                    elif cat in ["cz", "pc"]:
                        DEVICE_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "category": "plug", "icon": "power", "type": "switch", "code": "switch_1"
                        }
                    elif cat in ["wsdcg", "th", "jqbj"]:
                        DEVICE_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "category": "climate", "icon": "thermostat", "type": "sensor"
                        }
                    elif cat in ["kt"]:
                        DEVICE_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "category": "ac", "icon": "ac_unit", "type": "ac", "code": "switch"
                        }
                    elif cat in ["infrared_tv", "infrared_light"]:
                        DEVICE_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "category": "ir", "icon": "tv" if cat == "infrared_tv" else "lightbulb", "type": cat
                        }
                    elif cat in ["sp", "cdsxj"]:
                        CAMERA_REGISTRY[dev_id] = {
                            "id": dev_id, "name": name, "location": "Hogar", "category": "camera", "type": "camera", "icon": "videocam"
                        }
                self._save_cache()
                print(f"[TuyaService] Auto-discovery complete: {len(self.all_cloud_devices)} devices registered.")
                return len(self.all_cloud_devices)
        except Exception as e:
            print(f"[TuyaService] Auto-discovery error: {e}")
        return len(self.all_cloud_devices)

    def parse_device_status(self, dev_id, status_list):
        parsed = {}
        kv = {item.get("code"): item.get("value") for item in status_list if isinstance(item, dict)}
        reg = DEVICE_REGISTRY.get(dev_id) or CAMERA_REGISTRY.get(dev_id, {})
        cat = reg.get("category")

        multi_switches = {
            k: bool(v)
            for k, v in kv.items()
            if k.startswith("switch_") and k[7:].isdigit()
        }
        if len(multi_switches) > 1:
            ordered = dict(sorted(multi_switches.items(), key=lambda x: int(x[0].split("_")[1])))
            parsed["switches"] = ordered
            parsed["state"] = any(ordered.values())
        elif "switch_1" in kv:
            parsed["state"] = bool(kv["switch_1"])
        elif "switch" in kv:
            parsed["state"] = bool(kv["switch"])

        if cat == "climate":
            temp_raw = kv.get("va_temperature", kv.get("temp_current", 0))
            if temp_raw > 100:
                parsed["temperature"] = round(temp_raw / 10.0, 1)
            else:
                parsed["temperature"] = float(temp_raw)
            hum_raw = kv.get("va_humidity", kv.get("humidity_value", 0))
            parsed["humidity"] = int(round(hum_raw / 10.0)) if hum_raw > 100 else int(hum_raw)
            parsed["battery"] = kv.get("battery_percentage", kv.get("battery_state", "--"))
            if "co2_value" in kv:
                parsed["co2"] = kv["co2_value"]
            if "voc_value" in kv:
                parsed["voc"] = kv["voc_value"]
            if "ch2o_value" in kv:
                parsed["ch2o"] = kv["ch2o_value"]

        elif cat == "solar":
            phase_a = kv.get("phase_a")
            watts = 0
            volts = 230.0
            amps = 0.0
            if phase_a:
                try:
                    raw = base64.b64decode(phase_a)
                    volts = int.from_bytes(raw[0:2], "big") / 10.0
                    amps = int.from_bytes(raw[2:5], "big") / 1000.0
                    watts = int.from_bytes(raw[5:8], "big")
                except Exception:
                    pass
            parsed["watts"] = watts
            parsed["volts"] = round(volts, 1)
            parsed["amps"] = round(amps, 3)
            parsed["state"] = kv.get("switch", True)

        elif cat == "battery":
            parsed["battery_percentage"] = kv.get("battery_percentage", 0)
            parsed["temperature"] = kv.get("temp_current", 0)
            v_raw = kv.get("charge_voltage", 0)
            parsed["voltage"] = round(v_raw / 100.0, 2) if v_raw > 100 else float(v_raw)

        elif cat == "security":
            if reg.get("type") == "alarm":
                parsed["master_mode"] = kv.get("master_mode", "disarmed")
                parsed["battery"] = kv.get("battery_percentage", 100)
            elif reg.get("type") == "door":
                parsed["is_open"] = bool(kv.get("doorcontact_state", False))
                parsed["battery"] = kv.get("battery_state", "normal")
            elif reg.get("type") == "lock":
                parsed["battery"] = kv.get("battery_state", kv.get("battery_percentage", "normal"))
                parsed["battery_state"] = kv.get("battery_state", "normal")
                parsed["alarm_lock"] = kv.get("alarm_lock", "")
            elif reg.get("type") == "motion":
                parsed["battery"] = kv.get("battery_percentage", kv.get("battery_state", "normal"))
                parsed["pir"] = kv.get("pir", "")

        elif cat == "camera":
            parsed["online"] = True
            parsed["motion"] = bool(kv.get("motion_switch", True))
            parsed["indicator"] = bool(kv.get("basic_indicator", True))

        if cat == "ac":
            parsed["state"] = bool(kv.get("switch", False))
            t_set = kv.get("temp_set", 230)
            parsed["temp_set"] = round(t_set / 10.0, 1) if t_set > 100 else float(t_set)
            t_cur = kv.get("temp_current", 0)
            parsed["temp_current"] = round(t_cur / 10.0, 1) if t_cur > 100 else float(t_cur)
            parsed["mode"] = str(kv.get("mode", "cold"))

        if cat == "plug":
            v_raw = kv.get("cur_voltage", 0)
            parsed["voltage"] = round(v_raw / 10.0, 1) if v_raw > 1000 else float(v_raw)
            p_raw = kv.get("cur_power", 0)
            parsed["power"] = round(p_raw / 10.0, 1) if p_raw > 0 else 0

        # Universal fallback for battery indicators
        for b_key in ("battery_percentage", "battery_state", "va_battery"):
            if b_key in kv and "battery" not in parsed:
                parsed["battery"] = kv[b_key]

        parsed["updated_at"] = datetime.datetime.now().isoformat()
        return parsed

    def refresh_device(self, dev_id):
        try:
            res = self.cloud.getstatus(dev_id)
            if res.get("success") and res.get("result"):
                parsed = self.parse_device_status(dev_id, res["result"])
                if dev_id not in self.states:
                    self.states[dev_id] = {}
                self.states[dev_id].update(parsed)
                return True
        except Exception:
            pass
        return False

    def get_camera_stream_url(self, dev_id, stream_type="HLS"):
        """Requests HLS/WebRTC streaming URL from Tuya Cloud."""
        try:
            res = self.cloud.cloudrequest(f"/v1.0/devices/{dev_id}/stream/actions/allocate", post={"type": stream_type})
            if res.get("success") and res.get("result"):
                return {"success": True, "url": res["result"].get("url")}
            return {"success": False, "code": res.get("code"), "msg": res.get("msg")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _poll_loop(self):
        # Initial cloud discovery
        if self.cloud is not None:
            self.sync_cloud_devices()
        loop_counter = 0

        while self.running:
            try:
                if self.cloud is None:
                    self.cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
                    self.sync_cloud_devices()
                cloud_ids = [d.get("id") for d in self.all_cloud_devices if isinstance(d, dict) and d.get("id")]
                all_ids = list(dict.fromkeys(list(DEVICE_REGISTRY.keys()) + list(CAMERA_REGISTRY.keys()) + cloud_ids))
                for dev_id in all_ids:
                    self.refresh_device(dev_id)
                    time.sleep(0.6)
                self._save_cache(persist_disk=(loop_counter % 30 == 0))
                self.last_update = time.time()
            except Exception as e:
                print(f"[TuyaService] Poll loop error: {e}", flush=True)

            loop_counter += 1
            if loop_counter >= 30:  # Every ~10 minutes, rescan cloud for new devices
                self.sync_cloud_devices()
                loop_counter = 0

            time.sleep(15)

    def get_structured_devices(self):
        result = {
            "lights": [],
            "climate": [],
            "ac": [],
            "ir": [],
            "solar": {},
            "battery": {},
            "plugs": [],
            "security": {},
            "cameras": [],
            "total_devices": len(self.all_cloud_devices) or 42
        }

        for dev_id, meta in DEVICE_REGISTRY.items():
            state = self.states.get(dev_id, {})
            item = {
                "id": dev_id,
                "name": meta["name"],
                "category": meta["category"],
                "icon": meta["icon"],
                "type": meta.get("type", "switch"),
                "state": state
            }
            cat = meta["category"]
            if cat == "light":
                result["lights"].append(item)
            elif cat == "climate":
                result["climate"].append(item)
            elif cat == "ac":
                result["ac"].append(item)
            elif cat == "ir":
                result["ir"].append(item)
            elif cat == "solar":
                result["solar"] = item
            elif cat == "battery":
                result["battery"] = item
            elif cat == "plug":
                result["plugs"].append(item)
            elif cat == "security":
                result["security"][meta["type"]] = item

        for dev_id, meta in CAMERA_REGISTRY.items():
            state = self.states.get(dev_id, {})
            result["cameras"].append({
                "id": dev_id,
                "name": meta["name"],
                "location": meta.get("location", "Hogar"),
                "category": "camera",
                "type": meta.get("type", "camera"),
                "icon": meta.get("icon", "videocam"),
                "online": state.get("online", True),
                "state": state
            })

        return result

    def send_command(self, dev_id, code, value):
        reg = DEVICE_REGISTRY.get(dev_id) or CAMERA_REGISTRY.get(dev_id) or next((d for d in self.all_cloud_devices if isinstance(d, dict) and d.get("id") == dev_id), None)
        if not reg:
            return {"success": False, "error": "Unknown device"}

        try:
            res = self.cloud.sendcommand(dev_id, {"commands": [{"code": code, "value": value}]})
            if res.get("success"):
                if dev_id not in self.states:
                    self.states[dev_id] = {}
                if code.startswith("switch_") and code[7:].isdigit():
                    if isinstance(self.states[dev_id].get("switches"), dict):
                        self.states[dev_id]["switches"][code] = bool(value)
                        self.states[dev_id]["state"] = any(self.states[dev_id]["switches"].values())
                    elif code == "switch_1":
                        self.states[dev_id]["state"] = bool(value)
                elif code == "switch":
                    self.states[dev_id]["state"] = bool(value)
                elif code == "master_mode":
                    self.states[dev_id]["master_mode"] = str(value)
                elif code == "temp_set":
                    v_num = float(value)
                    self.states[dev_id]["temp_set"] = round(v_num / 10.0, 1) if v_num > 100 else v_num
                elif code == "mode":
                    self.states[dev_id]["mode"] = str(value)
                self._save_cache()
                return {"success": True, "result": res.get("result")}
            return {"success": False, "error": res}
        except Exception as e:
            return {"success": False, "error": str(e)}

service = TuyaService()
