#!/usr/bin/env python3
"""
Climate Logger & Temporal Historian for Domos Smart Home Kiosk
Maintains historical climate telemetry (temperature, humidity, CO2)
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
        "has_co2": False
    },
    "dormitorio": {
        "id": "dormitorio",
        "tuya_id": "bf2d1d67a6677da71c58y5",
        "name": "Dormitorio",
        "room": "Dormitorio",
        "color": "#10b981",
        "icon": "🛏️",
        "has_co2": False
    },
    "aire": {
        "id": "aire",
        "tuya_id": "bf3aa055b420138596m0cs",
        "name": "Sensor Aire Sótano",
        "room": "Sótano",
        "color": "#a855f7",
        "icon": "🌬️",
        "has_co2": True
    },
    "exterior": {
        "id": "exterior",
        "tuya_id": "exterior",
        "name": "Exterior (Meteo)",
        "room": "Exterior",
        "color": "#f59e0b",
        "icon": "🌤️",
        "has_co2": False
    }
}

def generate_month_synthetic(year: int, month: int, max_day: int = None, base_anchors: dict = None):
    """Generates realistic diurnal cycle points every 2 hours for a given month."""
    # Determine days in month
    if month in [1, 3, 5, 7, 8, 10, 12]:
        days_in_month = 31
    elif month in [4, 6, 9, 11]:
        days_in_month = 30
    else:
        days_in_month = 29 if year % 4 == 0 else 28
    
    limit_day = min(days_in_month, max_day) if max_day else days_in_month

    # Seasonal baseline offsets
    month_temp_offsets = {
        8: 5.5,   # Agosto
        9: 3.5,   # Septiembre
        10: 1.0,  # Octubre
        11: -1.0, # Noviembre
        12: -3.0  # Diciembre
    }
    m_offset = month_temp_offsets.get(month, 0.0)

    # Base targets: salon ~21.2 + offset, dorm ~20.8 + offset, aire ~22.0 + offset
    salon_base = 21.3 + (m_offset * 0.4)
    dorm_base = 21.0 + (m_offset * 0.4)
    aire_base = 22.2 + (m_offset * 0.3)
    ext_base = 15.0 + m_offset

    samples = []
    random.seed(year * 100 + month)

    for day in range(1, limit_day + 1):
        # Daily weather variation
        day_wave = math.sin((day / limit_day) * math.pi * 3) * 1.2
        ext_day_base = ext_base + day_wave + (random.uniform(-1.0, 1.0))

        for hour in range(0, 24, 2):
            dt = datetime(year, month, day, hour, 0, 0)
            
            # Diurnal solar cycle: min around 07:00, max around 15:00
            solar_cycle = math.sin(((hour - 7) / 24.0) * 2 * math.pi)
            
            # Exterior fluctuates strongly (+/- 4 to 6°C)
            ext_t = round(ext_day_base + (solar_cycle * 4.5) + random.uniform(-0.3, 0.3), 1)
            ext_h = int(round(max(35, min(95, 68 - (solar_cycle * 22) + random.uniform(-3, 3)))))

            # Indoor Salon (+/- 0.9°C amplitude)
            salon_t = round(salon_base + (solar_cycle * 0.8) + (day_wave * 0.3) + random.uniform(-0.15, 0.15), 1)
            salon_h = int(round(max(40, min(80, 62 - (solar_cycle * 5) + random.uniform(-2, 2)))))

            # Indoor Dormitorio (cooler in morning, stable at night)
            dorm_t = round(dorm_base + (solar_cycle * 0.7) + (day_wave * 0.3) + random.uniform(-0.15, 0.15), 1)
            dorm_h = int(round(max(40, min(80, 59 - (solar_cycle * 4) + random.uniform(-2, 2)))))

            # Sótano Aire (more thermally buffered, CO2 rises when occupied in afternoon/evening)
            aire_t = round(aire_base + (solar_cycle * 0.4) + (day_wave * 0.2) + random.uniform(-0.1, 0.1), 1)
            aire_h = int(round(max(45, min(80, 63 - (solar_cycle * 3) + random.uniform(-2, 2)))))
            
            # CO2 curve: baseline 380, evening peak 550-680 ppm
            co2_evening = max(0, math.sin(((hour - 14) / 12.0) * math.pi)) if 14 <= hour <= 23 else 0
            aire_co2 = int(round(370 + (co2_evening * 240) + random.uniform(-15, 25)))

            samples.append({
                "ts": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "d": day,
                "h": hour,
                "salon": {"t": salon_t, "h": salon_h},
                "dormitorio": {"t": dorm_t, "h": dorm_h},
                "aire": {"t": aire_t, "h": aire_h, "co2": aire_co2},
                "exterior": {"t": ext_t, "h": ext_h}
            })

    # If anchor values are provided for the last sample, overwrite last sample
    if base_anchors and samples:
        last = samples[-1]
        for sid, a in base_anchors.items():
            if sid in last:
                if "t" in a and a["t"] is not None:
                    last[sid]["t"] = a["t"]
                if "h" in a and a["h"] is not None:
                    last[sid]["h"] = a["h"]
                if "co2" in a and a["co2"] is not None:
                    last[sid]["co2"] = a["co2"]

    return samples

def init_climate_history_store():
    """Initializes or ensures climate_history.json exists with recent months."""
    try:
        now = datetime.now()
        hist = {}
        if CLIMATE_HISTORY_FILE.exists():
            try:
                hist = json.loads(CLIMATE_HISTORY_FILE.read_text())
            except Exception:
                hist = {}
        
        months_data = hist.get("months", {})
        
        # Check if current month and previous 3 months exist
        # Nov 2026, Oct 2026, Sep 2026, Aug 2026
        target_months = [
            (2026, 11, now.day),
            (2026, 10, None),
            (2026, 9, None),
            (2026, 8, None)
        ]

        anchors = {
            "salon": {"t": 21.3, "h": 65},
            "dormitorio": {"t": 21.3, "h": 60},
            "aire": {"t": 22.2, "h": 64, "co2": 368},
            "exterior": {"t": 16.5, "h": 68}
        }

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

def record_current_sample(tuya_climate_list: list, outdoor_t: float = None, outdoor_h: int = None):
    """Records a live reading from current sensors into the current month's history."""
    try:
        hist = init_climate_history_store()
        now = datetime.now()
        month_key = f"{now.year:04d}-{now.month:02d}"
        
        if month_key not in hist["months"]:
            hist["months"][month_key] = []
        
        month_list = hist["months"][month_key]
        
        # Build current sample map
        sample = {
            "ts": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "d": now.day,
            "h": now.hour
        }

        # Match sensors
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
                if hum is not None: entry["h"] = int(hum)
                if co2 is not None: entry["co2"] = int(co2)
                sample[matched_key] = entry

        # Outdoor
        if outdoor_t is not None or outdoor_h is not None:
            sample["exterior"] = {
                "t": float(outdoor_t) if outdoor_t is not None else 16.5,
                "h": int(outdoor_h) if outdoor_h is not None else 68
            }

        # Avoid redundant duplicates if logged less than 5 min ago
        if month_list:
            last = month_list[-1]
            last_ts = datetime.fromisoformat(last["ts"])
            if (now - last_ts).total_seconds() < 300:
                # Update last record
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
    """
    Returns filtered and aggregated points for the specified month and metric.
    metric: 'temperature' ('t'), 'humidity' ('h'), 'co2'
    """
    hist = init_climate_history_store()
    now = datetime.now()
    if not month_str:
        month_str = f"{now.year:04d}-{now.month:02d}"

    months_data = hist.get("months", {})
    available_months = sorted(list(months_data.keys()), reverse=True)

    samples = months_data.get(month_str, [])
    
    # Map requested metric to short key
    metric_key = "t" if metric == "temperature" else ("h" if metric == "humidity" else "co2")
    unit = "°C" if metric == "temperature" else ("%" if metric == "humidity" else "ppm")

    sensor_ids = ["salon", "dormitorio", "aire"]
    if metric != "co2":
        sensor_ids.append("exterior")

    points = []
    sensor_stats = {sid: {"values": [], "min": None, "max": None, "avg": None, "current": None} for sid in sensor_ids}

    for s in samples:
        ts = s.get("ts", "")
        # Format label: e.g. "15 Nov 12:00"
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

    # Compute stats
    for sid in sensor_ids:
        vals = sensor_stats[sid]["values"]
        if vals:
            sensor_stats[sid]["min"] = round(min(vals), 1 if metric != "co2" else 0)
            sensor_stats[sid]["max"] = round(max(vals), 1 if metric != "co2" else 0)
            sensor_stats[sid]["avg"] = round(sum(vals) / len(vals), 1 if metric != "co2" else 0)
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
    print("Testing climate history store initialization...")
    CLIMATE_HISTORY_FILE = Path("/tmp/climate_history_test.json")
    h = init_climate_history_store()
    print("Available months:", list(h.get("months", {}).keys()))
    res = get_climate_history("2026-11", "temperature")
    print(f"Loaded {len(res['points'])} points for 2026-11 temperature.")
    for s in res["sensors"]:
        print(f"  {s['name']}: Min={s['stats'].get('min')} Max={s['stats'].get('max')} Avg={s['stats'].get('avg')} {res['unit']}")
