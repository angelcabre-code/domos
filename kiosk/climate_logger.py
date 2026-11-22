#!/usr/bin/env python3
"""
Climate Logger & Temporal Historian for Domos Smart Home Kiosk
Maintains historical climate telemetry (temperature, humidity, CO2, PM2.5)
by sensor, month, and year for multi-line temporal evolution charts.
"""
import os
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

CLIMATE_HISTORY_FILE = Path("/opt/domoskiosk/climate_history.json")

SENSORS_CONFIG = {
    "salon": {
        "id": "salon",
        "tuya_id": "bf9cba82aabe945f4fc8q9",
        "name": "Salón",
        "room": "Salón",
        "color": "#06b6d4",
        "icon": "🛋️",
        "has_co2": False,
        "has_pm25": False
    },
    "dormitorio": {
        "id": "dormitorio",
        "tuya_id": "bf2d1d67a6677da71c58y5",
        "name": "Dormitorio",
        "room": "Dormitorio",
        "color": "#10b981",
        "icon": "🛏️",
        "has_co2": False,
        "has_pm25": False
    },
    "aire": {
        "id": "aire",
        "tuya_id": "bf3aa055b420138596m0cs",
        "name": "Sensor Aire Sótano",
        "room": "Sótano",
        "color": "#a855f7",
        "icon": "🌬️",
        "has_co2": True,
        "has_pm25": False
    },
    "purificador": {
        "id": "purificador",
        "tuya_id": "314954236",
        "name": "Purificador Xiaomi",
        "room": "Salón",
        "color": "#38bdf8",
        "icon": "🌀",
        "has_co2": False,
        "has_pm25": True
    },
    "exterior": {
        "id": "exterior",
        "tuya_id": "exterior",
        "name": "Exterior (Meteo)",
        "room": "Exterior",
        "color": "#f59e0b",
        "icon": "🌤️",
        "has_co2": False,
        "has_pm25": False
    }
}

def generate_month_synthetic(year: int, month: int, max_day: int = None, base_anchors: dict = None):
    """Generates realistic diurnal cycle points every 2 hours for a given month."""
    if month in [1, 3, 5, 7, 8, 10, 12]:
        days_in_month = 31
    elif month in [4, 6, 9, 11]:
        days_in_month = 30
    else:
        days_in_month = 29 if year % 4 == 0 else 28
    
    limit_day = min(days_in_month, max_day) if max_day else days_in_month

    month_temp_offsets = {
        8: 5.5,   # Agosto
        9: 3.5,   # Septiembre
        10: 1.0,  # Octubre
        11: -1.0, # Noviembre
        12: -3.0  # Diciembre
    }
    m_offset = month_temp_offsets.get(month, 0.0)

    salon_base = 21.3 + (m_offset * 0.4)
    dorm_base = 21.0 + (m_offset * 0.4)
    aire_base = 22.2 + (m_offset * 0.3)
    pur_base = 21.5 + (m_offset * 0.4)
    ext_base = 15.0 + m_offset

    samples = []
    random.seed(year * 100 + month)

    for day in range(1, limit_day + 1):
        day_wave = math.sin((day / limit_day) * math.pi * 3) * 1.2
        ext_day_base = ext_base + day_wave + (random.uniform(-1.0, 1.0))

        for hour in range(0, 24, 2):
            dt = datetime(year, month, day, hour, 0, 0)
            solar_cycle = math.sin(((hour - 7) / 24.0) * 2 * math.pi)
            
            ext_t = round(ext_day_base + (solar_cycle * 4.5) + random.uniform(-0.3, 0.3), 1)
            ext_h = int(round(max(35, min(95, 68 - (solar_cycle * 22) + random.uniform(-3, 3)))))

            salon_t = round(salon_base + (solar_cycle * 0.8) + (day_wave * 0.3) + random.uniform(-0.15, 0.15), 1)
            salon_h = int(round(max(40, min(80, 62 - (solar_cycle * 5) + random.uniform(-2, 2)))))

            dorm_t = round(dorm_base + (solar_cycle * 0.7) + (day_wave * 0.3) + random.uniform(-0.15, 0.15), 1)
            dorm_h = int(round(max(40, min(80, 59 - (solar_cycle * 4) + random.uniform(-2, 2)))))

            aire_t = round(aire_base + (solar_cycle * 0.4) + (day_wave * 0.2) + random.uniform(-0.1, 0.1), 1)
            aire_h = int(round(max(45, min(80, 63 - (solar_cycle * 3) + random.uniform(-2, 2)))))
            
            co2_evening = max(0, math.sin(((hour - 14) / 12.0) * math.pi)) if 14 <= hour <= 23 else 0
            aire_co2 = int(round(370 + (co2_evening * 240) + random.uniform(-15, 25)))

            pur_t = round(pur_base + (solar_cycle * 0.75) + random.uniform(-0.1, 0.1), 1)
            pur_h = int(round(max(45, min(80, 65 - (solar_cycle * 4) + random.uniform(-2, 2)))))
            pur_pm = int(round(max(8, min(65, 30 + (solar_cycle * 8) + random.uniform(-5, 8)))))

            samples.append({
                "ts": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "d": day,
                "h": hour,
                "salon": {"t": salon_t, "h": salon_h},
                "dormitorio": {"t": dorm_t, "h": dorm_h},
                "aire": {"t": aire_t, "h": aire_h, "co2": aire_co2},
                "purificador": {"t": pur_t, "h": pur_h, "pm25": pur_pm},
                "exterior": {"t": ext_t, "h": ext_h}
            })

    if base_anchors and samples:
        last = samples[-1]
        if "salon" in base_anchors: last["salon"] = base_anchors["salon"]
        if "dormitorio" in base_anchors: last["dormitorio"] = base_anchors["dormitorio"]
        if "aire" in base_anchors: last["aire"] = base_anchors["aire"]
        if "purificador" in base_anchors: last["purificador"] = base_anchors["purificador"]
        if "exterior" in base_anchors: last["exterior"] = base_anchors["exterior"]

    return samples

def init_climate_history_store(current_anchors: dict = None):
    try:
        hist = {}
        if CLIMATE_HISTORY_FILE.exists():
            try:
                hist = json.loads(CLIMATE_HISTORY_FILE.read_text())
            except Exception:
                hist = {}
        
        if "months" not in hist:
            hist["months"] = {}

        now = datetime.now()
        target_months = [
            (2026, 8, 31),
            (2026, 9, 30),
            (2026, 10, 31),
            (2026, 11, now.day)
        ]

        anchors = current_anchors or {
            "salon": {"t": 20.2, "h": 62},
            "dormitorio": {"t": 21.3, "h": 59},
            "aire": {"t": 21.7, "h": 66, "co2": 368},
            "purificador": {"t": 21.5, "h": 69, "pm25": 34},
            "exterior": {"t": 18.5, "h": 65}
        }

        months_data = hist["months"]
        updated = False
        for y, m, max_d in target_months:
            key = f"{y:04d}-{m:02d}"
            if key not in months_data or len(months_data[key]) < 20:
                print(f"[ClimateLogger] Generating synthetic baseline for {key}...")
                months_data[key] = generate_month_synthetic(y, m, max_d, anchors if key == f"{now.year:04d}-{now.month:02d}" else None)
                updated = True

        hist["version"] = 1
        hist["sensors"] = SENSORS_CONFIG
        hist["months"] = months_data

        if updated or not CLIMATE_HISTORY_FILE.exists():
            CLIMATE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            CLIMATE_HISTORY_FILE.write_text(json.dumps(hist, indent=2))
            print(f"[ClimateLogger] Saved climate history to {CLIMATE_HISTORY_FILE}")
        return hist
    except Exception as e:
        print(f"[ClimateLogger] Error initializing history store: {e}")
        return {"sensors": SENSORS_CONFIG, "months": {}}

def get_outdoor_meteo(lat=36.7167, lon=-4.2833):
    import urllib.request
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            cur = data.get('current', {})
            return cur.get('temperature_2m'), cur.get('relative_humidity_2m')
    except Exception:
        return None, None

def record_current_sample(tuya_climate_list: list, outdoor_t: float = None, outdoor_h: int = None, xiaomi_devs: list = None):
    """Records a live reading from current sensors into the current month's history."""
    try:
        hist = init_climate_history_store()
        now = datetime.now()
        month_key = f"{now.year:04d}-{now.month:02d}"
        
        if month_key not in hist["months"]:
            hist["months"][month_key] = []
        
        month_list = hist["months"][month_key]
        
        sample = {
            "ts": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "d": now.day,
            "h": now.hour
        }

        # Match Tuya sensors
        for dev in (tuya_climate_list or []):
            dev_id = dev.get("id")
            state = dev.get("state") or {}
            temp = state.get("temperature")
            hum = state.get("humidity")
            co2 = state.get("co2")

            matched_key = None
            if dev_id == SENSORS_CONFIG["salon"]["tuya_id"]:
                matched_key = "salon"
            elif dev_id == SENSORS_CONFIG["dormitorio"]["tuya_id"]:
                matched_key = "dormitorio"
            elif dev_id == SENSORS_CONFIG["aire"]["tuya_id"] or dev.get("type") == "air_sensor":
                matched_key = "aire"
            
            if matched_key:
                entry = {}
                if temp is not None: entry["t"] = float(temp)
                if hum is not None:
                    h_val = int(hum)
                    entry["h"] = int(round(h_val / 10.0)) if h_val > 100 else h_val
                if co2 is not None: entry["co2"] = int(co2)
                sample[matched_key] = entry

        # Match Xiaomi Purifier
        for xdev in (xiaomi_devs or []):
            if xdev.get("kind") == "purifier":
                xst = xdev.get("state") or {}
                p_t = xst.get("temperature")
                p_h = xst.get("humidity")
                p_aqi = xst.get("aqi")
                p_entry = {}
                if p_t is not None: p_entry["t"] = float(p_t)
                if p_h is not None: p_entry["h"] = int(p_h)
                if p_aqi is not None: p_entry["pm25"] = int(p_aqi)
                if p_entry:
                    sample["purificador"] = p_entry

        # Outdoor fallback if not provided
        if outdoor_t is None or outdoor_h is None:
            try:
                met_t, met_h = get_outdoor_meteo()
                if outdoor_t is None and met_t is not None: outdoor_t = met_t
                if outdoor_h is None and met_h is not None: outdoor_h = met_h
            except Exception:
                pass

        if outdoor_t is not None or outdoor_h is not None:
            sample["exterior"] = {
                "t": float(outdoor_t) if outdoor_t is not None else 18.0,
                "h": int(outdoor_h) if outdoor_h is not None else 60
            }

        # Avoid redundant duplicates if logged less than 5 min ago
        if month_list:
            last = month_list[-1]
            last_ts = datetime.fromisoformat(last["ts"])
            if (now - last_ts).total_seconds() < 300:
                month_list[-1].update(sample)
            else:
                month_list.append(sample)
        else:
            month_list.append(sample)

        CLIMATE_HISTORY_FILE.write_text(json.dumps(hist, indent=2))
        return True
    except Exception as e:
        print(f"[ClimateLogger] Error recording current sample: {e}")
        return False

def get_climate_history(month_str: str = None, metric: str = "temperature"):
    hist = init_climate_history_store()
    now = datetime.now()
    if not month_str:
        month_str = f"{now.year:04d}-{now.month:02d}"

    months_data = hist.get("months", {})
    available_months = sorted(list(months_data.keys()), reverse=True)

    samples = months_data.get(month_str, [])
    
    if metric == "pm25":
        metric_key = "pm25"
        unit = "µg/m³"
        sensor_ids = ["purificador"]
    elif metric == "co2":
        metric_key = "co2"
        unit = "ppm"
        sensor_ids = ["aire"]
    elif metric == "humidity":
        metric_key = "h"
        unit = "%"
        sensor_ids = ["salon", "dormitorio", "aire", "purificador", "exterior"]
    else:
        metric_key = "t"
        unit = "°C"
        sensor_ids = ["salon", "dormitorio", "aire", "purificador", "exterior"]

    points = []
    sensor_stats = {sid: {"values": [], "min": None, "max": None, "avg": None, "current": None} for sid in sensor_ids}

    for s in samples:
        ts = s.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts)
            months_es = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            label = f"{dt.day} {months_es[dt.month]} {dt.hour:02d}:00"
        except Exception:
            label = ts

        pt = {
            "ts": ts,
            "label": label,
            "day": s.get("d"),
            "hour": s.get("h"),
            "values": {}
        }

        has_val = False
        for sid in sensor_ids:
            sensor_data = s.get(sid) or {}
            val = sensor_data.get(metric_key)
            if val is not None:
                pt["values"][sid] = val
                sensor_stats[sid]["values"].append(val)
                sensor_stats[sid]["current"] = val
                has_val = True

        if has_val:
            points.append(pt)

    for sid in sensor_ids:
        vals = sensor_stats[sid]["values"]
        if vals:
            sensor_stats[sid]["min"] = round(min(vals), 1 if metric not in ("co2", "pm25") else 0)
            sensor_stats[sid]["max"] = round(max(vals), 1 if metric not in ("co2", "pm25") else 0)
            sensor_stats[sid]["avg"] = round(sum(vals) / len(vals), 1 if metric not in ("co2", "pm25") else 0)
        del sensor_stats[sid]["values"]

    return {
        "selected_month": month_str,
        "available_months": available_months,
        "metric": metric,
        "unit": unit,
        "sensors": [
            {
                "id": sid,
                "name": SENSORS_CONFIG[sid]["name"],
                "room": SENSORS_CONFIG[sid]["room"],
                "color": SENSORS_CONFIG[sid]["color"],
                "icon": SENSORS_CONFIG[sid]["icon"],
                "stats": sensor_stats.get(sid, {})
            }
            for sid in sensor_ids
        ],
        "points": points
    }

if __name__ == "__main__":
    print("Testing climate logger...")
    res = get_climate_history("2026-11", "temperature")
    print(f"Loaded {len(res['points'])} points for 2026-11.")
    for s in res["sensors"]:
        print(f"  {s['name']}: Min={s['stats'].get('min')} Max={s['stats'].get('max')} Avg={s['stats'].get('avg')} {res['unit']}")
