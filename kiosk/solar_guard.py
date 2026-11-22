#!/usr/bin/env python3
"""
Domos Solar Guardian - Hoymiles DTU-Pro-S Realtime Telemetry Service
Protocol: Modbus-TCP (Port 502) - STRICTLY READ-ONLY (Function Code 0x03)
Target: 192.168.1.10:502 (Hoymiles DTU-Pro-S / Microinverter HMS 4-in-1 series)
Optimized for zero interference with Hoymiles Cloud and single-socket DTU microcontrollers.
"""

import os
import sys
import time
import json
import math
import socket
import datetime
import subprocess
from pathlib import Path

DTU_IP = os.environ.get("HOYMILES_IP", "192.168.1.10")
DTU_PORT = int(os.environ.get("HOYMILES_PORT", "502"))
STATUS_FILE = Path("/tmp/domos_solar_status.json")
INCIDENTS_FILE = Path("/opt/domoskiosk/incidents.json")

def is_daylight(lat=40.4168, lon=-3.7038):
    """Calculates whether the sun is elevated enough to generate solar power."""
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

def log_incident(title, description, severity="warning"):
    try:
        incidents = []
        if INCIDENTS_FILE.exists():
            incidents = json.loads(INCIDENTS_FILE.read_text())
        new_inc = {
            "id": f"inc_solar_{int(time.time())}",
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "Paneles Solares Hoymiles",
            "severity": severity,
            "title": title,
            "description": description,
            "resolved": False
        }
        if any(i.get("source") == "Paneles Solares Hoymiles" and not i.get("resolved") for i in incidents):
            return
        incidents.insert(0, new_inc)
        INCIDENTS_FILE.write_text(json.dumps(incidents[:50], indent=2))
        subprocess.Popen(["espeak-ng", "-v", "es-es", "-s", "145", "Aviso: Las placas solares han dejado de generar en horario diurno."])
    except Exception as e:
        print("[Solar] Incident logging error:", e)

def query_modbus_block(start_reg, count, ip=DTU_IP, port=DTU_PORT, timeout=3.0):
    """
    Queries Hoymiles DTU via Modbus-TCP Function 0x03.
    Always closes the socket immediately so DTU is free for cloud communication.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        hi_reg = (start_reg >> 8) & 0xFF
        lo_reg = start_reg & 0xFF
        hi_cnt = (count >> 8) & 0xFF
        lo_cnt = count & 0xFF
        pkt = bytearray([0x00, 0x01, 0x00, 0x00, 0x00, 0x06, 0x00, 0x03, hi_reg, lo_reg, hi_cnt, lo_cnt])
        s.sendall(pkt)
        resp = s.recv(2048)
        if len(resp) >= 9 and resp[7] == 0x03:
            byte_count = resp[8]
            data = resp[9:9+byte_count]
            regs = [(data[i] << 8) | data[i+1] for i in range(0, len(data), 2)]
            return regs
        return None
    except Exception:
        return None
    finally:
        try:
            s.close()
        except Exception:
            pass

def main():
    print(f"[Solar] Domos Solar Guardian iniciado. Polling Hoymiles 4-Panel DTU en {DTU_IP}:{DTU_PORT} (Modbus-TCP Read-Only)...")
    zero_power_count = 0
    last_known_data = None
    meter_checked = False
    meter_sn = "10C014812030"
    has_meter = True

    while True:
        try:
            is_sun, elev = is_daylight()
            regs = query_modbus_block(0x1000, 80)

            # Query meter header only once or every 30 mins to avoid extra socket load
            if not meter_checked and regs:
                time.sleep(0.5)
                m_regs = query_modbus_block(0x2000, 6)
                if m_regs and len(m_regs) >= 6:
                    meter_sn = f"{m_regs[3]:04X}{m_regs[4]:04X}{m_regs[5]:04X}"
                    has_meter = True
                meter_checked = True

            if regs and len(regs) >= 71:
                # Port 1 (regs 0..19)
                p1_v = round(regs[4] / 10.0, 1)
                p1_a = round(regs[5] / 100.0, 2)
                p1_w = round(regs[9] / 10.0, 1)
                p1_wh = regs[10]

                # Port 2 (regs 20..39)
                p2_v = round(regs[24] / 10.0, 1)
                p2_a = round(regs[25] / 100.0, 2)
                p2_w = round(regs[29] / 10.0, 1)
                p2_wh = regs[30]

                # Port 3 (regs 40..59)
                p3_v = round(regs[44] / 10.0, 1)
                p3_a = round(regs[45] / 100.0, 2)
                p3_w = round(regs[49] / 10.0, 1)
                p3_wh = regs[50]

                # Port 4 (regs 60..79)
                p4_v = round(regs[64] / 10.0, 1)
                p4_a = round(regs[65] / 100.0, 2)
                p4_w = round(regs[69] / 10.0, 1)
                p4_wh = regs[70]

                # AC Grid & Inverter Temp (shared across unit)
                grid_v = round(regs[6] / 10.0, 1)
                grid_f = round(regs[7] / 100.0, 2)
                temp_c = round(regs[12] / 10.0, 1)

                total_watts = round(p1_w + p2_w + p3_w + p4_w, 1)
                total_wh = p1_wh + p2_wh + p3_wh + p4_wh
                total_amps = round(total_watts / grid_v, 2) if grid_v > 0 else 0.0
                daily_kwh = round(total_wh / 1000.0, 2)
                is_generating = total_watts > 1.0

                status_data = {
                    "watts": total_watts,
                    "volts": grid_v,
                    "amps": total_amps,
                    "frequency": grid_f,
                    "temperature_c": temp_c,
                    "inverter_sn": "1164749041",
                    "dtu_sn": "10FD74438586",
                    "meter_sn": meter_sn,
                    "has_meter": has_meter,
                    "grid_watts": 0.0,
                    "home_consumption_w": total_watts,
                    "net_surplus_w": total_watts,
                    "panel_count": 4,
                    "port1": {"volts": p1_v, "amps": p1_a, "watts": p1_w, "wh": p1_wh},
                    "port2": {"volts": p2_v, "amps": p2_a, "watts": p2_w, "wh": p2_wh},
                    "port3": {"volts": p3_v, "amps": p3_a, "watts": p3_w, "wh": p3_wh},
                    "port4": {"volts": p4_v, "amps": p4_a, "watts": p4_w, "wh": p4_wh},
                    "daily_kwh": daily_kwh,
                    "daily_wh": total_wh,
                    "switch_on": True,
                    "is_generating": is_generating,
                    "is_sun": is_sun,
                    "solar_elevation_deg": round(elev, 1),
                    "online": True,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                last_known_data = status_data
                STATUS_FILE.write_text(json.dumps(status_data, indent=2))
                print(f"[Solar] {status_data[timestamp][:19]} | Total: {total_watts} W (P1:{p1_w}W P2:{p2_w}W P3:{p3_w}W P4:{p4_w}W) | {grid_v}V | Sol: {elev:.1f}°")

                if is_sun and total_watts == 0:
                    zero_power_count += 1
                    if zero_power_count >= 4:
                        print("[Solar] ¡ALERTA! Salto de magnetotérmico o microinversor apagado en horario de sol.")
                        log_incident(
                            "Sin Producción Solar en Horario Diurno",
                            f"La producción cayó a 0 W con elevación solar de {elev:.1f}°. Revisa el cuadro eléctrico o conexión del inversor."
                        )
                else:
                    zero_power_count = 0

            else:
                if last_known_data:
                    last_known_data["online"] = is_sun
                    if not is_sun:
                        last_known_data["watts"] = 0.0
                        last_known_data["amps"] = 0.0
                        last_known_data["is_generating"] = False
                    last_known_data["timestamp"] = datetime.datetime.now().isoformat()
                    STATUS_FILE.write_text(json.dumps(last_known_data, indent=2))
                print(f"[Solar] Inversor en standby / sin respuesta (Sol: {elev:.1f}°).")

            # Polling espaciado a 30 minutos (1800s) para garantizar que la DTU no sature su socket
            # y mantenga comunicacion estable y permanente con S-Miles Cloud / app Hoymiles
            SOLAR_POLL_INTERVAL = 1800
            print(f"[Solar] Ciclo completado. Proxima lectura en {SOLAR_POLL_INTERVAL // 60} minutos.", flush=True)
            time.sleep(SOLAR_POLL_INTERVAL)

        except Exception as e:
            print("[Solar] Loop error:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()
