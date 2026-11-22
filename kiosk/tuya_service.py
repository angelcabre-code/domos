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

CACHE_FILE = Path("/opt/domoskiosk/domos_live_devices.json")
ALL_DEVICES_CACHE = Path("/opt/domoskiosk/domos_all_cloud_devices.json")

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
    "bf736f7cfc729a8d8cb7eo": {
        "id": "bf736f7cfc729a8d8cb7eo",
        "name": "Detector Humo y CO Cocina",
        "category": "security",
        "icon": "detector_smoke",
        "type": "smoke_co"
    },
    "bfe5e0eee875e23682hlez": {
        "id": "bfe5e0eee875e23682hlez",
        "name": "Sensor Movimiento PIR",
        "category": "security",
        "icon": "motion_photos_on",
        "type": "pir"
    },
    "bf3f3e9f42a2a9101extac": {
        "id": "bf3f3e9f42a2a9101extac",
        "name": "Sensor Vibración Ventana",
        "category": "security",
        "icon": "vibration",
        "type": "vibration"
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
        "name": "Luz Dormitorio (IR)",
        "category": "ir",
        "icon": "lightbulb",
        "type": "infrared_light"
    }
}

class TuyaService:
    def __init__(self):
        try:
            self.cloud = None  # Disabled openapi.tuyaeu.com IoT Core to consume 0 cloud quota (using LAN + tuya_sharing MQTT)
        except Exception as e:
            print(f"[TuyaService] Deferred cloud init (network not ready): {e}", flush=True)
            self.cloud = None
        self.states = {}
        self.doorbell_ring_seq = 0
        self.doorbell_ring_ts = 0.0
        self.all_cloud_devices = []
        self.local_devices = {}
        self.last_update = 0
        self._load_local_devices()
        self._load_cache()
        self._init_sharing_sdk()
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        self.udp_thread = threading.Thread(target=self._udp_listen_loop, daemon=True)
        self.udp_thread.start()


    def _init_sharing_sdk(self):
        self.sharing_managers = []
        try:
            from tuya_sharing import Manager, SharingTokenListener, SharingDeviceListener
        except Exception as e:
            print(f"[TuyaService] tuya_sharing not available: {e}", flush=True)
            return

        service_ref = self

        class _TokenListener(SharingTokenListener):
            def __init__(self, path):
                self.path = path
            def update_token(self, token_info):
                try:
                    data = json.loads(self.path.read_text())
                    data.update(token_info)
                    self.path.write_text(json.dumps(data, indent=2))
                except Exception:
                    pass

        class _DevListener(SharingDeviceListener):
            def update_device(self, device, updated_status_properties=None, dp_timestamps=None):
                dev_id = getattr(device, "id", "")
                props = list(updated_status_properties or [])
                if dev_id in ("bf77eed8534deaf66f2xpj", "bf216abd6b1934fa11rl63", "64326051e8db8480acc0"):
                    print(f"[TuyaService] MQTT PUSH {dev_id} ({getattr(device, 'name', '')}): updated={props}", flush=True)
                service_ref._apply_sharing_device(device)
                # ONLY real-time MQTT push for actual doorbell ring (never polling, never motion)
                if dev_id == "bf77eed8534deaf66f2xpj" and props:
                    st_dict = getattr(device, "status", None) or {}
                    is_ring = False
                    if "doorbell_pic" in props:
                        is_ring = True
                    elif "doorbell_active" in props:
                        val = str(st_dict.get("doorbell_active") or "")
                        if val and val != "-1":
                            is_ring = True
                    elif "alarm_message" in props:
                        raw_msg = st_dict.get("alarm_message")
                        if raw_msg:
                            try:
                                import base64
                                decoded = base64.b64decode(raw_msg).decode("utf-8", errors="ignore")
                                parsed_msg = json.loads(decoded)
                                cmd = str(parsed_msg.get("cmd") or "").lower()
                                print(f"[TuyaService] Videoportero MQTT alarm_message cmd={cmd}", flush=True)
                                if cmd == "ipc_doorbell":
                                    is_ring = True
                            except Exception:
                                pass
                    if is_ring:
                        service_ref.doorbell_ring_seq += 1
                        service_ref.doorbell_ring_ts = time.time()
                        print(f"[TuyaService] REAL DOORBELL RING MQTT PUSH (seq={service_ref.doorbell_ring_seq}, props={props})", flush=True)
            def add_device(self, device):
                service_ref._apply_sharing_device(device)
            def remove_device(self, device_id: str):
                pass

        for auth_file in sorted(Path("/opt/domoskiosk").glob("tuya_sharing_auth*.json")):
            try:
                auth = json.loads(auth_file.read_text())
                if not auth.get("access_token"):
                    continue
                mgr = Manager(
                    auth["client_id"],
                    auth["user_code"],
                    auth["terminal_id"],
                    auth["endpoint"],
                    auth,
                    _TokenListener(auth_file)
                )
                mgr.update_device_cache()
                for dev in mgr.device_map.values():
                    dev.set_up = True
                    self._apply_sharing_device(dev)
                mgr.add_device_listener(_DevListener())
                try:
                    mgr.refresh_mq()
                    print(f"[TuyaService] Real-time MQTT Push started for {auth_file.name} ({len(mgr.device_map)} devices set_up=True)", flush=True)
                except Exception as mq_err:
                    print(f"[TuyaService] MQTT start warning for {auth_file.name}: {mq_err}", flush=True)
                self.sharing_managers.append(mgr)
                print(f"[TuyaService] Tuya Sharing SDK active from {auth_file.name}: {len(mgr.device_map)} devices", flush=True)
            except Exception as e:
                print(f"[TuyaService] Error loading {auth_file.name}: {e}", flush=True)

    def _apply_sharing_device(self, dev):
        try:
            dev_id = dev.id
            status_dict = getattr(dev, "status", {}) or {}
            status_list = [{"code": k, "value": v} for k, v in status_dict.items()]
            parse_id = "bf9cba82aabe945f4fc8q9" if dev_id == "bf29b1a036ad20f17079pv" else dev_id
            parsed = self.parse_device_status(parse_id, status_list)
            parsed["online"] = bool(getattr(dev, "online", True))
            for k in ("alarm_message", "doorbell_active", "doorbell_pic"):
                if k in status_dict:
                    parsed[k] = status_dict[k]
            if dev_id not in self.states:
                self.states[dev_id] = {}
            self.states[dev_id].update(parsed)
            # Mirror new Higrómetro Salón ID (bf29b1a036ad20f17079pv) into legacy ID (bf9cba82aabe945f4fc8q9)
            if dev_id == "bf29b1a036ad20f17079pv":
                if "bf9cba82aabe945f4fc8q9" not in self.states:
                    self.states["bf9cba82aabe945f4fc8q9"] = {}
                self.states["bf9cba82aabe945f4fc8q9"].update(parsed)
            self._save_cache(persist_disk=False)
        except Exception as e:
            print(f"[TuyaService] _apply_sharing_device err: {e}", flush=True)

    def _sync_sharing_sdk(self):
        if not getattr(self, "sharing_managers", None):
            self._init_sharing_sdk()
            return
        for mgr in self.sharing_managers:
            try:
                mgr.update_device_cache()
                for dev in mgr.device_map.values():
                    dev.set_up = True
                    self._apply_sharing_device(dev)
            except Exception as e:
                print(f"[TuyaService] _sync_sharing_sdk err: {e}", flush=True)

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
        if self.cloud is None:
            return len(self.all_cloud_devices)
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
                parsed["master_state"] = kv.get("master_state", "normal")
                raw_msg = kv.get("alarm_msg", "")
                if raw_msg:
                    try:
                        parsed["alarm_msg_text"] = base64.b64decode(raw_msg).decode("utf-16-be", errors="ignore").strip("\x00 ")
                    except Exception:
                        parsed["alarm_msg_text"] = str(raw_msg)
            elif reg.get("type") == "door":
                parsed["is_open"] = bool(kv.get("doorcontact_state", False))
                parsed["battery"] = kv.get("battery_state", "normal")
            elif reg.get("type") == "lock":
                parsed["battery"] = kv.get("battery_state", kv.get("battery_percentage", "normal"))
                parsed["battery_state"] = kv.get("battery_state", "normal")
                parsed["alarm_lock"] = kv.get("alarm_lock", "")
            elif reg.get("type") in ("motion", "pir"):
                parsed["battery"] = kv.get("battery", kv.get("battery_percentage", kv.get("battery_state", "normal")))
                parsed["pir"] = kv.get("pir", "")
            elif reg.get("type") == "vibration":
                parsed["battery"] = kv.get("battery_percentage", kv.get("battery_state", "normal"))
                parsed["vibration"] = kv.get("vibration_state", kv.get("vibration", "normal"))
            elif reg.get("type") == "smoke_co":
                smoke_st = kv.get("smoke_sensor_status", kv.get("smoke_sensor_state", "normal"))
                co_st = kv.get("co_status", kv.get("co_state", "normal"))
                parsed["smoke_status"] = smoke_st
                parsed["co_status"] = co_st
                parsed["is_alarm"] = (smoke_st == "alarm" or co_st == "alarm")
                parsed["co_ppm"] = int(kv.get("co_value", 0))
                parsed["battery"] = kv.get("battery_percentage", kv.get("battery_state", "normal"))

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

        if "battery" not in parsed or parsed["battery"] in ("--", "normal", None):
            if "battery" in kv:
                parsed["battery"] = kv["battery"]
            elif "battery_percentage" in kv:
                parsed["battery"] = kv["battery_percentage"]
            elif "battery_state" in kv:
                parsed["battery"] = kv["battery_state"]
        parsed["updated_at"] = datetime.datetime.now().isoformat()
        return parsed

    def _load_local_devices(self):
        devs_path = Path("/opt/domoskiosk/devices.json")
        if devs_path.exists():
            try:
                raw = json.loads(devs_path.read_text())
                for dev_id, info in raw.items():
                    if info.get("key"):
                        self.local_devices[dev_id] = info
                print(f"[TuyaService] Loaded {len(self.local_devices)} local LAN Tuya devices", flush=True)
            except Exception as e:
                print(f"[TuyaService] Error reading local devices: {e}", flush=True)

    def _send_local_command(self, dev_id, code, value):
        info = self.local_devices.get(dev_id)
        if not info or not info.get("ip") or not info.get("key"):
            return None
        try:
            ip = info["ip"]
            key = info["key"]
            ver = float(info.get("version", 3.4))
            d = tinytuya.OutletDevice(dev_id, ip, key, version=ver)
            d.set_socketTimeout(2.0)

            dps_id = 1
            val_to_send = value
            if code.startswith("switch_") and code[7:].isdigit():
                dps_id = int(code[7:])
            elif code == "switch":
                dps_id = 1
            elif code == "switch_usb1":
                dps_id = 7
            elif code == "temp_set":
                dps_id = 2
                val_num = float(value)
                val_to_send = int(val_num * 10) if val_num < 100 else int(val_num)
            elif code == "mode":
                dps_id = 4
            elif code == "master_mode":
                dps_id = 1
                val_to_send = str(value)

            res = d.set_status(val_to_send, dps_id)
            if res and isinstance(res, dict) and (res.get("Error") is None or "dps" in res or res.get("protocol")):
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
                elif code == "temp_set":
                    self.states[dev_id]["temp_set"] = float(value)
                elif code == "mode":
                    self.states[dev_id]["mode"] = str(value)
                self._save_cache()
                print(f"[TuyaService] Local command success for {info.get('name', dev_id)}: {code}={value}", flush=True)
                return {"success": True, "local": True, "result": res}
        except Exception as e:
            print(f"[TuyaService] Local command failed for {dev_id}: {e}", flush=True)
        return None

    def _apply_dps(self, dev_id, dps):
        if not dps or not isinstance(dps, dict):
            return
        if dev_id not in self.states:
            self.states[dev_id] = {}
        parsed = self.states[dev_id]
        info = self.local_devices.get(dev_id, {})
        reg = DEVICE_REGISTRY.get(dev_id, {})
        cat = info.get("category") or reg.get("category", "")
        dev_type = reg.get("type", "")

        if '1' in dps:
            v1 = dps['1']
            if isinstance(v1, bool):
                parsed["state"] = v1
                if "switches" in parsed and isinstance(parsed["switches"], dict):
                    parsed["switches"]["switch_1"] = v1
            elif isinstance(v1, str):
                parsed["master_mode"] = v1
                parsed["state"] = (v1 in ["arm", "armed", "home_arm", "away"])

        for i in range(2, 8):
            k = str(i)
            if k in dps and "switches" in parsed and isinstance(parsed["switches"], dict):
                if isinstance(dps[k], bool):
                    parsed["switches"][f"switch_{i}"] = bool(dps[k])

        if '19' in dps and isinstance(dps['19'], (int, float)):
            parsed["power"] = round(float(dps['19']) / 10.0, 1)
        if '20' in dps and isinstance(dps['20'], (int, float)):
            parsed["voltage"] = round(float(dps['20']) / 10.0, 1)
        if '18' in dps and isinstance(dps['18'], (int, float)):
            if cat not in ("jqbj", "wsdcg", "climate"):
                parsed["current"] = dps['18']

        if cat == "kt":
            if '1' in dps: parsed["state"] = bool(dps['1'])
            if '2' in dps:
                t_set = float(dps['2'])
                parsed["temp_set"] = round(t_set / 10.0, 1) if t_set > 100 else t_set
            if '3' in dps:
                t_cur = float(dps['3'])
                parsed["temp_current"] = round(t_cur / 10.0, 1) if t_cur > 100 else t_cur
            if '4' in dps: parsed["mode"] = str(dps['4'])

        if cat in ("jqbj", "wsdcg", "climate", "th") or dev_id in ("bf9cba82aabe945f4fc8q9", "bf2d1d67a6677da71c58y5", "bf3aa055b420138596m0cs"):
            if '1' in dps and isinstance(dps['1'], (int, float)) and cat != "kt":
                raw_t = float(dps['1'])
                parsed["temperature"] = round(raw_t / 10.0, 1) if raw_t > 100 else raw_t
            if '18' in dps and isinstance(dps['18'], (int, float)):
                raw_t = float(dps['18'])
                parsed["temperature"] = round(raw_t / 10.0, 1) if raw_t > 100 else raw_t
            if '2' in dps and isinstance(dps['2'], (int, float)):
                val2 = int(dps['2'])
                if cat == "jqbj" or dev_id == "bf3aa055b420138596m0cs":
                    parsed["ch2o"] = val2
                else:
                    parsed["humidity"] = int(round(val2 / 10.0)) if val2 > 100 else val2
            if '19' in dps and isinstance(dps['19'], (int, float)):
                val19 = int(dps['19'])
                parsed["humidity"] = int(round(val19 / 10.0)) if val19 > 100 else val19
            if '3' in dps:
                parsed["battery"] = dps['3']
            if '21' in dps: parsed["voc"] = int(dps['21'])
            if '22' in dps: parsed["co2"] = int(dps['22'])

        if cat in ("mcs", "door") or dev_type == "door" or dev_id == "bf216abd6b1934fa11rl63":
            if '1' in dps:
                v1 = dps['1']
                parsed["is_open"] = bool(v1) if isinstance(v1, bool) else (str(v1).lower() in ("true", "1", "open"))
            if '2' in dps:
                parsed["battery"] = dps['2']
            if '3' in dps:
                parsed["battery_state"] = str(dps['3'])

        if cat == "mal" or dev_id == "64326051e8db8480acc0":
            if '1' in dps: parsed["master_mode"] = str(dps['1'])
            if '16' in dps: parsed["battery"] = int(dps['16'])

        if cat in ("pir", "motion") or dev_type in ("pir", "motion"):
            if '1' in dps: parsed["pir"] = dps['1']
            if '2' in dps: parsed["battery"] = dps['2']

        if cat in ("zd", "vibration") or dev_type == "vibration":
            if '1' in dps: parsed["vibration"] = dps['1']
            if '2' in dps: parsed["battery"] = dps['2']

        parsed["online"] = True
        parsed["updated_at"] = datetime.datetime.now().isoformat()
        self._save_cache(persist_disk=False)

    def _refresh_local_device(self, dev_id):
        info = self.local_devices.get(dev_id)
        if not info or not info.get("ip") or not info.get("key"):
            return False
        try:
            ip = info["ip"]
            key = info["key"]
            ver = float(info.get("version", 3.4))
            d = tinytuya.Device(dev_id, ip, key, version=ver)
            d.set_socketTimeout(0.8)
            st = d.status()
            if st and isinstance(st, dict) and "dps" in st:
                self._apply_dps(dev_id, st["dps"])
                return True
        except Exception:
            pass
        return False

    def _udp_listen_loop(self):
        """Listens on UDP 6667 and 6666 for Tuya broadcast packets from battery & AC devices."""
        import socket, select
        sockets = []
        for port in (6667, 6666):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("", port))
                s.setblocking(False)
                sockets.append(s)
                print(f"[TuyaService] UDP listener bound on port {port}", flush=True)
            except Exception as e:
                print(f"[TuyaService] Could not bind UDP port {port}: {e}", flush=True)

        if not sockets:
            print("[TuyaService] No UDP sockets bound, listener exiting", flush=True)
            return

        while self.running:
            try:
                r, _, _ = select.select(sockets, [], [], 1.0)
                for s in r:
                    try:
                        data, addr = s.recvfrom(4096)
                        self._handle_udp_packet(data, addr)
                    except Exception:
                        pass
            except Exception as e:
                time.sleep(1)

    def _handle_udp_packet(self, data, addr):
        try:
            dec = tinytuya.decrypt_udp(data)
            if not dec:
                return
            pkt = json.loads(dec)
            dev_id = pkt.get("gwId") or pkt.get("devId")
            if not dev_id:
                return
            ip = pkt.get("ip") or addr[0]

            if dev_id in self.local_devices:
                old_ip = self.local_devices[dev_id].get("ip")
                if old_ip != ip:
                    self.local_devices[dev_id]["ip"] = ip
                    print(f"[TuyaService] Learned IP for {self.local_devices[dev_id].get('name', dev_id)}: {ip}", flush=True)

            dps = pkt.get("dps")
            if dps and isinstance(dps, dict):
                self._apply_dps(dev_id, dps)

            if dev_id in self.local_devices and self.local_devices[dev_id].get("key"):
                cat = self.local_devices[dev_id].get("category", "")
                if cat in ("mcs", "wsdcg", "pir", "zd") or dev_id in ("bf216abd6b1934fa11rl63", "bf9cba82aabe945f4fc8q9", "bf2d1d67a6677da71c58y5"):
                    threading.Thread(target=self._refresh_local_device, args=(dev_id,), daemon=True).start()
        except Exception:
            pass

    def refresh_device(self, dev_id):
        # 1. Local LAN refresh (0ms latency, zero cloud quota)
        if dev_id in self.local_devices and self.local_devices[dev_id].get("ip"):
            if self._refresh_local_device(dev_id):
                return True

        # 2. Never query cameras or local AC devices via cloud getstatus
        if dev_id in CAMERA_REGISTRY:
            return False
        info = self.local_devices.get(dev_id, {})
        reg = DEVICE_REGISTRY.get(dev_id, {})
        cat = info.get("category") or reg.get("category", "")
        # Only battery sensors and non-local cloud devices should use cloud quota
        is_battery_sensor = cat in ("mcs", "wsdcg", "pir", "zd", "jtmspro", "ywbj") or dev_id in (
            "bf216abd6b1934fa11rl63", "bf9cba82aabe945f4fc8q9", "bf2d1d67a6677da71c58y5"
        )
        if not is_battery_sensor and info.get("ip"):
            return False

        if self.cloud is None:
            return False

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
        """Requests RTSP/HLS streaming URL via Tuya Sharing SDK (0 IoT Core quota)."""
        try:
            stype = str(stream_type or "hls").lower()
            for mgr in getattr(self, "sharing_managers", []):
                if dev_id in mgr.device_map:
                    url = mgr.get_device_stream_allocate(dev_id, stype)
                    if url:
                        return {"success": True, "url": url}
            return {"success": False, "error": "Camera not found in active Tuya Sharing accounts"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _poll_loop(self):
        # Initial cloud discovery
        if self.cloud is not None:
            self.sync_cloud_devices()
        loop_counter = 0

        while self.running:
            try:
                if self.cloud is None and API_KEY and API_SECRET:
                    try:
                        self.cloud = None  # Disabled openapi.tuyaeu.com IoT Core to consume 0 cloud quota (using LAN + tuya_sharing MQTT)
                        self.sync_cloud_devices()
                    except Exception:
                        pass

                # Rapid local poll for LAN-connected devices (plugs, air sensor, lights)
                for dev_id, info in self.local_devices.items():
                    if info.get("ip") and dev_id not in CAMERA_REGISTRY:
                        self._refresh_local_device(dev_id)
                        time.sleep(0.1)

                # Sync battery sensors via Tuya Sharing SDK (every ~90s, plus instant MQTT push)
                if loop_counter % 6 == 0:
                    self._sync_sharing_sdk()

                self._save_cache(persist_disk=(loop_counter % 20 == 0))
                self.last_update = time.time()
            except Exception as e:
                print(f"[TuyaService] Poll loop error: {e}", flush=True)

            loop_counter += 1
            if loop_counter >= 60:  # Rescan devices every ~15 minutes
                if self.cloud is not None:
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

    def _send_local_ir_code(self, dev_id, code):
        ir_file = Path("/opt/domoskiosk/local_ir_codes.json")
        if not ir_file.exists():
            return None
        try:
            ir_map = json.loads(ir_file.read_text())
            entry = ir_map.get(dev_id)
            if not entry:
                return None
            buttons = entry.get("buttons", {})
            ir_code = buttons.get(code) or buttons.get("PowerToggle")
            if not ir_code:
                return None
            from tinytuya.Contrib import IRRemoteControlDevice
            hub = IRRemoteControlDevice(
                entry["hub_id"],
                entry["hub_ip"],
                entry["hub_key"],
                version=float(entry.get("hub_version", 3.3))
            )
            hub.set_socketTimeout(3.0)
            res = hub.send_button(ir_code)
            print(f"[TuyaService] Local LAN IR send_button({dev_id}, {code}) via {entry['hub_ip']} -> {res}", flush=True)
            return {"success": True, "local_ir": True, "result": res}
        except Exception as e:
            print(f"[TuyaService] Local LAN IR error ({dev_id}): {e}", flush=True)
            return {"success": False, "error": str(e)}

    def send_command(self, dev_id, code, value):
        # 0. Try saved 100% local LAN IR learned codes first (e.g. Luz Dormitorio IR)
        ir_res = self._send_local_ir_code(dev_id, code)
        if ir_res is not None:
            return ir_res

        # 1. Try local LAN execution first (zero cloud dependency, 0ms latency)
        local_res = self._send_local_command(dev_id, code, value)
        if local_res is not None:
            return local_res

        reg = DEVICE_REGISTRY.get(dev_id) or CAMERA_REGISTRY.get(dev_id) or next((d for d in self.all_cloud_devices if isinstance(d, dict) and d.get("id") == dev_id), None)
        if not reg:
            return {"success": False, "error": "Unknown device"}

        try:
            res = None
            # 2. Execute via Tuya Sharing SDK (0 IoT Core cloud quota — works for IR virtual remotes & all cloud-bridged devices)
            for mgr in getattr(self, "sharing_managers", []):
                if dev_id in getattr(mgr, "device_map", {}):
                    # Call device_repository.api.post directly to bypass tuya_sharing's duplicate-command Filter
                    # (which blocks pressing Volume+/Volume-/Channel+/Brightness+ multiple times in a row!)
                    api = getattr(getattr(mgr, "device_repository", None), "api", None)
                    if api is not None:
                        res = api.post(f"/v1.1/m/thing/{dev_id}/commands", None, {"commands": [{"code": code, "value": value}]})
                    else:
                        res = mgr.send_commands(dev_id, [{"code": code, "value": value}])
                    print(f"[TuyaService] Sharing SDK send_commands({dev_id}, {code}={value}) -> {res}", flush=True)
                    break
            if res is None and self.cloud is not None:
                res = self.cloud.sendcommand(dev_id, {"commands": [{"code": code, "value": value}]})
            if isinstance(res, dict) and res.get("success"):
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
