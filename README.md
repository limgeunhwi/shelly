# Lettuce Grow Farmstand - 야외 수경재배 자동 제어 시스템

## 1. 개요 및 기기 정보
* **모델**: Shelly Plug US Gen4 (`S4PL-00116US`)
* **설치 환경**: 캘리포니아 야외 수경재배
* **인증 설정**: `credentials.example.json`을 복사하여 로컬 `credentials.json` 생성 (Git 추적 제외)

---

## 2. 현재 가동 중인 순환 주기 (Plan A + 계절 자동 전환)

스크립트가 플러그에 배포되어 **기기 단독으로 실시간 24시간 자동 순환**합니다.

### 🌸 봄 / 여름 / 가을 모드 (3월 ~ 11월)
* **일반 낮 (07:00 ~ 11:00, 15:00 ~ 21:00)**: **3분 급수 (ON) / 15분 휴식 (OFF)**
  * 건조한 야외 바람과 온화한 시간대에 적합한 순환 주기
* **한낮 피크 (11:00 ~ 15:00)**: **2분 급수 (ON) / 8분 휴식 (OFF)**
  * 강렬한 한낮 직사광선/고온기에 넷팟 배지 마름 방지 및 적극적인 뿌리 냉각
  * 8분 휴식 / 2분 가동(시간당 6회)으로 모터 열 축적 없이 신선한 수분 공급
* **밤 (21:00 ~ 07:00)**: **1분 급수 (ON) / 45분 휴식 (OFF)**
  * 기온 하강에 따른 뿌리 냉해 방지 및 야간 낙수 소음 차단

### ❄️ 겨울 모드 (12월 ~ 2월) - [자동 전환]
* **낮 (08:00 ~ 17:00)**: **3분 급수 (ON) / 35분 휴식 (OFF)**
  * 우기(Rainy season) 습도 상승 및 증산량 감소에 맞춘 과습/뿌리 썩음 방지
* **밤 (17:00 ~ 08:00)**: **1분 급수 (ON) / 90분 휴식 (OFF)**
  * 차가운 밤 기온(4~7°C) 영양액 순환 최소화로 뿌리 동해 방지

### 🛡️ 안전 보호 장치
* **최대 5분 차단**: 어떤 이유로든 펌프가 5분 이상 연속 가동 시 모터 소손 및 수조 물 고갈을 막기 위해 강제 OFF
* **정전/재부팅 안전**: 정전 후 복구 시 기기 부팅과 동시에 스크립트 자동 재시작(`enable: true`)

---

## 3. 관리 및 제어 방법

### 초기 설정
```bash
cp credentials.example.json credentials.json
# credentials.json 파일에 플러그 IP와 비밀번호 입력
```

### CLI 도구 (`shelly_control.py`)
```bash
# 플러그 현재 상태 (전원, 전력량, 전압, 온도) 확인
./shelly_control.py status

# 수동 제어 (필요 시)
./shelly_control.py on
./shelly_control.py off
./shelly_control.py toggle
```

### 스크립트 재배포/업데이트 (`deploy_script.py`)
`hydro_pump_cycle.js` 코드를 수정한 후 아래 명령어를 실행하면 즉시 플러그로 전송되어 재적용됩니다:
```bash
./deploy_script.py
```

---

## 4. 파일 목록
* `hydro_pump_cycle.js`: 플러그에서 실행 중인 내장 mJS 스크립트
* `config.json`: 계절 및 스케줄 설정 메타데이터
* `deploy_script.py`: 플러그 원격 업로드/배포 도구
* `shelly_control.py`: 터미널 제어 CLI
* `credentials.example.json`: 기기 접속 정보 설정 템플릿
