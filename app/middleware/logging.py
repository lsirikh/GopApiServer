"""
API Logging Middleware
Logs all API requests to database with Client UUID and Request ID tracking

v5.4 후속 — 문서 A-7 #1 대응:
- 이전: async dispatch 안에서 동기 SessionLocal() + INSERT + commit → 이벤트루프 블로킹.
  풀 30 커넥션이 idle-in-transaction으로 굳으면 /health까지 정지 (문서 A-2 ②③).
- v5.4: 실 INSERT는 `asyncio.to_thread(...)`로 threadpool 이관 → 이벤트루프 자유.
  fire-and-forget 태스크로 발행하여 응답 지연도 최소화.

v6.0 P2 정합성 결정 (2026-07-03):
- 위 to_thread + fire-and-forget 패턴을 v6.0에서도 그대로 유지한다.

v6.0 Phase 4 (2026-07-03) — 문서 A-7 #1 후속:
- to_thread + 요청당 태스크 → **asyncio.Queue 단일 producer/consumer 배치** 로 전환.
- 이유:
  1) 요청당 threadpool worker + sync SessionLocal 획득은 QPS 폭주 시
     스레드풀·커넥션 풀 동시 압박 (문서 A-2 ②③ 재발 위험).
  2) 배치 INSERT (100건 or 500ms) → COMMIT 횟수·wal 부하 대폭 감소.
  3) AsyncSession + `insert(ApiLog).values([...])` executemany → async 스택 일원화.
- 계약 보존:
  * 응답 지연 0 원칙 — enqueue 는 put_nowait, 큐 full 시 drop-and-log 로 요청 방해 금지.
  * `_persist_api_log_sync` **완전 유지** (테스트/폴백 caller 존재).
  * ApiLog 컬럼(resource/method/client_uuid/request_id/description/status_code/body/param/error_message/timestamp) 그대로.
- 라이프사이클:
  * `start_log_consumer()` — FastAPI startup 훅에서 호출 (main.py).
  * `stop_log_consumer()` — shutdown 훅에서 호출, 큐 drain 후 종료.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import insert
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.utils.datetime import utc_now  # datetime-unification: api_logs naive-UTC 저장
from app.database import AsyncSessionLocal, SessionLocal
from app.models.log import ApiLog


# ─── 모듈 스코프 큐 / consumer 태스크 ────────────────────────────
_LOG_QUEUE_MAXSIZE = 10000
_BATCH_SIZE = 100
_BATCH_TIMEOUT = 0.5  # seconds — 첫 아이템 수신 후 최대 대기 시간

_log_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_LOG_QUEUE_MAXSIZE)
_consumer_task: Optional[asyncio.Task[None]] = None

# 큐 full 상황 관측용 카운터 (프로세스 재시작 시 리셋). 진단/모니터링 용도.
_dropped_count: int = 0


# ─── SEC-01: 민감 요청 본문 마스킹 ──────────────────────────────
# api_logs.body 에 로그인 비밀번호·토큰이 평문 저장되던 문제 차단.
# 요청 body(JSON)에서 민감 키 값을 재귀 마스킹한다. JSON 이 아니면(폼/멀티파트/평문)
# 민감정보 포함 여부를 알 수 없으므로 원문을 저장하지 않는다(보수적 default-deny).
_SENSITIVE_BODY_KEYS = frozenset({
    "password", "current_password", "new_password", "user_password",
    "access_token", "refresh_token", "token", "secret", "authorization",
})
_REDACTED = "***REDACTED***"


def _redact_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: (_REDACTED if isinstance(k, str) and k.lower() in _SENSITIVE_BODY_KEYS
                else _redact_obj(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_obj(x) for x in obj]
    return obj


def redact_request_body(raw: Optional[str]) -> Optional[str]:
    """요청 body 문자열의 민감 키 값을 마스킹한 JSON 문자열을 반환한다.
    JSON 파싱 불가(폼/멀티파트/평문)면 원문 저장을 막기 위해 None 을 반환한다."""
    if not raw:
        return raw
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return json.dumps(_redact_obj(parsed), ensure_ascii=False)


def _persist_api_log_sync(
    *, resource, method, client_uuid, request_id,
    description, status_code, body, param, error_message,
) -> None:
    """threadpool 에서 실행될 동기 INSERT — 이벤트루프 자유 유지.

    v6.0 Phase 4 이후에는 미들웨어 정상 경로에서 호출되지 않으나,
    테스트/폴백/외부 caller 를 위해 완전 유지한다.
    """
    db: Session = SessionLocal()
    try:
        log_entry = ApiLog(
            resource=resource,
            method=method,
            client_uuid=client_uuid,
            request_id=request_id,
            description=description,
            status_code=status_code,
            body=body,
            param=param,
            error_message=error_message,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        print(f"Logging error: {e}")
    finally:
        db.close()


async def _enqueue_log(payload: dict[str, Any]) -> None:
    """
    미들웨어 dispatch 에서 호출하는 enqueue 훅.
    - 큐 full 시 drop-and-log 로 처리 → 요청 응답 방해 금지 (계약 유지).
    - put_nowait 라 코루틴 실행 시간은 O(1).
    """
    global _dropped_count
    try:
        _log_queue.put_nowait(payload)
    except asyncio.QueueFull:
        _dropped_count += 1
        # 과도한 로그 방지: 128건 단위로만 경고 출력
        if _dropped_count % 128 == 1:
            print(
                f"[log_consumer] queue full — drop-and-log "
                f"(total dropped={_dropped_count}, qsize={_log_queue.qsize()})"
            )


async def _flush_batch(batch: list[dict[str, Any]]) -> None:
    """배치를 AsyncSession 기반 executemany INSERT 로 저장."""
    if not batch:
        return
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(insert(ApiLog), batch)
            await db.commit()
        except Exception as e:
            print(f"[log_consumer] batch INSERT failed ({len(batch)} rows): {e}")
            try:
                await db.rollback()
            except Exception:
                pass


async def _log_consumer() -> None:
    """
    단일 consumer 코루틴 — 배치 flush.
    - 첫 아이템은 blocking get (이벤트루프 슬립).
    - 첫 아이템 수신 후 최대 _BATCH_TIMEOUT 동안 _BATCH_SIZE-1 개까지 추가 수집.
    - 셧다운 시 CancelledError 를 잡아 남은 큐 drain 후 종료.
    """
    loop = asyncio.get_event_loop()

    while True:
        batch: list[dict[str, Any]] = []
        try:
            # 첫 아이템 대기 — 큐 비어있으면 코루틴 sleep, CPU/DB 부하 0.
            first = await _log_queue.get()
            batch.append(first)

            # 배치 창(window): 첫 아이템 수신 시각 기준으로 _BATCH_TIMEOUT 안에
            # _BATCH_SIZE-1 개까지 추가 수집. 이 창이 지나면 즉시 flush → 지연 상한 보장.
            deadline = loop.time() + _BATCH_TIMEOUT
            while len(batch) < _BATCH_SIZE:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(_log_queue.get(), timeout=remaining)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            await _flush_batch(batch)

        except asyncio.CancelledError:
            # graceful shutdown: 남은 큐 drain 후 재-raise.
            drain_size = _log_queue.qsize()
            print(f"[log_consumer] shutdown — draining {drain_size} queued items (batch={len(batch)})")
            while not _log_queue.empty():
                try:
                    batch.append(_log_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            try:
                await _flush_batch(batch)
            except Exception as e:
                print(f"[log_consumer] shutdown drain flush failed: {e}")
            raise

        except Exception as e:
            # 알 수 없는 예외 — 다음 루프에서 재시도. 1초 백오프.
            print(f"[log_consumer] error: {e}")
            await asyncio.sleep(1)


async def start_log_consumer() -> None:
    """
    FastAPI startup 훅에서 호출.
    - 이미 실행 중이면 무시(idempotent).
    """
    global _consumer_task
    if _consumer_task is not None and not _consumer_task.done():
        return
    _consumer_task = asyncio.create_task(_log_consumer(), name="api_log_consumer")


async def stop_log_consumer() -> None:
    """
    FastAPI shutdown 훅에서 호출.
    - consumer 태스크 cancel → drain → 종료 대기.
    """
    global _consumer_task
    if _consumer_task is None:
        return
    _consumer_task.cancel()
    try:
        await _consumer_task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[log_consumer] stop error: {e}")
    finally:
        _consumer_task = None


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests to database
    - Captures Request ID and Client UUID from headers
    - Records resource, method, description, and status code
    - Stores timestamp in ISO 8601 format
    """

    def get_description(self, method: str, path: str, status_code: int) -> str:
        """Generate description based on method and path"""
        resource_map = {
            "controllers": "제어기",
            "sensors": "센서",
            "cameras": "카메라",
            "detections": "탐지 이벤트",
            "malfunctions": "장애 이벤트",
            "connections": "연결 이벤트",
            "actions": "조치 이벤트",
        }

        action_map = {
            "GET": "조회",
            "POST": "생성",
            "PUT": "전체 수정",
            "PATCH": "부분 수정",
            "DELETE": "삭제",
        }

        # Extract resource from path
        parts = path.strip("/").split("/")
        resource_key = parts[-1] if len(parts) > 0 else "unknown"

        # Check if it's a detail endpoint (has ID)
        is_detail = len(parts) > 0 and parts[-1].isdigit()
        if is_detail and len(parts) >= 2:
            resource_key = parts[-2]

        resource_name = resource_map.get(resource_key, resource_key)
        action = action_map.get(method, method)

        # Generate description
        if status_code >= 400:
            return f"{resource_name} {action} 실패"
        elif is_detail:
            return f"{resource_name} {action}"
        else:
            if method == "GET":
                return f"{resource_name} 목록 {action}"
            return f"{resource_name} {action}"

    async def dispatch(self, request: Request, call_next):
        # Get headers
        client_uuid = request.headers.get("X-Client-UUID")
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

        # Get resource path (remove /api prefix)
        path = request.url.path
        resource = path.replace("/api/", "").strip("/")

        # Capture URL query parameters
        query_params = None
        if request.url.query:
            query_params = str(request.url.query)
            # Limit param length to prevent database overflow
            if len(query_params) > 1000:
                query_params = query_params[:997] + "..."

        # Capture request body for POST, PUT, PATCH methods
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    # SEC-01: 원문 전체를 먼저 마스킹한 뒤 길이 제한
                    # (truncate 후 JSON 파싱 실패로 마스킹이 무력화되는 것 방지)
                    body = redact_request_body(body_bytes.decode('utf-8', errors='replace'))
                    if body and len(body) > 2000:
                        body = body[:1997] + "..."
                # Re-create request with body (since body() consumes the stream)
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception as e:
                print(f"Error capturing request body: {e}")

        # Call next middleware/endpoint
        response = await call_next(request)

        # Capture error message from response if status >= 400
        error_message = None
        if response.status_code >= 400:
            try:
                # For responses with body, try to extract error message
                # (SEC-01: 별도 지역변수 사용 — 마스킹된 요청 body 를 덮어쓰지 않도록)
                if hasattr(response, 'body'):
                    resp_body = response.body
                    if resp_body:
                        response_data = json.loads(resp_body.decode('utf-8'))
                        error_message = response_data.get('message') or response_data.get('detail')
                        # Limit error message length
                        if error_message and len(error_message) > 1000:
                            error_message = error_message[:997] + "..."
            except Exception as e:
                print(f"Error extracting error message: {e}")

        # Generate description
        description = self.get_description(request.method, path, response.status_code)

        # Skip logging for non-API routes (docs, openapi, static, health)
        # v5.4 P0-1: /reports/preview 제외 제거 — 인증 필요 엔드포인트는 감사 로그에 남긴다.
        if path in ("/docs", "/redoc", "/openapi.json", "/health", "/", "/favicon.ico"):
            return response

        # v6.0 Phase 4 (A-7 #1): asyncio.Queue → 배치 consumer 로 이관.
        # - 응답 지연 0 원칙 유지: put_nowait 만 수행, 큐 full 시 drop-and-log.
        # - 타임스탬프는 요청 완료 시점에서 캡처 → 배치 flush 지연 무관하게 정확도 보존.
        try:
            payload: dict[str, Any] = {
                "resource": resource,
                "method": request.method,
                "client_uuid": client_uuid,
                "request_id": request_id,
                "description": description,
                "status_code": response.status_code,
                "body": body,
                "param": query_params,
                "error_message": error_message,
                # datetime-unification: api_logs.timestamp = TIMESTAMP WITHOUT TIME ZONE(파티션키, v67까지 유지).
                # 전역 serializer(naive=UTC) 규약과 정합되도록 naive-UTC 벽시계로 저장. sweep cutoff(utcnow)와도 일치.
                "timestamp": utc_now().replace(tzinfo=None),
            }
            await _enqueue_log(payload)
        except Exception as e:
            print(f"Log enqueue error: {e}")

        return response
