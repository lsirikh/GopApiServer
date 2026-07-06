# GOP 서버(API) 응답: `servers.port=0` 이슈 처리 결과 통지 — SensorwayManagers 대상

- **작성일**: 2026-07-06
- **응답 대상**: SensorwayManagers 팀 (`docs/prds/GOPDB_servers_port0_issue.md` 원 이슈 제기 팀)
- **응답 세션**: api-test-server 서버 세션
- **커밋/태그**: `release/v6.0` 위 → `v6.0-servers_port_response_relax`
- **브랜치**: `release/v6.0` (Swagger `info.version=6.0.0`)
- **관련 원인 문서**: `docs/prds/GOPDB_servers_port0_issue.md` (귀 팀 원문)

---

## 📌 두괄식 결론

| 항목 | 상태 |
|---|---|
| 이슈 원인 진단 | ✅ 서버측 응답 스키마 설계 실수 자인 |
| 서버측 근본 픽스 | ✅ 완료 (2층 방어: L1 스키마 완화 + L2 목록 fault tolerance) |
| 로컬 실측 검증 | ✅ port=0 인위 주입 후 GET /api/servers **500 → 200**, 해당 행 그대로 노출 |
| 원격 GOPDB 배포 | ⚠️ 서버 팀이 원격 GOPDB 이미지 재빌드/재기동 진행 후 별도 통지 예정 |
| **데이터 위생 조치 필요** | ⚠️ **원격 GOPDB `servers` 테이블의 `port=0` 행 UPDATE 필요** (아래 §3) |
| 귀 팀 클라 코드 | ✅ 이미 `port = Math.Max(1, ManagerServerPort)` 로 방어됨 — 추가 조치 없음 |

**요약**: 서버 응답 500은 근본 시정 완료. 다만 이미 DB에 박힌 옛 `port=0` 행 자체는 서버 픽스가 지우지 못하므로, 귀 팀 또는 GOP DB 관리자가 원격 DB에서 SQL `UPDATE`로 정리 부탁드립니다.

---

## 1. 원인 자인 (서버측 잘못)

원 이슈에서 지적하신 대로 **응답 스키마 `ServerResponse.port` 에도 요청과 동일한 `ge=1` 제약을 부여한 것**이 지뢰였습니다. API 설계 원칙 "요청은 엄격, 응답은 관대"(Postel's Law)를 응답 쪽에서 위배했습니다.

- 요청 검증(`ServerCreate.port ge=1`) — 정당: 새 데이터는 유효해야
- **응답 검증(`ServerResponse.port ge=1`) — 부당**: DB에 이미 저장된 옛 값(`port=0`)을 응답으로 노출할 때 pydantic이 거부 → 목록 API 전체 500
- 게다가 **행 1개가 목록 전체를 죽이는 blast radius** — 정상 서버 13대까지 못 읽힘

원인 분석까지 정확한 실측 데이터를 담아주셔서 감사드립니다. 그대로 반영했습니다.

---

## 2. 서버측 픽스 (2층 방어)

### L1. 응답 스키마 제약 완화

**파일**: `app/schemas/server.py`

| 스키마 | 필드 | 이전 | 이후 |
|---|---|---|---|
| `ServerCreate.port` | 요청 | `Field(..., ge=1, le=65535)` | **유지** (새 등록 데이터 위생) |
| `ServerUpdate.port` | 요청 | `Optional[int]... ge=1, le=65535` | **유지** |
| **`ServerResponse.port`** | 응답 | `Field(..., ge=1, le=65535)` | **`Field(..., ge=0, le=65535)`** |
| **`ServerNestedResponse.port`** | 응답 (다른 리소스 nested) | `Field(..., ge=1, le=65535)` | **`Field(..., ge=0, le=65535)`** |

- `port=0` 을 "미지정" 값으로 응답에 그대로 노출 가능
- `le=65535` 상한과 `int` 타입은 유지 (완전 무제약은 아님)
- description 문구: `"서버 포트 (0~65535, 0=미지정)"`

**요청은 여전히 `ge=1` 유지** — 새로 등록되는 데이터는 여전히 유효 강제. 다만 귀 팀 코드가 이미 `Math.Max(1, ...)` 로 방어되어 있으므로 실제로 422 가 나오는 케이스는 없어야 합니다.

### L2. 목록 fault tolerance

**파일**: `app/routers/servers.py`

- 신설: `_safe_server_to_response(server)` — try/except로 감싸 실패 시 `logger.warning(...)` 로 로그 남기고 `None` 반환
- 반영: `list_servers` / `get_server_summary` 의 리스트 컴프리헨션을 **walrus(`:=`) + `None` 필터**로 변경
- 효과: 한 행이 어떤 이유로든 스키마 위반이어도 나머지 정상 행은 그대로 반환. **목록 API 전체가 500 되지 않음**
- 단건 조회(`get_server`)는 이 헬퍼를 쓰지 않음 — 단건은 원인을 사용자에게 명확히 알려주는 게 옳음 (500 유지)

```python
# L2 정책
def _safe_server_to_response(server: Server) -> Optional[ServerResponse]:
    try:
        return _server_to_response(server)
    except Exception as exc:
        logger.warning(
            "[servers.list] response 직렬화 실패 → 목록에서 skip: server_id=%s name=%r port=%r reason=%s",
            server.id, server.name, server.port, exc,
        )
        return None

# 사용처
server_responses = [r for s in servers if (r := _safe_server_to_response(s)) is not None]
```

**즉 이제 실패 행 하나가 있어도**:
- 목록 응답은 **200**으로 유지 (스키마 위반 행만 skip)
- 서버 로그에 `[servers.list] response 직렬화 실패 → 목록에서 skip: server_id=X ...` WARN 남김 → 관측 가능

---

## 3. 로컬 실측 검증

로컬 환경(`pids-api-server`, PostgreSQL 16)에서 4단계 실측:

| # | 시나리오 | HTTP | 상세 |
|---|---|---|---|
| 1 | **회귀** — 정상 상태 GET /api/servers | 200 | 14 rows 정상 |
| 2 | **인위 주입** — `UPDATE servers SET port=0 WHERE id=3` (`VMS-ab1120`) | — | `port=0` 저장 확인 |
| 3 | **핵심** — GET /api/servers (port=0 존재 상태) | **200** ✅ | **14 rows 응답, `id=3 port=0` 그대로 노출** (이전 사이클엔 500) |
| 4 | 원위치 — `UPDATE servers SET port=8080 WHERE id=3` | — | 정상 복구 |

**즉 원격 GOPDB에서 겪으신 `INTERNAL_ERROR / greater_than_equal / input_value=0` 500 케이스가 이제 200으로 정상 처리됩니다.**

---

## 4. 원격 GOPDB 데이터 위생 조치 (요청)

⚠️ **서버 픽스는 응답 500을 막는 대증요법이고, 근본은 데이터 정리**입니다.
아래 SQL을 GOP DB 관리자가 원격 실행 부탁드립니다:

### 진단
```sql
SELECT id, name, ip_address, port
  FROM servers
 WHERE port = 0
    OR port IS NULL;
```

### 갱신 (권장 — 이력 보존)
```sql
UPDATE servers
   SET port = 1                              -- 매니저는 실제 노출 포트가 없으므로 sentinel
 WHERE port = 0
    OR port IS NULL;
```

### 대체안 — 삭제 (metrics FK CASCADE 주의)
```sql
-- 쓰레기 행이면 삭제. server_metrics 등 자식 테이블 참조가 있으면 선삭제 필요.
-- DELETE FROM servers WHERE port = 0;
```

### 검증
```bash
GET /api/servers   (Bearer 토큰)   →   200 (여전히 유지)
```

---

## 5. 원격 GOPDB 배포

- 현재 픽스는 **로컬 `pids-api-server`** 이미지에 반영 완료 (실측 4단계 통과)
- 원격 GOPDB(`https://123.141.236.253:8455`) 재빌드/재기동은 **서버 팀에서 별도 사이클로 진행**
- 배포 완료 시 별도 통지 예정

---

## 6. 귀 팀 클라측 조치 요약

원 이슈 §6에 언급하신 대로 **귀 팀 코드는 이미 방어 완료**입니다:

```csharp
// ProxyWorker.Core/Services/ServerMetricsReporterHostedService.cs
port = Math.Max(1, _options.ManagerServerPort),
```

- 새 등록은 `port >= 1` 보장 → 422 재발 없음
- 기존 `port=0` 행 정리는 서버 §4 SQL 조치로 대응
- **추가 클라 코드 변경 필요 없음**

권장: `appsettings` 의 `ServerMetricsReporter:ManagerServerPort` 를 매니저별 실제 포트(예: HTTP diagnostic port)로 명시하시면 진단 목적 상 더 유용합니다. `Math.Max(1, 0)=1` 이 sentinel 이라 그 자체로도 무방합니다.

---

## 7. 서버측 정책 반성 및 개선

이번 사고에서 배운 것:

1. **응답 스키마에는 요청 제약을 그대로 복사하지 않는다** — 응답 관대 원칙(Postel's Law) 적용
2. **목록 API는 행별 실패에 관대해야 한다** — 한 행이 전체를 죽이지 않도록 fault tolerance
3. **스키마 강화는 데이터 마이그레이션과 병행해야** — 뒤에 강화하면 옛 데이터가 지뢰
4. **응답 스키마도 pydantic 검증이 있다** — 요청만 신경 쓰면 안 됨

향후 유사 필드(예: 다른 리소스의 `ge=1`, enum 등)에 동일 패턴이 있는지 별도 감사 사이클 진행 예정입니다.

---

## 8. 참조

- **원 이슈**: `docs/prds/GOPDB_servers_port0_issue.md` (귀 팀)
- **서버 커밋**: 태그 `v6.0-servers_port_response_relax` (release/v6.0 위)
- **CHANGELOG**: `CHANGELOG.md` → v6.0-servers_port_response_relax 섹션
- **파일**: `app/schemas/server.py` (L1), `app/routers/servers.py` (L2)
- **저장소**: origin=`github.com/lsirikh/GopApiServer`, gitea=`192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server`

문의/피드백은 서버 세션으로 회신 부탁드립니다. 원격 GOPDB 배포 완료 시 별도 후속 통지 예정입니다.
