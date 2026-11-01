#!/usr/bin/env python3
"""
Shelly Plug US Gen4 Script Deployer
Uploads hydro_pump_cycle.js in chunks and enables 'Run on Boot'.
"""
import os
import sys
import json
from shelly_control import send_rpc, load_credentials

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JS_FILE = os.path.join(SCRIPT_DIR, "hydro_pump_cycle.js")
CHUNK_SIZE = 1024

def deploy():
    if not os.path.exists(JS_FILE):
        print(f"Error: {JS_FILE} not found.")
        sys.exit(1)

    with open(JS_FILE, "r", encoding="utf-8") as f:
        code = f.read()

    creds = load_credentials()
    print(f"📡 Connecting to Shelly Plug at {creds['ip']}...")

    # 1. Check existing scripts
    res = send_rpc(creds, "Script.List")
    existing_scripts = res.get("scripts", [])
    script_id = None

    for s in existing_scripts:
        if s.get("name") == "hydro_pump_cycle":
            script_id = s.get("id")
            print(f"기존 스크립트 발견 (ID: {script_id}). 정지 및 초기화합니다.")
            try:
                send_rpc(creds, "Script.Stop", {"id": script_id})
            except Exception:
                pass
            break

    # 2. If not found, create new script slot
    if script_id is None:
        print("새 스크립트 슬롯 생성 중...")
        res_create = send_rpc(creds, "Script.Create", {"name": "hydro_pump_cycle"})
        script_id = res_create.get("id", 1)
        print(f"생성된 Script ID: {script_id}")

    # 3. Upload code in chunks
    print(f"스크립트 코드 업로드 중 (총 {len(code)} 글자, {CHUNK_SIZE}바이트 단위)...")
    for i in range(0, len(code), CHUNK_SIZE):
        chunk = code[i:i + CHUNK_SIZE]
        is_first = (i == 0)
        res_chunk = send_rpc(creds, "Script.PutCode", {
            "id": script_id,
            "code": chunk,
            "append": not is_first
        })
        print(f"  - 청크 {i // CHUNK_SIZE + 1} 업로드 완료 (누적 길이: {res_chunk.get('len')} bytes)")

    # 4. Set Run on Boot (enable: True)
    print("부팅 시 자동 실행(Run on Boot) 활성화...")
    send_rpc(creds, "Script.SetConfig", {"id": script_id, "config": {"name": "hydro_pump_cycle", "enable": True}})

    # 5. Start Script
    print("스크립트 실행(Start)...")
    send_rpc(creds, "Script.Start", {"id": script_id})

    # 6. Check status
    status = send_rpc(creds, "Script.GetStatus", {"id": script_id})
    print("\n✅ 배포 및 가동 성공!")
    print(f"Script ID: {script_id}")
    print(f"실행 상태: {'실행 중 (Running)' if status.get('running') else '중지됨'}")
    print(f"메모리 사용량: {status.get('mem_usage', 0)} bytes")

if __name__ == "__main__":
    deploy()
