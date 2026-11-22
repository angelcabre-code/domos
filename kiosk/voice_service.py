#!/usr/bin/env python3
"""
Domos Voice Assistant Engine (Spanish / Vosk Offline + Piper es_ES Male TTS)
Fast partial wake-word detection, rich offline Spanish intent comprehension,
and smooth Iberian Spanish male voice replies via Piper (es_ES-davefx-medium).
"""
import datetime
import json
import logging
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import unicodedata
import requests
import sounddevice as sd
from vosk import Model, KaldiRecognizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [VOZ] %(message)s")

MODEL_PATH = "/opt/domoskiosk/voice_models/vosk-model-small-es-0.42"
PIPER_BIN = "/opt/domoskiosk/tts/piper/piper"
PIPER_MODEL = "/opt/domoskiosk/tts/es_ES-davefx-medium.onnx"
API_URL = "http://127.0.0.1:8080"
WAKE_ALIASES = ("domos", "domo", "domas", "nomas", "tomos", "tomo", "tomas", "somos", "donos", "damos", "domus", "dobles", "lomos")

DAYS_ES = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MONTHS_ES = ("", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")

RADIO_MAP = {
    "cadena 100": ("cadena100", "Cadena 100"),
    "cadena cien": ("cadena100", "Cadena 100"),
    "cadena siento": ("cadena100", "Cadena 100"),
    "la cien": ("cadena100", "Cadena 100"),
    "europa": ("europafm", "Europa FM"),
    "planeta": ("radioplaneta", "Radio Planeta"),
    "loca": ("locafm", "Loca FM"),
    "cuarenta": ("los40", "LOS40"),
    "40": ("los40", "LOS40"),
    "cadena ser": ("cadenaser", "Cadena SER"),
    "la ser": ("cadenaser", "Cadena SER"),
    "radio ser": ("cadenaser", "Cadena SER"),
    "pon ser": ("cadenaser", "Cadena SER"),
    "cope": ("cope", "COPE"),
    "onda cero": ("ondacero", "Onda Cero"),
    "radio 3": ("radio3", "RNE Radio 3"),
    "kiss": ("kissfm", "Kiss FM"),
    "quis": ("kissfm", "Kiss FM"),
    "chillout": ("chillout", "Antenne Chillout"),
    "chill out": ("chillout", "Antenne Chillout"),
    "chill": ("chillout", "Antenne Chillout"),
    "lofi": ("groovesalad", "SomaFM Groove Salad"),
    "lo fi": ("groovesalad", "SomaFM Groove Salad"),
    "groove": ("groovesalad", "SomaFM Groove Salad"),
    "relajante": ("groovesalad", "SomaFM Groove Salad"),
}

q = queue.Queue()
tts_lock = threading.Lock()
tts_busy_until = 0.0

def norm_text(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    for w, d in (("uno", "1"), ("una", "1"), ("dos", "2"), ("tres", "3"), ("cien", "100")):
        s = s.replace(f" {w}", f" {d}")
    return s.strip()

piper_proc = None

def get_piper_proc():
    global piper_proc
    if piper_proc is None or piper_proc.poll() is not None:
        piper_proc = subprocess.Popen(
            [PIPER_BIN, "--model", PIPER_MODEL, "--length_scale", "1.06", "--json-input"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    return piper_proc

def speak_text(text: str):
    if not text or not os.path.exists(PIPER_BIN) or not os.path.exists(PIPER_MODEL):
        return
    clean_speech = text.replace("°C", " grados").replace("·", ",").replace("%", " por ciento")
    def _run():
        global tts_busy_until, piper_proc
        with tts_lock:
            tts_busy_until = time.time() + max(2.0, len(clean_speech) * 0.08)
            wav_path = "/tmp/domos_tts_reply.wav"
            try:
                proc = get_piper_proc()
                payload = json.dumps({"text": clean_speech, "output_file": wav_path}) + "\n"
                proc.stdin.write(payload)
                proc.stdin.flush()
                proc.stdout.readline()
                subprocess.run(["paplay", wav_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            except Exception as e:
                logging.warning(f"TTS error: {e}")
                piper_proc = None
            finally:
                tts_busy_until = time.time() + 0.5
    threading.Thread(target=_run, daemon=True).start()

def set_ui_assistant(state: str, prompt: str = "", reply: str = ""):
    try:
        requests.post(f"{API_URL}/api/assistant/state", json={
            "state": state,
            "prompt": prompt,
            "reply": reply,
        }, timeout=1.2)
    except Exception:
        pass

def arm_voice_backend(seconds: float = 9.0):
    try:
        until = time.time() + seconds if seconds > 0 else 0.0
        Path("/tmp/domos_voice_arm").write_text(str(until))
        requests.post(f"{API_URL}/api/voice/arm?seconds={seconds}", timeout=1.0)
    except Exception:
        pass

def schedule_idle_reset(delay_sec: float = 5.5):
    def _reset():
        time.sleep(delay_sec)
        set_ui_assistant("idle")
    threading.Thread(target=_reset, daemon=True).start()

def is_voice_armed() -> bool:
    try:
        p = Path("/tmp/domos_voice_arm")
        if p.exists():
            return time.time() < float(p.read_text().strip() or "0")
    except Exception:
        pass
    return False

def audio_callback(indata, frames, time_info, status):
    if status:
        logging.warning(f"Audio status: {status}")
    q.put(bytes(indata))

def weather_code_es(code: int) -> str:
    if code == 0:
        return "despejado"
    if 1 <= code <= 3:
        return "parcialmente nublado"
    if 45 <= code <= 48:
        return "niebla"
    if 51 <= code <= 67:
        return "lluvia"
    if 71 <= code <= 77:
        return "nieve"
    if 80 <= code <= 82:
        return "chubascos"
    if code >= 95:
        return "tormenta"
    return "variable"

def get_weather_reply(tomorrow: bool = False) -> str:
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=36.7167&longitude=-4.2833"
            "&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=2",
            timeout=3,
        )
        if r.ok:
            d = r.json()
            daily = d.get("daily", {})
            if tomorrow and len(daily.get("temperature_2m_max") or []) > 1:
                cond = weather_code_es(int((daily.get("weather_code") or [0, 0])[1]))
                tmax = round(daily["temperature_2m_max"][1])
                tmin = round(daily["temperature_2m_min"][1])
                rain = (daily.get("precipitation_probability_max") or [0, 0])[1]
                return f"Mañana en Rincón de la Victoria se espera {cond}, máxima de {tmax}°C, mínima de {tmin}°C y {rain}% de lluvia."
            cur = d.get("current", {})
            t = round(cur.get("temperature_2m", 0))
            cond = weather_code_es(int(cur.get("weather_code", 0)))
            tmax = round((daily.get("temperature_2m_max") or [t])[0])
            tmin = round((daily.get("temperature_2m_min") or [t])[0])
            rain = (daily.get("precipitation_probability_max") or [0])[0]
            return f"En Rincón de la Victoria hay {t}°C, {cond}. Máxima de {tmax}°C, mínima de {tmin}°C y {rain}% de lluvia."
    except Exception:
        pass
    return "No pude consultar el tiempo en este momento."

def match_and_control_devices(clean_text: str, is_on: bool):
    try:
        res = requests.get(f"{API_URL}/api/devices", timeout=2)
        if not res.ok:
            return None
        data = res.json()
        lights = data.get("lights") or []
        plugs = data.get("plugs") or []
        candidates = lights + plugs

        if any(p in clean_text for p in ("todas las luces", "todas", "todo")):
            matched = lights if "luz" in clean_text or "luces" in clean_text else candidates
        else:
            matched = []
            for dev in candidates:
                dname = norm_text(dev.get("name", ""))
                short = dname.replace("luz ", "").replace("led ", "").strip()
                if dname in clean_text or (short and short in clean_text):
                    matched.append(dev)
            if not matched and "cocina" in clean_text:
                matched = [d for d in lights if "cocina" in norm_text(d.get("name", ""))]
            elif not matched and "habitacion" in clean_text:
                matched = [d for d in lights if "habitacion" in norm_text(d.get("name", ""))]

        if not matched:
            return None
        names = []
        for dev in matched:
            requests.post(f"{API_URL}/api/devices/control", json={
                "device_id": dev["id"],
                "code": "switch_1",
                "value": is_on,
            }, timeout=2)
            names.append(dev.get("name"))
        return names
    except Exception as e:
        logging.error(f"Error controlando dispositivo: {e}")
        return None

def execute_command(raw_text: str):
    clean = norm_text(raw_text)
    logging.info(f"Comando reconocido: '{clean}'")
    set_ui_assistant("processing", prompt=raw_text.capitalize())
    reply_msg = "No entendí la orden. Prueba con luces, tiempo, hora, placas o radio."

    import re as _re_cmd

    # 00Z. Intercomunicador a altavoces Google (Salita, Dormitorio, Sótano, Todos)
    if any(k in clean for k in ("avisa en ", "anuncia en ", "di en ", "megafonia", "intercomunicador")):
        target = "all"
        if "sotano" in clean:
            target = "sotano"
        elif "dormitorio" in clean or "habitacion" in clean:
            target = "dormitorio_1"
        elif "salita" in clean or "cocina" in clean:
            target = "salita"
        msg_body = raw_text
        for sep in (" que ", " en el sotano ", " en el dormitorio ", " en la cocina ", " en la salita ", " en toda la casa "):
            if sep in raw_text.lower():
                msg_body = raw_text.lower().split(sep, 1)[1].strip()
                break
        if len(msg_body) < 2:
            msg_body = "Atención desde el salón."
        try:
            requests.post(f"{API_URL}/api/cast/announce", json={"targets": target, "text": msg_body}, timeout=8)
            reply_msg = f"Aviso enviado a {'toda la casa' if target == 'all' else target}."
        except Exception:
            reply_msg = "No pude enviar el aviso a los altavoces Google."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(4.5)
        return

    # 00Y. Doctor DOMOS: leer diagnóstico en voz alta
    if any(k in clean for k in ("diagnostico", "doctor", "salud del sistema", "informe de salud", "lee el informe")):
        try:
            requests.post(f"{API_URL}/api/doctor/speak", timeout=15)
            set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply="Leyendo el diagnóstico de Doctor DOMOS...")
            schedule_idle_reset(12.0)
        except Exception:
            reply_msg = "No pude leer el diagnóstico de Doctor DOMOS."
            set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
            speak_text(reply_msg)
            schedule_idle_reset(5.0)
        return

    # 0A. Silenciar timbre del videoportero
    if any(k in clean for k in ("silencia el timbre", "para el timbre", "calla el timbre", "quita el timbre", "silenciar timbre", "parar timbre")):
        try:
            requests.post(f"{API_URL}/api/doorbell/silence", timeout=2)
            reply_msg = "Timbre silenciado."
        except Exception:
            reply_msg = "No pude silenciar el timbre."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(4.0)
        return

    # 0B. Calidad del Aire, CO2 y Polen (antes de "aire" para no confundir con Aire Acondicionado)
    if any(k in clean for k in ("calidad del aire", "calidad aire", "polen", "co2", "dioxido", "particulas", "aire del sotano", "aire interior", "humo")):
        try:
            aq = requests.get(f"{API_URL}/api/air/quality", timeout=3).json()
            ev = aq.get("evaluation") or {}
            ind = aq.get("indoor") or {}
            pur = ind.get("purifier") or {}
            sot = ind.get("sotano") or {}
            out = aq.get("outdoor") or {}
            badge = str(ev.get("badge") or "Buena").replace("🟢", "").replace("🟡", "").replace("🔴", "").strip()
            reply_msg = (
                f"La calidad del aire es {badge}. "
                f"En el salón hay {pur.get('aqi', '--')} de PM2.5, "
                f"en el sótano {sot.get('co2', '--')} partes por millón de CO2, "
                f"y el polen exterior está {out.get('pollen_level', 'bajo')}."
            )
        except Exception:
            reply_msg = "No pude consultar la calidad del aire ahora mismo."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(6.5)
        return

    # 0C. Ahorro Solar y Autoconsumo Inteligente (consulta + cambio de modo)
    if any(k in clean for k in ("autoconsumo", "ahorro solar", "excedente", "excedentes", "modo vacaciones", "pausa el ahorro", "pausar ahorro", "como va el ahorro")):
        try:
            if "vacaciones" in clean:
                requests.post(f"{API_URL}/api/energy/savings/mode", json={"mode": "vacation"}, timeout=2)
                reply_msg = "Modo vacaciones activado. Termo y secatoallas permanecerán apagados."
            elif any(w in clean for w in ("pausa", "deten", "desactiva", "manual", "quita")):
                requests.post(f"{API_URL}/api/energy/savings/mode", json={"mode": "paused"}, timeout=2)
                reply_msg = "Autoconsumo pausado en modo manual."
            elif any(w in clean for w in ("activa", "enciende", "pon", "reanuda")):
                requests.post(f"{API_URL}/api/energy/savings/mode", json={"mode": "auto"}, timeout=2)
                reply_msg = "Autoconsumo inteligente activado."
            else:
                es = requests.get(f"{API_URL}/api/energy/savings", timeout=3).json()
                mode_map = {"auto": "activo", "paused": "pausado", "vacation": "en modo vacaciones"}
                m_txt = mode_map.get((es.get("config") or {}).get("mode", "auto"), "activo")
                tel = es.get("telemetry") or {}
                s_kwh = (es.get("summary") or {}).get("total_saved_kwh_today", 0)
                reply_msg = (
                    f"El ahorro solar está {m_txt}. "
                    f"Generación actual de {int(tel.get('solar_w', 0))} vatios y {s_kwh} kilovatios hora aprovechados hoy."
                )
        except Exception:
            reply_msg = "No pude consultar el ahorro solar."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(6.0)
        return

    # 0D. Avisos, Incidencias y Alertas del Hogar
    if any(k in clean for k in ("avisos", "aviso", "incidencias", "incidencia", "alertas", "alerta", "pilas", "bateria baja", "baterias bajas")):
        try:
            if any(w in clean for w in ("silencia", "borra", "quita", "limpia", "resuelve", "revisado")):
                requests.post(f"{API_URL}/api/incidents/resolve", json={}, timeout=2)
                reply_msg = "Todos los avisos han sido silenciados."
            else:
                inc = requests.get(f"{API_URL}/api/incidents", timeout=3).json()
                items = inc.get("incidents") or []
                if not items:
                    reply_msg = "No hay ningún aviso activo. Todo funciona correctamente en casa."
                else:
                    titles = [i.get("title", "Aviso") for i in items[:3]]
                    extra = f" y {len(items) - 3} más" if len(items) > 3 else ""
                    reply_msg = f"Tienes {len(items)} avisos activos: " + ", ".join(titles) + extra + "."
        except Exception:
            reply_msg = "No pude consultar los avisos del sistema."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(6.5)
        return

    # 0E. Armar / Desarmar Alarma + Consulta completa de seguridad
    if any(k in clean for k in ("arma la alarma", "armar alarma", "activa la alarma", "activar alarma", "pon la alarma", "poner alarma", "alarma en casa", "desarma", "desarmar", "quita la alarma", "desactiva la alarma")):
        try:
            if any(w in clean for w in ("desarma", "desarmar", "quita", "desactiva", "apaga")):
                requests.post(f"{API_URL}/api/devices/control", json={"device_id": "64326051e8db8480acc0", "code": "master_mode", "value": "disarmed"}, timeout=3)
                reply_msg = "Alarma desarmada."
            elif "en casa" in clean or "noche" in clean or "parcial" in clean:
                requests.post(f"{API_URL}/api/devices/control", json={"device_id": "64326051e8db8480acc0", "code": "master_mode", "value": "home"}, timeout=3)
                reply_msg = "Alarma armada en modo en casa."
            else:
                requests.post(f"{API_URL}/api/devices/control", json={"device_id": "64326051e8db8480acc0", "code": "master_mode", "value": "armed"}, timeout=3)
                reply_msg = "Alarma armada en modo total."
        except Exception:
            reply_msg = "No pude cambiar el estado de la alarma."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.0)
        return

    # 0F. Copia de seguridad (Backup) por voz
    if any(k in clean for k in ("copia de seguridad", "backup", "respaldo")):
        try:
            bres = requests.post(f"{API_URL}/api/system/backup", timeout=15).json()
            created = bres.get("created") or {}
            sd_txt = " y copiada en la tarjeta SD" if created.get("sd_mirrored") else ""
            reply_msg = f"Copia de seguridad completada con {created.get('files_count', 0)} archivos{sd_txt}."
        except Exception:
            reply_msg = "Hubo un problema al crear la copia de seguridad."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.5)
        return

    # 0G. Agenda / Calendario Familiar
    if any(k in clean for k in ("agenda", "calendario", "eventos", "citas", "que tengo hoy", "que tengo manana", "recordatorios")):
        try:
            cal = requests.get(f"{API_URL}/api/calendar", timeout=3).json()
            evs = cal.get("events") or []
            target_dt = datetime.datetime.now() + (datetime.timedelta(days=1) if "manana" in clean else datetime.timedelta(days=0))
            target_str = target_dt.strftime("%Y-%m-%d")
            day_lbl = "mañana" if "manana" in clean else "hoy"
            day_evs = [e for e in evs if str(e.get("date", "")).startswith(target_str)]
            if not day_evs:
                reply_msg = f"No tienes ningún evento apuntado para {day_lbl}."
            else:
                desc = []
                for e in day_evs[:4]:
                    t_str = f" a las {e['reminder_time']}" if e.get("reminder_time") else ""
                    desc.append(f"{e.get('title', 'Evento')}{t_str}")
                reply_msg = f"Para {day_lbl} tienes {len(day_evs)} eventos: " + ", ".join(desc) + "."
        except Exception:
            reply_msg = "No pude consultar el calendario."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(6.5)
        return

    # 0H. Consumo eléctrico de enchufes (en vivo + hoy)
    if any(k in clean for k in ("consumo", "cuanto consume", "gasto electrico", "cuanto gasta")):
        try:
            ph = requests.get(f"{API_URL}/api/power/history?period=daily", timeout=3).json()
            totals = ph.get("totals") or {}
            termo_kwh = round(float(totals.get("termo", 0)), 2)
            sec_kwh = round(float(totals.get("secatoallas", 0)), 2)
            sot_kwh = round(float(totals.get("breaker_sotano", 0)), 2)
            reply_msg = (
                f"Hoy llevan consumidos: el termo {termo_kwh} kilovatios hora, "
                f"el secatoallas {sec_kwh}, y el sótano {sot_kwh} kilovatios hora."
            )
        except Exception:
            reply_msg = "No pude consultar el consumo eléctrico."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(6.0)
        return

    # 0I. Luz Dormitorio (IR local 192.168.5.73)
    if any(k in clean for k in ("luz del dormitorio", "luz dormitorio", "lampara del dormitorio", "lampara dormitorio")):
        try:
            requests.post(f"{API_URL}/api/devices/control", json={"device_id": "bffaf4f9e3e652a793t9n0", "code": "PowerToggle", "value": "PowerToggle"}, timeout=3)
            reply_msg = "Enviando señal infrarroja a la luz del dormitorio."
        except Exception:
            reply_msg = "No pude accionar la luz del dormitorio."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(4.5)
        return

    # 0J. Volúmenes independientes por canal (radio, timbre, cámaras, general)
    if "volumen" in clean and any(ch in clean for ch in ("radio", "timbre", "portero", "camara", "camaras", "general")):
        ch_key = "master"
        ch_lbl = "general"
        if "radio" in clean:
            ch_key, ch_lbl = "radio", "de la radio"
        elif "timbre" in clean:
            ch_key, ch_lbl = "doorbell", "del timbre"
        elif any(w in clean for w in ("camara", "camaras", "portero")):
            ch_key, ch_lbl = "cameras", "de las cámaras"
        try:
            cur_v = (requests.get(f"{API_URL}/api/audio/volumes", timeout=2).json().get("volumes") or {}).get(ch_key, 75)
            m_pct = _re_cmd.search(r"(\d{1,3})", clean)
            if m_pct:
                new_v = max(0, min(100, int(m_pct.group(1))))
            elif any(w in clean for w in ("baja", "menos", "suave", "flojo")):
                new_v = max(0, int(cur_v) - 15)
            else:
                new_v = min(100, int(cur_v) + 15)
            requests.post(f"{API_URL}/api/audio/volumes", json={ch_key: new_v}, timeout=2)
            reply_msg = f"Volumen {ch_lbl} ajustado al {new_v} por ciento."
        except Exception:
            reply_msg = f"No pude ajustar el volumen {ch_lbl}."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(4.5)
        return

    # 00. Dispositivos Xiaomi (Aspiradora & Purificador)
    if any(k in clean for k in ("aspirador", "aspiradora", "robot", "limpia la casa", "barrer")):
        if any(w in clean for w in ("base", "carga", "vuelve", "casa", "regresa")):
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "647544791", "action": "home"}, timeout=4)
            reply_msg = "Mandando el aspirador de vuelta a la base."
        elif any(w in clean for w in ("para", "pausa", "deten", "apaga")):
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "647544791", "action": "pause"}, timeout=4)
            reply_msg = "Pausando la aspiradora."
        else:
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "647544791", "action": "start"}, timeout=4)
            reply_msg = "Poniendo en marcha la aspiradora."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.0)
        return
    elif "purificador" in clean:
        if "noche" in clean or "silencio" in clean:
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "314954236", "action": "mode", "value": "silent"}, timeout=4)
            reply_msg = "Purificador en modo noche."
        elif "favorito" in clean or "maximo" in clean or "fuerte" in clean:
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "314954236", "action": "mode", "value": "favorite"}, timeout=4)
            reply_msg = "Purificador en modo favorito."
        elif "auto" in clean:
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "314954236", "action": "mode", "value": "auto"}, timeout=4)
            reply_msg = "Purificador en modo automático."
        elif any(w in clean for w in ("apaga", "desactiva", "quita", "para")):
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "314954236", "action": "power", "value": False}, timeout=4)
            reply_msg = "Apagando el purificador de aire."
        else:
            requests.post(f"{API_URL}/api/xiaomi/control", json={"device_id": "314954236", "action": "power", "value": True}, timeout=4)
            reply_msg = "Encendiendo el purificador de aire."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.0)
        return

    # 0. Aire acondicionado & TV IR
    if any(k in clean for k in ("aire", "climatizacion", "aire acondicionado")):
        ac_id = "215081148c4f0047898d" if "pueblo" in clean else "607584008c4f0049de61"
        ac_name = "Aire del Pueblo" if "pueblo" in clean else "Aire acondicionado"
        import re as _re_ac
        m_temp = _re_ac.search(r"(\d{2})\s*grado", clean)
        if m_temp:
            deg = max(16, min(30, int(m_temp.group(1))))
            requests.post(f"{API_URL}/api/devices/control", json={"device_id": ac_id, "code": "temp_set", "value": deg * 10}, timeout=2)
            reply_msg = f"{ac_name} ajustado a {deg} grados."
        elif any(w in clean for w in ("apaga", "desactiva", "quita", "para")):
            requests.post(f"{API_URL}/api/devices/control", json={"device_id": ac_id, "code": "switch", "value": False}, timeout=2)
            reply_msg = f"Apagando {ac_name}."
        else:
            requests.post(f"{API_URL}/api/devices/control", json={"device_id": ac_id, "code": "switch", "value": True}, timeout=2)
            reply_msg = f"Encendiendo {ac_name}."
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.0)
        return
    elif any(k in clean for k in ("tele", "television", "televisor")):
        is_bedroom = any(w in clean for w in ("dormitorio", "habitacion", "cuarto"))
        tv_id = "bf9b0283af185020bd8evy" if is_bedroom else "bf221ae9a7e021a4374abl"
        tv_lbl = "del dormitorio" if is_bedroom else "del salón"
        if any(w in clean for w in ("sube canal", "siguiente canal", "canal arriba", "otro canal")):
            code, reply_msg = "Channel+", f"Cambiando al siguiente canal en la tele {tv_lbl}."
        elif any(w in clean for w in ("baja canal", "canal anterior", "canal abajo")):
            code, reply_msg = "Channel-", f"Cambiando al canal anterior en la tele {tv_lbl}."
        elif any(w in clean for w in ("sube", "mas volumen")):
            code, reply_msg = "Volume+", f"Subiendo el volumen de la tele {tv_lbl}."
        elif any(w in clean for w in ("baja", "menos volumen")):
            code, reply_msg = "Volume-", f"Bajando el volumen de la tele {tv_lbl}."
        elif any(w in clean for w in ("atras", "volver", "vuelve")):
            code, reply_msg = "Back", f"Pulsando atrás en la tele {tv_lbl}."
        elif any(w in clean for w in ("inicio", "home", "menu")):
            code, reply_msg = "Home", f"Abriendo inicio en la tele {tv_lbl}."
        elif "ok" in clean or "acepta" in clean:
            code, reply_msg = "OK", f"Pulsando OK en la tele {tv_lbl}."
        else:
            code, reply_msg = "Power", f"Enviando encendido a la tele {tv_lbl}."
        requests.post(f"{API_URL}/api/devices/control", json={"device_id": tv_id, "code": code, "value": code}, timeout=3)
        set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
        speak_text(reply_msg)
        schedule_idle_reset(5.0)
        return

    # 1. Saludos / Ayuda
    if any(w in clean for w in ("hola", "buenos dias", "buenas tardes", "buenas noches")):
        reply_msg = "Hola, soy Domos. ¿En qué te puedo ayudar?"
    elif any(w in clean for w in ("quien eres", "que sabes hacer", "ayuda")):
        reply_msg = "Controlo luces, enchufes, teles, aires, alarma, timbre, volúmenes, radio, ahorro solar, calidad del aire, avisos, agenda y copias de seguridad."
    elif "gracias" in clean:
        reply_msg = "De nada, para eso estoy."

    # 2. Hora y fecha
    elif any(w in clean for w in ("que hora", "la hora", "hora es", "que dia", "fecha")):
        now = datetime.datetime.now()
        reply_msg = f"Son las {now:%H:%M} del {DAYS_ES[now.weekday()]} {now.day} de {MONTHS_ES[now.month]}."

    # 3. Tiempo exterior
    elif any(w in clean for w in ("que tiempo", "tiempo hace", "clima", "llueve", "llover", "pronostico", "prevision", "temperatura exterior", "calor", "frio")):
        reply_msg = get_weather_reply(tomorrow=("manana" in clean))

    # 4. Temperatura / humedad interior
    elif any(w in clean for w in ("temperatura", "humedad", "grados", "salon", "dormitorio")):
        try:
            clim = requests.get(f"{API_URL}/api/devices", timeout=2).json().get("climate") or []
            parts = []
            for c in clim:
                st = c.get("state") or {}
                name = c.get("name", "").replace("Higrómetro ", "")
                parts.append(f"En el {name} hay {st.get('temperature', '--')}°C y {st.get('humidity', '--')}% de humedad")
            reply_msg = ". ".join(parts) if parts else "Sin datos de sensores interiores."
        except Exception:
            reply_msg = "No pude leer los sensores interiores."

    # 5. Placas solares
    elif any(w in clean for w in ("placa", "solar", "solares", "vatios", "energia", "produciendo")):
        try:
            d = requests.get(f"{API_URL}/api/solar/details", timeout=3).json()
            s = (d.get("solar") or {}).get("state") or {}
            ex = d.get("extra") or {}
            kwh = round((ex.get("total_forward_energy") or 0) / 100.0, 2)
            reply_msg = f"Las placas producen {s.get('watts', 0)} vatios ahora mismo, con {kwh} kilovatios hora acumulados."
        except Exception:
            reply_msg = "No pude consultar las placas solares."

    # 6. Puerta y alarma
    elif any(w in clean for w in ("alarma", "seguridad", "esta abierta la puerta", "como esta la puerta")):
        try:
            sec = requests.get(f"{API_URL}/api/devices", timeout=2).json().get("security") or {}
            door_txt = "abierta" if sec.get("door_open") else "cerrada"
            alarm_txt = "armada" if sec.get("alarm_armed") else "desarmada"
            reply_msg = f"La puerta está {door_txt} y la alarma está {alarm_txt}."
        except Exception:
            reply_msg = "No pude consultar la seguridad."

    # 7. Radio
    elif any(w in clean for w in ("radio", "emisora", "musica")) or any(k in clean for k in RADIO_MAP):
        if any(w in clean for w in ("para", "apaga", "deten", "quita", "silencia")):
            requests.post(f"{API_URL}/api/radio/control", json={"action": "stop"}, timeout=2)
            reply_msg = "Radio detenida."
        else:
            chosen = None
            for k, v in RADIO_MAP.items():
                if k in clean:
                    chosen = v
                    break
            if chosen:
                requests.post(f"{API_URL}/api/radio/control", json={"action": "play", "station": chosen[0]}, timeout=2)
                reply_msg = f"Poniendo {chosen[1]}."
            else:
                requests.post(f"{API_URL}/api/radio/control", json={"action": "open"}, timeout=2)
                reply_msg = "Abriendo selector de radio."

    # 8. Volumen y silencio
    elif any(w in clean for w in ("quita el silencio", "activa el sonido", "desmutea", "con sonido")):
        requests.post(f"{API_URL}/api/audio/volume", json={"delta": "unmute"}, timeout=2)
        reply_msg = "Sonido activado."
    elif any(w in clean for w in ("silencio", "silencia", "mutea", "quita el sonido", "sin sonido", "callate")):
        requests.post(f"{API_URL}/api/audio/volume", json={"delta": "mute"}, timeout=2)
        reply_msg = "Sonido silenciado."
    elif any(w in clean for w in ("volumen", "mas alto", "mas bajo", "mas fuerte", "mas flojo", "sube el sonido", "baja el sonido")):
        delta = "-10%" if any(w in clean for w in ("baja", "menos", "bajo", "flojo", "suave")) else "+10%"
        try:
            vres = requests.post(f"{API_URL}/api/audio/volume", json={"delta": delta}, timeout=2)
            vdata = vres.json() if vres.ok else {}
            if vdata.get("limit_triggered"):
                reply_msg = "Volumen frenado al 70 por ciento por seguridad. Confírmalo en pantalla si deseas subir más."
            else:
                reply_msg = "Subiendo el volumen." if delta == "+10%" else "Bajando el volumen."
        except Exception:
            reply_msg = "Ajustando el volumen."

    # 9. Videoportero / Cámaras
    elif any(w in clean for w in ("portero", "timbre", "camara", "camaras", "puerta", "quien es", "quien llama")):
        reply_msg = "Mostrando el videoportero exterior."
        try:
            requests.post(f"{API_URL}/api/doorbell/trigger", json={"title": "Videoportero (Voz)"}, timeout=2)
        except Exception:
            pass

    # 10. Cerrar visor / Volver al marco
    elif any(w in clean for w in ("cierra", "cerrar", "marco", "fotos", "salvapantallas", "atras")):
        reply_msg = "Volviendo al marco de fotos."
        try:
            requests.post(f"{API_URL}/api/doorbell/dismiss", timeout=2)
        except Exception:
            pass

    # 11. Brillo / Pantalla
    elif any(w in clean for w in ("apaga pantalla", "apagar pantalla", "modo noche", "atenuar", "oscurecer")):
        reply_msg = "Atenuando la pantalla a modo noche."
        try:
            requests.post(f"{API_URL}/api/brightness", json={"brightness": 10}, timeout=2)
        except Exception:
            pass
    elif any(w in clean for w in ("enciende pantalla", "encender pantalla", "maximo brillo", "brillo")):
        reply_msg = "Brillo restablecido al 80 por ciento."
        try:
            requests.post(f"{API_URL}/api/brightness", json={"brightness": 80}, timeout=2)
        except Exception:
            pass

    # 12. Luces y enchufes Tuya
    elif any(w in clean for w in ("enciende", "encender", "prende", "pon", "activa", "apaga", "apagar", "desconecta", "quita")):
        is_on = not any(w in clean for w in ("apaga", "apagar", "desconecta", "quita"))
        names = match_and_control_devices(clean, is_on)
        if names:
            action = "Encendiendo" if is_on else "Apagando"
            reply_msg = f"{action} {', '.join(names)}."
        else:
            reply_msg = "No encontré ese dispositivo."

    set_ui_assistant("speaking", prompt=raw_text.capitalize(), reply=reply_msg)
    speak_text(reply_msg)
    schedule_idle_reset(5.5)

STRICT_WAKE_WORDS = ("domos", "domo", "domas", "domus", "donos", "tomos", "lomos")

def strip_wake_word(clean_text: str):
    words = clean_text.split()
    if not words:
        return False, ""
    if words[0] in WAKE_ALIASES:
        return True, " ".join(words[1:]).strip()
    if len(words) <= 2 and any(w in WAKE_ALIASES for w in words):
        rem = " ".join(w for w in words if w not in WAKE_ALIASES).strip()
        return True, rem
    # Also detect strict wake word anywhere in a longer sentence (e.g. when TV audio precedes "Domos")
    for idx in range(len(words) - 1, -1, -1):
        if words[idx] in STRICT_WAKE_WORDS:
            return True, " ".join(words[idx + 1:]).strip()
    return False, clean_text

def main():
    logging.info("Cargando modelo de reconocimiento de voz en español...")
    if os.path.exists(PIPER_BIN) and os.path.exists(PIPER_MODEL):
        get_piper_proc()
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=3200, dtype="int16",
                           channels=1, callback=audio_callback):
        logging.info("Motor de voz 'Domos' activo con Piper TTS (es_ES-davefx-medium)...")
        active_until = 0.0
        armed_cache = False
        last_arm_check = 0.0
        last_partial_wake = 0.0

        while True:
            data = q.get()
            now = time.time()
            if now < tts_busy_until:
                continue

            samples = memoryview(data).cast("h")[::16]
            avg_amp = sum(abs(s) for s in samples) / max(1, len(samples))

            if now - last_arm_check > 0.3:
                last_arm_check = now
                armed_cache = is_voice_armed()

            if avg_amp > 45 or armed_cache:
                active_until = now + 4.0
            if now > active_until:
                continue

            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text = (res.get("text") or "").strip()
                if text:
                    logging.info(f"Escuchado: '{text}' (armed={armed_cache})")
                    clean = norm_text(text)
                    has_wake, remainder = strip_wake_word(clean)
                    if has_wake and not remainder:
                        arm_voice_backend(9.0)
                        armed_cache = True
                        set_ui_assistant("listening", prompt="Te escucho...", reply='Di tu orden ahora (ej. "Qué tiempo hace hoy")')
                        schedule_idle_reset(9.0)
                    elif has_wake and remainder:
                        arm_voice_backend(0.0)
                        armed_cache = False
                        execute_command(remainder)
                    elif armed_cache:
                        if (now - last_partial_wake < 2.5) and len(clean.split()) <= 2:
                            # Finalized wake-word revision (e.g. domos -> domas/nomas); keep listening
                            pass
                        else:
                            arm_voice_backend(0.0)
                            armed_cache = False
                            execute_command(clean)
            else:
                if not armed_cache and (now - last_partial_wake > 3.0):
                    part = json.loads(rec.PartialResult()).get("partial", "")
                    if part:
                        has_wake, _ = strip_wake_word(norm_text(part))
                        if has_wake:
                            last_partial_wake = now
                            arm_voice_backend()
                            armed_cache = True
                            set_ui_assistant("listening", prompt="Te escucho...", reply='Di tu orden ahora (ej. "Qué tiempo hace hoy")')
                            schedule_idle_reset(9.0)

if __name__ == "__main__":
    main()
