#!/usr/bin/env python3
"""
Domos Solar Cloud Sync - Hoymiles S-Miles Cloud API Integration
Syncs solar generation, per-port microinverter telemetry via Protobuf charts,
and CHINT meter data directly from Hoymiles S-Miles Cloud.
Zero local Modbus polling to DTU-Pro-S.
"""

import os
import sys
import time
import json
import math
import base64
import hashlib
import datetime
import requests
from pathlib import Path

# Load chart protobuf decoder
try:
    from chart_pb import decode_line_chart
except ImportError:
    try:
        import sys
        sys.path.append("/opt/domoskiosk")
        from chart_pb import decode_line_chart
    except ImportError:
        decode_line_chart = None

CONFIG_FILE = Path("/opt/domoskiosk/hoymiles_config.json")
STATUS_FILE = Path("/tmp/domos_solar_status.json")
INCIDENTS_FILE = Path("/opt/domoskiosk/incidents.json")
BASE_URL = "https://neapi.hoymiles.com"

# Default coordinates: La Cala del Moral, Málaga (36.7196° N, 4.3033° W)
LAT = 36.7196
LON = -4.3033

def is_daylight(lat=LAT, lon=LON):
    now = datetime.datetime.now(datetime.timezone.utc)
    day_of_year = now.timetuple().tm_yday
    decl = 23.45 * math.sin(math.radians((360.0 / 365.0) * (day_of_year - 81)))
    b = math.radians((360.0 / 365.0) * (day_of_year - 81))
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    solar_time = (now.hour * 60 + now.minute + now.second / 60.0) + (eot + 4 * lon)
    hour_angle = (solar_time / 4.0) - 180.0
    lat_r, decl_r, ha_r = math.radians(lat), math.radians(decl), math.radians(hour_angle)
    elevation = math.degrees(math.asin(math.sin(lat_r) * math.sin(decl_r) + math.cos(lat_r) * math.cos(decl_r) * math.cos(ha_r)))
    return (elevation > 1.0), elevation

def log_incident(title, description, severity="warning"):
    try:
        incidents = []
        if INCIDENTS_FILE.exists():
            incidents = json.loads(INCIDENTS_FILE.read_text())
        new_inc = {
            "id": f"inc_solar_{int(time.time())}",
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "Paneles Solares Hoymiles Cloud",
            "severity": severity,
            "title": title,
            "description": description,
            "resolved": False
        }
        if any(i.get("source") == "Paneles Solares Hoymiles Cloud" and not i.get("resolved") for i in incidents):
            return
        incidents.insert(0, new_inc)
        INCIDENTS_FILE.write_text(json.dumps(incidents[:50], indent=2))
    except Exception as e:
        print(f"[CloudSync] Incident log error: {e}")

class HoymilesCloudSync:
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.config = self._load_config()
        self.token = None
        self.token_expiry = 0
        self.last_known_data = None
        self._load_previous_state()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file {self.config_path} not found.")
        return json.loads(self.config_path.read_text())

    def _load_previous_state(self):
        if STATUS_FILE.exists():
            try:
                self.last_known_data = json.loads(STATUS_FILE.read_text())
            except Exception:
                pass

    def login(self):
        username = self.config.get("username")
        password = self.config.get("password")
        print(f"[CloudSync] Authenticating {username} on Hoymiles Cloud API (v3)...")

        # 1. Pre-inspection
        r_insp = requests.post(
            f"{BASE_URL}/iam/pub/3/auth/pre-insp",
            json={"u": username},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if r_insp.status_code != 200:
            raise RuntimeError(f"Pre-inspection failed: HTTP {r_insp.status_code}")
        nonce = r_insp.json().get("data", {}).get("n")
        if not nonce:
            raise RuntimeError("No nonce received in pre-inspection")

        # 2. Hash calculation: md5(pwd).base64(sha256(pwd))
        md5_p = hashlib.md5(password.encode()).hexdigest()
        sha256_p = hashlib.sha256(password.encode())
        ch = f"{md5_p}.{base64.b64encode(sha256_p.digest()).decode()}"

        # 3. Login
        r_login = requests.post(
            f"{BASE_URL}/iam/pub/3/auth/login",
            json={"u": username, "ch": ch, "n": nonce},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        data = r_login.json()
        if data.get("status") == "0":
            self.token = data.get("data", {}).get("token")
            self.token_expiry = time.time() + 6300
            print("[CloudSync] Authentication successful! Token active.")
            return self.token
        raise RuntimeError(f"Login rejected: {data}")

    def ensure_authenticated(self):
        if not self.token or time.time() >= self.token_expiry:
            self.login()

    def _auth_headers(self, accept_protobuf=False):
        accept_type = "application/x-protobuf, application/octet-stream, */*" if accept_protobuf else "application/json"
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": accept_type,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DomosCloudSync/2.0"
        }

    def fetch_station_telemetry(self):
        self.ensure_authenticated()
        sid = self.config.get("station_id", 401540)
        mi_id = self.config.get("inverter_id", 1969430)
        headers = self._auth_headers()

        # 1. Real time summary
        r_rt = requests.post(
            f"{BASE_URL}/pvm-data/api/0/station/data/count_station_real_data",
            json={"sid": sid},
            headers=headers,
            timeout=10
        )
        if r_rt.status_code == 401 or r_rt.json().get("status") in ("1", "401"):
            print("[CloudSync] Token expired during query, re-authenticating...")
            self.login()
            headers = self._auth_headers()
            r_rt = requests.post(
                f"{BASE_URL}/pvm-data/api/0/station/data/count_station_real_data",
                json={"sid": sid},
                headers=headers,
                timeout=10
            )

        rt_data = r_rt.json().get("data", {})
        today_eq_wh = float(rt_data.get("today_eq", 0.0) or 0.0)
        daily_kwh = round(today_eq_wh / 1000.0, 2)
        real_power_w = float(rt_data.get("real_power", 0.0) or 0.0)

        reflux = rt_data.get("reflux_station_data", {})
        grid_power_w = float(reflux.get("grid_power", 0.0) or 0.0)
        load_power_w = float(reflux.get("load_power", 0.0) or 0.0)

        # 2. Grid Indicators (type 2)
        grid_v = 238.0
        grid_f = 50.0
        grid_meter_connected = False
        try:
            r_grid = requests.post(
                f"{BASE_URL}/pvm-data/api/0/indicators/data/select_real_indicators_data",
                json={"sid": sid, "type": 2},
                headers=headers,
                timeout=8
            )
            g_list = r_grid.json().get("data", {}).get("list", [])
            for item in g_list:
                key = item.get("key")
                val = item.get("val")
                if key == "grid_state" and str(val) == "1":
                    grid_meter_connected = True
                elif key == "v_a" and val and val != "-":
                    try:
                        v = float(val)
                        if v > 100: grid_v = round(v, 1)
                    except ValueError: pass
                elif key == "grid_f" and val and val != "-":
                    try:
                        f = float(val)
                        if 40 <= f <= 65: grid_f = round(f, 2)
                    except ValueError: pass
        except Exception as e:
            print(f"[CloudSync] Grid indicators notice: {e}")

        # 3. Individual Panel Telemetry (Protobuf Chart per Port)
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        headers_pb = self._auth_headers(accept_protobuf=True)
        ports_data = {}

        if decode_line_chart:
            for port in range(1, 5):
                prev_port = (self.last_known_data or {}).get(f"port{port}", {})
                p_w = prev_port.get("watts", 0.0)
                p_v = prev_port.get("volts", 40.0)
                p_i = prev_port.get("amps", 0.0)
                try:
                    payload = {
                        "sid": sid,
                        "date": today_str,
                        "mi_list": [{"id": mi_id, "port": port}],
                        "quota": ["MODULE_POWER", "MODULE_V", "MODULE_I"]
                    }
                    r_chart = requests.post(
                        f"{BASE_URL}/pvm-data/api/0/module/data/count_by_day",
                        json=payload,
                        headers=headers_pb,
                        timeout=5
                    )
                    if len(r_chart.content) > 0:
                        chart = decode_line_chart(r_chart.content)
                        for s in chart.get("series", []):
                            t = s.get("type")
                            d = s.get("data", [])
                            if t == "MODULE_POWER" and d:
                                p_w = round(d[-1], 1)
                            elif t == "MODULE_V" and d:
                                p_v = round(d[-1], 1)
                            elif t == "MODULE_I" and d:
                                p_i = round(d[-1], 2)
                except Exception as e:
                    print(f"[CloudSync] Port {port} chart notice: {e}")

                ports_data[f"port{port}"] = {
                    "watts": p_w,
                    "volts": p_v,
                    "amps": p_i,
                    "wh": prev_port.get("wh", int(today_eq_wh / 4.0))
                }
        else:
            for port in range(1, 5):
                prev_port = (self.last_known_data or {}).get(f"port{port}", {})
                ports_data[f"port{port}"] = {
                    "watts": prev_port.get("watts", 0.0),
                    "volts": prev_port.get("volts", 40.0),
                    "amps": prev_port.get("amps", 0.0),
                    "wh": prev_port.get("wh", int(today_eq_wh / 4.0))
                }

        # Actual sum of individual panels
        sum_panel_watts = round(sum(ports_data[f"port{p}"]["watts"] for p in range(1, 5)), 1)
        if sum_panel_watts > 0:
            total_solar_w = sum_panel_watts
        else:
            total_solar_w = real_power_w

        is_sun, elev = is_daylight()
        is_generating = total_solar_w > 1.0

        # CHINT Meter Status:
        # The CHINT meter is only considered active and measuring live house load
        # if load_power_w > 0 or grid_meter_connected is True with grid_power_w != 0.
        meter_has_live_reading = False
        if load_power_w > 0:
            meter_has_live_reading = True
            home_consumption_w = load_power_w
            net_surplus_w = round(total_solar_w - home_consumption_w, 1)
        elif grid_power_w != 0.0 and grid_meter_connected:
            meter_has_live_reading = True
            net_surplus_w = round(-grid_power_w, 1)
            home_consumption_w = max(0.0, round(total_solar_w - net_surplus_w, 1))
        else:
            # Meter is in standby or not transmitting live kW to S-Cloud.
            # Do NOT claim fake grid export or fake total house consumption!
            meter_has_live_reading = False
            home_consumption_w = 0.0
            net_surplus_w = 0.0

        amps_ac = round(total_solar_w / grid_v, 2) if grid_v > 0 else 0.0

        status_data = {
            "watts": total_solar_w,
            "volts": grid_v,
            "amps": amps_ac,
            "frequency": grid_f,
            "temperature_c": (self.last_known_data or {}).get("temperature_c", 34.6),
            "inverter_sn": self.config.get("inverter_sn", "116474904118")[:10],
            "dtu_sn": self.config.get("dtu_sn", "10FD74438586"),
            "meter_sn": self.config.get("meter_sn", "10C014812030"),
            "has_meter": bool(self.config.get("meter_sn")),
            "meter_online": meter_has_live_reading,
            "grid_watts": round(grid_power_w, 1) if meter_has_live_reading else 0.0,
            "home_consumption_w": home_consumption_w,
            "net_surplus_w": net_surplus_w,
            "panel_count": 4,
            "port1": ports_data["port1"],
            "port2": ports_data["port2"],
            "port3": ports_data["port3"],
            "port4": ports_data["port4"],
            "daily_kwh": daily_kwh,
            "daily_wh": int(today_eq_wh),
            "switch_on": True,
            "is_generating": is_generating,
            "is_sun": is_sun,
            "solar_elevation_deg": round(elev, 1),
            "online": True,
            "source": "hoymiles_cloud_api",
            "station_id": sid,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Atomic write
        tmp_file = STATUS_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(status_data, indent=2))
        os.replace(tmp_file, STATUS_FILE)
        self.last_known_data = status_data

        ts = status_data["timestamp"][:19]
        p1 = ports_data['port1']['watts']
        p2 = ports_data['port2']['watts']
        p3 = ports_data['port3']['watts']
        p4 = ports_data['port4']['watts']
        print(f"[CloudSync] {ts} | Solar: {total_solar_w}W (P1:{p1}W P2:{p2}W P3:{p3}W P4:{p4}W) | Hoy: {daily_kwh}kWh | CHINT: {meter_has_live_reading} | Sol: {elev:.1f}°")
        return status_data

    def run_loop(self):
        interval = int(self.config.get("poll_interval_seconds", 60))
        print(f"[CloudSync] Loop running every {interval}s. Hoymiles Cloud -> Domos Kiosk.")
        while True:
            try:
                self.fetch_station_telemetry()
            except Exception as e:
                print(f"[CloudSync] Error in sync cycle: {e}")
                if self.last_known_data:
                    self.last_known_data["timestamp"] = datetime.datetime.now().isoformat()
                    try:
                        STATUS_FILE.write_text(json.dumps(self.last_known_data, indent=2))
                    except Exception: pass
            time.sleep(interval)

if __name__ == "__main__":
    sync = HoymilesCloudSync()
    if "--once" in sys.argv:
        res = sync.fetch_station_telemetry()
        print(json.dumps(res, indent=2))
    else:
        sync.run_loop()
