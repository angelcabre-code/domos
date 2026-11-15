import base64
import datetime
import hashlib
import hmac
import json
import threading
import time
from pathlib import Path
import requests

CONFIG_FILE = Path("/opt/domoskiosk/ewelink_config.json")
APP_ID = "oeVkj2lYFGnJu5XUtWisfW4utiN4u9Mq"
APP_SECRET = b"6Nz4n0xA8s8qdxQf2GqurZj2Fs55FUvM"


class EwelinkService:
    def __init__(self):
        self.cfg = {}
        self.access_token = None
        self.base_url = "https://eu-apia.coolkit.cc"
        self.devices = {}
        self.lock = threading.Lock()
        self.running = True
        self._load_config()
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                self.cfg = json.loads(CONFIG_FILE.read_text())
                region = self.cfg.get("region", "eu")
                self.base_url = f"https://{region}-apia.coolkit.cc"
            except Exception as e:
                print(f"[EwelinkService] Config error: {e}", flush=True)

    def _login(self):
        if not self.cfg.get("email") or not self.cfg.get("password"):
            return False
        payload = {
            "email": self.cfg["email"],
            "password": self.cfg["password"],
            "countryCode": self.cfg.get("country_code", "+34"),
        }
        body = json.dumps(payload, separators=(",", ":"))
        sign = base64.b64encode(
            hmac.new(APP_SECRET, body.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-CK-Appid": APP_ID,
            "X-CK-Nonce": "domos123",
            "Authorization": f"Sign {sign}",
        }
        try:
            r = requests.post(f"{self.base_url}/v2/user/login", data=body, headers=headers, timeout=10)
            res = r.json()
            if res.get("error") == 0 and res.get("data", {}).get("at"):
                self.access_token = res["data"]["at"]
                return True
            print(f"[EwelinkService] Login failed: {res}", flush=True)
        except Exception as e:
            print(f"[EwelinkService] Login exception: {e}", flush=True)
        return False

    def refresh_devices(self):
        if not self.access_token and not self._login():
            return
        try:
            r = requests.get(
                f"{self.base_url}/v2/device/thing",
                headers={"X-CK-Appid": APP_ID, "Authorization": f"Bearer {self.access_token}"},
                timeout=10,
            )
            res = r.json()
            if res.get("error") in (401, 402):
                if self._login():
                    r = requests.get(
                        f"{self.base_url}/v2/device/thing",
                        headers={"X-CK-Appid": APP_ID, "Authorization": f"Bearer {self.access_token}"},
                        timeout=10,
                    )
                    res = r.json()
            if res.get("error") != 0:
                return
            now = datetime.datetime.now().isoformat()
            new_map = {}
            for item in res.get("data", {}).get("thingList", []):
                dev = item.get("itemData", {})
                dev_id = dev.get("deviceid")
                if not dev_id:
                    continue
                name = dev.get("name", dev_id)
                params = dev.get("params", {})
                is_on = params.get("switch") == "on"
                online = bool(dev.get("online", False))
                is_light = "altar" in name.lower() or "luz" in name.lower()
                new_map[dev_id] = {
                    "id": dev_id,
                    "name": name,
                    "category": "light" if is_light else "plug",
                    "icon": "lightbulb" if is_light else "power",
                    "type": "switch",
                    "source": "ewelink",
                    "online": online,
                    "state": {
                        "state": is_on,
                        "online": online,
                        "updated_at": now,
                    },
                }
            with self.lock:
                self.devices = new_map
        except Exception as e:
            print(f"[EwelinkService] Refresh error: {e}", flush=True)

    def _poll_loop(self):
        while self.running:
            self.refresh_devices()
            time.sleep(15)

    def has_device(self, dev_id: str) -> bool:
        with self.lock:
            return str(dev_id) in self.devices

    def get_structured_devices(self):
        with self.lock:
            lights = [d for d in self.devices.values() if d["category"] == "light"]
            plugs = [d for d in self.devices.values() if d["category"] == "plug"]
            return lights, plugs

    def send_command(self, dev_id: str, value):
        dev_id = str(dev_id)
        if not self.access_token and not self._login():
            return {"success": False, "error": "eWeLink auth failed"}
        on_val = bool(value) if not isinstance(value, str) else value.lower() in ("true", "1", "on")
        switch_str = "on" if on_val else "off"
        payload = {"type": 1, "id": dev_id, "params": {"switch": switch_str}}
        headers = {
            "Content-Type": "application/json",
            "X-CK-Appid": APP_ID,
            "Authorization": f"Bearer {self.access_token}",
        }
        try:
            r = requests.post(
                f"{self.base_url}/v2/device/thing/status",
                json=payload,
                headers=headers,
                timeout=10,
            )
            res = r.json()
            if res.get("error") in (401, 402) and self._login():
                headers["Authorization"] = f"Bearer {self.access_token}"
                r = requests.post(
                    f"{self.base_url}/v2/device/thing/status",
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
                res = r.json()
            if res.get("error") == 0:
                with self.lock:
                    if dev_id in self.devices:
                        self.devices[dev_id]["state"]["state"] = on_val
                        self.devices[dev_id]["state"]["updated_at"] = datetime.datetime.now().isoformat()
                return {"success": True, "result": res}
            return {"success": False, "error": res.get("msg", "eWeLink error"), "raw": res}
        except Exception as e:
            return {"success": False, "error": str(e)}


service = EwelinkService()
