# GOP Message Broker 연동 설계서

**작성일**: 2026-02-05  
**최종 수정일**: 2026-07-30  
**버전**: v1.6  
**작성자**: 이기호 차장  
**목적**: GOP 통제시스템 내부 메시지 브로커(NATS) 기반 실시간 통신 설계  
**설계 원칙**: GOP RESTful API Response `data` 구조 재사용으로 View 일관성 확보, Subject 라우팅으로 수신 대상 식별  

---

## 목차

1. [개요](#1-개요)
2. [공통 사양](#2-공통-사양)
3. [Subject 규칙](#3-subject-규칙)
4. [Enum 타입 정의](#4-enum-타입-정의)
5. [메시지 카탈로그](#5-메시지-카탈로그)
6. [Event 메시지 설계](#6-event-메시지-설계)
   - 6.1 [Detection Event (탐지)](#61-detection-event-탐지)
   - 6.2 [Malfunction Event (장애)](#62-malfunction-event-장애)
   - 6.3 [Connection Event (연결)](#63-connection-event-연결)
   - 6.4 [Action Report (조치 보고)](#64-action-report-조치-보고)
   - 6.5 [System Event (서버 시스템 이벤트)](#65-system-event-서버-시스템-이벤트) *(NATS 신규)*
   - 6.6 [Enclosure Metrics (함체 텔레메트리)](#66-enclosure-metrics-함체-텔레메트리) *(NATS 신규)*
7. [Device 제어 메시지 설계](#7-device-제어-메시지-설계)
   - 7.1 [PidsProxy 제어](#71-pidsproxy-제어)
   - 7.2 [Broadcasting 제어](#72-broadcasting-제어)
   - 7.3 [Lamp 제어](#73-lamp-제어)
8. [Camera/NVR 제어 메시지 설계](#8-cameranvr-제어-메시지-설계)
   - 8.1 [PTZ 제어](#81-ptz-제어)
   - 8.2 [AI 탐지 메시지](#82-ai-탐지-메시지)
   - 8.3 [카메라 설정 제어](#83-카메라-설정-제어)
9. [마스터 데이터 동기화 메시지 설계](#9-마스터-데이터-동기화-메시지-설계)
    - 9.1 [개요](#91-개요)
    - 9.2 [SYNC_DEVICE (장비 동기화)](#92-sync_device-장비-동기화)
    - 9.3 [SYNC_SERVER (서버 동기화)](#93-sync_server-서버-동기화)
    - 9.4 [SYNC_CATEGORY (카테고리 동기화)](#94-sync_category-카테고리-동기화)
    - 9.5 [SYNC_DEVICE_GROUP (장비그룹 동기화)](#95-sync_device_group-장비그룹-동기화)
    - 9.6 [SYNC_EVENT_MAPPING (이벤트매핑 동기화)](#96-sync_event_mapping-이벤트매핑-동기화)
    - 9.7 [SYNC_PRESET (프리셋 동기화)](#97-sync_preset-프리셋-동기화)
    - 9.8 [SYNC_FILE_GROUP (파일그룹 동기화)](#98-sync_file_group-파일그룹-동기화)
    - 9.9 [SYNC_CAMERA_SETTING (카메라 설정 동기화)](#99-sync_camera_setting-카메라-설정-동기화)
    - 9.10 [SYNC_PROXY_SETTING (프록시 설정 동기화)](#910-sync_proxy_setting-프록시-설정-동기화)
10. [에러 처리](#10-에러-처리)
11. [부록](#11-부록)
    - 11.1 [전체 메시지 목록](#111-전체-메시지-목록)
    - 11.2 [REST API body 재사용 매핑표](#112-rest-api-body-재사용-매핑표)
    - 11.3 [변경 이력](#113-변경-이력)

---

## 1. 개요

### 1.1 설계 목적

GOP 통제시스템 내부 컴포넌트 간 **실시간 양방향 통신**을 NATS 메시지 브로커를 통해 제공합니다:

- **제어 메시지**: 장비 제어 명령 전달 (PTZ, 방송, 경광등, 모드 변경 등)
- **상태 업데이트**: 장비 및 서버 상태 변경 실시간 전파
- **이벤트 전송**: 탐지/장애/연결 이벤트 실시간 전파
- **조치 보고**: 이벤트에 대한 조치 결과 전파

### 1.2 설계 원칙

| 원칙 | 설명 |
|------|------|
| **DTO 재사용** | GOP RESTful API Response의 `data` 구조를 NATS body에 그대로 활용하여 동일 View 사용 가능 |
| **Subject 라우팅** | Subject는 `{도메인}.{부대ID}.{서브시스템}.{action}` 형식, 발신자는 `from` 필드로 식별, 수신 대상은 Subject 구독으로 식별 |
| **PUB 우선** | 운용 메시지는 PUB(단방향 발행) 우선, 응답이 필요한 경우만 REQ/RSP 패턴 사용 |
| **Envelope 표준화** | 모든 메시지는 공통 Envelope 구조를 준수 |
| **확장 가능** | 새 도메인/액션 추가 시 Subject 패턴만 확장 |

### 1.3 시스템 아키텍처

```
+----------------------------------------------------------------------------------------------+
|                                GOP Control System                                            |
|                                                                                              |
|  [ Frontend ]                  +-----------+                                                 |
|                                |  NVR API  |                                                 |
|                                +-----+-----+                                                 |
|                                      |                                                       |
|  +-----------+  +-----------+  +-----+-----+  +-----------+                                  |
|  |  Central  |  |    GIS    |  |    VMS    |  |   DBApi   |                                  |
|  | (Admin UI)|  |(Situation)|  | (NVR F/E) |  |           |                                  |
|  +-----------+  +-----------+  +-----------+  +-----------+                                  |
|       |              |              |              |                                         |
|       +--------------+--------------+--------------+                                         |
|                             |                                                                |
|  +==========================+===============================================================+|
|  ||                      NATS Core                                                         |||
|  ||          sensorway.{unitID}.{subsystem}.{action}                                       |||
|  +==========================================================================================+|
|                                                                                              |
|  [ Backend Services ]                                                                        |
|  +-----------+  +-----------------------------+  +-----------+  +-----------+                |
|  |    NVR    |  |     PidsProxy Manager       |  |    AI     |  | Broadcast |                |
|  |  Manager  |  |                             |  | Analysis  |  |  Manager  |                |
|  +-----+-----+  +------+---------------+------+  +-----------+  +-----+-----+                |
|        |               |               |                              |                      |
|  +-----+-----+ +-------+--------+ +----+--------+              +-------+------+              |
|  |  NVR API  | |  Middleware    | |  QLite Lamp |              |   Speaker    |              |
|  | (Emstone) | | (Preprocessor) | |   (QLite)   |              |              |              |
|  | + SPG API | +-------+--------+ +-------------+              +--------------+              |
|  +-----------+         |                                                                     |
+----------------------------------------------------------------------------------------------+
                         |
                  +------+------+
                  |    PIDS     |
                  | Controller  |
                  |  + Sensor   |
                  +-------------+
```

> **VMS(NVR Frontend)**: NVR API에 직접 접근하여 영상 데이터를 조회/표출합니다. NATS를 통해서는 VMS_DETECT 수신, PTZ 제어 명령 발행, 카메라 설정 등을 처리합니다.
>
> **AiAnalysis**: NVRManager를 통해 카메라 피드를 수신하며, NATS에서는 Backend Service로 분류되지만 NVRManager에 의존합니다.

**서브시스템 목록 (8개):**

| 서브시스템 | `from` 값 | 계층 | 역할 | 외부 연결 |
|-----------|----------|------|------|-----------|
| 통합관리 Frontend | `Central` | Frontend | 통합 관제 UI, 제어 명령 발행, 테스트 명령, 이벤트 조회는 DBApi 경유 HTTP RESTful 기반 | - |
| GIS 통합상황도 | `GIS` | Frontend | 지도 기반 상황 표시, 조치 보고, 경광등/방송 제어, PTZ 좌표 이동 | - |
| NVR Frontend | `VMS` | Frontend | NVR을 자사 제품처럼 표출하는 영상 관제 UI | NVR API (직접 접근) |
| DB Api | `DBApi` | Frontend | REST API 서버, 모든 서브시스템의 마스터 데이터 제공(캐싱 원본), DB 상태 변경 시 SYNC 알림 발행, 시스템 이벤트·함체 텔레메트리 주기 발행 | PostgreSQL |
| NVR Manager | `NVRManager` | Backend | NVR API/SPG API 브릿지 — PTZ 제어, 카메라 설정(팔레트/와이퍼/열선 등), PTZ 상태 보고, AiAnalysis 카메라 기능 지원, 이벤트 수신 시 프리셋 회전 | NVR API (Emstone), SPG API |
| PidsProxy Manager | `PidsProxy` | Backend | 센서 이벤트 중계 (탐지/장애/연결), 센서 모드 제어, 경광등 색상/부저 제어, 이벤트 연동 경광등 동작 | 센서/제어기 (TCP), 경광등 (QLite) |
| Broadcasting Manager | `BroadcastingManager` | Backend | TTS 음성 변환, 음원 재생, 방송 실행 | 스피커 |
| 영상분석 서버 | `AiAnalysis` | Backend | AI 영상 분석, 객체 탐지/추적, 탐지 결과 발행 | NVRManager (카메라 피드) |

> **공통 원칙 — DBApi 캐싱**: Central/DBApi를 제외한 모든 서브시스템은 시작 시 DBApi(HTTP RESTful)로부터 자신에게 필요한 마스터 데이터를 조회하여 로컬에 캐싱합니다. Central은 DBApi와 동일 시스템이므로 DB에 직접 접근합니다.
>
> | 서브시스템 | 캐싱 REST API | 관련 SYNC 메시지 | 용도 |
> |-----------|--------------|-----------------|------|
> | GIS | `/api/devices/*` (controllers, sensors, cameras, speakers, lamps, enclosures), `/api/devices/groups`, `/api/integrations/event-mappings` (+ cameras, speakers, lamps), `/api/devices/cameras/{id}/presets` | SYNC_DEVICE, SYNC_DEVICE_GROUP, SYNC_EVENT_MAPPING, SYNC_PRESET | 상황도 장비 표시, 이벤트 연동 정보, PTZ 좌표 이동 |
> | VMS | `/api/devices/cameras`, `/api/devices/cameras/{id}/settings`, `/api/devices/cameras/{id}/presets` | SYNC_DEVICE, SYNC_CAMERA_SETTING, SYNC_PRESET | 영상 표출, 카메라 설정 표시, PTZ 프리셋 제어 |
> | NVRManager | `/api/devices/cameras`, `/api/devices/cameras/{id}/settings`, `/api/devices/cameras/{id}/presets`, `/api/integrations/event-mappings` (+ cameras), `/api/servers` | SYNC_DEVICE, SYNC_CAMERA_SETTING, SYNC_PRESET, SYNC_EVENT_MAPPING, SYNC_SERVER | PTZ 제어, 카메라 설정 브릿지, 이벤트 수신 시 프리셋 회전 |
> | PidsProxy | `/api/devices/controllers`, `/api/devices/sensors`, `/api/devices/lamps`, `/api/integrations/event-mappings` (+ lamps), `/api/servers/{id}/proxy-settings` | SYNC_DEVICE, SYNC_EVENT_MAPPING, SYNC_PROXY_SETTING | 센서 이벤트 중계, 경광등 제어, 이벤트 연동 경광등 동작 |
> | BroadcastingManager | `/api/devices/speakers`, `/api/servers`, `/api/file-groups`, `/api/integrations/event-mappings` (+ speakers) | SYNC_DEVICE, SYNC_SERVER, SYNC_FILE_GROUP, SYNC_EVENT_MAPPING | 방송 실행, TTS 변환, 이벤트 연동 자동 방송 |
> | AiAnalysis | `/api/devices/cameras`, `/api/devices/cameras/{id}/presets` (+ ROIs, XyPoints) | SYNC_DEVICE, SYNC_PRESET | 영상 분석 대상 카메라, ROI 기반 탐지 영역 설정 |
>
> 이후 DBApi가 발행하는 **SYNC 메시지**를 구독하여 캐시를 실시간 갱신합니다.

#### 주요 메시지 흐름도

```
[1] 센서 탐지 이벤트 전파
    센서 → PidsProxy ──PUB(all.event.detect)──→ GIS, NVRManager, BroadcastingManager, PidsProxy(경광등 연동)

[2] AI 영상 탐지 이벤트 전파
    AiAnalysis──PUB(all.event_ai.detect)──→ GIS, NVRManager, BroadcastingManager, PidsProxy(경광등 연동)

[3] PTZ 제어
    Central/GIS/VMS ──REQ(nvr.ptz)──→ NVRManager ──→ NVR API ──→ Camera

[4] 카메라 설정 제어
    Central/VMS ──REQ(camera.*)──→ NVRManager ──NVR API/SPG API──→ Camera

[5] PTZ 상태 보고
    SPG API → NVRManager ──PUB(gis.ptz-status)──→ GIS, AiAnalysis, VMS

[6] 조치 보고 → 복귀 동작
    GIS ──PUB(all.event.action-report)──→ NVRManager (카메라 홈 복귀), BroadcastingManager (방송 종료), PidsProxy(경광등 연동), VMS

[7] 경광등 이벤트 연동
    이벤트 수신 → PidsProxy (자동 동작)
    GIS ──PUB(lamp.clear/color/buzzer)──→ PidsProxy (수동 제어)──→ QLiteLamp
    Central ──PUB(lamp.off)──→ PidsProxy (비활성화)──→ QLiteLamp

[8] 방송 이벤트 연동
    이벤트 수신 → BroadcastingManager (자동 방송)
    GIS ──PUB(broadcast.play/stop)──→ BroadcastingManager (수동 제어)──→ Speaker
    Central ──PUB(broadcast.tts/test)──→ BroadcastingManager (TTS/테스트)──→ Speaker

[9] 자동 추적
    Central ──REQ(camera.tracking)──→ NVRManager → AiAnalysis
    AiAnalysis ──PUB(camera.tracking-status)──→ GIS

[10] 서버/함체 모니터링
    DBApi ──PUB(all.event.system)──→ GIS (서버 시스템 이벤트)
    DBApi ──PUB(gis.enclosure-metrics)──→ GIS (함체 텔레메트리, 주기)
```

---

## 2. 공통 사양

### 2.1 Envelope 구조

모든 NATS 메시지는 다음 공통 Envelope 구조를 따릅니다.

#### PUB (운용 메시지 - 단방향)

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "DETECT",
  "from": "PidsProxy",
  "body": {},
  "created": "2026-02-05T10:30:00.000Z"
}
```

#### REQ (요청 메시지 - 응답 필요)

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_PAN_LEFT",
  "from": "Central",
  "body": {},
  "created": "2026-02-05T10:30:00.000Z"
}
```

#### RSP (응답 메시지)

```json
{
  "id": "uuid-v4",
  "m_type": "RSP",
  "cmd": "PTZ_PAN_LEFT",
  "from": "NVRManager",
  "body": {},
  "created": "2026-02-05T10:30:00.100Z",
  "success": true,
  "message": "처리 완료",
  "req_id": "original-request-uuid"
}
```

### 2.2 Envelope 필드 정의

| 필드 | 타입 | PUB | REQ | RSP | 설명 |
|------|------|-----|-----|-----|------|
| `id` | string (UUID v4) | **필수** | **필수** | **필수** | 메시지 고유 ID |
| `m_type` | string | `"PUB"` | `"REQ"` | `"RSP"` | 메시지 유형 |
| `cmd` | string | **필수** | **필수** | **필수** | 명령 타입 |
| `from` | EnumSubsystem | **필수** | **필수** | **필수** | 송신자 식별자 (2.3 참조) |
| `body` | object | **필수** | **필수** | **필수** | 페이로드 데이터 |
| `created` | string (ISO 8601) | **필수** | **필수** | **필수** | 생성 시각 |
| `success` | boolean | - | - | **필수** | 성공 여부 |
| `message` | string | - | - | 선택 | 상태 메시지 |
| `req_id` | string (UUID) | - | - | **필수** | 원본 요청 ID |

### 2.3 `from` 고정 값 (EnumSubsystem)

| 값 | 서브시스템 | 설명 |
|----|-----------|------|
| `Central` | 통합관리 Frontend | 통합 관제 소프트웨어 (제어 명령 발행) |
| `GIS` | GIS 통합상황도 | 지도/조치 소프트웨어 (조치 보고 발행) |
| `DBApi` | DB Api | Control Service (DB/상태 변경 발행) |
| `PidsProxy` | PidsProxy Manager | PIDS 프록시 (센서 이벤트 발행) |
| `NVRManager` | NVR Manager | NVR 매니저 (PTZ 제어, 카메라 설정, PTZ 상태 보고, AI 지원) |
| `VMS` | NVR Frontend | 영상 관제 VMS (카메라 제어, 영상 표출) |
| `BroadcastingManager` | Broadcasting Manager | 방송 매니저 (TTS/방송 실행) |
| `AiAnalysis` | 영상분석 서버 | AI 영상 분석, 탐지 결과 발행 |

> **참고**: Enum 정의는 [4.1 EnumSubsystem](#41-메시지-전용-enum) 참조

### 2.4 body 설계 원칙

NATS 메시지는 **용도에 따라 세 가지 패턴**으로 구분됩니다.

#### 패턴 1: Full DTO (이벤트/탐지)

- **대상**: Event 메시지 (DETECT, MALFUNCTION, CONNECTION, ACTION_REPORT), AI 탐지 메시지 (VMS_DETECT)
- **body** = REST API Response `data` 구조 재사용
- **이유**: 실시간 UI 표시 필요, View/DTO 재사용으로 클라이언트 일관성 확보

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "DETECT",
  "from": "PidsProxy",
  "body": {
    "id": 1001,
    "type_event": "Intrusion",
    "device": { "id": 101, "name_device": "Sensor-A-1" },
    "result": "PIR_SENSOR",
    "detail": { }
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

#### 패턴 2: ID + 파라미터 (제어 메시지)

- **대상**: Device 제어 (TTS, PTZ, Lamp, Camera 등)
- **body** = **대상 ID + 제어 파라미터만** (Full DTO 미포함)
- **이유**: 메시지 경량화, 수신자는 로컬 캐시에서 상세 정보 조회
- **전제조건**: 수신자(매니저)가 시작 시 마스터 데이터를 캐시하고 SYNC 메시지로 갱신

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "TTS",
  "from": "Central",
  "body": {
    "speaker_ids": [101, 102],
    "message": "경계 경보입니다"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

```
제어 메시지 처리 흐름:
1. Central → NATS (PUB)           : speaker_ids + message
2. BroadcastingManager ← NATS     : 메시지 수신
3. BroadcastingManager            : 로컬 캐시에서 speaker 상세정보 조회
4. BroadcastingManager → 장비     : 실제 제어 실행
```

#### 패턴 3: 알림만 (상태 변경, 데이터 동기화)

- **대상**: Status 메시지, Sync 메시지
- **body** = **알림 정보만** (ID, action, status 등)
- **이유**: 변경 사실만 전달, 상세 데이터는 REST API 직접 조회

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "type_device": "Speaker",
    "resource_id": 101
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

```
알림 메시지 흐름:
1. 매니저/SubSystem → DBApi (PATCH/PUT)  : 데이터 변경
2. DBApi → NATS (Broadcast)               : 알림만! (데이터 없음)
3. 다른 SubSystem ← NATS                  : 알림 수신
4. SubSystem → DBApi (GET)                : 필요 시 직접 조회하여 캐시 갱신
```

#### 패턴별 메시지 분류

| 패턴 | 메시지 유형 | body 구성 | 수신자 동작 |
|------|------------|----------|------------|
| **1. Full DTO** | Event, AI 탐지 | REST API `data` 전체 | 바로 UI 표시 |
| **2. ID + 파라미터** | Device 제어 | 대상 ID + 제어값 | 캐시 조회 후 실행 |
| **3. 알림만** | Status, Sync | ID + action/status | 필요 시 REST API 조회 |

#### 캐시 의존성 주의사항

> **⚠️ 모든 서브시스템**은 반드시:
> 1. 시작 시 DBApi REST API로 자신에게 필요한 마스터 데이터 로딩 (GET /api/devices/\*, /api/servers, /api/integrations/event-mappings 등)
> 2. SYNC 메시지를 구독하여 캐시 실시간 갱신
> 3. 캐시 miss 시 REST API fallback 구현 권장
>
> 캐싱 대상은 서브시스템별로 다릅니다 — 장비(Device) 정보, 이벤트 매핑, 그룹 정보, 서버 정보, 프리셋 등 자신의 역할에 필요한 데이터를 선택적으로 캐싱합니다. (서브시스템별 상세 목록은 [1.3 서브시스템 목록](#13-시스템-아키텍처) 참조)

---

## 3. Subject 규칙

### 3.1 패턴 구조

```
sensorway.{부대ID}.{서브시스템}.{action}              (제어/상태 — 4토큰)
sensorway.{부대ID}.{서브시스템}.event.{type}           (이벤트 — 5토큰)
sensorway.{부대ID}.{서브시스템}.sync.{resource}        (동기화 — 5토큰)
```

**4~5 토큰**, 점(`.`)으로 구분

| 토큰 | 설명 | 예제 |
|------|------|------|
| `sensorway` | 도메인 (고정) | `sensorway` |
| `{부대ID}` | 부대 식별자 | `unit001`, `unit002`, `*` (전체) |
| `{서브시스템}` | 서브시스템 영역 | `all`, `proxy`, `broadcast_manager`, `nvr_manager`, `vms`, `gis`, `ai_analysis`, `db_api`, `central` |
| `event` | 이벤트 카테고리 (이벤트 메시지만) | `event` (이벤트 메시지에만 포함) |
| `sync` | 동기화 카테고리 (동기화 메시지만) | `sync` (§9 동기화 메시지에만 포함) |
| `{action}` / `{resource}` | 동작 또는 리소스 (하이픈으로 상세 구분) | `detect`, `action-report`, `mode-change`, `ptz` / `device`, `device-group`, `event-suppression` |

> **동기화 subject 명명 규칙**: `sync.{resource}` 의 `{resource}` 는 **REST 리소스명의 케밥 단수형**을 쓴다
> (`device-group` ← `/api/devices/groups`, `proxy-setting` ← `/api/servers/{id}/proxy-settings`,
> `event-suppression` ← `/api/event-suppression-schedules`).

> **`all` 서브시스템**: 특정 수신자를 지정하지 않는 브로드캐스트 이벤트의 기본(default) 서브시스템입니다. 모든 대상을 지칭하며, 발신자/수신자 어디에도 속하지 않는 중립적 도메인 토큰입니다.
>
> **발신자 식별**: Subject에서 제거됨. 메시지 Envelope의 `from` 필드로 발신자를 식별합니다.
>
> **부대 ID**: 메시지가 특정 부대에 한정되는 경우 해당 부대 ID 사용, 전체 부대 대상인 경우 와일드카드(`*`) 사용

### 3.2 서브시스템별 Subject 목록

> **Subject 패턴**: `sensorway.{부대ID}.{서브시스템}.{action}`
> **예시**: 부대 ID가 `unit001`인 경우 → `sensorway.unit001.event.detect`

#### Event (all.event.* / all.event_ai.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.all.event.detect` | PidsProxy | All | DETECT | 센서 탐지 이벤트 |
| `sensorway.unit001.all.event_ai.detect` | AiAnalysis | All | DETECT | 영상 AI 탐지 이벤트 |
| `sensorway.unit001.all.event.malfunction` | PidsProxy | All | MALFUNCTION | 장애 이벤트 |
| `sensorway.unit001.all.event.connection` | PidsProxy | All | CONNECTION | 연결 이벤트 |
| `sensorway.unit001.all.event.action-report` | GIS | All | ACTION_REPORT | 조치 보고 |
| `sensorway.unit001.all.event.system` | DBApi | All (GIS) | SYSTEM_EVENT | 서버 시스템 이벤트 |

#### PidsProxy 제어 (proxy.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.proxy.mode-change` | Central | PidsProxy | MODE_CHANGE | 모드 변경 |
| `sensorway.unit001.proxy.windy` | GIS/Central | PidsProxy | WINDY | 풍량 모드 (GIS: REQ, Central: PUB) |
| `sensorway.unit001.proxy.lamp-clear` | GIS | PidsProxy | LAMP_CLEAR | 경광등 이벤트 해제 |
| `sensorway.unit001.proxy.lamp-off` | GIS/Central | PidsProxy | LAMP_OFF | 경광등 비활성화 (GIS: REQ, Central: PUB) |
| `sensorway.unit001.proxy.lamp-color` | GIS | PidsProxy | LAMP_COLOR_SET | 색상 직접 설정 |
| `sensorway.unit001.proxy.lamp-buzzer` | GIS | PidsProxy | LAMP_BUZZER_SET | 부저 직접 설정 |
| `sensorway.unit001.proxy.lamp-test-color` | Central | PidsProxy | LAMP_COLOR_TEST | 색상 테스트 (5초 후 OFF) |
| `sensorway.unit001.proxy.lamp-test-buzzer` | Central | PidsProxy | LAMP_BUZZER_TEST | 부저 테스트 (5초 후 OFF) |

#### Broadcasting 제어 (broadcast_manager.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.broadcast_manager.tts` | Central | BroadcastingManager | TTS | TTS 방송 |
| `sensorway.unit001.broadcast_manager.play` | GIS | BroadcastingManager | BROADCAST_PLAY | 음원 재생 |
| `sensorway.unit001.broadcast_manager.stop` | GIS | BroadcastingManager | BROADCAST_STOP | 방송 정지 |
| `sensorway.unit001.broadcast_manager.test` | Central | BroadcastingManager | BROADCAST_TEST | 방송 테스트 (자동 정지) |

#### NVR Manager 제어 (nvr_manager.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.nvr_manager.ptz` | Central, GIS, VMS | NVRManager | PTZ_* | PTZ 제어 |
| `sensorway.unit001.nvr_manager.palette` | VMS/Central | NVRManager | PALETTE_SET | 열화상 팔레트 |
| `sensorway.unit001.nvr_manager.wiper` | VMS/Central | NVRManager | WIPER_SET | 와이퍼/브러시 |
| `sensorway.unit001.nvr_manager.heater` | VMS/Central | NVRManager | HEATER_SET | 열선 |
| `sensorway.unit001.nvr_manager.fan` | VMS/Central | NVRManager | FAN_SET | 팬 |
| `sensorway.unit001.nvr_manager.tracking` | VMS/Central | NVRManager | TRACKING_SET | 자동 추적 |
| `sensorway.unit001.nvr_manager.weather-mode` | VMS/Central | NVRManager | WEATHER_MODE_SET | 악천후 모드 |
| `sensorway.unit001.nvr_manager.camera-mode` | VMS/Central | NVRManager | CAMERA_MODE_SET | 카메라 영상 모드 |
| `sensorway.unit001.nvr_manager.headlight` | VMS/Central | NVRManager | HEADLIGHT_SET | 전조등 |
| `sensorway.unit001.nvr_manager.day-night` | VMS/Central | NVRManager | DAY_NIGHT_SET | 주/야간 모드 |
| `sensorway.unit001.nvr_manager.power` | VMS/Central | NVRManager | POWER_SET | 카메라 전원 ON/OFF |

> **PTZ 이동/정지, 프리셋, 투어**: `nvr_manager.ptz` Subject의 `PTZ_*` 명령 사용
>
> **`PTZ_AIM_LOCATION`** *(v1.4)*: GIS 통합상황도 '특정 위치 확인' — 지도 클릭 GPS 좌표로 카메라 조준. 동일 `nvr_manager.ptz` Subject + `PTZ_*`(Absolute) 패밀리이며, 다른 PTZ_*와 동일하게 `GIS → NVRManager` **REQ**. (→ §8.1)

#### AI 탐지 (vms.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.vms.event_ai.detect` | AiAnalysis | VMS/GIS | VMS_DETECT | AI 영상 탐지 전달 (카메라 URL, 이벤트 매핑 포함) |

#### GIS 연동 (gis.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.gis.ptz-status` | NVRManager | GIS, AiAnalysis, VMS | PTZ_STATUS | PTZ 상태 보고 (+ v4.6 감시금지구역 신호) |
| `sensorway.unit001.gis.broadcast-status` | BroadcastingManager | GIS | BROADCAST_STATUS | 방송 동작 상태 보고 (ON/OFF) |
| `sensorway.unit001.gis.tracking-status` | AiAnalysis | GIS | TRACKING_STATUS | 추적 상태 보고 |
| `sensorway.unit001.gis.enclosure-metrics` | DBApi | GIS | ENCLOSURE_METRICS | 함체 환경 텔레메트리 (주기) |

#### Sync (all.sync.*)

| Subject 패턴 | 발신자 (`from`) | 수신자 | cmd | 설명 |
|-------------|----------------|--------|-----|------|
| `sensorway.unit001.all.sync.device` | DBApi | All | SYNC_DEVICE | 장비 동기화 (CRUD + 상태 변경 통합) |
| `sensorway.unit001.all.sync.server` | DBApi | All | SYNC_SERVER | 서버 동기화 (CRUD + 상태 변경 통합) |
| `sensorway.unit001.all.sync.category` | DBApi | All | SYNC_CATEGORY | 카테고리 동기화 |
| `sensorway.unit001.all.sync.device-group` | DBApi | All | SYNC_DEVICE_GROUP | 장비그룹 동기화 |
| `sensorway.unit001.all.sync.event-mapping` | DBApi | All | SYNC_EVENT_MAPPING | 이벤트매핑 동기화 |
| `sensorway.unit001.all.sync.preset` | DBApi | All | SYNC_PRESET | 프리셋 동기화 |
| `sensorway.unit001.all.sync.file-group` | DBApi | All | SYNC_FILE_GROUP | 파일그룹 동기화 |
| `sensorway.unit001.all.sync.camera-setting` | DBApi | All | SYNC_CAMERA_SETTING | 카메라 설정 동기화 |
| `sensorway.unit001.all.sync.proxy-setting` | DBApi | All | SYNC_PROXY_SETTING | 프록시 설정 동기화 |
| `sensorway.unit001.all.sync.detection` | DBApi | All | SYNC_DETECTION | 탐지 이벤트 상태(action_reported)·detail(회전 후 썸네일) 변경 알림 (UPDATE/DELETE만, INSERT 미발행) |
| `sensorway.unit001.all.sync.event-suppression` | DBApi | All | SYNC_EVENT_SUPPRESSION | **이벤트 억제(정비 창)** 변경·창경계 전이 알림 — 이벤트 파이프라인 통제 상태 (§9.12) |

### 3.3 구독 패턴

와일드카드를 사용한 구독 예시:

```
# 특정 부대의 센서 탐지 이벤트 수신
sensorway.unit001.all.event.detect

# 특정 부대의 영상 AI 탐지 이벤트 수신
sensorway.unit001.all.event_ai.detect

# 모든 부대의 센서 탐지 이벤트 수신
sensorway.*.all.event.detect

# 특정 부대의 조치 보고 수신
sensorway.unit001.all.event.action-report

# 특정 부대의 모든 GIS 이벤트 메시지
sensorway.unit001.all.event.>

# 특정 부대의 모든 Lamp 제어
#  ⚠️ NATS `*`는 토큰 전체를 대체하며 접두사 wildcard가 아님 → `proxy.lamp-*`는 매칭 안 됨.
#  개별 subject를 나열하거나 `sensorway.unit001.proxy.*`(proxy 전체)를 구독한다.
sensorway.unit001.proxy.lamp-clear
sensorway.unit001.proxy.lamp-off
sensorway.unit001.proxy.lamp-color
sensorway.unit001.proxy.lamp-buzzer
sensorway.unit001.proxy.lamp-test-color
sensorway.unit001.proxy.lamp-test-buzzer

# 특정 부대의 NVR PTZ 제어
sensorway.unit001.nvr_manager.ptz

# 모든 부대의 모든 메시지 (관제 시스템용)
sensorway.>
```

### 3.4 서브시스템별 구독 목록

> **배포 유형에 따른 구독 패턴**:
> - **통합 관제** (GIS, DBApi): 모든 부대 메시지 수신 → `sensorway.*.{서브시스템}.{action}` *(Central은 NATS 수신 없음, 발행만)*
> - **부대별 서브시스템**: 담당 부대만 수신 → `sensorway.unit001.{서브시스템}.{action}`

#### 통합 관제 시스템 (모든 부대 구독)

| 서브시스템 (`from`) | 구독 Subject |
|-------------------|-------------|
| **Central** (통합관리 Frontend) | - (NATS 수신 없음, 발행 전용. 이벤트/동기화 데이터는 DBApi HTTP 경유) |
| **GIS** (GIS 통합상황도) | `sensorway.*.all.event.detect`, `sensorway.*.all.event_ai.detect`, `sensorway.*.all.event.malfunction`, `sensorway.*.all.event.system`, `sensorway.*.vms.event_ai.detect`, `sensorway.*.gis.tracking-status`, `sensorway.*.gis.ptz-status`, `sensorway.*.gis.broadcast-status`, `sensorway.*.gis.enclosure-metrics`, `sensorway.*.all.sync.*` |
| **DBApi** (DB Api) | - (발행 전용) |

#### 부대별 서브시스템 (담당 부대만 구독, 예: unit001)

| 서브시스템 (`from`) | 구독 Subject |
|-------------------|-------------|
| **PidsProxy** | `sensorway.unit001.all.event.detect`, `sensorway.unit001.all.event_ai.detect`, `sensorway.unit001.all.event.action-report`(경광등 이벤트 연동), `sensorway.unit001.proxy.*`, `sensorway.unit001.all.sync.*` |
| **BroadcastingManager** | `sensorway.unit001.all.event.detect`, `sensorway.unit001.all.event_ai.detect`, `sensorway.unit001.all.event.action-report`, `sensorway.unit001.broadcast_manager.*`, `sensorway.unit001.all.sync.*` |
| **NVRManager** | `sensorway.unit001.all.event.detect`, `sensorway.unit001.all.event_ai.detect`, `sensorway.unit001.all.event.action-report`, `sensorway.unit001.nvr_manager.*`, `sensorway.unit001.all.sync.*` |
| **VMS** (VMS) | `sensorway.unit001.vms.event_ai.detect`, `sensorway.unit001.all.event.action-report`, `sensorway.unit001.gis.ptz-status`, `sensorway.unit001.all.sync.*` |
| **AiAnalysis** | `sensorway.unit001.all.event.action-report`, `sensorway.unit001.all.sync.*`, `sensorway.unit001.gis.ptz-status` |

---

## 4. Enum 타입 정의

> **참조**: `GOP_Restful_Api_연동설계_v4.6` 섹션 4에 정의된 Enum을 그대로 사용합니다.

NATS 메시지에서 사용하는 주요 Enum:

### 4.1 메시지 전용 Enum

#### EnumMessageType
```python
class EnumMessageType(str, Enum):
    PUB = "PUB"     # 단방향 발행 (운용)
    REQ = "REQ"     # 요청 (응답 필요)
    RSP = "RSP"     # 응답
```

#### EnumSubsystem (from 필드)
```python
class EnumSubsystem(str, Enum):
    # 통합 시스템
    CENTRAL = "Central"                     # 통합관리 Frontend
    GIS = "GIS"                             # GIS 통합상황도
    DBAPI = "DBApi"                         # DB Api

    # 부대별 매니저
    PIDS_PROXY = "PidsProxy"                # PidsProxy Manager
    BROADCASTING = "BroadcastingManager"    # 방송 Manager
    NVR = "NVRManager"                       # NVR Manager
    VMS = "VMS"                             # NVR Frontend (VMS)
    AI_ANALYSIS = "AiAnalysis"              # 영상분석 서버 (AI 영상 분석)
```

#### EnumThreatLevel (위협 등급, NATS 전용)
```python
class EnumThreatLevel(str, Enum):
    NORMAL  = "NORMAL"    # 일반 — 탐지됐으나 위협 아님
    CAUTION = "CAUTION"   # 경계 — 주의 필요 (경계구역 접근 등)
    THREAT  = "THREAT"    # 위협 — 즉각 대응 필요 (침입/접근)
```
> AiAnalysis가 탐지 객체별로 산출하여 `TRACKING_STATUS` body의 `targets[].threat_level`로 전송.
> 현재 REST/DB 대응 컬럼이 없는 **NATS 전용 파생값**(DB 영속화 여부는 별도 결정).

### 4.2 REST API 공유 Enum (참조)

아래 Enum은 `GOP_Restful_Api_연동설계_v4.6` 섹션 4에서 정의된 것을 그대로 사용합니다.
NATS 메시지 body의 Enum 필드는 REST API와 동일한 값을 사용하여 변환 없이 DB 저장이 가능합니다.

| Enum | REST API 섹션 | NATS 사용처 |
|------|--------------|-------------|
| EnumDeviceType | 4.1 | Device 관련 body |
| EnumDeviceStatus | 4.1 | Device 상태 변경 |
| EnumCameraMode | 4.1 | Camera body |
| EnumCameraType | 4.1 | Camera body |
| EnumDeviceCategory | 4.1 | Device 카테고리 |
| EnumEventType | 4.2 | Event body (`type_event` 필드) |
| EnumEventCategory | 4.2 | Event 카테고리 (detection, malfunction, connection) |
| EnumDetectionType | 4.2 | Detection Event body (`result`; AI 영상 탐지 시 `AI_DETECT`=12) |
| EnumFaultType | 4.2 | Malfunction Event body |
| EnumTrueFalse | 4.2 | action_reported 필드 |
| EnumLampColor | 4.1 | Lamp 제어 body |
| EnumBuzzerSound | 4.1 | Lamp 제어 body |
| EnumLightMode | 4.1 | Lamp 제어 body |
| EnumServerStatus | 4.4 | Server 상태 변경 |
| EnumOperationMode | 4.9 | ProxySetting 운용 모드 (MODE_CHANGE) |
| EnumWindyMode | 4.9 | ProxySetting 풍량 모드 (WINDY) |
| EnumWeatherMode | 4.9 | WEATHER_MODE_SET body |
| EnumCameraVideoMode | 4.9 | CAMERA_MODE_SET body |
| EnumOnOff | 4.9 | HEATER_SET, FAN_SET, HEADLIGHT_SET, WIPER_SET, TRACKING_SET, BROADCAST_STATUS body |
| EnumDayNightMode | 4.9 | DAY_NIGHT_SET body |
| EnumPalette | 4.9 | PALETTE_SET body |
| EnumFocusMode | 4.9 | CameraSetting 초점 모드 *(v3.7)* |
| EnumIrisMode | 4.9 | CameraSetting 조리개 모드 *(v3.7)* |
| EnumSystemEventSeverity | 8.7 | SYSTEM_EVENT body (`severity`) *(v3.9)* |
| EnumSuppressionStatus | 6.8 | SYNC_EVENT_SUPPRESSION body (`status`) — `pending`/`active`/`expired`/`cancelled` (소문자) *(v6.3)* |

---

## 5. 메시지 카탈로그

### 5.1 전체 메시지 요약 (총 44종)

#### Event/탐지 메시지 (7종)

| # | cmd | Subject 패턴 | 방향 | m_type | REST API body 재사용 |
|---|-----|-------------|------|--------|---------------------|
| 1 | `DETECT` | `sensorway.{부대ID}.all.event.detect` (센서), `sensorway.{부대ID}.all.event_ai.detect` (영상AI) | PidsProxy/AiAnalysis → All | PUB | `GET /api/events/detections/{id}` Response `data` |
| 2 | `VMS_DETECT` | `sensorway.{부대ID}.vms.event_ai.detect` | AiAnalysis → VMS, GIS | PUB | Detection Event `data` + EventMapping + Camera URLs |
| 3 | `MALFUNCTION` | `sensorway.{부대ID}.all.event.malfunction` | PidsProxy → All | PUB | `GET /api/events/malfunctions/{id}` Response `data` |
| 4 | `CONNECTION` | `sensorway.{부대ID}.all.event.connection` | PidsProxy → All | PUB | `GET /api/events/connections/{id}` Response `data` |
| 5 | `ACTION_REPORT` | `sensorway.{부대ID}.all.event.action-report` | GIS → All | PUB | `GET /api/events/actions/{id}` Response `data` |
| 6 | `SYSTEM_EVENT` | `sensorway.{부대ID}.all.event.system` | DBApi → All | PUB | `GET /api/servers/{id}/system-events` Response `data.items[]` |
| 7 | `ENCLOSURE_METRICS` | `sensorway.{부대ID}.gis.enclosure-metrics` | DBApi → GIS | PUB | `GET /api/enclosure-metrics` Response `data.items[]` |

#### PidsProxy 제어 메시지 (2종)

| # | cmd | Subject 패턴 | 방향 | m_type |
|---|-----|-------------|------|--------|
| 5 | `MODE_CHANGE` | `sensorway.{부대ID}.proxy.mode-change` | Central → PidsProxy | PUB |
| 6 | `WINDY` | `sensorway.{부대ID}.proxy.windy` | Central → PidsProxy | PUB |
| 6 | `WINDY` | `sensorway.{부대ID}.proxy.windy` | GIS → PidsProxy | REQ |

#### Broadcast 제어 메시지 (5종)

| # | cmd | Subject 패턴 | 방향 | m_type | 설명 |
|---|-----|-------------|------|--------|------|
| 7 | `TTS` | `sensorway.{부대ID}.broadcast_manager.tts` | Central → BroadcastingManager | PUB | 텍스트 음성 변환 |
| 8 | `BROADCAST_PLAY` | `sensorway.{부대ID}.broadcast_manager.play` | GIS → BroadcastingManager | REQ | 음원 파일 재생 |
| 9 | `BROADCAST_STOP` | `sensorway.{부대ID}.broadcast_manager.stop` | GIS → BroadcastingManager | REQ | 방송 정지 |
| 10 | `BROADCAST_TEST` | `sensorway.{부대ID}.broadcast_manager.test` | Central → BroadcastingManager | PUB | 테스트 (자동 정지) |
| 11 | `BROADCAST_STATUS` | `sensorway.{부대ID}.gis.broadcast-status` | BroadcastingManager → GIS | PUB | 방송 동작 상태 보고 (ON/OFF) |

#### Lamp 제어 메시지 (6종)

| # | cmd | Subject 패턴 | 방향 | m_type | 설명 |
|---|-----|-------------|------|--------|------|
| 12 | `LAMP_CLEAR` | `sensorway.{부대ID}.proxy.lamp-clear` | GIS → PidsProxy | REQ | 이벤트 해제 |
| 13 | `LAMP_OFF` | `sensorway.{부대ID}.proxy.lamp-off` | GIS/Central → PidsProxy | REQ/PUB | 경광등 비활성화 |
| 14 | `LAMP_COLOR_SET` | `sensorway.{부대ID}.proxy.lamp-color` | GIS → PidsProxy | REQ | 색상 직접 설정 |
| 15 | `LAMP_BUZZER_SET` | `sensorway.{부대ID}.proxy.lamp-buzzer` | GIS → PidsProxy | REQ | 부저 직접 설정 |
| 16 | `LAMP_COLOR_TEST` | `sensorway.{부대ID}.proxy.lamp-test-color` | Central → PidsProxy | PUB | 색상 테스트 (자동 OFF) |
| 17 | `LAMP_BUZZER_TEST` | `sensorway.{부대ID}.proxy.lamp-test-buzzer` | Central → PidsProxy | PUB | 부저 테스트 (자동 OFF) |

#### NVR/Camera 제어 메시지 (13종)

| # | cmd | Subject 패턴 | 방향 | m_type | DB 저장 |
|---|-----|-------------|------|--------|---------|
| 18 | `PTZ_*` (37종) | `sensorway.{부대ID}.nvr_manager.ptz` | Central/GIS/VMS → NVRManager | REQ¹ | - |
| 19 | `PTZ_STATUS` | `sensorway.{부대ID}.gis.ptz-status` | NVRManager → GIS, AiAnalysis, VMS | PUB | - |
| 20 | `PALETTE_SET` | `sensorway.{부대ID}.nvr_manager.palette` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 21 | `WIPER_SET` | `sensorway.{부대ID}.nvr_manager.wiper` | VMS/Central → NVRManager | REQ | - (조작) |
| 22 | `HEATER_SET` | `sensorway.{부대ID}.nvr_manager.heater` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 23 | `FAN_SET` | `sensorway.{부대ID}.nvr_manager.fan` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 24 | `TRACKING_SET` | `sensorway.{부대ID}.nvr_manager.tracking` | VMS/Central → NVRManager | REQ | - |
| 25 | `TRACKING_STATUS` | `sensorway.{부대ID}.gis.tracking-status` | AiAnalysis → GIS | PUB | - |
| 26 | `WEATHER_MODE_SET` | `sensorway.{부대ID}.nvr_manager.weather-mode` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 27 | `CAMERA_MODE_SET` | `sensorway.{부대ID}.nvr_manager.camera-mode` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 28 | `HEADLIGHT_SET` | `sensorway.{부대ID}.nvr_manager.headlight` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 29 | `DAY_NIGHT_SET` | `sensorway.{부대ID}.nvr_manager.day-night` | VMS/Central → NVRManager | REQ | ✅ CameraSetting |
| 30 | `POWER_SET` | `sensorway.{부대ID}.nvr_manager.power` | VMS/Central → NVRManager | REQ | - (조작) |

> **DB 저장**: ✅ 표시된 cmd는 NVRManager가 카메라 제어 성공 후 `PATCH /api/devices/cameras/{id}/settings`로 DBApi에 저장
>
> **PTZ 속도**: `pan_tilt_speed`, `zoom_speed`는 별도 cmd 없이 PTZ 제어 메시지(`PTZ_*`) body에 선택 속성으로 포함
>
> **¹ PTZ_AIM_LOCATION** *(v1.4, 37번째 PTZ_*)*: GIS 통합상황도 '특정 위치 확인' — 지도 GPS 좌표로 카메라 조준. 동일 `nvr_manager.ptz` Subject이며 나머지 PTZ_*와 동일하게 **`GIS → NVRManager` REQ**. body=GPS 좌표+거리/방위. (→ §8.1)

#### 마스터 데이터 동기화 메시지 (11종)

| # | cmd | Subject 패턴 | 방향 | m_type | 알림 후 조회 API |
|---|-----|-------------|------|--------|-----------------|
| 32 | `SYNC_DEVICE` | `sensorway.{부대ID}.all.sync.device` | DBApi → All | PUB | `GET /api/devices/{type}/{id}` |
| 33 | `SYNC_SERVER` | `sensorway.{부대ID}.all.sync.server` | DBApi → All | PUB | `GET /api/servers/{id}` |
| 34 | `SYNC_CATEGORY` | `sensorway.{부대ID}.all.sync.category` | DBApi → All | PUB | `GET /api/servers/categories/{id}` |
| 35 | `SYNC_DEVICE_GROUP` | `sensorway.{부대ID}.all.sync.device-group` | DBApi → All | PUB | `GET /api/devices/groups/{id}` |
| 36 | `SYNC_EVENT_MAPPING` | `sensorway.{부대ID}.all.sync.event-mapping` | DBApi → All | PUB | `GET /api/integrations/event-mappings/{id}` |
| 37 | `SYNC_PRESET` | `sensorway.{부대ID}.all.sync.preset` | DBApi → All | PUB | `GET /api/devices/cameras/{id}/presets/{id}` |
| 38 | `SYNC_FILE_GROUP` | `sensorway.{부대ID}.all.sync.file-group` | DBApi → All | PUB | `GET /api/file-groups/{id}` |
| 39 | `SYNC_CAMERA_SETTING` | `sensorway.{부대ID}.all.sync.camera-setting` | DBApi → All | PUB | `GET /api/devices/cameras/{camera_id}/settings` |
| 40 | `SYNC_PROXY_SETTING` | `sensorway.{부대ID}.all.sync.proxy-setting` | DBApi → All | PUB | `GET /api/servers/{server_id}/proxy-settings` |
| 41 | `SYNC_DETECTION` | `sensorway.{부대ID}.all.sync.detection` | DBApi → All | PUB | `GET /api/events/detections/{id}` |
| 42 | `SYNC_EVENT_SUPPRESSION` | `sensorway.{부대ID}.all.sync.event-suppression` | DBApi → All | PUB | `GET /api/event-suppression-schedules/{id}` + `/active` |

> **동기화 메시지 = 알림(Notification)만 전달**
> - NATS 메시지 body에는 `action`, `resource_id`만 포함 (데이터 없음!)
> - `SYNC_DEVICE`는 추가로 `type_device` 필드 포함
> - 알림 수신 후 Subsystem이 직접 REST API 호출하여 최신 데이터 조회
> - `action`: `CREATED` (신규 생성) / `UPDATED` (수정) / `DELETED` (삭제)
> - 초기 로딩은 REST API 직접 호출, NATS는 변경 알림만 담당

---

## 6. Event 메시지 설계

### 6.1 Detection Event (탐지)

**cmd**: `DETECT`
**Subject**: `sensorway.{부대ID}.all.event.detect` (센서), `sensorway.{부대ID}.all.event_ai.detect` (영상AI)
**방향**: PidsProxy/AiAnalysis → GIS, NVRManager, BroadcastingManager, PidsProxy(경광등 연동)
**m_type**: PUB  
**트리거**: 센서 침입 탐지 또는 영상 AI 탐지 발생 시  

> **REST API 참조**: `GET /api/events/detections/{id}` Response `data` 구조 재사용
>
> **설계 원칙**: GOP RESTful API Response `data` 구조 재사용으로 View 일관성 확보

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "DETECT",
  "from": "PidsProxy",
  "body": {
    "id": 1001,
    "type_event": "Intrusion",
    "action_reported": "False",
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "controller_id": 1,
      "geolocation": {
        "location": "A구역 1번 초소",
        "latitude": 38.1201,
        "longitude": 127.5612,
        "altitude": 230.0,
        "heading": 90.0
      },
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "result": "PIR_SENSOR",
    "detail": {
      "signal": 2000,
      "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
      "frame_width": 1280,
      "frame_height": 720,
      "objects": [
        {"label": "person", "confidence": 0.92, "bbox": [150, 220, 60, 120]}
      ],
      "model": "yolov8n",
      "inference_ms": 42
    },
    "created_at": "2026-02-05T10:30:00.000Z",
    "updated_at": "2026-02-05T10:30:00.000Z"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `id` | integer | Y | 이벤트 ID | Response `data.id` |
| `type_event` | string | Y | 이벤트 타입 (EnumEventType: `Intrusion`) | Response `data.type_event` |
| `action_reported` | string | Y | 조치 보고 여부 (EnumTrueFalse) — **시스템 자동 관리**(v2.8/v4.6): ActionEvent 1:N 생성/삭제 시 자동 갱신(남은 ActionEvent 0개일 때만 `False` 복원), 클라이언트 전송 불가 | Response `data.action_reported` |
| `device` | object | N | Device DTO (삭제된 경우 null, **nested 객체는 created_at/updated_at 제외**) | Response `data.device` |
| `device_description` | string | Y | Device 정보 스냅샷 | Response `data.device_description` |
| `result` | string | Y | 탐지 결과 (EnumDetectionType — 센서계열 + AI 영상 탐지는 `AI_DETECT`=12) | Response `data.result` |
| `detail` | object | N | 상세 정보 (JSONB). `objects[].bbox`(픽셀 `[x,y,w,h]`)는 `detail.frame_width`/`frame_height`(**AI 추론 프레임 해상도, px**) 기준으로 해석 — 프레임 크기 없이는 bbox 비율을 알 수 없음. 이 값은 **AiAnalysis가 추론 시 처리한 실제 프레임 크기를 직접 기록**(자산 API 조회 아님)하며, 카메라 자산 `resolution_width/height`(설정 해상도)와 다를 수 있음 | Response `data.detail` |
| `created_at` | datetime | Y | 생성 시간 (ISO 8601) | Response `data.created_at` |
| `updated_at` | datetime | Y | 수정 시간 (ISO 8601) | Response `data.updated_at` |

> **Nested 객체 원칙**: Event body의 `device` nested 객체에서는 `created_at`, `updated_at` 필드를 제외합니다 (Action Report의 `from_event` 제외).
>
> **`geolocation` 구조**: `device.geolocation`은 `{ location, latitude(WGS84), longitude(WGS84), altitude(m), heading }` 객체이며 미설정 시 `null`. `heading`(0~360° optional float)은 **장비 설치 방위각**으로, v4.4에서 추가되어 GIS의 **부채꼴(FOV) 방향 시각화**에 사용된다. REST `Device.geolocation` DTO를 그대로 재사용하므로 별도 변환 없이 `SYNC_DEVICE`(수신 후 REST 조회) 및 geolocation을 싣는 이벤트 메시지(`DETECT`/`MALFUNCTION`/`CONNECTION`/`ACTION_REPORT`/`VMS_DETECT`)의 `device.geolocation`을 통해 공통 전달된다.
>
> **EventMapping 연동 흐름**: 수신 매니저는 `device.device_groups[]`를 기준으로 EventMapping을 조회하여 연동 동작(카메라 프리셋 이동, 방송, 경광등 등)을 수행합니다.
>
> ```
> 1. DetectionEvent 수신 (device.id = 101)
> 2. device.device_groups[] 에서 DeviceGroup ID 목록 추출
> 3. EventMapping 조회 (device_group_id + category_event_mapping)
> 4. EventMappingCamera/Speaker/Lamp 실행
> ```

> **AI 영상 탐지 (VMS_DETECT)**: AiAnalysis 기반 영상 AI 탐지 이벤트는 `all.event_ai.detect` 브로드캐스트 외에, AiAnalysis가 VMS/GIS에게 카메라 URL과 이벤트 매핑 정보를 포함한 VMS_DETECT를 **PUB**(브로드캐스트, 수신자 VMS·GIS 둘)로 직접 전달합니다. 섹션 8.2.1 VMS_DETECT를 참조하세요.

---

> **DBApi는 탐지 INSERT를 재발행하지 않는다(중복 방지)**: 최초 `DETECT`는 필드(PidsProxy 센서 / AiAnalysis AI)가 유일 발행한다. DBApi는 탐지 행의 **UPDATE/DELETE**(예: PTZ 회전 후 `detail.thumbnail` 갱신, `action_reported` 변경)만 `SYNC_DETECTION`(§9.11)으로 **별도 subject·from(DBApi)** 으로 알린다. (v6.3 detection-sync-message)

### 6.2 Malfunction Event (장애)

**cmd**: `MALFUNCTION`  
**Subject**: `sensorway.{부대ID}.all.event.malfunction`
**방향**: PidsProxy → All (GIS 등, Central은 NATS 미수신·DBApi HTTP 경유)  
**m_type**: PUB  
**트리거**: 센서/제어기에서 장애 감지 시  

> **REST API 참조**: `GET /api/events/malfunctions/{id}` Response `data` 구조 재사용
>
> **설계 원칙**: GOP RESTful API Response `data` 구조 재사용으로 View 일관성 확보

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "MALFUNCTION",
  "from": "PidsProxy",
  "body": {
    "id": 2001,
    "type_event": "Fault",
    "action_reported": "False",
    "device": {
      "id": 103,
      "number_device": 3,
      "group_device": 1,
      "name_device": "Sensor-A-3",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "controller_id": 1,
      "geolocation": {
        "location": "A구역 3번 펜스",
        "latitude": 38.1208,
        "longitude": 127.5625,
        "altitude": 232.0,
        "heading": 180.0
      },
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
    "reason": "FAULT_CABLE_CUTTING",
    "detail": {
      "first_start": 10,
      "first_end": 15,
      "second_start": 20,
      "second_end": 25
    },
    "created_at": "2026-02-05T10:30:00.000Z",
    "updated_at": "2026-02-05T10:30:00.000Z"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `id` | integer | Y | 이벤트 ID | Response `data.id` |
| `type_event` | string | Y | 이벤트 타입 (EnumEventType: `Fault`) | Response `data.type_event` |
| `action_reported` | string | Y | 조치 보고 여부 (EnumTrueFalse) — **시스템 자동 관리**(v2.8/v4.6): ActionEvent 1:N 생성/삭제 시 자동 갱신(남은 ActionEvent 0개일 때만 `False` 복원), 클라이언트 전송 불가 | Response `data.action_reported` |
| `device` | object | N | Device DTO (삭제된 경우 null, **nested 객체는 created_at/updated_at 제외**) | Response `data.device` |
| `device_description` | string | Y | Device 정보 스냅샷 | Response `data.device_description` |
| `reason` | string | Y | 장애 원인 (EnumFaultType) | Response `data.reason` |
| `detail` | object | N | 장애 상세 정보 (JSONB) | Response `data.detail` |
| `created_at` | datetime | Y | 생성 시간 (ISO 8601) | Response `data.created_at` |
| `updated_at` | datetime | Y | 수정 시간 (ISO 8601) | Response `data.updated_at` |

---

### 6.3 Connection Event (연결)

**cmd**: `CONNECTION`  
**Subject**: `sensorway.{부대ID}.all.event.connection`
**방향**: PidsProxy → All (Central은 NATS 미수신·DBApi HTTP 경유)  
**m_type**: PUB  
**트리거**: 장비 연결/재연결 감지 시  

> **참고 (v1.5.1)**: `all.event.connection`으로 브로드캐스트하나 **현재 이를 소비하는 서브시스템은 없다**(수신해도 처리 동작이 아직 없는 상태). 향후 활용을 대비해 발행은 **유지**하며, 소비가 필요해지면 §3.4 구독 목록에 소비자(GIS 등)를 추가한다.
>
> **REST API 참조**: `GET /api/events/connections/{id}` Response `data` 구조 재사용
>
> **설계 원칙**: GOP RESTful API Response `data` 구조 재사용으로 View 일관성 확보

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "CONNECTION",
  "from": "PidsProxy",
  "body": {
    "id": 3001,
    "type_event": "Connection",
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "controller_id": 1,
      "geolocation": {
        "location": "A구역 1번 초소",
        "latitude": 38.1201,
        "longitude": 127.5612,
        "altitude": 230.0,
        "heading": 90.0
      },
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Fence] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-02-05T10:30:00.000Z",
    "updated_at": "2026-02-05T10:30:00.000Z"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `id` | integer | Y | 이벤트 ID | Response `data.id` |
| `type_event` | string | Y | 이벤트 타입 (EnumEventType: `Connection`) | Response `data.type_event` |
| `device` | object | N | Device DTO (삭제된 경우 null, **nested 객체는 created_at/updated_at 제외**) | Response `data.device` |
| `device_description` | string | Y | Device 정보 스냅샷 | Response `data.device_description` |
| `created_at` | datetime | Y | 생성 시간 (ISO 8601) | Response `data.created_at` |
| `updated_at` | datetime | Y | 수정 시간 (ISO 8601) | Response `data.updated_at` |

> **참고**: Connection Event는 `action_reported` 필드가 없으며, Detection/Malfunction Event와 달리 조치 보고 기능이 없습니다.
>
> **Nested 객체 원칙**: Event body의 `device` nested 객체에서는 `created_at`, `updated_at` 필드를 제외합니다 (Action Report의 `from_event` 제외).

---

### 6.4 Action Report (조치 보고)

**cmd**: `ACTION_REPORT`  
**Subject**: `sensorway.{부대ID}.all.event.action-report`
**방향**: GIS → All (NVRManager 홈복귀, BroadcastingManager 방송종료, PidsProxy 경광등 연동, VMS)  
**m_type**: PUB  
**트리거**: 운영자가 이벤트에 대한 조치를 보고할 때  

> **REST API 참조**: `GET /api/events/actions/{id}` Response `data` 구조 재사용
>
> **설계 원칙**: GOP RESTful API Response `data` 구조 재사용으로 View 일관성 확보

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "ACTION_REPORT",
  "from": "GIS",
  "body": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
    "from_event": {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "controller_id": 1,
        "geolocation": {
          "location": "A구역 1번 초소",
          "latitude": 38.1201,
          "longitude": 127.5612,
          "altitude": 230.0,
          "heading": 90.0
        },
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "result": "PIR_SENSOR",
      "detail": {
        "signal": 2000,
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg"
      },
      "created_at": "2026-02-05T10:30:00.000Z",
      "updated_at": "2026-02-05T10:31:00.000Z"
    },
    "created_at": "2026-02-05T10:31:00.000Z",
    "updated_at": "2026-02-05T10:31:00.000Z"
  },
  "created": "2026-02-05T10:31:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `id` | integer | Y | ActionEvent ID | Response `data.id` |
| `type_event` | string | Y | 이벤트 타입 (`Action`) | Response `data.type_event` |
| `content` | string | Y | 조치 내용 | Response `data.content` |
| `user` | string | Y | 조치 수행자 | Response `data.user` |
| `from_event` | object | Y | 원본 이벤트 (DetectionEvent/MalfunctionEvent 전체 DTO) | Response `data.from_event` |
| `created_at` | datetime | Y | 생성 시간 (ISO 8601) | Response `data.created_at` |
| `updated_at` | datetime | Y | 수정 시간 (ISO 8601) | Response `data.updated_at` |

> **EventMapping 복귀 동작 흐름**: 수신 매니저는 `from_event.device.device_groups[]`를 기준으로 EventMapping을 조회하여 복귀 동작을 수행합니다.
>
> ```
> 1. ActionEvent 수신 (from_event.device.id = 101)
> 2. from_event.device.device_groups[] 에서 DeviceGroup ID 목록 추출
> 3. EventMapping 조회 (device_group_id + category_event_mapping)
> 4. 복귀 동작 수행:
>    - NVRManager: 카메라 홈 프리셋 복귀
>    - BroadcastingManager: 방송 종료
> ```

---

### 6.5 System Event (서버 시스템 이벤트)

> *(NATS 신규 메시지)*

**cmd**: `SYSTEM_EVENT`  
**Subject**: `sensorway.{부대ID}.all.event.system`  
**방향**: DBApi → All (GIS 관제)  
**m_type**: PUB  
**트리거**: 서버 메트릭 임계 초과 등 시스템 이벤트 발생 시  

> **REST API 참조**: `GET /api/servers/{server_id}/system-events` Response `data.items[]` 요소 재사용
> **설계 원칙**: Full-DTO 패턴. REST 응답은 `server_id`가 경로 파라미터이나 NATS는 경로가 없으므로 body에 포함.

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "SYSTEM_EVENT",
  "from": "DBApi",
  "body": {
    "id": 1,
    "server_id": 1,
    "type_event": "threshold_warning",
    "severity": "WARNING",
    "source": "server_metrics",
    "message": "CPU usage exceeded 80%",
    "acknowledged": false,
    "server_description": "VMS Server #1",
    "created_at": "2026-02-13T10:00:00.000Z"
  },
  "created": "2026-02-13T10:00:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `id` | integer | Y | 시스템 이벤트 ID | `data.items[].id` |
| `server_id` | integer | Y | 발생 서버 ID (NATS 전용 — REST는 경로 파라미터) | path `{server_id}` |
| `type_event` | string | Y | 이벤트 타입 (예: `threshold_warning`, `BACKUP_FAILED`) | `data.items[].type_event` |
| `severity` | string | Y | 심각도 (EnumSystemEventSeverity: `INFO`/`WARNING`/`ERROR`/`CRITICAL`) | `data.items[].severity` |
| `source` | string | N | 발생 출처 (예: `server_metrics`) | `data.items[].source` |
| `message` | string | Y | 이벤트 메시지 | `data.items[].message` |
| `acknowledged` | boolean | Y | 확인 여부 | `data.items[].acknowledged` |
| `server_description` | string | N | 서버 정보 스냅샷 | `data.items[].server_description` |
| `created_at` | datetime | Y | 발생 시각 (ISO 8601) | `data.items[].created_at` |

---

### 6.6 Enclosure Metrics (함체 텔레메트리)

> *(NATS 신규 메시지 — 주기 텔레메트리)*

**cmd**: `ENCLOSURE_METRICS`  
**Subject**: `sensorway.{부대ID}.gis.enclosure-metrics`  
**방향**: DBApi → GIS  
**m_type**: PUB  
**전송 주기**: 주기 push (운영 설정값, 권장 기본 10초)  

> **REST API 참조**: `GET /api/enclosure-metrics` Response `data.items[]` 요소 재사용
> **성격**: 이벤트가 아닌 **주기적 텔레메트리(상태 전파)**. 의미상 상태 메시지에 가까우나 발행 주체(DBApi)·소비처(GIS) 정합을 위해 §6에 함께 둔다.

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "ENCLOSURE_METRICS",
  "from": "DBApi",
  "body": {
    "enclosure_id": 1,
    "temperature": 25.5,
    "humidity": 60.0,
    "voltage": 220.0,
    "current": 1.5,
    "measured_at": "2026-02-13T10:00:00.000Z"
  },
  "created": "2026-02-13T10:00:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `enclosure_id` | integer | Y | 함체(Enclosure) ID | `data.items[].enclosure_id` |
| `temperature` | float | N | 내부 온도 (℃) | `data.items[].temperature` |
| `humidity` | float | N | 내부 습도 (%) | `data.items[].humidity` |
| `voltage` | float | N | 전압 (V) | `data.items[].voltage` |
| `current` | float | N | 전류 (A) | `data.items[].current` |
| `measured_at` | datetime | Y | 측정 시각 (ISO 8601, REST `created_at` 대응) | `data.items[].created_at` |

> **다중 함체**: 동시 다발 시 단건 반복 발행. 묶음 전송이 필요하면 `metrics[]` 배열화 검토(TRACKING_STATUS `targets[]` 선례).

---

## 7. Device 제어 메시지 설계

### 7.1 PidsProxy 제어

> **참고**: NATS는 Middleware(PIDS)와 직접 연동하지 않습니다. PidsProxy가 PIDS Middleware를 관리하며, NATS 메시지는 PidsProxy로 전달됩니다.

#### 7.1.1 MODE_CHANGE (모드 변경)

**cmd**: `MODE_CHANGE`  
**Subject**: `sensorway.{부대ID}.proxy.mode-change`  
**방향**: Central → PidsProxy  
**m_type**: PUB  

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "MODE_CHANGE",
  "from": "Central",
  "body": {
    "mode": "REGISTER"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `mode` | EnumOperationMode | Y | NORMAL, REGISTER |

---

#### 7.1.2 WINDY (풍량 모드)

**cmd**: `WINDY`
**Subject**: `sensorway.{부대ID}.proxy.windy`
**방향**: Central → PidsProxy (PUB), GIS → PidsProxy (REQ)
**m_type**: PUB / REQ

**① PUB (Central → PidsProxy, 단방향):**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "WINDY",
  "from": "Central",
  "body": {
    "mode": "wind1"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**② REQ (GIS → PidsProxy, 응답 필요):**

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "WINDY",
  "from": "GIS",
  "body": {
    "mode": "wind2"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**③ RSP (PidsProxy → GIS):**

```json
{
  "id": "uuid-v4",
  "m_type": "RSP",
  "cmd": "WINDY",
  "from": "PidsProxy",
  "body": {
    "mode": "wind2"
  },
  "success": true,
  "message": "풍량 모드 변경 완료",
  "req_id": "original-request-uuid",
  "created": "2026-02-05T10:30:00.100Z"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `mode` | EnumWindyMode | Y | wind0, wind1, wind2, wind3 |

---

### 7.2 Broadcasting 제어

> **제어 유형 원칙**: GIS(Frontend) → 매니저 단일대상 **제어는 REQ/RSP**(운영자 확인 필요). Central 발행 및 다중수신 브로드캐스트는 **PUB**. RSP는 §2 표준 봉투(`success`/`req_id`/`message`)를 사용한다.
>
> **설계 패턴**: ID + 파라미터 (패턴 2)
> - BroadcastingManager는 시작 시 Speaker/Server 정보를 캐시
> - 메시지에는 `speaker_ids`만 포함, 상세 정보는 캐시에서 조회

#### 7.2.1 TTS (문자음성 방송)

**cmd**: `TTS`  
**Subject**: `sensorway.{부대ID}.broadcast_manager.tts`  
**방향**: Central → BroadcastingManager  
**m_type**: PUB  

**Publish Body:**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "TTS",
  "from": "Central",
  "body": {
    "speaker_ids": [101, 102],
    "message": "경계 경보입니다. 즉시 확인 바랍니다."
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `speaker_ids` | array[integer] | Y | 대상 스피커 ID 목록 |
| `message` | string | Y | TTS 변환할 텍스트 |

**BroadcastingManager 처리:**
```python
def on_tts(msg):
    for speaker_id in msg.body.speaker_ids:
        # 로컬 캐시에서 Speaker 정보 조회
        speaker = cache.get_speaker(speaker_id)
        if not speaker:
            logger.warning(f"Speaker {speaker_id} not found in cache")
            continue

        # Server 정보도 캐시에서 조회
        server = cache.get_server(speaker.server_id)

        # TTS 실행
        broadcast_tts(server, speaker, msg.body.message)
```

> **EventMapping 기반 스피커 선택**: 이벤트 발생 시 스피커 선택은 서버에서 EventMapping 조회를 통해 수행됩니다.
> - DetectionEvent.device.device_groups[] → EventMapping → EventMappingSpeaker → speaker_ids[]

---

#### 7.2.2 BROADCAST_PLAY (음원 재생)

**cmd**: `BROADCAST_PLAY`
**Subject**: `sensorway.{부대ID}.broadcast_manager.play`
**방향**: GIS → BroadcastingManager
**m_type**: REQ

> **용도**: 음원 파일 재생 (STOP 명령 전까지 또는 재생 완료까지 유지)
>
> **RSP**: §2 표준 봉투(`success`/`req_id`/`message`) 사용

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "BROADCAST_PLAY",
  "from": "GIS",
  "body": {
    "speaker_ids": [101, 102],
    "file_group_id": 15,
    "repeat": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `speaker_ids` | integer[] | Y | 대상 스피커 ID 목록 |
| `file_group_id` | integer | Y | 재생할 파일 그룹 ID |
| `repeat` | integer | N | 반복 횟수 (기본: 1, 0=무한반복) |

---

#### 7.2.3 BROADCAST_STOP (방송 정지)

**cmd**: `BROADCAST_STOP`
**Subject**: `sensorway.{부대ID}.broadcast_manager.stop`
**방향**: GIS → BroadcastingManager
**m_type**: REQ

> **용도**: 진행 중인 방송 정지 (TTS, PLAY, TEST 모두 정지)
>
> **RSP**: §2 표준 봉투(`success`/`req_id`/`message`) 사용

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "BROADCAST_STOP",
  "from": "GIS",
  "body": {
    "speaker_ids": [101, 102]
  },
  "created": "2026-02-05T10:32:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `speaker_ids` | integer[] | Y | 정지할 스피커 ID 목록 |

---

#### 7.2.4 BROADCAST_TEST (방송 테스트)

**cmd**: `BROADCAST_TEST`  
**Subject**: `sensorway.{부대ID}.broadcast_manager.test`  
**방향**: Central → BroadcastingManager  
**m_type**: PUB  

> **용도**: 스피커 테스트 (`duration_sec` 후 자동 정지)

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "BROADCAST_TEST",
  "from": "Central",
  "body": {
    "speaker_ids": [101],
    "file_group_id": 15,
    "duration_sec": 5
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `speaker_ids` | integer[] | Y | 대상 스피커 ID 목록 |
| `file_group_id` | integer | Y | 재생할 파일 그룹 ID |
| `duration_sec` | integer | N | 자동 정지 시간 (초, 기본: 5) |

> **캐시 조회**: BroadcastingManager는 `speaker_ids`로 캐시에서 Speaker/Server 정보 조회, `file_group_id`로 FileGroup 정보 조회

#### 7.2.5 BROADCAST_STATUS (방송 상태 보고)

**cmd**: `BROADCAST_STATUS`
**Subject**: `sensorway.{부대ID}.gis.broadcast-status`
**방향**: BroadcastingManager → GIS
**m_type**: PUB
**트리거**: 스피커 방송 시작/종료 시

> **용도**: 스피커의 현재 방송 동작 상태(ON/OFF)를 GIS에 알림. PLAY/TTS/TEST 시작 시 ON, STOP 또는 자동 종료 시 OFF 발행.

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "BROADCAST_STATUS",
  "from": "BroadcastingManager",
  "body": {
    "speaker_id": 101,
    "status": "ON"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `speaker_id` | integer | Y | 대상 스피커 ID |
| `status` | string | Y | 방송 동작 상태 (EnumOnOff: `ON` / `OFF`) |

---

### 7.3 Lamp 제어

> **제어 유형 원칙**: GIS(Frontend) → 매니저 단일대상 **제어는 REQ/RSP**(운영자 확인 필요). Central 발행(테스트 포함) 및 다중수신 브로드캐스트는 **PUB**. RSP는 §2 표준 봉투(`success`/`req_id`/`message`)를 사용한다.
>
> **설계 패턴**: ID + 파라미터 (패턴 2)
> - PidsProxy는 시작 시 Lamp 정보를 캐시
> - 메시지에는 `lamp_ids`만 포함, 상세 정보는 캐시에서 조회

#### 7.3.1 LAMP_CLEAR (경광등 이벤트 해제)

**cmd**: `LAMP_CLEAR`
**Subject**: `sensorway.{부대ID}.proxy.lamp-clear`
**방향**: GIS → PidsProxy
**m_type**: REQ

> **참고**: LAMP_CLEAR는 알람/깜빡임 등 이벤트 연동 동작을 해제합니다 (LAMP_OFF와 달리 장비 비활성화가 아닌 이벤트 상태 초기화)
>
> **RSP**: §2 표준 봉투(`success`/`req_id`/`message`) 사용

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "LAMP_CLEAR",
  "from": "GIS",
  "body": {
    "lamp_ids": [501, 502]
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | N | 대상 경광등 ID 목록 (없으면 전체 OFF) |

---

#### 7.3.2 LAMP_OFF (경광등 비활성화)

**cmd**: `LAMP_OFF`
**Subject**: `sensorway.{부대ID}.proxy.lamp-off`
**방향**: GIS/Central → PidsProxy
**m_type**: REQ (GIS), PUB (Central)

> **참고**: LAMP_OFF는 DB의 `status`를 `DEACTIVATED`로 변경합니다 (LAMP_CLEAR와 달리 장비 자체를 비활성화)

**REQ (GIS → PidsProxy):**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "LAMP_OFF",
  "from": "GIS",
  "body": {
    "lamp_ids": [501]
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**PUB (Central → PidsProxy):**
```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "LAMP_OFF",
  "from": "Central",
  "body": {
    "lamp_ids": [501]
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | Y | 대상 경광등 ID 목록 |

---

#### 7.3.3 LAMP_COLOR_SET (색상 직접 설정)

**cmd**: `LAMP_COLOR_SET`
**Subject**: `sensorway.{부대ID}.proxy.lamp-color`
**방향**: GIS → PidsProxy
**m_type**: REQ

> **직접 제어**: LAMP_CLEAR 명령 전까지 색상 유지
>
> **RSP**: §2 표준 봉투(`success`/`req_id`/`message`) 사용

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "LAMP_COLOR_SET",
  "from": "GIS",
  "body": {
    "lamp_ids": [501, 502],
    "color": "Red",
    "mode": "blinking"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | Y | 대상 경광등 ID 목록 |
| `color` | EnumLampColor | Y | Red, Orange, Green, Blue, White |
| `mode` | EnumLightMode | Y | steady, blinking |

---

#### 7.3.4 LAMP_BUZZER_SET (부저 직접 설정)

**cmd**: `LAMP_BUZZER_SET`
**Subject**: `sensorway.{부대ID}.proxy.lamp-buzzer`
**방향**: GIS → PidsProxy
**m_type**: REQ

> **직접 제어**: LAMP_CLEAR 명령 전까지 부저 유지
>
> **RSP**: §2 표준 봉투(`success`/`req_id`/`message`) 사용

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "LAMP_BUZZER_SET",
  "from": "GIS",
  "body": {
    "lamp_ids": [501, 502],
    "buzzer": "PI-PI-PI"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | Y | 대상 경광등 ID 목록 |
| `buzzer` | EnumBuzzerSound | Y | Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue |

---

#### 7.3.5 LAMP_COLOR_TEST (색상 테스트)

**cmd**: `LAMP_COLOR_TEST`  
**Subject**: `sensorway.{부대ID}.proxy.lamp-test-color`  
**방향**: Central → PidsProxy  
**m_type**: PUB  

> **테스트**: 지정 시간(기본 5초) 후 **자동 OFF**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "LAMP_COLOR_TEST",
  "from": "Central",
  "body": {
    "lamp_ids": [501, 502],
    "color": "Red",
    "mode": "steady",
    "duration_sec": 5
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | Y | 대상 경광등 ID 목록 |
| `color` | EnumLampColor | Y | Red, Orange, Green, Blue, White |
| `mode` | EnumLightMode | Y | steady, blinking |
| `duration_sec` | integer | N | 테스트 지속 시간 (초, 기본: 5) |

---

#### 7.3.6 LAMP_BUZZER_TEST (부저 테스트)

**cmd**: `LAMP_BUZZER_TEST`  
**Subject**: `sensorway.{부대ID}.proxy.lamp-test-buzzer`  
**방향**: Central → PidsProxy  
**m_type**: PUB  

> **테스트**: 지정 시간(기본 5초) 후 **자동 OFF**

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "LAMP_BUZZER_TEST",
  "from": "Central",
  "body": {
    "lamp_ids": [501, 502],
    "buzzer": "PI-PI-PI",
    "duration_sec": 5
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `lamp_ids` | array[integer] | Y | 대상 경광등 ID 목록 |
| `buzzer` | EnumBuzzerSound | Y | Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue |
| `duration_sec` | integer | N | 테스트 지속 시간 (초, 기본: 5) |

**PidsProxy 처리:**
```python
def on_lamp_control(msg):
    for lamp_id in msg.body.lamp_ids:
        # 로컬 캐시에서 Lamp 정보 조회
        lamp = cache.get_lamp(lamp_id)
        if not lamp:
            logger.warning(f"Lamp {lamp_id} not found in cache")
            continue

        # Lamp 장비에 명령 전송
        send_command(lamp.ip_address, lamp.ip_port, msg.cmd, msg.body)
```

---

## 8. Camera/NVR 제어 메시지 설계

> **설계 패턴**: ID + 파라미터 (패턴 2)
> - NVRManager는 시작 시 Camera 정보를 캐시
> - 메시지에는 `camera_id`만 포함, 상세 정보는 캐시에서 조회

### 8.1 PTZ 제어

**Subject**: `sensorway.{부대ID}.nvr_manager.ptz`  
**방향**: Central/GIS/VMS → NVRManager
**m_type**: REQ  

#### PTZ 이동 방식

| 방식 | 동작 | 정지 조건 | 해당 cmd |
|------|------|-----------|----------|
| **Continuous** | 명령 시작 → 계속 이동 | `PTZ_STOP` 또는 `timeout_ms` 초과 | PTZ_PAN_*, PTZ_TILT_*, PTZ_ZOOM_*, PTZ_FOCUS_* |
| **Absolute** | 지정 좌표/프리셋으로 이동 | 도착 시 자동 정지 | PTZ_POSITION, PTZ_PRESET_MOVE, PTZ_HOME_MOVE |

> **timeout_ms = 안전장치**
> - Continuous 모드에서 `PTZ_STOP`을 못 받을 경우 자동 정지
> - 이동 시간이 아님! (네트워크 장애 대비용)
> - 기본값: `3000ms` (3초), 생략 가능

#### 지원 cmd 목록 (37종)

| 카테고리 | cmd | 방식 |
|---------|-----|------|
| **팬/틸트** | PTZ_PAN_LEFT, PTZ_PAN_RIGHT, PTZ_TILT_UP, PTZ_TILT_DOWN, PTZ_LEFT_UP, PTZ_LEFT_DOWN, PTZ_RIGHT_UP, PTZ_RIGHT_DOWN | Continuous |
| **줌** | PTZ_ZOOM_IN, PTZ_ZOOM_OUT | Continuous |
| **프리셋** | PTZ_PRESET_MOVE, PTZ_PRESET_SET, PTZ_PRESET_RESET | Absolute |
| **포커스** | PTZ_FOCUS_AUTO, PTZ_FOCUS_NEAR, PTZ_FOCUS_FAR | Continuous |
| **투어** | PTZ_TOUR_START, PTZ_TOUR_STOP | - |
| **홈** | PTZ_HOME_MOVE, PTZ_HOME_SET, PTZ_HOME_RESET | Absolute |
| **위치** | PTZ_CENTER, PTZ_POSITION, PTZ_AIM_LOCATION | Absolute |
| **보조** | PTZ_AUX_ON, PTZ_AUX_OFF, PTZ_LIGHT_ON, PTZ_LIGHT_OFF, PTZ_WIPER_ON, PTZ_WIPER_OFF, PTZ_WASHER_ON, PTZ_WASHER_OFF | - |
| **아이리스** | PTZ_IRIS_IN, PTZ_IRIS_OUT, PTZ_IRIS_AUTO | - |
| **정지** | PTZ_STOP | - |
| **기타** | PTZ_POSITION_RESTORE | Absolute |

#### Continuous 이동 예시 (조이스틱)

> **흐름**: `PTZ_PAN_LEFT` → (사용자 조작 중) → `PTZ_STOP`

**1. 이동 시작**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_PAN_LEFT",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "pan_tilt_speed": 50,
    "timeout_ms": 3000
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**2. 줌 시작**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_ZOOM_IN",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "zoom_speed": 30,
    "timeout_ms": 3000
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**3. 이동 정지 (필수!)**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_STOP",
  "from": "Central",
  "body": {
    "camera_id": 201
  },
  "created": "2026-02-05T10:30:01.500Z"
}
```

> **주의**: `PTZ_STOP`을 보내지 않으면 `timeout_ms` 후 자동 정지됨

#### Absolute 이동 예시 (자동 정지)

> **특징**: 목표 도달 시 자동 정지, `PTZ_STOP` 불필요

**프리셋 이동**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_PRESET_MOVE",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "preset": 3,
    "pan_tilt_speed": 80,
    "zoom_speed": 50
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**절대좌표 이동**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_POSITION",
  "from": "VMS",
  "body": {
    "camera_id": 201,
    "pan": 1000,
    "tilt": 5000,
    "zoom": 2000,
    "pan_tilt_speed": 70,
    "zoom_speed": 50
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**PTZ body 필드 (이동 유형별):**

**공통 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID (전체 PTZ cmd 공통) |

**Continuous 이동** (PTZ_PAN_*, PTZ_TILT_*, PTZ_LEFT_*, PTZ_RIGHT_*, PTZ_ZOOM_*, PTZ_FOCUS_NEAR/FAR):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `pan_tilt_speed` | integer | N | 팬/틸트 속도 (0-100, 기본: 50). ONVIF Velocity.PanTilt에 매핑. cmd에 따라 부호(±) 자동 결정 |
| `zoom_speed` | integer | N | 줌 속도 (0-100, 기본: 50). ONVIF Velocity.Zoom에 매핑. PTZ_ZOOM_IN/OUT 시 사용 |
| `timeout_ms` | integer | N | 안전장치 - PTZ_STOP 미수신 시 자동 정지 (기본: 3000ms) |

**Absolute 이동 — 프리셋/홈** (PTZ_PRESET_MOVE, PTZ_HOME_MOVE):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `preset` | integer | Y* | 프리셋 번호 (*PTZ_PRESET_MOVE만 필수) |
| `pan_tilt_speed` | integer | N | 프리셋/홈까지 이동하는 팬/틸트 속도 (0-100). ONVIF Speed.PanTilt에 매핑 |
| `zoom_speed` | integer | N | 프리셋/홈까지 이동하는 줌 속도 (0-100). ONVIF Speed.Zoom에 매핑 |

> 속도 생략 시 카메라의 DefaultPTZSpeed 사용 (ONVIF PTZConfiguration)
>
> **v4.6 — 감시금지구역 이동 처리**: 대상 프리셋이 `is_restricted_zone=true`(REST CameraPreset 속성; SYNC_PRESET 수신 후 REST 조회로 캐시)이면, `PTZ_PRESET_MOVE` 실행 시 매니저들이 **통일 차단**을 적용한다 — VMS=RTSP 차단, NVR=녹화 중지, db_monitor=이벤트 발행 차단, Central UI=화면 마스킹. `false`이면 정상 감시. (REST 가이드: `docs/v46_camera_preset_restricted_zone_guide.md`)
>
> **NATS 동기화 방식 (v4.6 확정)**: 통일 차단은 VMS/Central 등도 동시 인지해야 하므로, NVRManager가 프리셋 도달 시 `PTZ_STATUS`(§8.3.1)에 `current_preset` + `is_restricted` 필드를 실어 발행한다 — **신규 메시지 없이 기존 브로드캐스트 확장**. 구독자(GIS/VMS/AiAnalysis)는 이 신호로 차단을 적용하고, Central·db_monitor는 DBApi/REST 경로로 받는다.

**Absolute 이동 — 절대좌표** (PTZ_POSITION, PTZ_POSITION_RESTORE):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `pan` | integer | Y | 팬 절대좌표. ONVIF Position.PanTilt.x에 매핑 |
| `tilt` | integer | Y | 틸트 절대좌표. ONVIF Position.PanTilt.y에 매핑 |
| `zoom` | integer | Y | 줌 절대좌표. ONVIF Position.Zoom.x에 매핑 |
| `pan_tilt_speed` | integer | N | 해당 좌표까지 이동하는 팬/틸트 속도 (0-100). ONVIF Speed.PanTilt에 매핑 |
| `zoom_speed` | integer | N | 해당 좌표까지 이동하는 줌 속도 (0-100). ONVIF Speed.Zoom에 매핑 |

**화면 클릭 센터링** (PTZ_CENTER):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `x` | integer | Y | 화면 클릭 X 좌표 (정규화 0-10000) |
| `y` | integer | Y | 화면 클릭 Y 좌표 (정규화 0-10000) |
| `pan_tilt_speed` | integer | N | 센터링 이동 팬/틸트 속도 (0-100). ONVIF Speed.PanTilt에 매핑 |

> **PTZ_CENTER 동작**: 사용자가 영상 화면에서 클릭한 좌표(x, y)로 카메라 중심을 이동. 정규화 좌표 (0-10000) 사용, NVRManager가 ONVIF RelativeMove로 변환하여 처리

**GPS 좌표 조준** (PTZ_AIM_LOCATION) *(v1.4 신규)*:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `latitude` | number | Y | 조준 목표 위도 (지도 클릭 좌표) |
| `longitude` | number | Y | 조준 목표 경도 (지도 클릭 좌표) |
| `camera_latitude` | number | N | 카메라 설치 위도 (참고/검산용) |
| `camera_longitude` | number | N | 카메라 설치 경도 (참고/검산용) |
| `distance_m` | number | N | 카메라→목표 거리(m, 클라 계산값) |
| `bearing_deg` | number | N | 카메라→목표 방위(0-360°, 클라 계산값) |
| `requested_by` | string | N | 요청자 식별 |

> **PTZ_AIM_LOCATION 동작**: GIS 통합상황도에서 카메라 탐지범위 내 지도 지점을 클릭하면 해당 GPS 좌표로 카메라를 조준한다. 클라이언트는 좌표(+거리/방위 참고값)만 전달하고, NVRManager가 카메라 설치 위치/방위 기준으로 ONVIF Absolute/RelativeMove(pan/tilt)로 변환하여 회전한다. `PTZ_CENTER`(화면 픽셀 클릭)의 **GPS 좌표 버전**.
>
> **m_type**: 다른 PTZ_*와 동일하게 **`GIS → NVRManager` REQ**. `from` = `GIS`. RSP는 §2 표준 봉투(`success`/`req_id`/`message`)를 사용한다.

**예시 (PTZ_AIM_LOCATION, REQ)**
```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PTZ_AIM_LOCATION",
  "from": "GIS",
  "body": {
    "camera_id": 201,
    "latitude": 38.1240,
    "longitude": 127.5690,
    "camera_latitude": 38.1234,
    "camera_longitude": 127.5678,
    "distance_m": 73.5,
    "bearing_deg": 64,
    "requested_by": "operator"
  },
  "created": "2026-06-30T10:30:00.000Z"
}
```

**프리셋 설정/삭제** (PTZ_PRESET_SET, PTZ_PRESET_RESET):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `preset` | integer | Y | 프리셋 번호 |

**정지/보조/투어** (PTZ_STOP, PTZ_AUX_*, PTZ_LIGHT_*, PTZ_WIPER_*, PTZ_WASHER_*, PTZ_TOUR_*, PTZ_HOME_SET, PTZ_HOME_RESET, PTZ_IRIS_*, PTZ_FOCUS_AUTO):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID만 필요 (추가 파라미터 없음) |

> **ONVIF 속도 매핑**: GOP `pan_tilt_speed`/`zoom_speed` (0-100 정수) → ONVIF PTZSpeed (0.0-1.0 실수). NVRManager가 `값 / 100.0`으로 변환하여 ONVIF API에 전달

**NVRManager 처리:**
```python
def on_ptz_command(msg):
    # 로컬 캐시에서 Camera 정보 조회
    camera = cache.get_camera(msg.body.camera_id)
    if not camera:
        return error_response("Camera not found")

    # number_device에서 -1 보정 후 Emstone API로 전송
    emstone_camera_num = camera.number_device - 1
    emstone_api.ptz_control(emstone_camera_num, msg.cmd, msg.body)
```

---

### 8.2 AI 탐지 메시지

#### 8.2.1 VMS_DETECT (AI 영상 탐지 전달)

**cmd**: `VMS_DETECT`
**Subject**: `sensorway.{부대ID}.vms.event_ai.detect`
**방향**: AiAnalysis → VMS, GIS
**m_type**: PUB

> **m_type=PUB (v1.5 정정)**: 수신자가 VMS·GIS **둘**이므로 NATS request/reply(1:1 단일 응답자)와 양립 불가 → 브로드캐스트(fan-out) **PUB**로 정정. 응답이 필요 없는 일방향 전달.
>
> **AI 탐지 메시지**: AiAnalysis가 영상 AI 탐지 발생 시, `all.event_ai.detect` 브로드캐스트와 별도로 VMS/GIS에게 카메라 URL 및 이벤트 매핑 정보를 포함하여 직접 전달합니다.

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "VMS_DETECT",
  "from": "AiAnalysis",
  "body": {
    "name_event": "AI 객체 탐지",
    "category_event_mapping": "AI_CAMERA_ONLY",
    "origin_event": {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "False",
      "device": {
        "id": 201,
        "number_device": 109,
        "group_device": 1,
        "name_device": "Camera-A-1",
        "type_device": "IpCamera",
        "version": "v3.2.1",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.100",
        "ip_port": 554,
        "urls": {
          "live": "http://192.168.1.100:1102/webrtc.html?src=cam1&media=video+audio",
          "record": ""
        },
        "mode": "FIXED",
        "category": "IP",
        "is_record": false,
        "geolocation": {
          "location": "GOP 1구역 전방 초소",
          "latitude": 38.1234,
          "longitude": 127.5678,
          "altitude": 245.5,
          "heading": 135.0
        },
        "device_groups": [
          {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[IpCamera] Camera-A-1 (number: 109, id: 201)",
      "result": "AI_DETECT",
      "detail": {
        "signal": 0,
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "frame_width": 1920,
        "frame_height": 1080,
        "objects": [
          {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
        ],
        "model": "yolov8n",
        "inference_ms": 45
      },
      "created_at": "2026-01-14T10:15:23.100Z",
      "updated_at": "2026-01-14T10:15:23.100Z"
    },
    "urls": {
      "live": "http://192.168.1.100:1102/webrtc.html?src=cam1&media=video+audio",
      "record": ""
    }
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 | REST API 대응 |
|------|------|------|------|---------------|
| `name_event` | string | Y | 이벤트 매핑 이름 | EventMapping `name_event` |
| `category_event_mapping` | string | Y | 이벤트 매핑 카테고리 (EnumMappingEventCategory) | EventMapping `category_event_mapping` |
| `origin_event` | object | Y | 원본 Detection Event 전체 DTO | Detection Event Response `data` |
| `urls` | object | Y | 카메라 스트리밍 URL | NVR/Camera URL 정보 |

---

### 8.3 카메라 설정 제어

> **경량화 패턴**: 모든 제어/상태 메시지는 `camera_id` + 파라미터만 전송

#### 8.3.1 PTZ_STATUS (PTZ 상태 보고)

**cmd**: `PTZ_STATUS`  
**Subject**: `sensorway.{부대ID}.gis.ptz-status`  
**방향**: NVRManager → GIS, AiAnalysis, VMS  
**m_type**: PUB  

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "PTZ_STATUS",
  "from": "NVRManager",
  "body": {
    "camera_id": 201,
    "pan": 1000,
    "tilt": 5000,
    "zoom": 2000,
    "current_preset": 3,
    "is_restricted": true
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `pan` | integer | Y | 현재 팬 위치 |
| `tilt` | integer | Y | 현재 틸트 위치 |
| `zoom` | integer | Y | 현재 줌 레벨 |
| `current_preset` | integer | N | **(v4.6)** 현재 위치에 해당하는 프리셋 번호. 프리셋 이동 직후 설정, 수동/연속 이동 중이면 `null` |
| `is_restricted` | boolean | N | **(v4.6)** 현재 프리셋이 감시금지구역(CameraPreset `is_restricted_zone=true`)인지. `true`면 구독자가 통일 차단 적용 |

> **v4.6 — 감시금지구역 런타임 신호**: `PTZ_PRESET_MOVE`로 카메라가 금지구역 프리셋에 도달하면 NVRManager가 `current_preset` + `is_restricted=true`를 실어 PTZ_STATUS를 발행한다(신규 메시지 없이 기존 브로드캐스트 확장). 수신자가 각자 차단 적용 — **GIS**=화면 마스킹, **VMS**=RTSP 차단, **AiAnalysis**=분석/이벤트 억제. **NVR(녹화 중지)**은 NVRManager 자체 처리. **Central·db_monitor**는 NATS 직접 구독 대상이 아니므로 DBApi/REST 경로로 상태를 받는다(REST §5.7 `is_restricted_zone` + 본 신호).

#### 8.3.2 PALETTE_SET (팔레트 설정)

**cmd**: `PALETTE_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.palette`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "PALETTE_SET",
  "from": "VMS",
  "body": {
    "camera_id": 201,
    "palette": "WHITE_HOT"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `palette` | EnumPalette | Y | WHITE_HOT, BLACK_HOT, RAINBOW, IRONBOW |

#### 8.3.3 WIPER_SET (와이퍼/브러시 설정)

**cmd**: `WIPER_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.wiper`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "WIPER_SET",
  "from": "VMS",
  "body": {
    "camera_id": 201,
    "wiper": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `wiper` | EnumOnOff | Y | on, off |

#### 8.3.4 HEATER_SET (열선 설정)

**cmd**: `HEATER_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.heater`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "HEATER_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "heater": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `heater` | EnumOnOff | Y | on, off |

#### 8.3.5 FAN_SET (팬 설정)

**cmd**: `FAN_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.fan`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "FAN_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "fan": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `fan` | EnumOnOff | Y | on, off |

#### 8.3.6 TRACKING_SET (자동 추적 제어)

**cmd**: `TRACKING_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.tracking`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "TRACKING_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "tracking": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `tracking` | EnumOnOff | Y | on, off |

> **`tracking` 표현 정합 (REST ↔ NATS 변환 규칙)**: 동일 개념이 3곳에서 다르게 표현되므로 아래 규칙으로 변환한다.
> REST `CameraSetting.tracking` = `EnumTrackingStatus`(`ACTIVE`/`LOST`/`IDLE`) · NATS `TRACKING_SET.tracking` = `EnumOnOff`(`on`/`off`) · NATS `TRACKING_STATUS.tracking` = 소문자(`active`/`lost`/`idle`).
>
> | 경계 | 변환 | 책임 주체 |
> |------|------|----------|
> | `TRACKING_SET` 수신 → CameraSetting 저장 | `on`→`ACTIVE`, `off`→`IDLE` | NVRManager |
> | 추적 엔진 상태 → `TRACKING_STATUS` 발행 | `ACTIVE`/`LOST`/`IDLE` → 소문자 `active`/`lost`/`idle` | AiAnalysis |
> | `LOST` | `TRACKING_SET`엔 없는 상태 — 추적 중 타겟 상실 시 AiAnalysis가 `lost` 발행 후 `idle`로 전환, CameraSetting엔 `LOST` 저장 | AiAnalysis |

---

#### 8.3.7 TRACKING_STATUS (추적 상태 보고)

**cmd**: `TRACKING_STATUS`  
**Subject**: `sensorway.{부대ID}.gis.tracking-status`  
**방향**: AiAnalysis → GIS  
**m_type**: PUB  
**전송 주기**: 1000ms (추적 중일 때)  

> **용도**: 탐지/추적 중인 타겟(들)의 종류·위협등급·GPS 좌표를 GIS 지도에 실시간 오버레이 오브젝트로 표시
> **참조**: Detection Event `detail.objects[]` 구조 기반

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "TRACKING_STATUS",
  "from": "AiAnalysis",
  "body": {
    "camera_id": 201,
    "tracking": "active",
    "ttl_sec": 5,
    "frame_width": 1280,
    "frame_height": 720,
    "targets": [
      {
        "track_id": "cam201-1738750245-007",
        "label": "person",
        "threat_level": "THREAT",
        "confidence": 0.92,
        "observed_at": "2026-02-05T10:30:00.000Z",
        "location": {
          "latitude": 38.1235,
          "longitude": 127.5680,
          "distance_m": 120.5
        },
        "bbox": [150, 220, 60, 120],
        "thumbnail": "http://192.168.1.50:8080/tracking/frame_001.jpg"
      }
    ]
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `tracking` | string | Y | 추적 상태 (`active`, `lost`, `idle`) |
| `ttl_sec` | integer | N | 소멸 안전장치 — 이 초만큼 갱신 없으면 GIS가 마커 자동 제거 (기본 5). `lost`/`idle` 신호 유실 대비 |
| `frame_width` | integer | N | AI 추론 프레임 기준 가로 해상도 (px). `bbox` 좌표 해석 기준 |
| `frame_height` | integer | N | AI 추론 프레임 기준 세로 해상도 (px). `bbox` 좌표 해석 기준 |
| `targets` | array | Y | 탐지/추적 타겟 배열. `active`면 1개 이상, `lost`/`idle`이면 빈 배열 `[]` 가능 |
| `targets[].track_id` | string | Y | 타겟 고유 식별자 — 프레임 간 동일 객체 추적/마커 갱신 키. 다중 카메라는 `camera_id`+`track_id` 복합키로 식별 |
| `targets[].label` | string | Y | 타겟 분류 (person, car, vehicle, animal 등) |
| `targets[].threat_level` | string (EnumThreatLevel) | Y | 위협 등급 (`NORMAL`, `CAUTION`, `THREAT`) — AiAnalysis 산출 (§4.1) |
| `targets[].confidence` | float | N | 탐지 신뢰도 (0.0–1.0) |
| `targets[].observed_at` | string (ISO 8601) | Y | 객체 단위 관측 시각 (UTC, ms). 순서 역전 시 과거 좌표가 최신을 덮어쓰지 않도록 비교 기준 |
| `targets[].location.latitude` | float | Y | 타겟 추정 GPS 위도 (WGS84) |
| `targets[].location.longitude` | float | Y | 타겟 추정 GPS 경도 (WGS84) |
| `targets[].location.distance_m` | float | N | 카메라로부터 거리 (미터) |
| `targets[].bbox` | array | N | 바운딩 박스 [x, y, w, h] (px, `frame_width`/`frame_height` 기준) |
| `targets[].thumbnail` | string | N | 타겟 캡처 이미지 URL |

**tracking 상태값:**

| 상태 | 설명 |
|------|------|
| `active` | 타겟 추적/탐지 중 (`targets[]`에 1개 이상 포함) |
| `lost` | 타겟 놓침 (마지막 위치 전송 후 idle로 전환, `targets[]` 빈 배열 가능) |
| `idle` | 추적 비활성 (TRACKING_SET off 시, `targets[]` 빈 배열) |

**GIS 오버레이 처리 (생성→갱신→소멸):**
```
수신 시 targets[]의 각 t에 대해:
  key = (camera_id, t.track_id)
  if t.observed_at < 기존_마커[key].observed_at: skip   # 순서 역전 방지
  upsert 마커[key] ← t.location, t.label, t.threat_level
  마커[key].expire_at = now + ttl_sec
소멸:
  tracking == "lost" / "idle"  → 해당 camera_id의 마커 제거(페이드)
  expire_at 경과               → 자동 제거 (lost/idle 메시지 유실 안전장치)
```

**추적 흐름:**
```
1. Central → NVRManager: TRACKING_SET (on)
2. AiAnalysis : AI로 타겟 탐지 및 추적 시작
3. AiAnalysis → GIS: TRACKING_STATUS (1초마다)
   └─ tracking: "active", targets[] (track_id·label·threat_level·location 포함)
4. (타겟 놓침 시)
   AiAnalysis → GIS: TRACKING_STATUS (tracking: "lost")
5. Central → AiAnalysis: TRACKING_SET (off)
6. AiAnalysis → GIS: TRACKING_STATUS (tracking: "idle")
```

> **변경 메모 (전면 교체, 하위호환 없음)**: 단일 `target`/`target_location` → 다중 `targets[]` 배열로 전환.
> 신규 필드 `track_id`(객체 식별), `threat_level`(위협 등급, §4.1 EnumThreatLevel), `observed_at`(관측 시각), `ttl_sec`(소멸 안전장치), `frame_width`/`frame_height`(bbox 해석 기준) 추가.
> `bbox`는 픽셀 좌표 유지(추론 프레임 해상도 기준) — Detection Event `detail.objects[].bbox`와 동일 체계.

**구현 규칙 — 오버레이 수명주기 (semantics):**

| 항목 | 규칙 |
|------|------|
| 좌표 최신성 | `targets[].observed_at`가 **유일 판정 기준**. 수신 `observed_at`가 기존 마커보다 과거면 갱신하지 않음(순서 역전 방지). `created`는 메시지 발행 시각(참고용)이며 최신성 판정에 쓰지 않음 |
| `track_id` 유일성 | AiAnalysis가 **카메라별 namespace**로 생성(예: `{camera_id}-{epoch}-{seq}`). GIS는 항상 `(camera_id, track_id)` **복합키**로 마커를 식별 → 카메라 간 `track_id` 충돌 방지 |
| 마커 만료 | `active` 수신마다 `expire_at = now + ttl_sec` 로 갱신. `expire_at` 경과 시 자동 제거(= `lost`/`idle` 신호 유실 시 폴백) |
| `lost` / `idle` | `targets[]`를 빈 배열 `[]`로 전송. 수신 시 **해당 `camera_id`의 모든 마커 즉시 제거**(`ttl_sec`와 무관) |
| 부분 소멸 | 일부 객체만 사라진 경우 별도 신호 없음 — 다음 `active`의 `targets[]`에서 빠지면 `expire_at` 경과로 자연 소멸 |

> `TRACKING_SET` on/off 연속 발행 시 상태 충돌 처리는 §8.3.6 TRACKING_SET(REQ/RSP) 스펙에서 다룬다.

---

#### 8.3.8 WEATHER_MODE_SET (악천후 모드 설정)

**cmd**: `WEATHER_MODE_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.weather-mode`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  
**DB 저장**: ✅ `PATCH /api/devices/cameras/{id}/settings` → CameraSetting.weather_mode  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "WEATHER_MODE_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "weather_mode": "FOG"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `weather_mode` | EnumWeatherMode | Y | NORMAL, FOG, SEA_FOG, YELLOW_DUST, RAIN, SNOW, HEAT_HAZE |

---

#### 8.3.9 CAMERA_MODE_SET (카메라 영상 모드 설정)

**cmd**: `CAMERA_MODE_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.camera-mode`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  
**DB 저장**: ✅ `PATCH /api/devices/cameras/{id}/settings` → CameraSetting.camera_mode  

> **참고**: 기존 BLC_SET(역광보정)은 이 명령의 `BLC` 모드로 통합

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "CAMERA_MODE_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "camera_mode": "BLC"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `camera_mode` | EnumCameraVideoMode | Y | NORMAL, STABILIZATION, BLC, NIGHT_ENHANCE |

---

#### 8.3.10 HEADLIGHT_SET (전조등 설정)

**cmd**: `HEADLIGHT_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.headlight`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  
**DB 저장**: ✅ `PATCH /api/devices/cameras/{id}/settings` → CameraSetting.headlight  

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "HEADLIGHT_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "headlight": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `headlight` | EnumOnOff | Y | on, off |

---

#### 8.3.11 DAY_NIGHT_SET (주/야간 모드 설정)

**cmd**: `DAY_NIGHT_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.day-night`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  
**DB 저장**: ✅ `PATCH /api/devices/cameras/{id}/settings` → CameraSetting.day_night_mode  

> **참고**: IR 컷필터 전환. AUTO 모드 시 카메라가 자동 판단

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "DAY_NIGHT_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "day_night_mode": "NIGHT"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `day_night_mode` | EnumDayNightMode | Y | AUTO, DAY, NIGHT |

---

#### 8.3.12 POWER_SET (카메라 전원)

**cmd**: `POWER_SET`  
**Subject**: `sensorway.{부대ID}.nvr_manager.power`  
**방향**: VMS/Central → NVRManager  
**m_type**: REQ  

> **참고**: 카메라 자체의 전원을 ON/OFF 제어. PTZ 전원이 아닌 카메라 하드웨어 전원

```json
{
  "id": "uuid-v4",
  "m_type": "REQ",
  "cmd": "POWER_SET",
  "from": "Central",
  "body": {
    "camera_id": 201,
    "power": "on"
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `camera_id` | integer | Y | 카메라 ID |
| `power` | EnumOnOff | Y | on, off |

---

## 9. 마스터 데이터 동기화 메시지 설계

### 9.1 개요

각 Subsystem은 시작 시 마스터 데이터를 REST API를 통해 조회하여 로컬에 캐싱합니다. 이후 데이터 변경이 발생하면 DBApi가 NATS를 통해 **변경 알림만** 브로드캐스트하고, 알림을 받은 Subsystem이 **직접 DBApi REST API를 호출**하여 최신 데이터를 조회합니다.

> **참고**: `all.sync.*` 계열에는 마스터 데이터 외에 **운영 통제 상태**도 포함됩니다 —
> `SYNC_EVENT_SUPPRESSION`(§9.12, 이벤트 억제/정비 창)은 캐시 갱신이 아니라 **수신자의 동작 변경**을
> 요구하는 신호입니다. 구독 패턴(`all.sync.*`)이 동일해 별도 구독 추가 없이 수신됩니다.

> **핵심 원칙**: NATS 메시지는 **알림(Notification)** 만 전달합니다. 실제 데이터는 포함하지 않으며, 필요한 Subsystem이 직접 REST API를 호출하여 데이터를 가져갑니다.

#### 동기화 대상 리소스

| 리소스 | cmd | Subject | 설명 |
|--------|-----|---------|------|
| Device | `SYNC_DEVICE` | `all.sync.device` | 모든 장비 (Controller, Sensor, Camera, Speaker, Enclosure, Lamp) |
| Server | `SYNC_SERVER` | `all.sync.server` | 서버 인스턴스 |
| Category | `SYNC_CATEGORY` | `all.sync.category` | 서버 카테고리 |
| DeviceGroup | `SYNC_DEVICE_GROUP` | `all.sync.device-group` | 장비 그룹 |
| EventMapping | `SYNC_EVENT_MAPPING` | `all.sync.event-mapping` | 이벤트 매핑 규칙 |
| CameraPreset | `SYNC_PRESET` | `all.sync.preset` | 카메라 프리셋 (ROI 포함) |
| FileGroup | `SYNC_FILE_GROUP` | `all.sync.file-group` | 방송 파일 그룹 |
| CameraSetting | `SYNC_CAMERA_SETTING` | `all.sync.camera-setting` | 카메라 설정 (v3.7) |
| ProxySetting | `SYNC_PROXY_SETTING` | `all.sync.proxy-setting` | 프록시 설정 (v3.6) |
| DetectionEvent | `SYNC_DETECTION` | `all.sync.detection` | 탐지 갱신 알림 — UPDATE/DELETE만, INSERT 미발행 (v6.3) |
| EventSuppression | `SYNC_EVENT_SUPPRESSION` | `all.sync.event-suppression` | **이벤트 억제(정비 창)** — 마스터 데이터가 아닌 **파이프라인 통제 상태**. 창 경계 전이 포함 (v6.3) |

#### 동기화 흐름

```
==========================================================================
  Master Data Synchronization Flow
==========================================================================

  Phase 1. Initial Loading (on Subsystem startup)
  ------------------------------------------------

  ┌─────────────┐    GET /api/devices/*     ┌─────────────┐
  │   GIS       │    GET /api/servers       │             │
  │   VMS       │    GET /api/groups        │    DBApi    │
  │   NVRMgr    │ ─────────────────────────>│   (REST)    │
  │   PidsProxy │    GET /api/event-mappings│             │
  │   Broadcast │    GET /api/...           │             │
  │   AiAnalysis│                           └─────────────┘
  └──────┬──────┘
         │
         v
  [ Local Cache Stored ]


  Phase 2. Incremental Sync (on data change)
  ------------------------------------------------

  Step 1: Data Mutation Request
  ┌─────────────┐                            ┌─────────────┐
  │  Central    │  POST/PATCH/DELETE         │             │
  │  (or GIS)   │ ─────────────────────────> │    DBApi    │──┐
  │             │  /api/devices/{id}         │             │  │ DB Update
  └─────────────┘                            └─────────────┘<─┘

  Step 2: Broadcast Change Notification
                                            ┌──────────────┐
                                            │    DBApi     │
                                            │  (Publisher) │
                                            └──────┬───────┘
                                                   │
                                                   v  NATS PUB
                                  ┌────────────────────────────────┐
                                  │          NATS Core             │
                                  │  subject: ...all.sync.device   │
                                  │  body: { action, resource_id } │
                                  │         (NO data payload!)     │
                                  └─────┬──────┬──────┬──────┬─────┘
                                        │      │      │      │
  Step 3: Receive Notification          v      v      v      v
                               ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
                               │ GIS │ │ VMS │ │ NVR │ │ ... │
                               └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘

  Step 4: Fetch Latest via REST   │       │       │       │
                                  v       v       v       v
                               GET /api/devices/{type}/{id}
                                            │
                                            v
                                  ┌──────────────┐
                                  │    DBApi     │
                                  │  (REST API)  │ ── Response data ──>
                                  └──────────────┘

  Step 5: Update Local Cache
                               ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
                               │ GIS │ │ VMS │ │ NVR │ │ ... │
                               │ [OK]│ │ [OK]│ │ [OK]│ │ [OK]│
                               └─────┘ └─────┘ └─────┘ └─────┘

==========================================================================
```

#### Action 타입

| action | 설명 | Subsystem 동작 |
|--------|------|----------------|
| `CREATED` | 신규 리소스 생성 | `GET /api/{resource}/{id}` 호출하여 캐시 추가 |
| `UPDATED` | 기존 리소스 수정 | `GET /api/{resource}/{id}` 호출하여 캐시 갱신 |
| `DELETED` | 리소스 삭제 | `resource_id`로 캐시에서 해당 항목 삭제 |

> **action 은 위 3종 고정**입니다. cmd 별로 **부분집합을 쓰거나 필드를 추가**할 수는 있으나 값을 늘리지 않습니다.

| cmd | action 부분집합 | 추가 body 필드 |
|-----|----------------|---------------|
| `SYNC_DEVICE` | 3종 전부 | `type_device` (조회 URL 구성용) |
| `SYNC_PRESET` | 3종 전부 | `camera_id` |
| `SYNC_CAMERA_SETTING` / `SYNC_PROXY_SETTING` | 3종 전부 | `camera_id` / `server_id` |
| `SYNC_DETECTION` | `UPDATED`·`DELETED` (**CREATED 없음** — INSERT 미발행) | — |
| `SYNC_EVENT_SUPPRESSION` | 3종 전부 | `status` (창의 파생 상태, `DELETED` 시 생략) |

#### 공통 Envelope 구조

> **중요**: `body`에 실제 데이터(`data`)는 포함하지 않습니다. 알림 정보만 전달합니다.
>
> **resource_type 생략**: cmd 이름에 리소스 타입이 이미 포함되어 있으므로 body에서 생략합니다. (예: `SYNC_DEVICE` → device)

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "type_device": "Camera",
    "resource_id": 101
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `CREATED` / `UPDATED` / `DELETED` |
| `type_device` | string | SYNC_DEVICE만 | 장비 유형 (SYNC_DEVICE에서만 사용) |
| `resource_id` | integer | Y | 변경된 리소스 ID |

**Subsystem 처리 로직:**
```python
# 알림 수신 시
def on_sync_message(msg):
    action = msg.body.action
    resource_id = msg.body.resource_id

    if action == "DELETED":
        # 캐시에서 삭제
        cache.delete(resource_id)
    else:
        # CREATED 또는 UPDATED: REST API 호출하여 최신 데이터 조회
        data = http_client.get(f"/api/devices/{resource_id}")
        cache.update(resource_id, data)
```

---

### 9.2 SYNC_DEVICE (장비 동기화)

**cmd**: `SYNC_DEVICE`  
**Subject**: `sensorway.{부대ID}.all.sync.device`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: Device CRUD 발생 시 (POST, PATCH, PUT, DELETE)  

> **대상 장비 타입**: Controller, Sensor, Camera, Speaker, Enclosure, Lamp
>
> **데이터 조회**: 알림 수신 후 `GET /api/devices/{type}/{id}` 호출

#### 9.2.1 Device 생성/수정 알림 (CREATED/UPDATED)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440201",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "type_device": "Camera",
    "resource_id": 201
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

#### 9.2.2 Device 삭제 알림 (DELETED)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440999",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE",
  "from": "DBApi",
  "body": {
    "action": "DELETED",
    "type_device": "Camera",
    "resource_id": 201
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `CREATED` / `UPDATED` / `DELETED` |
| `type_device` | string | Y | `Controller` / `Sensor` / `Camera` / `Speaker` / `Enclosure` / `Lamp` |
| `resource_id` | integer | Y | Device ID |

**Subsystem 처리:**
- `CREATED`/`UPDATED`: `GET /api/devices/{type}/{resource_id}` 호출하여 캐시 갱신
- `DELETED`: 캐시에서 해당 ID 삭제

---

### 9.3 SYNC_SERVER (서버 동기화)

**cmd**: `SYNC_SERVER`  
**Subject**: `sensorway.{부대ID}.all.sync.server`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: Server CRUD 발생 시  

> **데이터 조회**: 알림 수신 후 `GET /api/servers/{id}` 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440301",
  "m_type": "PUB",
  "cmd": "SYNC_SERVER",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

---

### 9.4 SYNC_CATEGORY (카테고리 동기화)

**cmd**: `SYNC_CATEGORY`  
**Subject**: `sensorway.{부대ID}.all.sync.category`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: Category CRUD 발생 시  

> **데이터 조회**: 알림 수신 후 `GET /api/servers/categories/{id}` 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440401",
  "m_type": "PUB",
  "cmd": "SYNC_CATEGORY",
  "from": "DBApi",
  "body": {
    "action": "CREATED",
    "resource_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

---

### 9.5 SYNC_DEVICE_GROUP (장비그룹 동기화)

**cmd**: `SYNC_DEVICE_GROUP`  
**Subject**: `sensorway.{부대ID}.all.sync.device-group`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: DeviceGroup CRUD 발생 시 또는 장비 할당/제거 시  

> **데이터 조회**: 알림 수신 후 `GET /api/devices/groups/{id}` 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440501",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE_GROUP",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

---

### 9.6 SYNC_EVENT_MAPPING (이벤트매핑 동기화)

**cmd**: `SYNC_EVENT_MAPPING`  
**Subject**: `sensorway.{부대ID}.all.sync.event-mapping`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: EventMapping CRUD 발생 시 또는 Camera/Speaker/Lamp 매핑 변경 시  

> **데이터 조회**: 알림 수신 후 `GET /api/integrations/event-mappings/{id}` 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440601",
  "m_type": "PUB",
  "cmd": "SYNC_EVENT_MAPPING",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

---

### 9.7 SYNC_PRESET (프리셋 동기화)

**cmd**: `SYNC_PRESET`  
**Subject**: `sensorway.{부대ID}.all.sync.preset`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: CameraPreset CRUD 발생 시 또는 ROI 변경 시  

> **데이터 조회**: 알림 수신 후 `GET /api/devices/cameras/{camera_id}/presets/{preset_id}` 호출
>
> **v4.6 — 감시금지구역(`is_restricted_zone`)**: CameraPreset에 `is_restricted_zone`(bool, 기본 `false`) 속성이 신설되었다(REST §5.7). SYNC_PRESET은 **알림만** 전달하므로 수신자는 REST 조회로 이 값을 캐시한다. `true`인 프리셋으로 카메라가 이동하면 매니저들이 **통일 차단 처리**를 적용한다 → §8.1 `PTZ_PRESET_MOVE` 참조.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440701",
  "m_type": "PUB",
  "cmd": "SYNC_PRESET",
  "from": "DBApi",
  "body": {
    "action": "CREATED",
    "resource_id": 1,
    "camera_id": 201
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `CREATED` / `UPDATED` / `DELETED` |
| `resource_id` | integer | Y | Preset ID |
| `camera_id` | integer | Y | 소속 Camera ID (REST API 조회용) |

---

### 9.8 SYNC_FILE_GROUP (파일그룹 동기화)

**cmd**: `SYNC_FILE_GROUP`  
**Subject**: `sensorway.{부대ID}.all.sync.file-group`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: FileGroup CRUD 발생 시  

> **데이터 조회**: 알림 수신 후 `GET /api/file-groups/{id}` 호출

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440801",
  "m_type": "PUB",
  "cmd": "SYNC_FILE_GROUP",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

### 9.9 SYNC_CAMERA_SETTING (카메라 설정 동기화)

**cmd**: `SYNC_CAMERA_SETTING`  
**Subject**: `sensorway.{부대ID}.all.sync.camera-setting`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: CameraSetting PATCH/PUT 발생 시  

> **데이터 조회**: 알림 수신 후 `GET /api/devices/cameras/{camera_id}/settings` 호출
>
> **필요 이유**: CameraSetting은 Device(Camera)와 별도 테이블. `SYNC_DEVICE`는 Camera 장비 자체의 변경만 알리므로, 설정 변경은 별도 알림 필요

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440901",
  "m_type": "PUB",
  "cmd": "SYNC_CAMERA_SETTING",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "camera_id": 201
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `UPDATED` (설정은 생성/삭제 없이 UPDATED만 발생) |
| `camera_id` | integer | Y | Camera ID (REST API 조회용) |

**동기화 흐름:**
```
1. NVRManager → DBApi: PATCH /api/devices/cameras/{id}/settings (설정 변경)
2. DBApi → NATS: SYNC_CAMERA_SETTING (알림만!)
3. VMS ← NATS: 알림 수신
4. VMS → DBApi: GET /api/devices/cameras/{id}/settings (최신 설정 조회)
```

---

### 9.10 SYNC_PROXY_SETTING (프록시 설정 동기화)

**cmd**: `SYNC_PROXY_SETTING`  
**Subject**: `sensorway.{부대ID}.all.sync.proxy-setting`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: ProxySetting PATCH/PUT 발생 시  

> **데이터 조회**: 알림 수신 후 `GET /api/servers/{server_id}/proxy-settings` 호출
>
> **필요 이유**: ProxySetting은 Server와 별도 테이블. `SYNC_SERVER`는 Server 자체의 변경만 알리므로, 프록시 설정 변경은 별도 알림 필요

```json
{
  "id": "550e8400-e29b-41d4-a716-446655441001",
  "m_type": "PUB",
  "cmd": "SYNC_PROXY_SETTING",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "server_id": 1
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `UPDATED` (설정은 생성/삭제 없이 UPDATED만 발생) |
| `server_id` | integer | Y | Server ID (REST API 조회용) |

---

### 9.11 SYNC_DETECTION (탐지 이벤트 갱신 알림)

**cmd**: `SYNC_DETECTION`  
**Subject**: `sensorway.{부대ID}.all.sync.detection`  
**방향**: DBApi → All  
**m_type**: PUB  
**트리거**: DetectionEvent **UPDATE / DELETE** 발생 시 (**INSERT 미발행** — 최초 탐지는 필드 `DETECT`(PidsProxy/AiAnalysis)가 이미 발행하므로 중복 방지)  

> **데이터 조회**: 알림 수신 후 `GET /api/events/detections/{id}` 호출. 재조회 시 현재 `detail` = **PTZ 회전 후 갱신된 썸네일**(+`frame_width`/`frame_height`).
>
> **필요 이유(1차 동인)**: PTZ 카메라는 탐지 후 타겟으로 회전한 뒤 유효 썸네일을 촬영한다. 최초 `DETECT` 시점 썸네일은 회전 전이라, 회전 후 갱신분을 소비자(GIS)가 다시 받아야 정확한 상황도 오버레이가 완성된다. `action_reported`(조치 상태) 변경 통지도 겸한다.
>
> **필드 DETECT와 분리**: subject(`all.sync.*` ≠ `all.event.detect`) · from(`DBApi` ≠ PidsProxy/AiAnalysis) 양쪽으로 구분되어 원본 DETECT와 중복/오인이 없다. 알림형(패턴3)이라 body에 Full-DTO 를 싣지 않는다.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655441002",
  "m_type": "PUB",
  "cmd": "SYNC_DETECTION",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 1001
  },
  "created": "2026-02-05T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `UPDATED`(상태/detail 변경) \| `DELETED`(삭제). INSERT 미발행이라 `CREATED` 없음 |
| `resource_id` | integer | Y | DetectionEvent ID (REST API 조회용) |

---

### 9.12 SYNC_EVENT_SUPPRESSION (이벤트 억제 / 정비 창 알림)

**cmd**: `SYNC_EVENT_SUPPRESSION`
**Subject**: `sensorway.{부대ID}.all.sync.event-suppression`
**방향**: DBApi → All
**m_type**: PUB
**트리거**: 억제 스케줄 **생성 / 변경(대상 배열 교체 포함) / 취소 / 하드삭제** + **시간창 자연 전이**(창 시작 `pending→active`, 창 종료 `active→expired`)

> **★ 성격이 다른 SYNC — 마스터 데이터가 아니라 "이벤트 파이프라인 통제 상태"다.**
> 다른 SYNC_* 는 수신자가 **캐시를 갱신**하는 용도지만, 이 메시지는 수신자가 **자신의 동작을 바꾸는**
> 신호다. 정비/공사/AS 로 특정 장비·그룹·전체의 이벤트를 일시 차단하는 창이 열리거나 닫히면,
> 각 서브시스템은 이를 **"지금 공사 중"** 으로 해석해 발행/녹화/알람을 조정해야 한다.
> 누가 정비 창을 만들거나 취소하면 **다른 서브시스템도 즉시 인지**하는 것이 이 메시지의 목적이다.
>
> **데이터 조회**: 알림 수신 후 `GET /api/event-suppression-schedules/{id}`(해당 창 상세) 및
> `GET /api/event-suppression-schedules/active`(현재 공사 상태 재계산). 판정 규칙은
> `docs/subsystems/event-suppression/INTEGRATION.md` **§2.5** 참조(event_scope ∧ 대상매치 ∧ side매치).
>
> **범위 경계**: DBApi 의 억제는 **저장(persistence) + DB 파생 다운스트림**을 막는다. PidsProxy/
> AiAnalysis 가 직접 쏘는 **실시간 방송은 막지 않는다** — 각 서브시스템이 본 알림과 `/active` 로
> 스스로 억제하는 것이 Phase 2 다.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655441004",
  "m_type": "PUB",
  "cmd": "SYNC_EVENT_SUPPRESSION",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "resource_id": 12,
    "status": "active"
  },
  "created": "2026-08-03T10:30:00.000Z"
}
```

**body 필드 정의:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action` | string | Y | `CREATED` \| `UPDATED` \| `DELETED` (§9.1 고정 3종) |
| `resource_id` | integer | Y | EventSuppressionSchedule ID (REST API 조회용) |
| `status` | string | N | `pending` \| `active` \| `expired` \| `cancelled` — 창의 파생 상태. `DELETED` 시 생략 |

**action 매핑** (HTTP 메서드와 다르므로 주의):

| 발생 사건 | action | status |
|---|---|---|
| 신규 정비 창 생성 | `CREATED` | 생성 시점 파생값 |
| 창 시간·이름·스코프 변경 / **대상 배열 교체** | `UPDATED` | 변경 후 파생값 |
| **취소** `DELETE /{id}` (soft-cancel — 물리삭제 아님) | **`UPDATED`** | **`cancelled`** |
| **창 시작** (시간 도달) | `UPDATED` | `active` |
| **창 종료** (시간 도달) | `UPDATED` | `expired` |
| **하드삭제** `POST /bulk-delete` | `DELETED` | (생략) |

- `DELETE /{id}` 는 `revoked_at` 을 세팅하는 **soft-cancel** 이라 DB 상 UPDATE 다. 진짜 하드삭제는
  `bulk-delete` 뿐이며 그 대상은 terminal(cancelled/expired)로 제한되므로 **정의상 이미 억제 중이 아니다**
  → `DELETED` 는 캐시 eviction 전용이고 억제 상태 변화가 아니다.
- 소비자 처리는 **"어떤 action 이든 `GET /active` 재조회로 억제 목록 갱신"** 한 줄로 단순화하면
  매핑 오해가 원천 제거된다.

**★ fail-safe 규범 (MUST) — 억제 해제는 신호에 의존하지 않는다**

NATS Core 는 at-most-once 이므로 **유실은 예외가 아니라 정상 경로**다. 안전 비대칭이 극단적이다:

| 유실 대상 | 결과 | 판정 |
|---|---|---|
| 창 시작(`status=active`) 신호 | 억제가 늦게 걸림(정비 중 알람이 시끄러움) | **허용** |
| 창 종료(`status=expired`) 신호 | **억제가 영원히 안 풀림 = 서브시스템 영구 침묵** | **금지** |

1. 소비자는 **`expired` 신호로 억제를 해제해서는 안 되며**, 캐시한 `window_end` **로컬 타이머
   만료로 스스로 푼다** — 이것이 **1차 권위**.
2. `GET /active` **30~60초 재조정 폴링은 권위**이며 본 메시지는 **가속 신호(비권위)** 다.
   SYNC 도입 후에도 **폴링 제거 금지**.
3. 소비자 캐시에 **TTL(폴링 주기 ×3)** 을 두어 신호·폴링 두절 시 자동으로 "억제 없음"으로 수렴
   (fail-open). 서버 게이트도 fail-open 이라 전 구간이 일관된다.

**통지 지연 상한(계약)**: 정상 경로(창 경계 date-job) **≤5초**, 잡 유실·서버 재기동 시
백스톱(sweep) **≤5분**. 단 이 상한은 **통지**에만 적용되며, 억제 판정 자체는 요청시점 계산이
권위라 **지연 0** 이다.

---

## 10. 에러 처리

### 10.1 RSP 에러 응답 구조

REQ/RSP 패턴에서의 에러 응답:

```json
{
  "id": "uuid-v4",
  "m_type": "RSP",
  "cmd": "PTZ_PAN_LEFT",
  "from": "NVRManager",
  "body": null,
  "success": false,
  "message": "Camera not found with id=999",
  "req_id": "original-request-uuid",
  "created": "2026-02-05T10:30:00.100Z"
}
```

### 10.2 에러 코드 참조

| message 패턴 | 설명 |
|-------------|------|
| `Unknown command: {cmd}` | 등록되지 않은 명령어 |
| `Handler error: {detail}` | 핸들러 실행 중 예외 |
| `Camera not found with id={id}` | 카메라 장비 없음 |
| `Lamp not found with id={id}` | 경광등 장비 없음 |
| `NVR connection failed` | NVR 서버 연결 실패 |
| `Timeout waiting for response` | 응답 대기 시간 초과 |

### 10.3 PUB 메시지 에러 처리

PUB 메시지는 응답이 없으므로 수신측에서 로컬 로깅으로 에러를 처리합니다:

- JSON 파싱 실패 → 로그 기록 후 무시
- 필수 필드 누락 → 로그 기록 후 무시
- 구독하지 않은 Subject → 자동 필터링 (무시)
- 핸들러 예외 → 로그 기록, 다음 메시지 처리 계속

---

## 11. 부록

### 11.1 전체 메시지 목록

| # | Domain | cmd | Subject | m_type | 발신자 | 수신자 |
|---|--------|-----|---------|--------|--------|--------|
| 1 | all | DETECT | `...all.event.detect`, `...all.event_ai.detect` | PUB | PidsProxy/AiAnalysis | All |
| 2 | all | MALFUNCTION | `...all.event.malfunction` | PUB | PidsProxy | All |
| 3 | all | CONNECTION | `...all.event.connection` | PUB | PidsProxy | All |
| 4 | all | ACTION_REPORT | `...all.event.action-report` | PUB | GIS | All |
| 5 | proxy | MODE_CHANGE | `...proxy.mode-change` | PUB | Central | PidsProxy |
| 6 | proxy | WINDY | `...proxy.windy` | REQ/PUB | GIS/Central | PidsProxy |
| 7 | broadcast_manager | TTS | `...broadcast_manager.tts` | PUB | Central | BroadcastingManager |
| 8 | broadcast_manager | BROADCAST_PLAY | `...broadcast_manager.play` | REQ | GIS | BroadcastingManager |
| 9 | broadcast_manager | BROADCAST_STOP | `...broadcast_manager.stop` | REQ | GIS | BroadcastingManager |
| 10 | broadcast_manager | BROADCAST_TEST | `...broadcast_manager.test` | PUB | Central | BroadcastingManager |
| 11 | gis | BROADCAST_STATUS | `...gis.broadcast-status` | PUB | BroadcastingManager | GIS |
| 12 | proxy | LAMP_CLEAR | `...proxy.lamp-clear` | REQ | GIS | PidsProxy |
| 13 | proxy | LAMP_OFF | `...proxy.lamp-off` | REQ/PUB | GIS/Central | PidsProxy |
| 14 | proxy | LAMP_COLOR_SET | `...proxy.lamp-color` | REQ | GIS | PidsProxy |
| 15 | proxy | LAMP_BUZZER_SET | `...proxy.lamp-buzzer` | REQ | GIS | PidsProxy |
| 16 | proxy | LAMP_COLOR_TEST | `...proxy.lamp-test-color` | PUB | Central | PidsProxy |
| 17 | proxy | LAMP_BUZZER_TEST | `...proxy.lamp-test-buzzer` | PUB | Central | PidsProxy |
| 18 | nvr_manager | PTZ_* (37종) | `...nvr_manager.ptz` | REQ¹ | Central/GIS/VMS | NVRManager |
| 19 | vms | VMS_DETECT | `...vms.event_ai.detect` | PUB | AiAnalysis | VMS, GIS |
| 20 | gis | PTZ_STATUS | `...gis.ptz-status` | PUB | NVRManager | GIS, AiAnalysis, VMS |
| 21 | nvr_manager | PALETTE_SET | `...nvr_manager.palette` | REQ | VMS/Central | NVRManager |
| 22 | nvr_manager | WIPER_SET | `...nvr_manager.wiper` | REQ | VMS/Central | NVRManager |
| 23 | nvr_manager | HEATER_SET | `...nvr_manager.heater` | REQ | VMS/Central | NVRManager |
| 24 | nvr_manager | FAN_SET | `...nvr_manager.fan` | REQ | VMS/Central | NVRManager |
| 25 | nvr_manager | TRACKING_SET | `...nvr_manager.tracking` | REQ | VMS/Central | NVRManager |
| 26 | gis | TRACKING_STATUS | `...gis.tracking-status` | PUB | AiAnalysis | GIS |
| 27 | nvr_manager | WEATHER_MODE_SET | `...nvr_manager.weather-mode` | REQ | VMS/Central | NVRManager |
| 28 | nvr_manager | CAMERA_MODE_SET | `...nvr_manager.camera-mode` | REQ | VMS/Central | NVRManager |
| 29 | nvr_manager | HEADLIGHT_SET | `...nvr_manager.headlight` | REQ | VMS/Central | NVRManager |
| 30 | nvr_manager | DAY_NIGHT_SET | `...nvr_manager.day-night` | REQ | VMS/Central | NVRManager |
| 31 | nvr_manager | POWER_SET | `...nvr_manager.power` | REQ | VMS/Central | NVRManager |
| 32 | all | SYNC_DEVICE | `...all.sync.device` | PUB | DBApi | All |
| 33 | all | SYNC_SERVER | `...all.sync.server` | PUB | DBApi | All |
| 34 | all | SYNC_CATEGORY | `...all.sync.category` | PUB | DBApi | All |
| 35 | all | SYNC_DEVICE_GROUP | `...all.sync.device-group` | PUB | DBApi | All |
| 36 | all | SYNC_EVENT_MAPPING | `...all.sync.event-mapping` | PUB | DBApi | All |
| 37 | all | SYNC_PRESET | `...all.sync.preset` | PUB | DBApi | All |
| 38 | all | SYNC_FILE_GROUP | `...all.sync.file-group` | PUB | DBApi | All |
| 39 | all | SYNC_CAMERA_SETTING | `...all.sync.camera-setting` | PUB | DBApi | All |
| 40 | all | SYNC_PROXY_SETTING | `...all.sync.proxy-setting` | PUB | DBApi | All |
| 41 | all | SYNC_DETECTION | `...all.sync.detection` | PUB | DBApi | All |
| 42 | all | SYNC_EVENT_SUPPRESSION | `...all.sync.event-suppression` | PUB | DBApi | All |
| 43 | all | SYSTEM_EVENT | `...all.event.system` | PUB | DBApi | All |
| 44 | gis | ENCLOSURE_METRICS | `...gis.enclosure-metrics` | PUB | DBApi | GIS |

**총: 44종 (PTZ 37종 세부 cmd 포함 시 80종)**

> **번호 정정 (v1.6)**: 종전 표는 `41` 이 `SYNC_DETECTION`·`SYSTEM_EVENT` 에 **중복 부여**되어 총계
> 표기(42종)와 실제 행 수가 어긋나 있었다. 본 개정에서 재번호했다.
> **메시지는 번호가 아니라 `cmd` 이름으로 참조할 것** — 번호는 문서 편의값이라 개정 시 바뀔 수 있다.

> **¹ PTZ_AIM_LOCATION** *(v1.4)*: 37번째 PTZ_* 명령. 동일 `nvr_manager.ptz` Subject이며 나머지 PTZ_*와 동일하게 `GIS → NVRManager` **REQ**. GIS '특정 위치 확인'의 GPS 좌표 조준. (→ §8.1)

---

### 11.2 메시지 Body 패턴 요약

> **세 가지 Body 패턴**:
>
> | 패턴 | 적용 대상 | body 내용 | 이유 |
> |------|-----------|-----------|------|
> | **Full DTO** | Event, AI 탐지 | REST API Response `data` 전체 | 실시간 표시, 히스토리 저장 필요 |
> | **ID + 파라미터** | 제어/설정 메시지 (Broadcasting, Lamp, Camera) | `{device}_id` + 제어값만 | 대역폭 절감, 캐시 활용 |
> | **알림만** | 상태 변경, 데이터 동기화 | `device_id`, `action`, `status` | 변경 알림 후 필요 시 조회 |

#### Event 메시지

| NATS cmd | REST API Endpoint | body 재사용 범위 |
|----------|-------------------|-----------------|
| DETECT | `GET /api/events/detections/{id}` Response `data` | DetectionEvent 전체 DTO (`id`, `type_event`, `action_reported`, `device`, `device_description`, `result`, `detail`, `created_at`, `updated_at`) |
| MALFUNCTION | `GET /api/events/malfunctions/{id}` Response `data` | MalfunctionEvent 전체 DTO (`id`, `type_event`, `action_reported`, `device`, `device_description`, `reason`, `detail`, `created_at`, `updated_at`) |
| CONNECTION | `GET /api/events/connections/{id}` Response `data` | ConnectionEvent 전체 DTO (`id`, `type_event`, `device`, `device_description`, `created_at`, `updated_at`) |
| ACTION_REPORT | `GET /api/events/actions/{id}` Response `data` | ActionEvent 전체 DTO (`id`, `type_event`, `content`, `user`, `from_event`, `device`, `device_description`, `created_at`, `updated_at`) |
| SYSTEM_EVENT | `GET /api/servers/{id}/system-events` Response `data.items[]` | SystemEvent 요소 (`id`, `server_id`, `type_event`, `severity`, `source`, `message`, `acknowledged`, `server_description`, `created_at`) |
| ENCLOSURE_METRICS | `GET /api/enclosure-metrics` Response `data.items[]` | EnclosureMetric 요소 (`enclosure_id`, `temperature`, `humidity`, `voltage`, `current`, `measured_at`) — 주기 텔레메트리 |

#### 동기화/상태 변경 메시지

> **SYNC 통합**: 장비 상태 변경(DEVICE_STATUS_CHANGE)과 서버 상태 변경(SERVER_STATUS_CHANGE)은 `SYNC_DEVICE`, `SYNC_SERVER`로 통합되었습니다. 모든 동기화 메시지는 **알림(Notification)만** 전달하며, 수신 후 REST API를 통해 최신 데이터를 조회합니다. (→ Section 9 참조)

#### AI 탐지 메시지

| NATS cmd | REST API Endpoint | body 재사용 범위 |
|----------|-------------------|-----------------|
| VMS_DETECT | Detection Event Response `data` + EventMapping + Camera URLs | `origin_event` (Detection DTO), `name_event`, `category_event_mapping`, `urls` |

#### Broadcasting 제어 메시지

> **경량화 패턴**: `speaker_ids` + 제어 파라미터만 전송 (Speaker 정보는 캐시 조회)

| NATS cmd | body 내용 | 비고 |
|----------|-----------|------|
| TTS | `speaker_ids[]`, `message` | 텍스트 음성 변환 |
| BROADCAST_PLAY | `speaker_ids[]`, `file_group_id`, `repeat` | 음원 재생 (STOP 전까지 유지) |
| BROADCAST_STOP | `speaker_ids[]` | 방송 정지 (TTS/PLAY/TEST 모두) |
| BROADCAST_TEST | `speaker_ids[]`, `file_group_id`, `duration_sec` | 테스트 (자동 정지) |
| BROADCAST_STATUS | `speaker_id`, `status` (EnumOnOff) | 방송 동작 상태 보고 (ON/OFF) |

#### Lamp 제어 메시지

> **경량화 패턴**: `lamp_ids` + 제어 파라미터만 전송 (Lamp 정보는 캐시 조회)

| NATS cmd | body 내용 | 비고 |
|----------|-----------|------|
| LAMP_CLEAR | `lamp_ids[]` (생략 시 전체) | 이벤트 해제 (알람/깜빡임 초기화) |
| LAMP_OFF | `lamp_ids[]` | 경광등 비활성화 (GIS: REQ, Central: PUB) |
| LAMP_COLOR_SET | `lamp_ids[]`, `color` (EnumLampColor), `mode` (EnumLightMode) | 직접 설정 (LAMP_CLEAR 전까지 유지) |
| LAMP_BUZZER_SET | `lamp_ids[]`, `buzzer` (EnumBuzzerSound) | 직접 설정 (LAMP_CLEAR 전까지 유지) |
| LAMP_COLOR_TEST | `lamp_ids[]`, `color` (EnumLampColor), `mode` (EnumLightMode), `duration_sec` | 테스트 (자동 OFF) |
| LAMP_BUZZER_TEST | `lamp_ids[]`, `buzzer` (EnumBuzzerSound), `duration_sec` | 테스트 (자동 OFF) |

#### PTZ/Camera 제어 메시지

> **경량화 패턴**: `camera_id` + 제어 파라미터만 전송 (Camera 정보는 캐시 조회)

| NATS cmd | body 내용 | 비고 |
|----------|-----------|------|
| PTZ_* Continuous | `camera_id`, `pan_tilt_speed`, `zoom_speed`, `timeout_ms` | PAN/TILT/ZOOM/FOCUS 이동 |
| PTZ_* Preset/Home | `camera_id`, `preset`, `pan_tilt_speed`, `zoom_speed` | PRESET_MOVE, HOME_MOVE |
| PTZ_* 절대좌표 | `camera_id`, `pan`, `tilt`, `zoom`, `pan_tilt_speed`, `zoom_speed` | POSITION, POSITION_RESTORE |
| PTZ_AIM_LOCATION | `camera_id`, `latitude`, `longitude`, `camera_latitude`, `camera_longitude`, `distance_m`, `bearing_deg`, `requested_by` | GPS 좌표 조준(지도 클릭). GIS→NVR **REQ**(타 PTZ_*와 동일). *(v1.4)* |
| PTZ_* 기타 | `camera_id` | STOP, PRESET_SET/RESET, AUX, MENU 등 |
| PTZ_STATUS | `camera_id`, `pan`, `tilt`, `zoom`, `current_preset`, `is_restricted` | PTZ 위치 보고 + v4.6 감시금지구역 신호 |
| PALETTE_SET | `camera_id`, `palette` (EnumPalette) | 열화상 팔레트 ✅ DB |
| WIPER_SET | `camera_id`, `wiper` (EnumOnOff) | 와이퍼/브러시 (조작) |
| HEATER_SET | `camera_id`, `heater` (EnumOnOff) | 열선 ✅ DB |
| FAN_SET | `camera_id`, `fan` (EnumOnOff) | 팬 ✅ DB |
| TRACKING_SET | `camera_id`, `tracking` (EnumOnOff) | 자동 추적 ON/OFF |
| TRACKING_STATUS | `camera_id`, `tracking`, `ttl_sec`, `frame_width/height`, `targets[]` (`track_id`, `label`, `threat_level`, `observed_at`, `location`, `bbox`) | 추적/탐지 타겟 오버레이 보고 (1초, 다중) |
| WEATHER_MODE_SET | `camera_id`, `weather_mode` (EnumWeatherMode) | 악천후 모드 ✅ DB |
| CAMERA_MODE_SET | `camera_id`, `camera_mode` (EnumCameraVideoMode) | 카메라 영상 모드 ✅ DB |
| HEADLIGHT_SET | `camera_id`, `headlight` (EnumOnOff) | 전조등 ✅ DB |
| DAY_NIGHT_SET | `camera_id`, `day_night_mode` (EnumDayNightMode) | 주/야간 모드 ✅ DB |
| POWER_SET | `camera_id`, `power` (EnumOnOff) | 카메라 전원 ON/OFF |

> **✅ DB**: NVRManager가 카메라 제어 성공 후 `PATCH /api/devices/cameras/{id}/settings`로 CameraSetting에 저장

#### 마스터 데이터 동기화 메시지

> **중요**: 동기화 메시지는 **알림(Notification)만** 전달합니다. 실제 데이터는 포함하지 않습니다!

| NATS cmd | NATS body 내용 | 알림 수신 후 조회 API |
|----------|----------------|---------------------|
| SYNC_DEVICE | `action`, `type_device`, `resource_id` | `GET /api/devices/{type}/{id}` |
| SYNC_SERVER | `action`, `resource_id` | `GET /api/servers/{id}` |
| SYNC_CATEGORY | `action`, `resource_id` | `GET /api/servers/categories/{id}` |
| SYNC_DEVICE_GROUP | `action`, `resource_id` | `GET /api/devices/groups/{id}` |
| SYNC_EVENT_MAPPING | `action`, `resource_id` | `GET /api/integrations/event-mappings/{id}` |
| SYNC_PRESET | `action`, `resource_id`, `camera_id` | `GET /api/devices/cameras/{camera_id}/presets/{id}` |
| SYNC_FILE_GROUP | `action`, `resource_id` | `GET /api/file-groups/{id}` |
| SYNC_CAMERA_SETTING | `action`, `camera_id` | `GET /api/devices/cameras/{camera_id}/settings` |
| SYNC_PROXY_SETTING | `action`, `server_id` | `GET /api/servers/{server_id}/proxy-settings` |
| SYNC_DETECTION | `action`, `resource_id` | `GET /api/events/detections/{id}` (UPDATE/DELETE만, INSERT 미발행) |
| SYNC_EVENT_SUPPRESSION | `action`, `resource_id`, `status` | `GET /api/event-suppression-schedules/{id}` + `/active`(공사 상태 재계산) |

> **동기화 흐름**:
> 1. SubSystem → DBApi: PATCH/PUT/POST/DELETE 요청
> 2. DBApi → NATS: 변경 알림 브로드캐스트 (데이터 없음!)
> 3. 다른 SubSystems ← NATS: 알림 수신
> 4. SubSystems → DBApi: 필요 시 REST API 호출하여 최신 데이터 조회
> 5. SubSystems: 로컬 캐시 업데이트

> **보안 참고**: 모든 Device DTO에서 `user_password` 필드는 REST API Response에서도 제외됩니다.
>
> **경량화 원칙**: 제어 메시지는 `{device}_id` + 파라미터만 전송합니다. 수신자는 시작 시 캐시한 마스터 데이터를 조회합니다.
>
> **Event 메시지 Nested 객체**: Event body의 nested `device` 객체에서는 `created_at`, `updated_at` 필드를 제외합니다. 단, Action Report의 `from_event`는 원본 이벤트 전체를 포함하므로 예외입니다.

---

### 11.3 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-02-05 | 초기 작성 |
| v1.2 | 2026-02-19 | Event/Device 제어/동기화 메시지 설계 완료 |
| v1.3 | 2026-03-05 | `BROADCAST_STATUS` 메시지 추가 (40종), Event nested device 구조 수정 (`description` 제거, `is_enable` 추가), ActionEvent root `device`/`device_description` 제거, VMS_DETECT Camera 전용 필드 추가 |
| v1.4 | 2026-06-30 | **`PTZ_AIM_LOCATION` 추가** — GIS 통합상황도 '특정 위치 확인'(지도 GPS 좌표로 카메라 조준). `PTZ_*` Absolute 패밀리 37번째, Subject=`nvr_manager.ptz`, `from`=`GIS`. **m_type=PUB**(타 PTZ_*=REQ 대비 예외, fire-and-forget) — `PTZ_CENTER`(화면 픽셀)의 GPS 좌표 버전. body=`camera_id`+목표/카메라 GPS+`distance_m`+`bearing_deg`+`requested_by`. 반영: §3.2(노트), §5.1(카탈로그 36→37, 각주¹), §8.1(cmd목록 37종/위치 카테고리/body표/예시), §11.1(목록 36→37, 총 78), §11.2(body 패턴 행). 클라(GIS) 코드 정렬: `EnumGopCommand.PTZ_AIM_LOCATION`, `CameraAimControlService`가 `nvr_manager.ptz`로 PUB. |
| v1.5 | 2026-07-13 | **REST v4.6 동기화 + 신규/확장**: TRACKING_STATUS 다중 `targets[]`(track_id/threat_level/observed_at/ttl_sec/frame_width·height) + `EnumThreatLevel` 신설, `SYSTEM_EVENT`·`ENCLOSURE_METRICS` 신규(from=DBApi, 40→42종), geolocation `heading` 추가, Detection `detail.frame_width/height`(AiAnalysis 출처), `AI_DETECT=12`, tracking enum 변환규칙, 감시금지구역(PTZ_STATUS `current_preset`/`is_restricted` + 수신자 VMS), `action_reported` 자동관리, REST 참조 v3.7→v4.6. **정합성 정정**: `VMS_DETECT` REQ→PUB(다중수신자 VMS/GIS), `lamp-*` wildcard 예시 정정, 흐름도[5]·PTZ_STATUS 수신자(GIS/AiAnalysis/VMS)·§9.2 번호·MALFUNCTION/CONNECTION 방향 정정. |
| v1.5.1 | 2026-07-13 | **재검토 정정(모순 해소)**: §6.1 노트 VMS_DETECT 'REQ'→'PUB' 잔재 정정, §1.3 흐름도[1] 센서 DETECT 수신자에서 VMS 제거(§3.4·§6.1 정합), §6.4 ACTION_REPORT 방향을 실 구독자(→All: NVRManager/BroadcastingManager/PidsProxy/VMS)로 통일, PALETTE_SET/WIPER_SET 방향 VMS/Central 통일, §8.3.1 `§5.7`→`REST §5.7`, WINDY GIS→PidsProxy REQ 변형을 §3.2·§11.1에 반영(§5.1·§7.1.2와 일치), CONNECTION은 현재 소비자 부재를 명시하고 발행 유지. **미진(후속 PRD 트랙)**: 전달보장(NATS Core at-most-once/재연결) 절, REQ/RSP reply subject·timeout·error code, §3.1 subject 3유형, §5.1 # 전역 재번호는 `PRD-NATS-개선사항-적용.md`에서 반영. |
| **v1.6** | **2026-08-03** | **`SYNC_EVENT_SUPPRESSION` 신설(§9.12) — 이벤트 억제(정비 창) 동기화.** 마스터 데이터가 아니라 **이벤트 파이프라인 통제 상태**로, 수신자는 캐시 갱신이 아니라 **자신의 발행/녹화/알람 동작을 조정**하고 "현재 공사 중"을 판정한다. Subject `all.sync.event-suppression`(케밥 단수형 규칙 — `/api/event-suppression-schedules`), from=DBApi, PUB, 패턴3(알림만). body `{action, resource_id, status}` — `status` ∈ pending/active/expired/cancelled. **action 은 §9.1 고정 3종 유지**(ACTIVATED/EXPIRED 신설 안 함 — 전이는 `UPDATED`+`status` 로 표현해 기존 소비자 파서 무변경). **soft-cancel(`DELETE /{id}`)은 `DELETED` 가 아니라 `UPDATED`/`status=cancelled`**, 하드삭제(`bulk-delete`)만 `DELETED`. **창 경계 자연 전이**(창 시작/종료) 통지 포함 — 지연 정상 ≤5초(date-job)/백스톱 ≤5분(sweep). **fail-safe 규범 명문화**: 억제 해제는 로컬 `window_end` 타이머가 1차 권위, `/active` 30~60초 폴링 존치(권위), SYNC 는 가속 신호(비권위) — 종료 신호 유실 시 영구 침묵 방지. **구독 개정 불필요**(전 서브시스템이 이미 `all.sync.*` 구독).<br><br>**동반 갱신**: §3.1 subject **3유형 정정**(동기화 5토큰 `sync.{resource}` 명문화 — v1.5.1 미진 항목 해소) + 케밥 단수형 명명 규칙, §3.2 Sync 표 행 추가, §9.1 개요 노트·리소스표 행·**Action 표에 'cmd별 부분집합/추가 필드' 열 신설**(SYNC_DETECTION 의 CREATED 부재도 함께 문서화), §4.2 `EnumSuppressionStatus` 등재, §11.2 동기화 body 표에 **SYNC_DETECTION 누락행 보강** + 신규행. **카운트 부채 정정**: §5.1 총계 42→**44**(실제 행 수와 불일치였음), 동기화 소분류 9종→**11종**, §11.1 **#41 중복(SYNC_DETECTION/SYSTEM_EVENT) 해소 + 재번호**(총 44). 이후 참조는 번호가 아닌 **cmd 이름** 사용 권장. |
| v1.5.2 | 2026-07-30 | **GIS 제어 메시지 REQ/RSP 통일**: GIS(Frontend)→매니저 단일대상 제어(`LAMP_CLEAR`/`LAMP_COLOR_SET`/`LAMP_BUZZER_SET`, `BROADCAST_PLAY`/`BROADCAST_STOP`, `PTZ_AIM_LOCATION`)를 PUB→**REQ/RSP**로 통일(운영자 확인 필요, RSP는 §2 표준 봉투 `success`/`req_id`/`message` 사용). Central 발행(MODE_CHANGE/TTS/BROADCAST_TEST/LAMP_COLOR_TEST/LAMP_BUZZER_TEST 및 Central의 LAMP_OFF/WINDY)과 `ACTION_REPORT`(GIS→All 1:N 브로드캐스트)는 **PUB 유지**. **`PTZ_AIM_LOCATION` PUB 예외 제거 → PTZ_* 37종 전부 REQ로 통일**. 반영: 스펙 헤더·JSON 예시·§5.1 카탈로그·§11.1 목록, §3.2/§5.1¹/§11.1¹/§8.1 노트의 'PTZ_* 중 AIM_LOCATION만 PUB 예외' 표현 삭제, §7.2·§7.3 서두 제어 유형 원칙 명시. |
