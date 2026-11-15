import re
import urllib.request
import urllib.parse
import tuya_service
import xiaomi_service
import ewelink_service
import time
import datetime
import os
import glob
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import shutil

app = FastAPI(title="DomosKiosk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_SOCKETS: Set[WebSocket] = set()

CONFIG_FILE = Path("/opt/domoskiosk/kiosk_config.json")
SD_STORAGE = Path("/media/storage")
FALLBACK_DIR = Path("/opt/domoskiosk/photos_fallback")
INCIDENTS_FILE = Path("/opt/domoskiosk/incidents.json")
CALENDAR_FILE = Path("/opt/domoskiosk/family_calendar.json")
SHARED_PHOTO_DIR = Path("/media/storage/Imagenes/Compartidas")

def get_kiosk_config():
    default_cfg = {
        "photo_folder": "Imagenes",
        "carousel_mode": "mixed",  # "sd", "online", "mixed"
        "theme": "light",          # "light" (default) or "dark"
        "hidden_devices": []       # List of hidden device/control IDs
    }
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
            default_cfg.update(saved)
        except Exception:
            pass
    return default_cfg

def save_kiosk_config(new_vals: dict):
    cfg = get_kiosk_config()
    cfg.update(new_vals)
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception as e:
        print("Error saving config:", e)
    return cfg

def get_battery_info():
    hist_file = Path("/opt/domoskiosk/battery_history.json")
    if hist_file.exists():
        try:
            hdata = json.loads(hist_file.read_text())
            if hdata.get("telemetry"):
                return hdata["telemetry"]
        except Exception:
            pass

    bat_path = Path("/sys/class/power_supply/BATC")
    if not bat_path.exists():
        bats = list(Path("/sys/class/power_supply").glob("BAT*"))
        bat_path = bats[0] if bats else None
    
    if bat_path and bat_path.exists():
        try:
            cap = int((bat_path / "capacity").read_text().strip())
            status = (bat_path / "status").read_text().strip()
            v_now = int((bat_path / "voltage_now").read_text().strip()) if (bat_path / "voltage_now").exists() else 7600000
            i_now = int((bat_path / "current_now").read_text().strip()) if (bat_path / "current_now").exists() else 500000
            cf = int((bat_path / "charge_full").read_text().strip()) if (bat_path / "charge_full").exists() else 2581000
            cfd = int((bat_path / "charge_full_design").read_text().strip()) if (bat_path / "charge_full_design").exists() else 5000000
            cycles = int((bat_path / "cycle_count").read_text().strip()) if (bat_path / "cycle_count").exists() else 401
            health = round((cf / cfd) * 100, 1) if cfd > 0 else 51.6
            power = round((v_now * abs(i_now)) / 1e12, 2)
            return {
                "capacity": cap,
                "status": status,
                "health_pct": health,
                "voltage_v": round(v_now / 1e6, 2),
                "power_w": power,
                "cycle_count": cycles,
                "charge_full_mah": round(cf / 1000),
                "charge_full_design_mah": round(cfd / 1000)
            }
        except Exception:
            pass
    return {"capacity": 100, "status": "Unknown", "health_pct": 51.6, "power_w": 4.5}

def get_brightness():
    try:
        out = subprocess.check_output(["brightnessctl", "get"], text=True).strip()
        max_b = subprocess.check_output(["brightnessctl", "max"], text=True).strip()
        pct = int(round(int(out) / int(max_b) * 100))
        return pct
    except Exception:
        return 80

def set_brightness(pct: int):
    try:
        pct = max(5, min(100, pct))
        subprocess.run(["brightnessctl", "set", f"{pct}%"], check=True)
        return True
    except Exception:
        return False

@app.get("/api/config")
async def api_get_config():
    return get_kiosk_config()

@app.post("/api/config")
async def api_set_config(request: Request):
    data = await request.json()
    cfg = save_kiosk_config(data)
    payload = json.dumps({"type": "CONFIG_UPDATE", "config": cfg})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "updated", "config": cfg}


DOMOS_REMOTE_KEY = os.environ.get("DOMOS_REMOTE_KEY", "your_secret_remote_key_here")
NTFY_TUNNEL_TOPIC = "domos_ep_94a7c2e1b8f03d5a"
_last_published_tunnel = ""

try:
    if not Path("/tmp/domos_voice_arm").exists():
        Path("/tmp/domos_voice_arm").write_text("0.0")
except Exception:
    pass

def _get_current_tunnel_url() -> str:
    global _last_published_tunnel
    log_p = Path("/var/log/domos_tunnel.log")
    if not log_p.exists():
        return _last_published_tunnel
    try:
        import re
        txt = log_p.read_text(errors="ignore")
        matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if matches:
            latest = matches[-1]
            if latest != _last_published_tunnel:
                _last_published_tunnel = latest
                def _pub(u):
                    try:
                        req = urllib.request.Request(
                            f"https://ntfy.sh/{NTFY_TUNNEL_TOPIC}",
                            data=u.encode("utf-8"),
                            method="POST"
                        )
                        urllib.request.urlopen(req, timeout=5).read()
                    except Exception:
                        pass
                import threading
                threading.Thread(target=_pub, args=(latest,), daemon=True).start()
            return latest
    except Exception:
        pass
    return _last_published_tunnel

@app.middleware("http")
async def remote_tunnel_auth_middleware(request: Request, call_next):
    # Local LAN requests do not carry Cf-Connecting-Ip header
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        key_hdr = request.headers.get("x-domos-key", "")
        key_q = request.query_params.get("domos_key", "")
        key_cookie = request.cookies.get("domos_key", "")
        if DOMOS_REMOTE_KEY not in (key_hdr, key_q, key_cookie):
            return JSONResponse({"error": "Acceso externo protegido por Domos"}, status_code=403)
        response = await call_next(request)
        if key_q == DOMOS_REMOTE_KEY and key_cookie != DOMOS_REMOTE_KEY:
            response.set_cookie("domos_key", DOMOS_REMOTE_KEY, max_age=31536000, httponly=True, samesite="lax")
        return response
    return await call_next(request)

@app.get("/api/status")
async def api_status():
    cfg = get_kiosk_config()
    target_folder = SD_STORAGE / cfg.get("photo_folder", "Imagenes")
    active_inc = compute_system_incidents()
    return {
        "battery": get_battery_info(),
        "brightness": get_brightness(),
        "photo_dir_exists": target_folder.exists(),
        "tunnel_url": _get_current_tunnel_url(),
        "config": cfg,
        "incidents_count": len(active_inc),
        "has_incidents": len(active_inc) > 0,
        "incidents": active_inc
    }

@app.get("/api/system/battery")
async def api_system_battery():
    hist_file = Path("/opt/domoskiosk/battery_history.json")
    if hist_file.exists():
        try:
            return json.loads(hist_file.read_text())
        except Exception:
            pass
    bat = get_battery_info()
    return {
        "telemetry": bat,
        "current_phase": {
            "type": "discharge" if bat.get("status") == "Discharging" else "charge",
            "current_pct": bat.get("capacity", 50),
            "start_pct": 70 if bat.get("status") == "Discharging" else 30,
            "elapsed_min": 25
        },
        "stats": {
            "avg_charge_min": 35,
            "avg_discharge_day_min": 75,
            "avg_discharge_night_min": 175,
            "total_cycles_recorded": 18
        },
        "cycles": []
    }

@app.post("/api/brightness")
async def api_set_brightness(request: Request):
    data = await request.json()
    pct = data.get("brightness", 80)
    success = set_brightness(pct)
    return {"success": success, "brightness": pct}

@app.get("/api/photos/folders")
async def api_photos_folders():
    folders = []
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ignored = {"System Volume Information", "MapData", "Music"}

    if SD_STORAGE.exists() and SD_STORAGE.is_dir():
        try:
            for d in sorted(SD_STORAGE.iterdir(), key=lambda x: x.name.lower()):
                if not d.is_dir() or d.name.startswith(".") or d.name in ignored:
                    continue
                c_direct = sum(1 for f in d.iterdir() if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                c_total = sum(1 for f in d.rglob("*") if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                if c_total > 0 or d.name in {"Imagenes", "Images", "Fotos"}:
                    folders.append({
                        "id": d.name,
                        "name": f"📁 {d.name} ({c_total})",
                        "path": d.name,
                        "count": c_total
                    })
                for sub in sorted(d.iterdir(), key=lambda x: x.name.lower()):
                    if sub.is_dir() and not sub.name.startswith("."):
                        sub_c = sum(1 for f in sub.rglob("*") if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                        if sub_c > 0:
                            folders.append({
                                "id": f"{d.name}/{sub.name}",
                                "name": f"  ↳ {sub.name} ({sub_c})",
                                "path": f"{d.name}/{sub.name}",
                                "count": sub_c
                            })
        except Exception as e:
            print("Folder scan error:", e)

    current = get_kiosk_config().get("photo_folder", "Images")
    return {"folders": folders, "current": current}

@app.post("/api/photos/folder")
async def api_set_photo_folder(request: Request):
    data = await request.json()
    folder = data.get("folder", "Imagenes")
    save_kiosk_config({"photo_folder": folder})
    return {"status": "folder_changed", "folder": folder}

@app.get("/api/photos")
async def api_photos():
    cfg = get_kiosk_config()
    folder_rel = cfg.get("photo_folder", "Imagenes")
    target_dir = SD_STORAGE / folder_rel if folder_rel else SD_STORAGE
    exts = (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG")
    photos = []
    
    # 1. Search in user SD Card target directory
    if target_dir.exists() and target_dir.is_dir():
        for ext in exts:
            for p in target_dir.rglob(f"*{ext}"):
                if not p.name.startswith("."):
                    rel = p.relative_to(SD_STORAGE)
                    photos.append(f"/photo_file/{rel}")
                    
    # 2. If no photos found, check fallback
    if not photos and FALLBACK_DIR.exists():
        for ext in exts:
            for p in FALLBACK_DIR.glob(f"*{ext}"):
                photos.append(f"/fallback_file/{p.name}")
                
    return {
        "photos": photos,
        "folder": folder_rel,
        "count": len(photos)
    }


# ========================================================
# SANDBOXED SD CARD FILE API (STRICTLY /media/storage ONLY)
# ========================================================
def _resolve_sd_path(rel_path: str = "") -> Path:
    base = SD_STORAGE.resolve()
    clean = (rel_path or "").lstrip("/").strip()
    target = (base / clean).resolve()
    target.relative_to(base)  # raises ValueError if path escapes /media/storage
    return target

@app.get("/api/sd/files")
async def sd_list_files(path: str = ""):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if not target.exists() or not target.is_dir():
        return JSONResponse({"error": "Carpeta no encontrada"}, status_code=404)
    items = []
    for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if entry.name.startswith(".") or entry.name == "System Volume Information":
            continue
        stat = entry.stat()
        items.append({
            "name": entry.name,
            "path": str(entry.relative_to(SD_STORAGE.resolve())),
            "is_dir": entry.is_dir(),
            "size": 0 if entry.is_dir() else stat.st_size,
            "mtime": int(stat.st_mtime),
        })
    return {"path": str(target.relative_to(SD_STORAGE.resolve())).replace(".", ""), "items": items}

@app.post("/api/sd/mkdir")
async def sd_mkdir(request: Request):
    data = await request.json()
    rel = data.get("path", "")
    try:
        target = _resolve_sd_path(rel)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    target.mkdir(parents=True, exist_ok=True)
    return {"status": "created", "path": str(target.relative_to(SD_STORAGE.resolve()))}

@app.post("/api/sd/upload")
async def sd_upload(file: UploadFile = File(...), folder: str = Form("Images")):
    try:
        dest_dir = _resolve_sd_path(folder)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or f"upload_{int(time.time())}").name
    dest = (dest_dir / safe_name).resolve()
    dest.relative_to(SD_STORAGE.resolve())
    content = await file.read()
    dest.write_bytes(content)
    payload = json.dumps({"type": "PHOTOS_UPDATED", "folder": folder, "file": safe_name})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {
        "status": "uploaded",
        "name": safe_name,
        "path": str(dest.relative_to(SD_STORAGE.resolve())),
        "size": len(content),
    }

@app.get("/api/sd/download")
async def sd_download(path: str):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if not target.exists() or not target.is_file():
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
    return FileResponse(target, filename=target.name)

@app.delete("/api/sd/file")
async def sd_delete(path: str):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if target == SD_STORAGE.resolve():
        return JSONResponse({"error": "No se puede eliminar la raíz de la SD"}, status_code=403)
    if target.is_file():
        target.unlink()
        return {"status": "deleted"}
    return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)

@app.get("/photo_file/{file_path:path}")
async def get_photo(file_path: str):
    full_path = (SD_STORAGE / file_path).resolve()
    # Path traversal protection
    try:
        full_path.relative_to(SD_STORAGE.resolve())
    except ValueError:
        return JSONResponse({"error": "Forbidden"}, status_code=403)
        
    if full_path.exists() and full_path.is_file():
        return FileResponse(full_path)
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.get("/fallback_file/{file_path:path}")
async def get_fallback(file_path: str):
    full_path = FALLBACK_DIR / file_path
    if full_path.exists() and full_path.is_file():
        return FileResponse(full_path)
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.post("/api/assistant/state")
async def set_assistant_state(request: Request):
    data = await request.json()
    state = data.get("state", "idle")  # "listening", "processing", "speaking", "idle"
    prompt = data.get("prompt", "")
    reply = data.get("reply", "")
    
    # Wake screen if assistant speaks or listens
    if state in ("listening", "speaking", "processing"):
        set_brightness(80)

    payload = json.dumps({
        "type": "ASSISTANT_STATE",
        "state": state,
        "prompt": prompt,
        "reply": reply
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "ok", "state": state}

@app.post("/api/doorbell/trigger")
async def trigger_doorbell(request: Request):
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    title = data.get("title", "¡Alguien está en la puerta!")
    stream_url = data.get("stream_url", "")
    
    set_brightness(100)
    
    payload = json.dumps({
        "type": "DOORBELL_ALERT",
        "title": title,
        "stream_url": stream_url,
        "timestamp": data.get("timestamp", "")
    })
    
    dead_sockets = set()
    for ws in ACTIVE_SOCKETS:
        try:
            await ws.send_text(payload)
        except Exception:
            dead_sockets.add(ws)
    for ws in dead_sockets:
        ACTIVE_SOCKETS.discard(ws)
        
    return {"status": "broadcast_sent", "clients": len(ACTIVE_SOCKETS)}

@app.post("/api/doorbell/dismiss")
async def dismiss_doorbell():
    payload = json.dumps({"type": "DOORBELL_DISMISS"})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "dismissed"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ACTIVE_SOCKETS.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all connected sockets
            for ws in list(ACTIVE_SOCKETS):
                try:
                    await ws.send_text(data)
                except Exception:
                    pass
    except WebSocketDisconnect:
        ACTIVE_SOCKETS.discard(websocket)
    except Exception:
        ACTIVE_SOCKETS.discard(websocket)

@app.post("/api/message/send")
async def send_family_message(request: Request):
    data = await request.json()
    sender = data.get("sender", "Papá")
    text = data.get("text", "")
    speak = data.get("speak", True)
    
    set_brightness(100)
    
    payload = json.dumps({
        "type": "FAMILY_MESSAGE",
        "sender": sender,
        "text": text,
        "timestamp": data.get("timestamp", "")
    })
    
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    if speak and text:
        try:
            msg_to_speak = f"Mensaje de {sender}: {text}"
            subprocess.Popen(["espeak-ng", "-v", "es-es", "-s", "145", msg_to_speak])
        except Exception as e:
            print("TTS Error:", e)
            
    return {"status": "sent", "sender": sender, "text": text}

@app.post("/api/presence/wake")
async def wake_screen(request: Request = None):
    seconds = 180
    if request:
        try:
            data = await request.json()
            seconds = data.get("seconds", 180)
        except Exception:
            pass
    Path("/tmp/domos_wake_trigger").write_text(str(seconds))
    return {"status": "wake_triggered", "seconds": seconds}

@app.get("/api/presence/status")
async def presence_status():
    status_file = Path("/tmp/domos_presence_status.json")
    if status_file.exists():
        try:
            return json.loads(status_file.read_text())
        except Exception:
            pass
    return {"status": "unknown"}

@app.post("/api/photos/upload")
async def upload_photo(file: UploadFile = File(...), sender: str = Form("Familia")):
    try:
        SHARED_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"{int(time.time())}_{file.filename}"
        dest_path = SHARED_PHOTO_DIR / safe_name
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        set_brightness(100)
        
        payload = json.dumps({
            "type": "NEW_PHOTO",
            "sender": sender,
            "url": f"/photo_file/Imagenes/Compartidas/{safe_name}"
        })
        for ws in list(ACTIVE_SOCKETS):
            try:
                await ws.send_text(payload)
            except Exception:
                pass
                
        return {"status": "uploaded", "file": safe_name}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

DISMISSED_INCIDENTS_CACHE = {}  # {inc_id: timestamp_dismissed}

def compute_system_incidents():
    active = []
    now_ts = time.time()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Read persistent/logged incidents from incidents.json
    logged_unresolved = []
    if INCIDENTS_FILE.exists():
        try:
            stored = json.loads(INCIDENTS_FILE.read_text())
            for inc in stored:
                if not inc.get("resolved", False):
                    inc_id = inc.get("id")
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) > 43200:  # 12h
                        logged_unresolved.append(inc)
        except Exception:
            pass

    active.extend(logged_unresolved)

    # Read live states from /tmp/domos_tuya_states.json & devices.json
    states_file = Path("/tmp/domos_tuya_states.json")
    devs_file = Path("/opt/domoskiosk/devices.json")
    states = {}
    devs = {}
    if states_file.exists():
        try:
            states = json.loads(states_file.read_text())
        except Exception:
            pass
    if devs_file.exists():
        try:
            devs = json.loads(devs_file.read_text())
        except Exception:
            pass

    # 1. Batería baja en sensores a pilas
    for dev_id, st in states.items():
        if not isinstance(st, dict):
            continue
        dinfo = devs.get(dev_id, {})
        name = dinfo.get("name", dev_id)

        bat_val = st.get("battery")
        if bat_val is None:
            bat_val = st.get("battery_percentage")
        if bat_val is None:
            bat_val = st.get("battery_state")

        if bat_val is not None:
            inc_id = f"bat_{dev_id}"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) < 43200:
                continue

            try:
                pct = int(bat_val)
                if pct <= 20:
                    sev = "critical" if pct <= 10 else "warning"
                    active.append({
                        "id": inc_id,
                        "type": "battery_low",
                        "category": "battery",
                        "source": name,
                        "severity": sev,
                        "title": f"Batería baja: {name}",
                        "description": f"Nivel de batería al {pct}%. Conviene cambiar o recargar las pilas pronto.",
                        "value": f"{pct}%",
                        "icon": "🔋",
                        "timestamp": now_str,
                        "resolved": False
                    })
            except (ValueError, TypeError):
                sval = str(bat_val).lower().strip()
                if sval in ("low", "lower", "empty", "alarm", "bat_low", "die"):
                    active.append({
                        "id": inc_id,
                        "type": "battery_low",
                        "category": "battery",
                        "source": name,
                        "severity": "warning",
                        "title": f"Batería baja: {name}",
                        "description": f"El sensor reporta estado de batería baja ('{sval}'). Sustituir pilas.",
                        "value": sval,
                        "icon": "🔋",
                        "timestamp": now_str,
                        "resolved": False
                    })

    # 2. Anomalías de tensión eléctrica en la red (< 180V o > 255V)
    for dev_id, st in states.items():
        if not isinstance(st, dict):
            continue
        dinfo = devs.get(dev_id, {})
        name = dinfo.get("name", dev_id)
        if "bater" in name.lower() or "battery" in name.lower():
            continue

        volt_val = st.get("volts") if st.get("volts") is not None else st.get("voltage")
        if volt_val is not None:
            try:
                v = float(volt_val)
                inc_id_low = f"volt_low_{dev_id}"
                inc_id_high = f"volt_high_{dev_id}"

                if 100.0 < v < 180.0:
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_low, 0) > 43200:
                        active.append({
                            "id": inc_id_low,
                            "type": "voltage_low",
                            "category": "grid",
                            "source": name,
                            "severity": "critical" if v < 170.0 else "warning",
                            "title": "Caída de tensión en red eléctrica",
                            "description": f"{name} detecta una tensión anormal de {v:.1f} V (límite seguro: 180 V). Posible bajada de suministro en el barrio.",
                            "value": f"{v:.1f} V",
                            "icon": "⚡",
                            "timestamp": now_str,
                            "resolved": False
                        })
                elif v > 255.0:
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_high, 0) > 43200:
                        active.append({
                            "id": inc_id_high,
                            "type": "voltage_high",
                            "category": "grid",
                            "source": name,
                            "severity": "warning",
                            "title": "Sobretensión en red eléctrica",
                            "description": f"{name} detecta sobretensión de {v:.1f} V (límite recomendado: 255 V).",
                            "value": f"{v:.1f} V",
                            "icon": "⚡",
                            "timestamp": now_str,
                            "resolved": False
                        })
            except (ValueError, TypeError):
                pass

    # 3. Supervisión de Batería y Salud de la Tablet Domos (Casos Extremos)
    try:
        bat_info = get_battery_info()
        tab_pct = bat_info.get("capacity") if bat_info.get("capacity") is not None else bat_info.get("percent")
        status = bat_info.get("status", "Discharging")
        health = bat_info.get("health_pct", 51.6)

        # 3.1 Nivel Crítico (<= 15%): Posible corte de luz, enchufe apagado o desconectado
        if tab_pct is not None and tab_pct <= 15:
            inc_id_crit = "tablet_domos_battery_critical"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_crit, 0) > 43200:
                active.append({
                    "id": inc_id_crit,
                    "type": "tablet_battery",
                    "category": "system",
                    "source": "Tablet Domos",
                    "severity": "critical",
                    "title": "Batería crítica en Domos (≤ 15%)",
                    "description": f"La tablet central está al {tab_pct}% de batería y no ha entrado en carga. Comprueba el enchufe o el suministro eléctrico.",
                    "value": f"{tab_pct}%",
                    "icon": "🪫",
                    "timestamp": now_str,
                    "resolved": False
                })

        # 3.2 Alerta de Degradación Severa / Prevención de Hinchado (< 30% de salud)
        if health is not None and health < 30.0:
            inc_id_degrade = "tablet_domos_battery_degraded"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_degrade, 0) > 86400: # 24h
                active.append({
                    "id": inc_id_degrade,
                    "type": "tablet_health",
                    "category": "system",
                    "source": "Batería Domos",
                    "severity": "critical",
                    "title": "Degradación crítica de batería",
                    "description": f"La salud de la celda de litio ha caído al {health}%. Se aconseja cambiar la batería de forma preventiva para evitar deformación o hinchamiento.",
                    "value": f"{health}% salud",
                    "icon": "⚠️",
                    "timestamp": now_str,
                    "resolved": False
                })

        # 3.3 Colapso de Autonomía Nocturna (< 60 min con pantalla apagada) o Carga Atascada (> 90 min cargando)
        hist_file = Path("/opt/domoskiosk/battery_history.json")
        if hist_file.exists():
            try:
                hdata = json.loads(hist_file.read_text())
                night_avg = hdata.get("stats", {}).get("avg_discharge_night_min", 170)
                if night_avg < 60:
                    inc_id_night = "tablet_domos_night_collapse"
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_night, 0) > 86400:
                        active.append({
                            "id": inc_id_night,
                            "type": "tablet_autonomy",
                            "category": "system",
                            "source": "Batería Domos",
                            "severity": "warning",
                            "title": "Pérdida acelerada de retención",
                            "description": f"La descarga nocturna (con pantalla apagada) dura menos de 1 hora ({night_avg} min). Posible fuga interna o degradación acelerada.",
                            "value": f"{night_avg} min noche",
                            "icon": "🌙",
                            "timestamp": now_str,
                            "resolved": False
                        })

                cur_phase = hdata.get("current_phase", {})
                if cur_phase.get("type") == "charge" and cur_phase.get("elapsed_min", 0) > 90:
                    inc_id_stall = "tablet_domos_charge_stall"
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_stall, 0) > 43200:
                        active.append({
                            "id": inc_id_stall,
                            "type": "tablet_charge",
                            "category": "system",
                            "source": "Cargador Domos",
                            "severity": "warning",
                            "title": "Carga de batería anormalmente lenta",
                            "description": f"La batería lleva {cur_phase.get('elapsed_min')} min cargando sin llegar al 70%. Comprueba el cable microUSB o el cargador.",
                            "value": f">{cur_phase.get('elapsed_min')} min",
                            "icon": "🔌",
                            "timestamp": now_str,
                            "resolved": False
                        })
            except Exception:
                pass
    except Exception:
        pass

    return active

@app.get("/api/incidents")
async def get_incidents():
    active = compute_system_incidents()
    history = []
    if INCIDENTS_FILE.exists():
        try:
            history = json.loads(INCIDENTS_FILE.read_text())
        except Exception:
            pass
    return {
        "count": len(active),
        "has_critical": any(i.get("severity") == "critical" for i in active),
        "incidents": active,
        "history": history[:30]
    }

@app.post("/api/incidents/log")
async def log_incident(request: Request):
    data = await request.json()
    incidents = []
    if INCIDENTS_FILE.exists():
        try:
            incidents = json.loads(INCIDENTS_FILE.read_text())
        except Exception:
            pass
            
    new_inc = {
        "id": f"inc_{int(time.time())}",
        "timestamp": datetime.datetime.now().isoformat(),
        "source": data.get("source", "Sistema"),
        "severity": data.get("severity", "warning"),
        "title": data.get("title", "Incidencia detectada"),
        "description": data.get("description", ""),
        "resolved": False
    }
    incidents.insert(0, new_inc)
    incidents = incidents[:50]
    INCIDENTS_FILE.write_text(json.dumps(incidents, indent=2))
    
    payload = json.dumps({"type": "INCIDENTS_UPDATED", "count": len(compute_system_incidents()), "incidents": compute_system_incidents()})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    return {"status": "logged", "incident": new_inc}

@app.post("/api/incidents/resolve")
async def resolve_incident(request: Request):
    data = await request.json()
    inc_id = data.get("id")
    if inc_id:
        DISMISSED_INCIDENTS_CACHE[inc_id] = time.time()
    else:
        for inc in compute_system_incidents():
            DISMISSED_INCIDENTS_CACHE[inc.get("id")] = time.time()

    if INCIDENTS_FILE.exists():
        try:
            incidents = json.loads(INCIDENTS_FILE.read_text())
            for inc in incidents:
                if inc.get("id") == inc_id or not inc_id:
                    inc["resolved"] = True
            INCIDENTS_FILE.write_text(json.dumps(incidents, indent=2))
        except Exception as e:
            pass

    active = compute_system_incidents()
    payload = json.dumps({"type": "INCIDENTS_UPDATED", "count": len(active), "incidents": active})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

    return {"status": "resolved", "count": len(active), "incidents": active}

_ics_cache = {"ts": 0.0, "events": []}

def _parse_ics_events(ics_text: str, source_name: str = "ICS"):
    import re
    # Unfold folded lines (CRLF/LF followed by space or tab)
    unfolded = re.sub(r"\r?\n[ \t]", "", ics_text or "")
    events = []
    in_ev = False
    cur = {}
    for line in unfolded.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_ev = True
            cur = {}
            continue
        if line == "END:VEVENT":
            in_ev = False
            dt_raw = cur.get("DTSTART", "")
            m = re.match(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", dt_raw)
            if m and cur.get("SUMMARY"):
                date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                time_str = f"{m.group(4)}:{m.group(5)}" if m.group(4) and m.group(5) else ""
                summary = cur["SUMMARY"].replace("\\,", ",").replace("\\n", " ").replace("\\;", ";")
                uid = cur.get("UID", f"{date_str}_{summary[:16]}")
                events.append({
                    "id": f"ics_{abs(hash(uid))}",
                    "title": summary,
                    "date": date_str,
                    "type": "ics",
                    "source": source_name,
                    "reminder_time": time_str,
                })
            continue
        if in_ev and ":" in line:
            k_part, val = line.split(":", 1)
            k = k_part.split(";", 1)[0].upper()
            if k in ("DTSTART", "SUMMARY", "UID", "DESCRIPTION"):
                cur[k] = val
    return events

def _fetch_ics_events_sync(force: bool = False):
    import urllib.request
    now = time.time()
    if not force and (now - _ics_cache["ts"]) < 300:
        return _ics_cache["events"]
    cfg = get_kiosk_config()
    sources = cfg.get("calendar_ics_urls") or []
    all_ev = []
    for src in sources:
        url = (src.get("url") or "").strip() if isinstance(src, dict) else ""
        name = (src.get("name") or "Calendario").strip() if isinstance(src, dict) else "Calendario"
        if not url:
            continue
        if url.startswith("webcal://"):
            url = "https://" + url[len("webcal://"):]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                txt = resp.read().decode("utf-8", errors="ignore")
                all_ev.extend(_parse_ics_events(txt, name))
        except Exception as e:
            print(f"[Calendar] ICS fetch error ({name}): {e}", flush=True)
    _ics_cache["ts"] = now
    _ics_cache["events"] = all_ev
    return all_ev

def _load_local_calendar():
    if CALENDAR_FILE.exists():
        try:
            evs = json.loads(CALENDAR_FILE.read_text())
            if isinstance(evs, list):
                today_iso = datetime.date.today().isoformat()
                cur_year = datetime.date.today().year
                for e in evs:
                    e.setdefault("source", "Domos")
                    if e.get("repeat") == "yearly" and isinstance(e.get("date"), str) and len(e["date"]) >= 10:
                        mmdd = e["date"][5:10]
                        cand = f"{cur_year}-{mmdd}"
                        if cand < today_iso:
                            cand = f"{cur_year + 1}-{mmdd}"
                        e["date"] = cand
                return evs
        except Exception:
            pass
    return []

@app.get("/api/calendar")
async def get_calendar():
    local_evs = _load_local_calendar()
    ics_evs = await asyncio.to_thread(_fetch_ics_events_sync, False)
    merged = local_evs + ics_evs
    merged.sort(key=lambda x: (x.get("date", ""), x.get("reminder_time", "")))
    return merged

@app.post("/api/calendar")
async def add_calendar_event(request: Request):
    data = await request.json()
    events = _load_local_calendar()
    event = {
        "id": f"cal_{int(time.time() * 1000)}",
        "title": data.get("title", "Nuevo Recordatorio"),
        "date": data.get("date", ""),
        "type": data.get("type", "event"),
        "source": "Domos",
        "reminder_time": data.get("reminder_time", "09:00")
    }
    events.append(event)
    CALENDAR_FILE.write_text(json.dumps(events, indent=2, ensure_ascii=False))
    return {"status": "added", "event": event}

@app.delete("/api/calendar/{event_id}")
async def delete_calendar_event(event_id: str):
    events = _load_local_calendar()
    new_events = [e for e in events if e.get("id") != event_id]
    CALENDAR_FILE.write_text(json.dumps(new_events, indent=2, ensure_ascii=False))
    return {"status": "deleted", "id": event_id}

@app.get("/api/calendar/sources")
async def get_calendar_sources():
    cfg = get_kiosk_config()
    return {"sources": cfg.get("calendar_ics_urls") or []}

@app.post("/api/calendar/sources")
async def save_calendar_sources(request: Request):
    data = await request.json()
    sources = data.get("sources")
    if not isinstance(sources, list):
        return JSONResponse({"error": "sources list required"}, status_code=400)
    save_kiosk_config({"calendar_ics_urls": sources})
    _ics_cache["ts"] = 0.0
    events = await get_calendar()
    return {"status": "updated", "sources": sources, "events": events}

_last_screen_cache = None
_last_screen_time = 0.0

@app.get("/api/screen/live.png")
async def live_screen():
    global _last_screen_cache, _last_screen_time
    now = time.time()
    # Cache for 350ms to prevent multiple concurrent grim forks from thrashing
    if _last_screen_cache and (now - _last_screen_time) < 0.35:
        return Response(content=_last_screen_cache, media_type="image/png")

    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = "wayland-0"
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    try:
        proc = await asyncio.create_subprocess_exec(
            "grim", "-",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=env
        )
        stdout, _ = await proc.communicate()
        if stdout and stdout.startswith(b"\x89PNG"):
            _last_screen_cache = stdout
            _last_screen_time = now
            return Response(content=stdout, media_type="image/png")
    except Exception as e:
        print("[SCREEN_CAPTURE_ERR]", e)

    if _last_screen_cache:
        return Response(content=_last_screen_cache, media_type="image/png")
    return JSONResponse({"error": "Failed to capture"}, status_code=500)

from evdev import UInput, AbsInfo, ecodes as _e

VIRTUAL_TOUCH = None

@app.post("/api/debug_log")
async def debug_log(request: Request):
    data = await request.json()
    print("[CLIENT_DEBUG]", data, flush=True)
    return {"ok": True}


@app.get("/api/solar/details")
async def get_solar_details():
    summary = _all_devices_payload()
    solar = summary.get("solar") or {}
    battery = summary.get("battery") or {}
    extra = {}
    solar_id = solar.get("id") or "bfe037c461c9c61da3pesr"
    try:
        res = await asyncio.to_thread(tuya_service.service.cloud.getstatus, solar_id)
        if res.get("success"):
            for item in res.get("result", []):
                c = item.get("code")
                if c in ("total_forward_energy", "fault", "breaker_number", "switch", "balance_energy", "charge_energy"):
                    extra[c] = item.get("value")
    except Exception as e:
        extra["error"] = str(e)
    return {"solar": solar, "battery": battery, "extra": extra}

@app.get("/api/cameras")
async def get_cameras():
    summary = _all_devices_payload()
    return summary.get("cameras", [])

def _go2rtc_register_sync(camera_id: str, rtsp_url: str):
    qs = urllib.parse.urlencode({"name": camera_id, "src": rtsp_url})
    req = urllib.request.Request(f"http://127.0.0.1:1984/api/streams?{qs}", method="PUT")
    with urllib.request.urlopen(req, timeout=4) as r:
        return r.status == 200

def _go2rtc_webrtc_sync(src: str, offer_sdp: bytes, content_type: str):
    qs = urllib.parse.urlencode({"src": src})
    req = urllib.request.Request(
        f"http://127.0.0.1:1984/api/webrtc?{qs}",
        data=offer_sdp,
        headers={"Content-Type": content_type or "application/sdp"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=6) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "application/sdp")

async def allocate_low_latency_stream(camera_id: str, force_hls: bool = False):
    if not force_hls:
        try:
            rtsp_res = await asyncio.to_thread(tuya_service.service.get_camera_stream_url, camera_id, "RTSP")
            if rtsp_res.get("success") and rtsp_res.get("url"):
                ok = await asyncio.to_thread(_go2rtc_register_sync, camera_id, rtsp_res["url"])
                if ok:
                    return {
                        "success": True,
                        "mode": "webrtc",
                        "webrtc_url": f"/api/go2rtc/webrtc?src={urllib.parse.quote(camera_id)}",
                        "stream_name": camera_id,
                    }
        except Exception as e:
            print(f"[GO2RTC_REG_ERR] {camera_id}: {e}", flush=True)

    hls_res = await asyncio.to_thread(tuya_service.service.get_camera_stream_url, camera_id, "HLS")
    if hls_res.get("success"):
        hls_res["mode"] = "hls"
    return hls_res

@app.get("/api/camera/stream/{camera_id}")
async def get_camera_stream(camera_id: str, force_hls: int = 0):
    return await allocate_low_latency_stream(camera_id, force_hls=bool(force_hls))

@app.post("/api/go2rtc/webrtc")
async def proxy_go2rtc_webrtc(request: Request):
    src = request.query_params.get("src", "")
    if not src:
        return Response(content="Missing src", status_code=400)
    body = await request.body()
    ctype = request.headers.get("content-type", "application/sdp")
    try:
        status, ans, resp_ctype = await asyncio.to_thread(_go2rtc_webrtc_sync, src, body, ctype)
        return Response(content=ans, status_code=status, media_type=resp_ctype)
    except Exception as e:
        print(f"[GO2RTC_WEBRTC_ERR] {src}: {e}", flush=True)
        return Response(content=str(e), status_code=502)

@app.post("/api/devices/sync")
async def sync_devices():
    count = tuya_service.service.sync_cloud_devices()
    summary = _all_devices_payload()
    payload = json.dumps({"type": "DEVICE_UPDATE", "devices": summary})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "synced", "total_devices": count}

def _all_devices_payload():
    d = tuya_service.service.get_structured_devices()
    d["xiaomi"] = xiaomi_service.service.get_devices()
    ew_lights, ew_plugs = ewelink_service.service.get_structured_devices()
    d["lights"] = list(d.get("lights", [])) + ew_lights
    d["plugs"] = list(d.get("plugs", [])) + ew_plugs
    d["total_devices"] = d.get("total_devices", 0) + len(ew_lights) + len(ew_plugs)
    return d

@app.get("/api/devices")
async def get_all_devices():
    return _all_devices_payload()

@app.post("/api/xiaomi/control")
async def control_xiaomi(request: Request):
    data = await request.json()
    dev_id = data.get("device_id")
    action = data.get("action")
    value = data.get("value")
    if not dev_id or not action:
        return JSONResponse({"error": "device_id and action required"}, status_code=400)
    res = await asyncio.to_thread(xiaomi_service.service.send_command, dev_id, action, value)
    summary = _all_devices_payload()
    payload = json.dumps({
        "type": "DEVICE_UPDATE",
        "device_id": dev_id,
        "code": action,
        "value": value,
        "devices": summary
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"result": res, "devices": summary}

@app.post("/api/devices/control")
async def control_device(request: Request):
    data = await request.json()
    dev_id = data.get("device_id")
    code = data.get("code", "switch_1")
    value = data.get("value")
    if not dev_id:
        return JSONResponse({"error": "device_id is required"}, status_code=400)
    
    if ewelink_service.service.has_device(dev_id):
        res = await asyncio.to_thread(ewelink_service.service.send_command, dev_id, value)
    else:
        res = tuya_service.service.send_command(dev_id, code, value)
    summary = _all_devices_payload()
    payload = json.dumps({
        "type": "DEVICE_UPDATE",
        "device_id": dev_id,
        "code": code,
        "value": value,
        "devices": summary
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    return res

@app.post("/api/screen/tap")
async def screen_tap(request: Request):
    data = await request.json()
    x_pct = float(data.get("x", 0.5))
    y_pct = float(data.get("y", 0.5))
    print(f"[TAP_LOG] Received tap at x_pct={x_pct:.4f}, y_pct={y_pct:.4f}, sockets={len(ACTIVE_SOCKETS)}", flush=True)
    
    set_brightness(80)

    payload = json.dumps({"type": "REMOTE_CLICK", "x": x_pct, "y": y_pct})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

    x = max(0, min(1366, int(round(x_pct * 1366))))
    y = max(0, min(768, int(round(y_pct * 768))))
    # Handled directly via REMOTE_CLICK WebSocket in app.js (prevents double-click on Atom CPU)

    return {"status": "tapped", "x": x, "y": y}

@app.get("/api/solar")
async def get_solar_status():
    status_file = Path("/tmp/domos_solar_status.json")
    if status_file.exists():
        try:
            return json.loads(status_file.read_text())
        except Exception:
            pass
    return {"watts": 0, "volts": 230, "amps": 0, "is_sun": False}


import evdev

def _trigger_screen_wake():
    try:
        Path("/tmp/domos_wake_trigger").write_text("180")
        st_path = Path("/tmp/domos_presence_status.json")
        if st_path.exists():
            st = json.loads(st_path.read_text())
            if int(st.get("current_brightness", 45)) < 10:
                subprocess.Popen(["sudo", "brightnessctl", "set", "45%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

async def monitor_physical_touchscreen():
    # Ensure I2C controller and SIS0817 touchscreen stay powered on
    for sys_p in [
        "/sys/devices/platform/80860F41:05/power/control",
        "/sys/bus/i2c/devices/i2c-SIS0817:00/power/control"
    ]:
        try:
            Path(sys_p).write_text("on")
        except Exception:
            pass

    target_dev = None
    for path in evdev.list_devices():
        try:
            d = evdev.InputDevice(path)
            if "SIS0817" in d.name or "0457:1084" in d.name:
                target_dev = d
                break
        except Exception:
            pass

    if not target_dev:
        print("[TOUCH_MONITOR] SIS0817 device not found", flush=True)
        return

    print(f"[TOUCH_MONITOR] Listening on {target_dev.path} ({target_dev.name})", flush=True)
    cur_x = 2048
    cur_y = 2048
    start_x = 2048
    start_y = 2048
    touch_down_time = 0.0
    is_touching = False

    need_start_pos = False
    last_pt_sent = 0.0
    try:
        async for ev in target_dev.async_read_loop():
            if ev.type == _e.EV_ABS:
                if ev.code in (_e.ABS_X, _e.ABS_MT_POSITION_X) and ev.value > 0:
                    cur_x = ev.value
                elif ev.code in (_e.ABS_Y, _e.ABS_MT_POSITION_Y) and ev.value > 0:
                    cur_y = ev.value
                elif ev.code == _e.ABS_MT_TRACKING_ID:
                    if ev.value >= 0 and not is_touching:
                        is_touching = True
                        need_start_pos = True
                        _trigger_screen_wake()
                        touch_down_time = time.time()
                    elif ev.value == -1 and is_touching:
                        is_touching = False
                        need_start_pos = False
                        dt = time.time() - touch_down_time
                        dist = abs(cur_x - start_x) + abs(cur_y - start_y)
                        if dt < 1.25 and dist < 550:
                            x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                            y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                            print(f"[PHYSICAL_TAP_SENT] MT x={x_pct:.3f} y={y_pct:.3f}", flush=True)
                            payload = json.dumps({"type": "PHYSICAL_TAP_FALLBACK", "x": x_pct, "y": y_pct})
                            for ws in list(ACTIVE_SOCKETS):
                                try:
                                    await ws.send_text(payload)
                                except Exception:
                                    pass
            elif ev.type == _e.EV_KEY and ev.code == _e.BTN_TOUCH:
                if ev.value == 1 and not is_touching:
                    is_touching = True
                    need_start_pos = True
                    _trigger_screen_wake()
                    touch_down_time = time.time()
                elif ev.value == 0 and is_touching:
                    is_touching = False
                    need_start_pos = False
                    dt = time.time() - touch_down_time
                    dist = abs(cur_x - start_x) + abs(cur_y - start_y)
                    if dt < 1.25 and dist < 550:
                        x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                        y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                        print(f"[PHYSICAL_TAP_SENT] BTN_TOUCH x={x_pct:.3f} y={y_pct:.3f}", flush=True)
                        payload = json.dumps({"type": "PHYSICAL_TAP_FALLBACK", "x": x_pct, "y": y_pct})
                        for ws in list(ACTIVE_SOCKETS):
                            try:
                                await ws.send_text(payload)
                            except Exception:
                                pass
            elif ev.type == _e.EV_SYN and ev.code == _e.SYN_REPORT:
                if need_start_pos:
                    start_x, start_y = cur_x, cur_y
                    need_start_pos = False
                if is_touching and ACTIVE_SOCKETS and (time.time() - last_pt_sent > 0.032):
                    last_pt_sent = time.time()
                    x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                    y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                    pt_payload = json.dumps({"type": "PHYSICAL_TOUCH_POINT", "x": x_pct, "y": y_pct})
                    for ws in list(ACTIVE_SOCKETS):
                        try:
                            await ws.send_text(pt_payload)
                        except Exception:
                            pass
    except Exception as ex:
        print("[TOUCH_MONITOR_ERR]", ex, flush=True)

@app.on_event("startup")
async def start_touch_monitor():
    asyncio.create_task(monitor_physical_touchscreen())


@app.post("/api/system/reboot")
async def system_reboot():
    print("[SYSTEM] Reboot requested via Domos Control Center", flush=True)
    asyncio.get_event_loop().call_later(0.8, lambda: subprocess.Popen(["sudo", "systemctl", "reboot"]))
    return {"status": "rebooting"}


@app.post("/api/system/poweroff")
async def system_poweroff():
    print("[SYSTEM] Poweroff requested via Domos Control Center", flush=True)
    asyncio.get_event_loop().call_later(0.8, lambda: subprocess.Popen(["sudo", "systemctl", "poweroff"]))
    return {"status": "powering_off"}


async def monitor_doorbell_ring():
    import base64
    dev_id = "bf77eed8534deaf66f2xpj"
    last_alarm_msg = None
    last_doorbell_active = ""
    last_doorbell_pic = ""
    last_trigger_time = 0.0

    # Initialize baseline without triggering on startup
    try:
        res = await asyncio.to_thread(tuya_service.service.cloud.getstatus, dev_id)
        if res.get("success"):
            for item in res.get("result", []):
                if item.get("code") == "alarm_message":
                    last_alarm_msg = item.get("value")
                elif item.get("code") == "doorbell_active":
                    last_doorbell_active = str(item.get("value") or "")
                elif item.get("code") == "doorbell_pic":
                    last_doorbell_pic = str(item.get("value") or "")
    except Exception:
        pass

    print("[DOORBELL_MONITOR] Watching Videoportero Exterior for ring events", flush=True)
    while True:
        await asyncio.sleep(2.5)
        try:
            res = await asyncio.to_thread(tuya_service.service.cloud.getstatus, dev_id)
            if not res.get("success"):
                continue
            cur_alarm = last_alarm_msg
            cur_active = last_doorbell_active
            cur_pic = last_doorbell_pic
            for item in res.get("result", []):
                c = item.get("code")
                v = item.get("value")
                if c == "alarm_message":
                    cur_alarm = v
                elif c == "doorbell_active":
                    cur_active = str(v or "")
                elif c == "doorbell_pic":
                    cur_pic = str(v or "")

            triggered = False
            if cur_active and cur_active != last_doorbell_active:
                triggered = True
            if cur_pic and cur_pic != last_doorbell_pic:
                triggered = True
            if cur_alarm and cur_alarm != last_alarm_msg:
                try:
                    decoded = base64.b64decode(cur_alarm).decode("utf-8", errors="ignore")
                    print(f"[DOORBELL_MOTION_OR_EVENT] {decoded}", flush=True)
                except Exception:
                    pass

            last_alarm_msg = cur_alarm
            last_doorbell_active = cur_active
            last_doorbell_pic = cur_pic

            if triggered and (time.time() - last_trigger_time > 45.0):
                last_trigger_time = time.time()
                print("[DOORBELL_RING_DETECTED] Opening fullscreen videoportero!", flush=True)
                set_brightness(100)
                stream_res = await allocate_low_latency_stream(dev_id)
                payload = json.dumps({
                    "type": "DOORBELL_ALERT",
                    "title": "🔔 ¡Alguien está en la puerta!",
                    "cameraId": dev_id,
                    "stream_url": stream_res.get("url", "") if stream_res.get("success") else "",
                    "stream_data": stream_res if stream_res.get("success") else None
                })
                for ws in list(ACTIVE_SOCKETS):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        pass
        except Exception as ex:
            print("[DOORBELL_MONITOR_ERR]", ex, flush=True)

@app.on_event("startup")
async def start_doorbell_monitor():
    asyncio.create_task(monitor_doorbell_ring())


SAFE_VOLUME_LIMIT = 70  # Acoustic safety ceiling (prevents distortion/tear on internal speakers)
MAX_HW_VOLUME_PCT = 80  # Hardware ceiling (-20% below 100%, eliminates 120% overdrive/clipping)

def _get_raw_sink_volume_pct():
    try:
        res = subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2
        )
        m = re.search(r"(\d+)%", res.stdout or "")
        if m:
            return int(m.group(1))
    except Exception as e:
        print("[AUDIO_VOL_GET_ERR]", e, flush=True)
    return None

def _set_exact_hw_volume(target_ui_pct: int):
    target_hw = max(0, min(MAX_HW_VOLUME_PCT, int(round(target_ui_pct * MAX_HW_VOLUME_PCT / 100.0))))
    subprocess.run(
        ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_hw}%"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return target_hw

def get_system_volume_pct():
    raw = _get_raw_sink_volume_pct()
    if raw is None:
        return None
    if raw > MAX_HW_VOLUME_PCT:
        subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{MAX_HW_VOLUME_PCT}%"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        raw = MAX_HW_VOLUME_PCT
    return min(100, int(round(raw * 100.0 / MAX_HW_VOLUME_PCT)))

def adjust_system_volume(delta: str, force_unlock: bool = False):
    try:
        cur_ui = get_system_volume_pct()
        if cur_ui is None:
            cur_ui = 50
        m = re.match(r"^([+-]?\d+)%$", delta.strip())
        step_ui = int(m.group(1)) if m else 10
        raw_target = cur_ui + step_ui

        cfg = get_kiosk_config()
        is_unlocked = bool(cfg.get("high_volume_unlocked", False)) or force_unlock

        limit_triggered = False
        if step_ui > 0 and not is_unlocked and raw_target > SAFE_VOLUME_LIMIT:
            new_ui = SAFE_VOLUME_LIMIT
            limit_triggered = True
        else:
            new_ui = max(0, min(100, int(round(raw_target / 5.0) * 5)))

        target_hw = _set_exact_hw_volume(new_ui)
        print(f"[AUDIO_VOL] Adjusted volume by {delta} -> UI {new_ui}% (HW {target_hw}%, limit_triggered={limit_triggered})", flush=True)
        return new_ui, limit_triggered, raw_target
    except Exception as e:
        print("[AUDIO_VOL_ERR]", e, flush=True)
        return None, False, None

async def broadcast_volume_osd(pct, delta: str):
    payload = json.dumps({"type": "VOLUME_OSD", "volume": pct, "delta": delta})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

async def broadcast_volume_safety_warning(current_vol: int, requested_vol: int):
    payload = json.dumps({
        "type": "VOLUME_SAFETY_LIMIT",
        "current": current_vol,
        "requested": requested_vol
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

@app.post("/api/audio/volume")
async def api_audio_volume(request: Request):
    data = await request.json()
    delta = str(data.get("delta", "+10%"))
    force_unlock = bool(data.get("force_unlock", False))
    if delta in ("mute", "unmute", "toggle_mute"):
        arg = "1" if delta == "mute" else ("0" if delta == "unmute" else "toggle")
        subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-mute", "@DEFAULT_SINK@", arg],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        mres = subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "get-sink-mute", "@DEFAULT_SINK@"],
            capture_output=True, text=True, check=False
        )
        is_muted = "yes" in (mres.stdout or "").lower() or "sí" in (mres.stdout or "").lower()
        pct = 0 if is_muted else get_system_volume_pct()
        await broadcast_volume_osd(pct, delta)
        return {"status": "ok", "delta": delta, "muted": is_muted, "volume": pct}

    if delta not in ("+10%", "-10%", "+5%", "-5%"):
        delta = "+10%"
    subprocess.run(
        ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    pct, limit_trig, requested = adjust_system_volume(delta, force_unlock=force_unlock)
    if pct is not None:
        await broadcast_volume_osd(pct, delta)
        if limit_trig:
            await broadcast_volume_safety_warning(pct, requested or 80)
    return {
        "status": "limit_reached" if limit_trig else "ok",
        "delta": delta,
        "volume": pct,
        "safety_limit": SAFE_VOLUME_LIMIT,
        "limit_triggered": limit_trig,
        "requested": requested
    }

@app.post("/api/audio/volume/unlock")
async def api_audio_volume_unlock(request: Request):
    data = await request.json()
    unlocked = bool(data.get("unlocked", False))
    cfg = get_kiosk_config()
    cfg["high_volume_unlocked"] = unlocked
    save_kiosk_config(cfg)
    target = data.get("target_volume")
    if unlocked and target is not None:
        target_pct = max(0, min(100, int(target)))
        _set_exact_hw_volume(target_pct)
        await broadcast_volume_osd(target_pct, "set")
        current_vol = target_pct
    else:
        current_vol = get_system_volume_pct()
    return {"status": "ok", "high_volume_unlocked": unlocked, "volume": current_vol}

async def monitor_hardware_volume_keys():
    vol_devs = []
    for path in evdev.list_devices():
        try:
            d = evdev.InputDevice(path)
            if "gpio-keys" in d.name or "Asus WMI" in d.name:
                keys = d.capabilities().get(_e.EV_KEY, [])
                if _e.KEY_VOLUMEUP in keys or _e.KEY_VOLUMEDOWN in keys:
                    vol_devs.append(d)
        except Exception:
            pass

    if not vol_devs:
        print("[VOL_MONITOR] No hardware volume key device found", flush=True)
        return

    print(f"[VOL_MONITOR] Listening on {[d.path + ':' + d.name for d in vol_devs]}", flush=True)

    async def _watch(dev):
        try:
            async for ev in dev.async_read_loop():
                if ev.type == _e.EV_KEY and ev.value in (1, 2):
                    if ev.code == _e.KEY_VOLUMEUP:
                        pct, limit_trig, requested = adjust_system_volume("+10%")
                        if pct is not None:
                            await broadcast_volume_osd(pct, "+10%")
                            if limit_trig:
                                await broadcast_volume_safety_warning(pct, requested or 80)
                    elif ev.code == _e.KEY_VOLUMEDOWN:
                        pct, _, _ = adjust_system_volume("-10%")
                        if pct is not None:
                            await broadcast_volume_osd(pct, "-10%")
        except Exception:
            pass

    await asyncio.gather(*[_watch(d) for d in vol_devs])

@app.on_event("startup")
async def start_volume_monitor():
    get_system_volume_pct()
    asyncio.create_task(monitor_hardware_volume_keys())


# --- Cached Online Landscapes (Batch of 20) & Voice Arm ---
LANDSCAPES_CACHE_DIR = Path("/opt/domoskiosk/landscapes_cache")
LANDSCAPES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
LANDSCAPE_URLS = [
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1439066615861-d1af74d74000?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1366&h=768&q=80",
]

def _download_landscapes_batch_sync(force: bool = False):
    for idx, url in enumerate(LANDSCAPE_URLS):
        dest = LANDSCAPES_CACHE_DIR / f"land_{idx:02d}.jpg"
        if dest.exists() and dest.stat().st_size > 10000 and not force:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = r.read()
                if len(data) > 10000:
                    dest.write_bytes(data)
        except Exception as e:
            print(f"[LANDSCAPE_CACHE_ERR] {idx}: {e}", flush=True)

@app.on_event("startup")
async def warmup_landscapes_cache():
    asyncio.create_task(asyncio.to_thread(_download_landscapes_batch_sync, False))

@app.get("/api/landscapes")
async def api_list_landscapes():
    files = sorted(LANDSCAPES_CACHE_DIR.glob("land_*.jpg"))
    return {"photos": [f"/api/landscapes/img/{f.name}" for f in files if f.stat().st_size > 10000]}

@app.post("/api/landscapes/refresh")
async def api_refresh_landscapes():
    await asyncio.to_thread(_download_landscapes_batch_sync, True)
    files = sorted(LANDSCAPES_CACHE_DIR.glob("land_*.jpg"))
    return {"count": len(files)}

@app.get("/api/landscapes/img/{filename}")
async def api_get_landscape_img(filename: str):
    safe_name = Path(filename).name
    target = LANDSCAPES_CACHE_DIR / safe_name
    if not target.exists():
        return Response(status_code=404)
    return FileResponse(target, media_type="image/jpeg")

VOICE_ARMED_UNTIL = 0.0


@app.post("/api/radio/control")
async def api_radio_control(request: Request):
    data = await request.json()
    payload = json.dumps({
        "type": "RADIO_CONTROL",
        "action": data.get("action", "open"),
        "station": data.get("station", "")
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "ok"}

@app.post("/api/voice/arm")
async def api_arm_voice(seconds: float = 9.0):
    global VOICE_ARMED_UNTIL
    VOICE_ARMED_UNTIL = time.time() + seconds if seconds > 0 else 0.0
    try:
        Path("/tmp/domos_voice_arm").write_text(str(VOICE_ARMED_UNTIL))
    except Exception:
        pass
    return {"armed": seconds > 0, "until": VOICE_ARMED_UNTIL}

@app.get("/api/voice/arm")
async def api_get_voice_arm():
    return {"armed": time.time() < VOICE_ARMED_UNTIL}


@app.websocket("/ws/radio-vu")
async def ws_radio_vu(websocket: WebSocket):
    import struct
    import math
    await websocket.accept()
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "sudo", "-u", "domos", "env", "XDG_RUNTIME_DIR=/run/user/1000",
            "parec", "-d", "alsa_output.platform-bytcr_rt5640.HiFi__Speaker__sink.monitor",
            "--rate=8000", "--channels=1", "--format=s16le", "--latency-msec=40",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        chunk_bytes = 640  # 320 samples @ 8kHz = 40ms
        bars = [0] * 16
        while True:
            try:
                raw = await asyncio.wait_for(proc.stdout.readexactly(chunk_bytes), timeout=1.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps([0] * 16))
                continue
            samples = struct.unpack("<320h", raw)
            # 16-band real-time spectrum (80Hz..3600Hz) with Hann window + dB scaling
            if not hasattr(ws_radio_vu, "_basis"):
                n_s = 320
                win = [0.5 * (1.0 - math.cos(2.0 * math.pi * n / (n_s - 1))) for n in range(n_s)]
                freqs = [80 * (45.0 ** (i / 15.0)) for i in range(16)]
                ws_radio_vu._basis = [
                    [(win[n] * math.cos(2.0 * math.pi * f * n / 8000.0),
                      win[n] * math.sin(2.0 * math.pi * f * n / 8000.0)) for n in range(n_s)]
                    for f in freqs
                ]
            norm_s = [x / 32768.0 for x in samples]
            new_bars = []
            for i, b in enumerate(ws_radio_vu._basis):
                re = sum(norm_s[n] * b[n][0] for n in range(320))
                im = sum(norm_s[n] * b[n][1] for n in range(320))
                mag = math.sqrt(re * re + im * im) / 80.0
                # Tilt slightly up for higher frequencies so treble bars stay lively
                mag *= (1.0 + i * 0.14)
                db = 20.0 * math.log10(max(mag, 1e-5))
                lvl = max(0, min(100, int((db + 42.0) * (100.0 / 38.0))))
                bars[i] = max(lvl, int(bars[i] * 0.65))
                new_bars.append(bars[i])
            await websocket.send_text(json.dumps(new_bars))
    except Exception:
        pass
    finally:
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=1.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

def _adguard_request(path: str, method: str = "GET", payload: dict = None):
    import base64
    import urllib.request
    adguard_auth = os.environ.get("ADGUARD_BASIC_AUTH", "admin:admin")
    token = base64.b64encode(adguard_auth.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {token}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"http://127.0.0.1:3000{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}

@app.get("/api/adguard/stats")
async def api_adguard_stats():
    try:
        st = await asyncio.to_thread(_adguard_request, "/control/status")
        stats = await asyncio.to_thread(_adguard_request, "/control/stats")
        total = int(stats.get("num_dns_queries", 0) or 0)
        blocked = int(stats.get("num_blocked_filtering", 0) or 0)
        pct = round((blocked / total) * 100, 1) if total > 0 else 0.0
        avg_ms = round(float(stats.get("avg_processing_time", 0.0) or 0.0) * 1000.0, 1) if float(stats.get("avg_processing_time", 0.0) or 0.0) < 0.5 else round(float(stats.get("avg_processing_time", 0.0) or 0.0), 1)
        return {
            "online": True,
            "protection_enabled": bool(st.get("protection_enabled", False)),
            "version": st.get("version", ""),
            "num_dns_queries": total,
            "num_blocked_filtering": blocked,
            "block_pct": pct,
            "num_malware_blocked": int(stats.get("num_replaced_safebrowsing", 0) or 0),
            "num_parental_blocked": int(stats.get("num_replaced_parental", 0) or 0),
            "avg_processing_ms": avg_ms,
            "top_blocked_domains": (stats.get("top_blocked_domains") or [])[:8],
            "top_clients": (stats.get("top_clients") or [])[:6],
            "top_queried_domains": (stats.get("top_queried_domains") or [])[:6],
        }
    except Exception as e:
        return {"online": False, "error": str(e)}

@app.post("/api/adguard/toggle")
async def api_adguard_toggle(request: Request):
    data = await request.json()
    enabled = bool(data.get("enabled", True))
    await asyncio.to_thread(_adguard_request, "/control/protection", "POST", {"enabled": enabled})
    return await api_adguard_stats()


app.mount("/", StaticFiles(directory="/opt/domoskiosk/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

