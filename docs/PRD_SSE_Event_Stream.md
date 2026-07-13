# PRD: SSE Event Stream 현황 분석 및 구현 방안

**문서 버전**: v1.0
**작성일**: 2026-02-04
**작성자**: AI Assistant
**상태**: Draft

---

## 1. 개요

### 1.1 목적

프론트엔드에서 `GET /api/events/stream` 엔드포인트로 반복 요청하며 `404 Not Found`가 발생하는 문제를 분석하고, SSE(Server-Sent Events) 구현 방안을 수립한다.

### 1.2 배경

Docker 환경에서 운영 중 아래 로그가 반복 발생:

```
172.19.0.1 - "GET /api/events/stream HTTP/1.1" 404 Not Found
172.19.0.1 - "GET /api/events/stream HTTP/1.1" 404 Not Found
172.19.0.1 - "GET /api/events/stream HTTP/1.1" 404 Not Found
...
```

- **요청 IP**: `172.19.0.1` (Docker bridge network — 프론트엔드 컨테이너)
- **요청 패턴**: 약 3~5초 간격 반복 (EventSource 자동 재연결 패턴)
- **원인**: API 서버에 `/api/events/stream` 엔드포인트가 존재하지 않음

### 1.3 SSE란?

SSE(Server-Sent Events)는 서버에서 클라이언트로 단방향 실시간 데이터를 push하는 HTTP 기반 프로토콜이다.

| 항목 | SSE | WebSocket | Polling |
|------|-----|-----------|---------|
| 방향 | 서버 → 클라이언트 (단방향) | 양방향 | 클라이언트 → 서버 (반복) |
| 프로토콜 | HTTP | WS/WSS | HTTP |
| 자동 재연결 | 내장 (EventSource API) | 수동 구현 필요 | 수동 구현 필요 |
| 적합한 케이스 | 알림, 이벤트 모니터링, 대시보드 | 채팅, 게임 | 단순 조회 |
| 브라우저 지원 | 모든 주요 브라우저 | 모든 주요 브라우저 | 모든 브라우저 |

**프론트엔드 코드 예시** (현재 프론트엔드가 사용 중인 것으로 추정):

```javascript
const eventSource = new EventSource('/api/events/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // 실시간 이벤트 처리
};

eventSource.onerror = (error) => {
    // 연결 실패 시 브라우저가 자동으로 재연결 시도 (3~5초 간격)
    // → 이것이 현재 404 반복 로그의 원인
};
```

---

## 2. 현황 분석 (코드 전수 조사 결과)

### 2.1 조사 범위

| 조사 대상 | 파일 수 | SSE 관련 코드 |
|-----------|---------|---------------|
| `app/routers/` | 32개 라우터 | **없음** |
| `app/services/` | 4개 서비스 | **없음** |
| `app/models/` | 15개 모델 | **없음** |
| `app/schemas/` | 16개 스키마 | **없음** |
| `app/middleware/` | 3개 미들웨어 | **없음** |
| `app/utils/` | 9개 유틸리티 | **없음** |
| `app/main.py` | 라우터 등록 | **없음** |
| `app/config.py` | 설정 | **없음** |
| `requirements.txt` | 의존성 | **없음** |
| `app/dependencies.py` | DI 정의 | **없음** |

### 2.2 검색 키워드 결과

| 검색 패턴 | 결과 | 비고 |
|-----------|------|------|
| `StreamingResponse` | 미발견 | FastAPI 스트리밍 응답 클래스 |
| `EventSourceResponse` | 미발견 | sse-starlette 라이브러리 |
| `text/event-stream` | 미발견 | SSE Content-Type |
| `sse-starlette` | 미발견 | Python SSE 라이브러리 |
| `async def` + `yield` (스트리밍용) | 미발견 | async generator for SSE |
| `WebSocket` (import) | 미발견 | WebSocket 구현 |
| `broadcast` / `publish` / `subscribe` | 미발견 | 이벤트 브로드캐스트 패턴 |
| `stream` (코드 내) | RTSP URL, 서버명 등 데이터 값만 존재 | SSE와 무관 |

### 2.3 현재 등록된 이벤트 관련 라우터

```
/api/events/detections    → detections.py (REST CRUD)
/api/events/malfunctions  → malfunctions.py (REST CRUD)
/api/events/connections   → connections.py (REST CRUD)
/api/events/actions       → actions.py (REST CRUD)
/api/events/stream        → ??? (미등록 — 404 발생)
```

### 2.4 유사 실시간 기능 현황

| 기능 | 위치 | 방식 | SSE 여부 |
|------|------|------|----------|
| Log Viewer 자동 갱신 | `logs.py` | `setInterval()` + `fetch()` (30초 폴링) | **아님** (REST 폴링) |
| Server Metrics | `server_metrics.py` | REST CRUD | **아님** |
| Enclosure Metrics | `enclosure_metrics.py` | REST CRUD | **아님** |

### 2.5 결론

> **API 서버에 SSE 구현 코드가 단 하나도 존재하지 않는다.**
>
> 프론트엔드가 `EventSource`로 `/api/events/stream`에 연결을 시도하지만,
> 서버에 해당 엔드포인트가 없어 404가 반환되고,
> `EventSource`의 자동 재연결 메커니즘에 의해 무한 반복된다.

### 2.6 PROGRESS_SUMMARY.md 참고

```
Long-term (Future Versions)
- WebSocket real-time notifications
```

WebSocket 실시간 알림이 **미래 계획**으로만 기록되어 있으며, 구현된 적 없다.

---

## 3. 문제 영향도

### 3.1 현재 발생하는 문제

| 문제 | 심각도 | 설명 |
|------|--------|------|
| 404 로그 폭주 | Medium | 3~5초마다 반복되어 로그 오염 |
| 불필요한 네트워크 트래픽 | Low | 매 요청마다 404 응답 전송 |
| API 로그 분석 방해 | Medium | 실제 의미있는 로그가 404 노이즈에 묻힘 |
| 실시간 데이터 미제공 | High | 프론트엔드의 실시간 대시보드가 동작하지 않음 |

### 3.2 프론트엔드 기대 동작 (추정)

프론트엔드는 SSE를 통해 아래 이벤트를 실시간으로 수신하려는 것으로 추정:

- 새로운 탐지(Detection) 이벤트 발생 알림
- 새로운 장애(Malfunction) 이벤트 발생 알림
- 장비 연결/해제(Connection) 이벤트 알림
- 조치(Action) 이벤트 알림
- 서버 상태 변경 알림
- 시스템 이벤트(System Event) 알림

---

## 4. 구현 방안 (제안)

### 4.1 기술 선택: SSE (sse-starlette)

**선택 근거**:
- 프론트엔드가 이미 `EventSource` API를 사용 중 (SSE 클라이언트)
- 서버 → 클라이언트 단방향 push만 필요 (양방향 불필요)
- HTTP 기반이므로 기존 CORS, 인증 미들웨어와 호환
- FastAPI에서 `sse-starlette` 라이브러리로 간단히 구현 가능

### 4.2 의존성 추가

```
# requirements.txt에 추가
sse-starlette>=1.6.0
```

### 4.3 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (EventSource)                                     │
│  const es = new EventSource('/api/events/stream')           │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP GET (text/event-stream)
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  SSE Router  (app/routers/event_stream.py)                  │
│  GET /api/events/stream                                     │
│  - 클라이언트 연결 관리                                       │
│  - EventSourceResponse 반환                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ subscribe
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Event Bus  (app/services/event_bus.py)                     │
│  - asyncio.Queue 기반 pub/sub                               │
│  - 다중 클라이언트 관리                                       │
│  - 이벤트 유형별 필터링                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ publish
                  ▲
┌─────────────────┴───────────────────────────────────────────┐
│  Event Publishers (기존 라우터에서 호출)                      │
│  - detections.py: POST 시 event_bus.publish("detection", …) │
│  - malfunctions.py: POST 시 event_bus.publish("malfunction") │
│  - connections.py: POST 시 event_bus.publish("connection")   │
│  - actions.py: POST 시 event_bus.publish("action", …)       │
│  - system_events.py: POST 시 event_bus.publish("system", …) │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 파일 구조 (신규)

```
app/
├── routers/
│   └── event_stream.py      ← SSE 엔드포인트 (신규)
├── services/
│   └── event_bus.py          ← 이벤트 버스 (신규)
└── schemas/
    └── event_stream.py       ← SSE 메시지 스키마 (신규)
```

### 4.5 SSE 메시지 포맷

```
event: detection
data: {"id": 1, "type": "detection", "result": "PERSON", "device_name": "CAM-01", "timestamp": "2026-02-04T10:30:00"}

event: malfunction
data: {"id": 5, "type": "malfunction", "reason": "SIGNAL_LOSS", "device_name": "CAM-03", "timestamp": "2026-02-04T10:31:00"}

event: connection
data: {"id": 12, "type": "connection", "status": "DISCONNECTED", "device_name": "SENSOR-02", "timestamp": "2026-02-04T10:32:00"}

event: heartbeat
data: {"timestamp": "2026-02-04T10:32:30"}
```

### 4.6 핵심 코드 설계

#### 4.6.1 Event Bus (app/services/event_bus.py)

```python
"""
Event Bus for SSE broadcasting
"""
import asyncio
from typing import AsyncGenerator, Optional
from datetime import datetime


class EventBus:
    """In-memory event bus using asyncio.Queue for SSE broadcasting"""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        """Subscribe to event stream"""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers.remove(queue)

    async def publish(self, event_type: str, data: dict):
        """Publish event to all subscribers"""
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        for queue in self._subscribers:
            await queue.put(event)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


# Singleton instance
event_bus = EventBus()
```

#### 4.6.2 SSE Router (app/routers/event_stream.py)

```python
"""
SSE Event Stream endpoint
"""
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse


router = APIRouter()


@router.get("/stream")
async def event_stream(request: Request):
    """
    SSE endpoint for real-time event streaming
    Content-Type: text/event-stream
    """
    async def generate():
        async for event in event_bus.subscribe():
            if await request.is_disconnected():
                break
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"])
            }

    return EventSourceResponse(generate())
```

#### 4.6.3 main.py 라우터 등록

```python
from app.routers import event_stream

app.include_router(
    event_stream.router,
    prefix="/api/events",
    tags=["Event Stream (SSE)"]
)
```

#### 4.6.4 기존 라우터 수정 (예: detections.py)

```python
from app.services.event_bus import event_bus

@router.post("/", response_model=DetectionEventResponse, status_code=201)
async def create_detection_event(...):
    # 기존 DB 저장 로직...
    result = crud_create(...)

    # SSE 이벤트 발행
    await event_bus.publish("detection", {
        "id": result.id,
        "result": result.result.value,
        "device_name": "...",
    })

    return result
```

### 4.7 Heartbeat

클라이언트 연결 유지를 위해 30초마다 heartbeat 이벤트를 전송:

```python
async def generate():
    heartbeat_interval = 30  # seconds
    last_heartbeat = time.time()

    async for event in event_bus.subscribe():
        if await request.is_disconnected():
            break

        # Heartbeat check
        if time.time() - last_heartbeat > heartbeat_interval:
            yield {"event": "heartbeat", "data": "{}"}
            last_heartbeat = time.time()

        yield {"event": event["event"], "data": json.dumps(event["data"])}
```

---

## 5. 구현 단계

### Phase 1: 기본 SSE 인프라 (P0)

| # | 항목 | 설명 |
|---|------|------|
| 1.1 | `sse-starlette` 의존성 추가 | requirements.txt |
| 1.2 | `EventBus` 서비스 구현 | app/services/event_bus.py |
| 1.3 | SSE 스키마 정의 | app/schemas/event_stream.py |
| 1.4 | `/api/events/stream` 엔드포인트 구현 | app/routers/event_stream.py |
| 1.5 | main.py 라우터 등록 | 404 해결 |
| 1.6 | Heartbeat 구현 | 연결 유지 |

### Phase 2: 이벤트 발행 연동 (P1)

| # | 항목 | 설명 |
|---|------|------|
| 2.1 | detections.py POST에 publish 추가 | 탐지 이벤트 |
| 2.2 | malfunctions.py POST에 publish 추가 | 장애 이벤트 |
| 2.3 | connections.py POST에 publish 추가 | 연결 이벤트 |
| 2.4 | actions.py POST에 publish 추가 | 조치 이벤트 |
| 2.5 | system_events.py POST에 publish 추가 | 시스템 이벤트 |

### Phase 3: 고급 기능 (P2, 선택)

| # | 항목 | 설명 |
|---|------|------|
| 3.1 | 이벤트 유형 필터링 | `?types=detection,malfunction` 쿼리 파라미터 |
| 3.2 | 인증 연동 | JWT 토큰으로 SSE 인증 |
| 3.3 | Last-Event-ID 지원 | 재연결 시 누락 이벤트 재전송 |
| 3.4 | 최대 연결 수 제한 | 서버 리소스 보호 |

---

## 6. 즉시 조치 가능한 대안 (SSE 구현 전)

SSE 전체 구현 전에 404 로그 폭주를 멈추기 위한 임시 조치:

### 대안 A: 빈 SSE 엔드포인트 등록

```python
# app/routers/event_stream.py (임시)
@router.get("/stream")
async def event_stream_placeholder():
    """Placeholder SSE endpoint — returns empty stream"""
    async def generate():
        while True:
            yield {"event": "heartbeat", "data": "{}"}
            await asyncio.sleep(30)

    return EventSourceResponse(generate())
```

- 장점: 404 로그 즉시 해결, 프론트엔드 에러 제거
- 단점: 실제 이벤트 데이터 없음

### 대안 B: 프론트엔드에서 SSE 비활성화

- 프론트엔드 코드에서 `EventSource` 연결을 조건부로 비활성화
- 서버 측 변경 불필요

---

## 7. 테스트 계획

### 7.1 단위 테스트

| 테스트 | 설명 |
|--------|------|
| `test_event_bus_publish_subscribe` | EventBus publish/subscribe 동작 확인 |
| `test_event_bus_multiple_subscribers` | 다중 구독자에게 이벤트 전달 |
| `test_event_bus_subscriber_cleanup` | 연결 해제 시 구독자 제거 |
| `test_sse_endpoint_returns_200` | `/api/events/stream` 200 응답 |
| `test_sse_content_type` | `text/event-stream` Content-Type 확인 |

### 7.2 통합 테스트

| 테스트 | 설명 |
|--------|------|
| `test_detection_post_publishes_sse` | Detection POST → SSE 이벤트 발행 확인 |
| `test_malfunction_post_publishes_sse` | Malfunction POST → SSE 이벤트 발행 확인 |
| `test_heartbeat_interval` | 30초 heartbeat 전송 확인 |

---

## 8. 참고 사항

### 8.1 sse-starlette 라이브러리

- GitHub: https://github.com/sysid/sse-starlette
- FastAPI 공식 문서에서 권장하는 SSE 구현 라이브러리
- Starlette의 `StreamingResponse`를 래핑하여 SSE 프로토콜 준수

### 8.2 CORS 호환성

현재 CORS 설정 (`allow_origins=["*"]`)은 SSE와 호환된다. SSE는 일반 HTTP GET 요청이므로 별도의 CORS 설정이 필요하지 않다.

### 8.3 인증 고려

현재 `AUTH_MODE`가 `"token"` 또는 `"public"` 모드를 지원한다. SSE 엔드포인트의 인증은:
- `EventSource` API는 커스텀 헤더를 지원하지 않으므로 JWT를 쿼리 파라미터로 전달하거나
- `AUTH_MODE=public`인 경우 인증 없이 접근 허용

---

## 9. 변경 이력

| 버전 | 일자 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-02-04 | 초안 작성 — 현황 분석 및 구현 방안 |
