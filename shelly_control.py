#!/usr/bin/env python3
"""
Shelly Plug US Gen4 Controller CLI
"""
import sys
import json
import os
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")

def load_credentials():
    if not os.path.exists(CREDS_FILE):
        print(f"Error: {CREDS_FILE} not found.")
        sys.exit(1)
    with open(CREDS_FILE, "r") as f:
        return json.load(f)

def send_rpc(creds, method, params=None):
    ip = creds["ip"]
    username = creds["username"]
    password = creds["password"]
    
    url = f"http://{ip}/rpc/{method}"
    data = json.dumps(params).encode("utf-8") if params else None
    
    # Configure HTTP Digest Authentication Handler
    pass_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pass_mgr.add_password(None, f"http://{ip}", username, password)
    auth_handler = urllib.request.HTTPDigestAuthHandler(pass_mgr)
    opener = urllib.request.build_opener(auth_handler)
    
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    
    try:
        with opener.open(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP Error {e.code}: {e.reason} -> {body}")
        sys.exit(1)
    except Exception as e:
        print(f"Request Error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 shelly_control.py [on|off|toggle|status]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    creds = load_credentials()

    if cmd == "on":
        res = send_rpc(creds, "Switch.Set", {"id": 0, "on": True})
        print("🔌 Shelly Plug: 켜짐 (ON)")
    elif cmd == "off":
        res = send_rpc(creds, "Switch.Set", {"id": 0, "on": False})
        print("🔌 Shelly Plug: 꺼짐 (OFF)")
    elif cmd == "toggle":
        res = send_rpc(creds, "Switch.Toggle", {"id": 0})
        status = send_rpc(creds, "Switch.GetStatus", {"id": 0})
        state = "ON" if status.get("output") else "OFF"
        print(f"🔌 Shelly Plug 토글됨: 현재 상태 -> {state}")
    elif cmd == "status":
        status = send_rpc(creds, "Switch.GetStatus", {"id": 0})
        is_on = status.get("output", False)
        power = status.get("apower", 0.0)
        current = status.get("current", 0.0)
        voltage = status.get("voltage", 0.0)
        temp_c = status.get("temperature", {}).get("tC", 0.0)

        aenergy = status.get("aenergy", {})
        total_wh = aenergy.get("total", 0.0)
        by_minute = aenergy.get("by_minute", [])

        counts = status.get("counts", {})
        total_on_sec = counts.get("on_time", 0)

        # Check automated script status
        scr_data = None
        try:
            eval_code = "JSON.stringify({cycleCount: cycleCount, phase: getCurrentPhase(getActiveProfile()), profile: getActiveProfile().name, isWatering: (safetyTimer !== null)})"
            scr = send_rpc(creds, "Script.Eval", {"id": 1, "code": eval_code})
            if scr and scr.get("result"):
                scr_data = json.loads(scr.get("result"))
        except Exception:
            pass

        print("=== 🔌 Shelly Plug 전원 & 전력 상태 ===")
        print(f"전원 상태: {'🟢 ON (급수 가동 중)' if is_on else '⚪ OFF (휴식 대기 중)'}")
        print(f"실시간 전력: {power:.2f} W")
        print(f"측정 전류: {current:.3f} A")
        print(f"측정 전압: {voltage:.1f} V")
        print(f"누적 전력량: {total_wh:.3f} Wh ({total_wh / 1000:.4f} kWh)")
        if by_minute:
            recent_mwh = ", ".join([f"{m:.1f}mWh" for m in by_minute])
            print(f"최근 3분 소비: [{recent_mwh}]")
        if total_on_sec:
            print(f"총 가동 시간: {total_on_sec // 60}분 {total_on_sec % 60}초")
        print(f"기기 온도: {temp_c:.1f} °C")

        if scr_data:
            phase = scr_data.get("phase", {})
            phase_name = phase.get("name", "")
            on_m = phase.get("on_sec", 0) // 60
            off_m = phase.get("off_sec", 0) // 60
            is_watering = scr_data.get("isWatering", False)
            print("\n=== 🌱 Farmstand 순환 제어 상태 ===")
            print(f"적용 프로필: {scr_data.get('profile', '')} [{phase_name} 모드]")
            print(f"설정 주기: {on_m}분 급수 / {off_m}분 휴식")
            print(f"진행 사이클: #{scr_data.get('cycleCount', 0)}회차")
            print(f"현재 단계: {'💦 급수 중 (Watering)' if is_watering else '🛑 휴식 대기 중 (Resting)'}")
    else:
        print(f"알 수 없는 명령어: {cmd}")
        print("사용 가능한 명령: on, off, toggle, status")
        sys.exit(1)

if __name__ == "__main__":
    main()
