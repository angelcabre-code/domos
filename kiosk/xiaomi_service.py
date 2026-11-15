import json
import time
import threading
import datetime
from pathlib import Path
from miio import AirPurifier, MiotDevice

CONFIG_FILE = Path("/opt/domoskiosk/xiaomi_config.json")

VACUUM_STATUS_MAP = {
    0: "En reposo",
    1: "Inactiva",
    2: "En pausa",
    3: "Volviendo a base",
    4: "Cargando en base",
    5: "Aspirando",
    6: "Aspirando y fregando",
    7: "Fregando",
    8: "Actualizando",
}


class XiaomiService:
    def __init__(self):
        self.devices_cfg = []
        self.states = {}
        self.running = True
        self._load_config()
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                self.devices_cfg = data.get("devices", [])
            except Exception as e:
                print(f"[XiaomiService] Config error: {e}", flush=True)

    def _refresh_purifier(self, cfg):
        ap = AirPurifier(cfg["ip"], cfg["token"], model=cfg["model"])
        st = ap.status()
        mode_str = str(st.mode).split(".")[-1].lower() if st.mode else "idle"
        return {
            "online": True,
            "is_on": bool(st.is_on),
            "mode": mode_str,
            "aqi": st.aqi,
            "temperature": round(float(st.temperature), 1) if st.temperature is not None else None,
            "humidity": st.humidity,
            "filter_life": st.filter_life_remaining,
            "updated_at": datetime.datetime.now().isoformat(),
        }

    def _refresh_vacuum(self, cfg):
        vac = MiotDevice(cfg["ip"], cfg["token"])
        res = vac.send("get_properties", [
            {"did": cfg["id"], "siid": 2, "piid": 1},
            {"did": cfg["id"], "siid": 2, "piid": 2},
            {"did": cfg["id"], "siid": 3, "piid": 1},
        ])
        vals = {item.get("piid") if item.get("siid") == 2 else "bat": item.get("value") for item in res if isinstance(item, dict) and item.get("code") == 0}
        status_code = vals.get(1, 1)
        return {
            "online": True,
            "status_code": status_code,
            "status_text": VACUUM_STATUS_MAP.get(status_code, f"Estado {status_code}"),
            "is_cleaning": status_code in (5, 6, 7),
            "battery": vals.get("bat", "--"),
            "updated_at": datetime.datetime.now().isoformat(),
        }

    def refresh_one(self, cfg):
        dev_id = cfg["id"]
        try:
            if cfg["kind"] == "purifier":
                self.states[dev_id] = self._refresh_purifier(cfg)
            elif cfg["kind"] == "vacuum":
                self.states[dev_id] = self._refresh_vacuum(cfg)
        except Exception as e:
            prev = self.states.get(dev_id, {})
            prev["online"] = False
            prev["error"] = str(e)
            self.states[dev_id] = prev

    def _poll_loop(self):
        while self.running:
            for cfg in self.devices_cfg:
                self.refresh_one(cfg)
                time.sleep(0.5)
            time.sleep(15)

    def get_devices(self):
        out = []
        for cfg in self.devices_cfg:
            out.append({
                "id": cfg["id"],
                "name": cfg["name"],
                "kind": cfg["kind"],
                "model": cfg["model"],
                "ip": cfg["ip"],
                "state": self.states.get(cfg["id"], {"online": False}),
            })
        return out

    def send_command(self, dev_id, action, value=None):
        cfg = next((d for d in self.devices_cfg if d["id"] == str(dev_id)), None)
        if not cfg:
            return {"success": False, "error": "Unknown Xiaomi device"}
        try:
            if cfg["kind"] == "purifier":
                ap = AirPurifier(cfg["ip"], cfg["token"], model=cfg["model"])
                if action == "power":
                    if value:
                        ap.on()
                    else:
                        ap.off()
                elif action == "mode":
                    m_str = str(value).lower()
                    if m_str not in ("auto", "silent", "favorite"):
                        m_str = "auto"
                    ap.on()
                    ap.send("set_mode", [m_str])
                self.refresh_one(cfg)
                return {"success": True, "state": self.states.get(dev_id)}

            elif cfg["kind"] == "vacuum":
                vac = MiotDevice(cfg["ip"], cfg["token"])
                if action == "start":
                    vac.send("action", {"did": cfg["id"], "siid": 2, "aiid": 1, "in": []})
                elif action in ("pause", "stop"):
                    vac.send("action", {"did": cfg["id"], "siid": 2, "aiid": 2, "in": []})
                elif action == "home":
                    vac.send("action", {"did": cfg["id"], "siid": 3, "aiid": 1, "in": []})
                time.sleep(0.4)
                self.refresh_one(cfg)
                return {"success": True, "state": self.states.get(dev_id)}

            return {"success": False, "error": "Unsupported device kind"}
        except Exception as e:
            return {"success": False, "error": str(e)}


service = XiaomiService()
