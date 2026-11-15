import time
import json
import base64
import math
import datetime
import subprocess
from pathlib import Path
import tinytuya

SOLAR_ID = os.environ.get("SOLAR_DEVICE_ID", "YOUR_SOLAR_DEVICE_ID")
API_REGION = "eu"
API_KEY = os.environ.get("TUYA_API_KEY", "YOUR_TUYA_API_KEY")
API_SECRET = os.environ.get("TUYA_API_SECRET", "YOUR_TUYA_API_SECRET")
STATUS_FILE = Path("/tmp/domos_solar_status.json")
INCIDENTS_FILE = Path("/opt/domoskiosk/incidents.json")

def is_daylight(lat=40.4168, lon=-3.7038):
    now = datetime.datetime.now(datetime.timezone.utc)
    day_of_year = now.timetuple().tm_yday
    decl = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    b = math.radians((360 / 365) * (day_of_year - 81))
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    solar_time = (now.hour * 60 + now.minute + now.second / 60) + (eot + 4 * lon)
    hour_angle = (solar_time / 4) - 180
    lat_r, decl_r, ha_r = math.radians(lat), math.radians(decl), math.radians(hour_angle)
    elevation = math.degrees(math.asin(math.sin(lat_r) * math.sin(decl_r) + math.cos(lat_r) * math.cos(decl_r) * math.cos(ha_r)))
    return (elevation > 8.0), elevation

def log_incident(title, description, severity="critical"):
    try:
        incidents = []
        if INCIDENTS_FILE.exists():
            incidents = json.loads(INCIDENTS_FILE.read_text())
        new_inc = {
            "id": f"inc_solar_{int(time.time())}",
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "Paneles Solares",
            "severity": severity,
            "title": title,
            "description": description,
            "resolved": False
        }
        if any(i.get("source") == "Paneles Solares" and not i.get("resolved") for i in incidents):
            return
        incidents.insert(0, new_inc)
        INCIDENTS_FILE.write_text(json.dumps(incidents[:50], indent=2))
        
        subprocess.Popen(["espeak-ng", "-v", "es-es", "-s", "145", "Atención: Las placas solares se han desconectado. Comprueba el cuadro eléctrico."])
    except Exception as e:
        print("[Solar] Incident logging error:", e)

def main():
    print("[Solar] Domos Solar Guardian iniciado.")
    c = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
    zero_power_count = 0

    while True:
        try:
            is_sun, elev = is_daylight()
            res = c.getstatus(SOLAR_ID)
            
            watts = 0
            volts = 230.0
            amps = 0.0
            switch_on = True

            if res.get("success"):
                for item in res.get("result", []):
                    code = item.get("code")
                    val = item.get("value")
                    if code == "switch":
                        switch_on = bool(val)
                    elif code == "phase_a" and val:
                        try:
                            raw = base64.b64decode(val)
                            volts = int.from_bytes(raw[0:2], "big") / 10.0
                            amps = int.from_bytes(raw[2:5], "big") / 1000.0
                            watts = int.from_bytes(raw[5:8], "big")
                        except Exception:
                            pass

                status_data = {
                    "watts": watts,
                    "volts": round(volts, 1),
                    "amps": round(amps, 3),
                    "switch_on": switch_on,
                    "is_sun": is_sun,
                    "solar_elevation_deg": round(elev, 1),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                STATUS_FILE.write_text(json.dumps(status_data, indent=2))
                print(f"[Solar] {status_data['timestamp'][:19]} | Generación: {watts} W | Tensión: {volts} V | Sol: {elev:.1f}°")

                if is_sun and (watts == 0 or not switch_on):
                    zero_power_count += 1
                    if zero_power_count >= 2:
                        print("[Solar] ¡ALERTA! Salto de magnetotérmico detectado en pleno día.")
                        log_incident(
                            "Disparo de Magnetotérmico en Placas Solares",
                            f"La generación cayó a 0 W con elevación solar de {elev:.1f}°. Revisa el cuadro eléctrico."
                        )
                else:
                    zero_power_count = 0

            time.sleep(60)

        except Exception as e:
            print("[Solar] Loop error:", e)
            time.sleep(30)

if __name__ == "__main__":
    main()
