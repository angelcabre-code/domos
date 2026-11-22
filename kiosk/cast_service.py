import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path("/opt/domoskiosk/cast_config.json")
CAST_MEDIA_DIR = Path("/tmp/domos_cast_media")
PIPER_BIN = "/opt/domoskiosk/tts/piper/piper"
PIPER_MODEL = "/opt/domoskiosk/tts/es_ES-davefx-medium.onnx"
DOMOS_LAN_BASE = "http://192.168.5.220:8080"

KNOWN_SPEAKERS_DEFAULT = [
    {
        "id": "salita",
        "name": "Salita",
        "label": "Cocina / Salita",
        "icon": "🍳",
        "model": "Google Home",
        "host": "192.168.5.137",
        "port": 8009,
        "uuid": "88c0dc42-4166-8505-9b8c-f85a055f53fb",
        "doorbell_enabled": True,
    },
    {
        "id": "dormitorio_1",
        "name": "Dormitorio 1",
        "label": "Dormitorio",
        "icon": "🛏️",
        "model": "Google Nest Mini",
        "host": "192.168.5.185",
        "port": 8009,
        "uuid": "dadcc330-f0bb-1be3-01c8-02223a7e1991",
        "doorbell_enabled": True,
    },
    {
        "id": "sotano",
        "name": "Sótano",
        "label": "Sótano",
        "icon": "🎮",
        "model": "Google Home Mini",
        "host": "192.168.5.179",
        "port": 8009,
        "uuid": "7ae83a76-ba1c-3cf9-c548-53a8dd33f0a0",
        "doorbell_enabled": True,
    },
]


class CastService:
    def __init__(self):
        CAST_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self._lock = threading.Lock()
        self._tts_lock = threading.Lock()

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                if isinstance(data, dict) and isinstance(data.get("speakers"), list):
                    return data
            except Exception:
                pass
        cfg = {
            "doorbell_cast_enabled": True,
            "quiet_night_dormitorio": True,
            "speakers": KNOWN_SPEAKERS_DEFAULT,
        }
        self._save_config(cfg)
        return cfg

    def _save_config(self, cfg: dict):
        try:
            CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[CastService] Config save error: {e}", flush=True)

    def get_speakers(self) -> dict:
        return {
            "doorbell_cast_enabled": bool(self.config.get("doorbell_cast_enabled", True)),
            "quiet_night_dormitorio": bool(self.config.get("quiet_night_dormitorio", True)),
            "speakers": self.config.get("speakers", []),
        }

    def update_config(self, data: dict) -> dict:
        if "doorbell_cast_enabled" in data:
            self.config["doorbell_cast_enabled"] = bool(data["doorbell_cast_enabled"])
        if "quiet_night_dormitorio" in data:
            self.config["quiet_night_dormitorio"] = bool(data["quiet_night_dormitorio"])
        if isinstance(data.get("speaker_doorbell"), dict):
            for sp in self.config.get("speakers", []):
                if sp["id"] in data["speaker_doorbell"]:
                    sp["doorbell_enabled"] = bool(data["speaker_doorbell"][sp["id"]])
        self._save_config(self.config)
        return self.get_speakers()

    def refresh_discovery(self, timeout: float = 5.0) -> dict:
        try:
            import pychromecast
            services, browser = pychromecast.discovery.discover_chromecasts(timeout=timeout)
            browser.stop_discovery()
            by_uuid = {sp["uuid"]: sp for sp in self.config.get("speakers", [])}
            for s in services:
                uid = str(s.uuid)
                if uid in by_uuid:
                    by_uuid[uid]["host"] = s.host
                    by_uuid[uid]["port"] = s.port
                    by_uuid[uid]["name"] = s.friendly_name
                else:
                    slug = s.friendly_name.lower().replace(" ", "_").replace("ó", "o").replace("á", "a").replace("é", "e").replace("í", "i").replace("ú", "u")
                    by_uuid[uid] = {
                        "id": slug,
                        "name": s.friendly_name,
                        "label": s.friendly_name,
                        "icon": "🔊",
                        "model": s.model_name,
                        "host": s.host,
                        "port": s.port,
                        "uuid": uid,
                        "doorbell_enabled": True,
                    }
            self.config["speakers"] = list(by_uuid.values())
            self._save_config(self.config)
        except Exception as e:
            print(f"[CastService] Discovery error: {e}", flush=True)
        return self.get_speakers()

    def _resolve_targets(self, targets) -> list:
        all_sp = self.config.get("speakers", [])
        if not targets or targets == "all" or (isinstance(targets, list) and "all" in targets):
            return list(all_sp)
        if isinstance(targets, str):
            targets = [targets]
        norm_t = [str(t).strip().lower() for t in targets]
        out = []
        for sp in all_sp:
            if (
                sp["id"].lower() in norm_t
                or sp["name"].lower() in norm_t
                or sp["label"].lower() in norm_t
                or any(t in sp["name"].lower() or t in sp["label"].lower() for t in norm_t)
            ):
                out.append(sp)
        return out

    def _connect_and_play_one(self, sp: dict, url: str, content_type: str, title: str, volume: float = None):
        import pychromecast
        try:
            cc = pychromecast.get_chromecast_from_host((sp["host"], int(sp.get("port", 8009)), sp["uuid"], sp["model"], sp["name"]))
            cc.wait(timeout=5.0)
            if volume is not None:
                try:
                    cc.set_volume(max(0.0, min(1.0, float(volume))))
                except Exception:
                    pass
            mc = cc.media_controller
            st_type = "BUFFERED" if content_type == "audio/wav" else "LIVE"
            mc.play_media(url, content_type, title=title, stream_type=st_type)
            mc.block_until_active(timeout=5.0)
            cc.disconnect(timeout=2.0)
            print(f"[CastService] Cast OK -> {sp['name']} ({sp['host']}): {title}", flush=True)
            return {"speaker": sp["name"], "success": True}
        except Exception as e:
            print(f"[CastService] Cast ERR -> {sp['name']} ({sp['host']}): {e}", flush=True)
            return {"speaker": sp["name"], "success": False, "error": str(e)}

    def _connect_and_stop_one(self, sp: dict):
        import pychromecast
        try:
            cc = pychromecast.get_chromecast_from_host((sp["host"], int(sp.get("port", 8009)), sp["uuid"], sp["model"], sp["name"]))
            cc.wait(timeout=4.0)
            try:
                cc.media_controller.stop()
            except Exception:
                pass
            try:
                cc.quit_app()
            except Exception:
                pass
            cc.disconnect(timeout=2.0)
            return {"speaker": sp["name"], "success": True}
        except Exception as e:
            return {"speaker": sp["name"], "success": False, "error": str(e)}

    def play_url(self, targets, url: str, title: str = "DOMOS Audio", content_type: str = "audio/mpeg", volume: float = None) -> dict:
        sps = self._resolve_targets(targets)
        if not sps:
            return {"success": False, "error": "No matching Google speakers"}
        if url.endswith(".m3u8"):
            content_type = "application/x-mpegURL"
        elif url.endswith(".wav"):
            content_type = "audio/wav"
        with ThreadPoolExecutor(max_workers=max(1, len(sps))) as ex:
            results = list(ex.map(lambda s: self._connect_and_play_one(s, url, content_type, title, volume), sps))
        return {"success": any(r["success"] for r in results), "results": results}

    def stop(self, targets="all") -> dict:
        sps = self._resolve_targets(targets)
        if not sps:
            return {"success": False, "error": "No matching Google speakers"}
        with ThreadPoolExecutor(max_workers=max(1, len(sps))) as ex:
            results = list(ex.map(self._connect_and_stop_one, sps))
        return {"success": any(r["success"] for r in results), "results": results}

    def synthesize_tts_wav(self, text: str) -> str:
        clean = str(text or "").strip()
        if not clean:
            return ""
        # Cleanup old TTS files (> 10 min)
        now = time.time()
        for old in CAST_MEDIA_DIR.glob("tts_*.wav"):
            try:
                if now - old.stat().st_mtime > 600:
                    old.unlink()
            except Exception:
                pass

        fname = f"tts_{int(now * 1000)}.wav"
        out_path = CAST_MEDIA_DIR / fname
        with self._tts_lock:
            proc = subprocess.run(
                [PIPER_BIN, "--model", PIPER_MODEL, "--length_scale", "1.05", "--output_file", str(out_path)],
                input=clean,
                text=True,
                capture_output=True,
                timeout=35,
                check=False,
            )
        if out_path.exists() and out_path.stat().st_size > 100:
            return fname
        raise RuntimeError(f"Piper TTS failed: {proc.stderr[:120]}")

    def announce(self, targets, text: str) -> dict:
        try:
            fname = self.synthesize_tts_wav(text)
            url = f"{DOMOS_LAN_BASE}/api/cast/media/{fname}"
            return self.play_url(targets, url, title="Aviso DOMOS", content_type="audio/wav")
        except Exception as e:
            print(f"[CastService] Announce error: {e}", flush=True)
            return {"success": False, "error": str(e)}

    def ring_doorbell_multiroom(self):
        if not self.config.get("doorbell_cast_enabled", True):
            return
        hour = datetime.now().hour
        quiet_night = bool(self.config.get("quiet_night_dormitorio", True)) and (hour >= 23 or hour < 8)
        targets = []
        for sp in self.config.get("speakers", []):
            if not sp.get("doorbell_enabled", True):
                continue
            if quiet_night and "dormitorio" in sp["id"].lower():
                continue
            targets.append(sp["id"])
        if not targets:
            return
        def _bg():
            try:
                self.announce(targets, "Atención, alguien está llamando al videoportero.")
            except Exception as e:
                print(f"[CastService] Doorbell multiroom err: {e}", flush=True)
        threading.Thread(target=_bg, daemon=True).start()


service = CastService()
