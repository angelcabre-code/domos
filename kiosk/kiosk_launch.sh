#!/bin/bash
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export WAYLAND_DISPLAY="wayland-0"

# Set brightness to 80% initially
brightnessctl set 80% 2>/dev/null || true

# Wait for local web server
while ! curl -s http://127.0.0.1:8080/api/status >/dev/null 2>&1; do
  sleep 1
done

# Launch Chromium inside Cage (Hardware accelerated with VA-API on Intel Bay Trail!)
exec chromium \
  --kiosk --ozone-platform=wayland --touch-events=enabled --disable-features=Translate,OptimizationHints \
  --noerrdialogs \
  --disable-infobars \
  --disable-translate --disable-features=Translate \
  --no-first-run \
  --fast \
  --fast-start \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  --check-for-update-interval=31536000 \
  --enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks \
  --ignore-gpu-blocklist \
  --enable-gpu-rasterization \
  --enable-zero-copy \
  --autoplay-policy=no-user-gesture-required \
  --disable-features=Translate --disable-popup-blocking --simulate-outdated-no-au="Tue, 31 Dec 2099 23:59:59 GMT" --app=http://127.0.0.1:8080
