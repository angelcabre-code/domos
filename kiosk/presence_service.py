import os
import sys
import time
import math
import json
import signal
import asyncio
import datetime
import subprocess
from pathlib import Path

CONFIG_FILE = Path("/opt/domoskiosk/presence_config.json")
WAKE_TRIGGER_FILE = Path("/tmp/domos_wake_trigger")
STATUS_EXPORT_FILE = Path("/tmp/domos_presence_status.json")

class DomosPresenceManager:
    def __init__(self):
        self.running = True
        self.wake_until = 0.0
        self.current_brightness = self.get_actual_brightness()
        self.config = self.load_config()
        self.tuya_devices = {}
        self.device_states = {
            "kitchen_light_1": False,
            "kitchen_light_2": False,
            "alarm_armed": False
        }
        self.power_outage = False
        self.net_down = False
        self._net_fail_count = 0

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Presence] Error loading config: {e}")
        return {
            "location": {"latitude": 40.4168, "longitude": -3.7038, "civil_twilight_threshold_deg": -6.0},
            "behavior": {"wake_duration_seconds": 180, "day_brightness": 75, "night_active_brightness": 45, "night_off_brightness": 0, "fade_duration_seconds": 1.0},
            "devices": {}
        }

    def get_actual_brightness(self):
        try:
            cur = int(subprocess.check_output(["brightnessctl", "get"], text=True).strip())
            max_b = int(subprocess.check_output(["brightnessctl", "max"], text=True).strip())
            return int(round((cur / max_b) * 100))
        except Exception:
            return 80

    def set_actual_brightness(self, pct):
        try:
            pct = max(0, min(100, int(round(pct))))
            subprocess.run(["brightnessctl", "set", f"{pct}%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.current_brightness = pct
        except Exception as e:
            print(f"[Presence] Error setting brightness: {e}")

    def fade_to_brightness(self, target_pct, duration=1.0):
        target_pct = max(0, min(100, int(round(target_pct))))
        start_pct = self.current_brightness
        if start_pct == target_pct:
            return

        steps = 15
        delay = duration / steps
        for step in range(1, steps + 1):
            fraction = step / steps
            interpolated = start_pct + (target_pct - start_pct) * fraction
            self.set_actual_brightness(interpolated)
            time.sleep(delay)
        self.set_actual_brightness(target_pct)

    def is_daylight(self):
        loc = self.config.get("location", {})
        lat = loc.get("latitude", 40.4168)
        lon = loc.get("longitude", -3.7038)
        threshold = loc.get("civil_twilight_threshold_deg", -6.0)

        now = datetime.datetime.now(datetime.timezone.utc)
        day_of_year = now.timetuple().tm_yday
        decl = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
        b = math.radians((360 / 365) * (day_of_year - 81))
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        solar_time = (now.hour * 60 + now.minute + now.second / 60) + (eot + 4 * lon)
        hour_angle = (solar_time / 4) - 180
        lat_r, decl_r, ha_r = math.radians(lat), math.radians(decl), math.radians(hour_angle)
        elevation = math.degrees(math.asin(math.sin(lat_r) * math.sin(decl_r) + math.cos(lat_r) * math.cos(decl_r) * math.cos(ha_r)))

        return (elevation > threshold), elevation

    def check_wake_trigger(self):
        if WAKE_TRIGGER_FILE.exists():
            try:
                wake_seconds = float(WAKE_TRIGGER_FILE.read_text().strip())
                self.wake_until = time.time() + wake_seconds
                WAKE_TRIGGER_FILE.unlink(missing_ok=True)
                print(f"[Presence] Wake triggered for {wake_seconds}s")
            except Exception:
                WAKE_TRIGGER_FILE.unlink(missing_ok=True)

    def poll_tuya_devices(self):
        """Polls local Tuya status if keys are configured in presence_config.json"""
        dev_cfg = self.config.get("devices", {})
        import tinytuya

        for key, name in [("kitchen_light_1", "Luz Cocina 1"), ("kitchen_light_2", "Luz Cocina 2")]:
            d = dev_cfg.get(key, {})
            dev_id = d.get("id")
            dev_key = d.get("key")
            dev_ip = d.get("ip")
            if dev_id and dev_key:
                try:
                    client = tinytuya.OutletDevice(dev_id, dev_ip or "auto", dev_key)
                    client.set_version(float(d.get("version", 3.3)))
                    status = client.status()
                    if "dps" in status:
                        is_on = bool(status["dps"].get("1") or status["dps"].get("20"))
                        self.device_states[key] = is_on
                except Exception:
                    pass

        # Alarm
        alarm_cfg = dev_cfg.get("alarm_system", {})
        if alarm_cfg.get("id") and alarm_cfg.get("key"):
            try:
                client = tinytuya.Device(alarm_cfg["id"], alarm_cfg.get("ip", "auto"), alarm_cfg["key"])
                client.set_version(float(alarm_cfg.get("version", 3.3)))
                status = client.status()
                if "dps" in status:
                    dps_val = str(status["dps"].get("1", "")).lower()
                    self.device_states["alarm_armed"] = (dps_val in ["arm", "armed", "away", "true"])
            except Exception:
                pass

    def check_power_and_internet(self):
        import socket
        import urllib.request

        # 1. Internet connectivity check (TCP 1.1.1.1:53 or 8.8.8.8:53)
        net_ok = False
        for host in ("1.1.1.1", "8.8.8.8"):
            try:
                with socket.create_connection((host, 53), timeout=1.5):
                    net_ok = True
                    break
            except Exception:
                pass
        if net_ok:
            self._net_fail_count = 0
            self.net_down = False
        else:
            self._net_fail_count += 1
            if self._net_fail_count >= 2:
                self.net_down = True

        # 2. Power outage check via local Domos devices (mains voltage & charger plug)
        outage = False
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/api/devices", timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                volts = (data.get("solar") or {}).get("state", {}).get("volts")
                if isinstance(volts, (int, float)) and volts < 50:
                    outage = True
                if not outage:
                    plug = next((p for p in (data.get("plugs") or []) if p.get("id") == self.config.get("charger_plug_id", "charger_plug")), None)
                    if plug and (plug.get("state") or {}).get("state") is True:
                        bats = list(Path("/sys/class/power_supply").glob("BAT*"))
                        if bats:
                            st = (bats[0] / "status").read_text().strip()
                            if st == "Discharging":
                                outage = True
        except Exception:
            pass
        self.power_outage = outage

    def evaluate_target_brightness(self):
        now = time.time()
        beh = self.config.get("behavior", {})
        day_b = beh.get("day_brightness", 75)
        night_act_b = beh.get("night_active_brightness", 45)
        night_off_b = beh.get("night_off_brightness", 0)

        # 1. Active User Touch / Voice Wake override
        if now < self.wake_until:
            is_day, elev = self.is_daylight()
            return (day_b if is_day else night_act_b), f"Interacción activa ({int(self.wake_until - now)}s restantes)"

        # 1b. Power Outage or Internet Loss -> Save battery (Screen 0%, touch wakes)
        if self.power_outage or self.net_down:
            why = "Corte eléctrico detectado" if self.power_outage else "Sin conexión a Internet"
            return night_off_b, f"{why} -> Pantalla Apagada 0% (toca para activar)"

        # 2. Alarm Armed -> Nobody at home -> Screen 0%
        if self.device_states.get("alarm_armed", False):
            return night_off_b, "Alarma Armada (Casa Vacía -> Pantalla Apagada 0%)"

        # 3. Daylight check
        is_day, elev = self.is_daylight()
        if is_day:
            return day_b, f"Luz Solar Diurna (Elevación: {elev:.1f}° -> Pantalla Encendida)"

        # 4. Nighttime: Check kitchen lights
        l1 = self.device_states.get("kitchen_light_1", False)
        l2 = self.device_states.get("kitchen_light_2", False)

        if l1 or l2:
            return night_act_b, f"Noche + Cocina en uso (Luz 1: {l1}, Luz 2: {l2} -> Pantalla Encendida Suave)"
        else:
            return night_off_b, f"Noche + Luces Cocina apagadas (Modo Sueño -> Pantalla 0% Apagada)"

    def export_status(self, target_b, reason, elev):
        is_day, _ = self.is_daylight()
        status_data = {
            "current_brightness": self.current_brightness,
            "target_brightness": target_b,
            "reason": reason,
            "solar_elevation_deg": round(elev, 2),
            "is_daylight": is_day,
            "wake_seconds_left": max(0, int(self.wake_until - time.time())),
            "power_outage": self.power_outage,
            "net_down": self.net_down,
            "devices": self.device_states,
            "timestamp": datetime.datetime.now().isoformat()
        }
        try:
            with open(STATUS_EXPORT_FILE, "w") as f:
                json.dump(status_data, f, indent=2)
        except Exception:
            pass

    def run(self):
        print("[Presence] Domos Presence & Smart Backlight Manager arrancado.")
        poll_counter = 0

        while self.running:
            try:
                if poll_counter % 15 == 0:
                    self.config = self.load_config()

                if poll_counter % 3 == 0:
                    self.poll_tuya_devices()
                    self.check_power_and_internet()

                self.check_wake_trigger()
                target_b, reason = self.evaluate_target_brightness()
                _, elev = self.is_daylight()

                if abs(self.current_brightness - target_b) >= 2:
                    print(f"[Presence] Ajustando brillo: {self.current_brightness}% -> {target_b}% | Motivo: {reason}")
                    fade_sec = self.config.get("behavior", {}).get("fade_duration_seconds", 1.0)
                    self.fade_to_brightness(target_b, duration=fade_sec)

                self.export_status(target_b, reason, elev)

                poll_counter += 1
                time.sleep(1.5)

            except Exception as e:
                print(f"[Presence] Loop error: {e}")
                time.sleep(2)

    def stop(self, *args):
        print("[Presence] Deteniendo servicio...")
        self.running = False

if __name__ == "__main__":
    manager = DomosPresenceManager()
    signal.signal(signal.SIGINT, manager.stop)
    signal.signal(signal.SIGTERM, manager.stop)
    manager.run()
