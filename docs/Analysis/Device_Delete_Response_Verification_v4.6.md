# API DELETE 응답 형식 일관성 검증 — 분석 보고서

> 작성: 백엔드 분석 · 일자: 2026-06-21
> 대상: 이기호 차장님 / 클라이언트팀
> 관련 보고: `docs/API_Delete_Response_Inconsistency-report.md` (클라이언트팀, 2026-06-21)

---

## TL;DR (두괄식)

- **클라이언트팀 보고는 100% 정확합니다.** 7개 엔드포인트 모두 코드 / OpenAPI 스키마 / 런타임 응답 3중 검증으로 일치 확인.
- **불일치 2건 confirmed** (`DELETE /api/devices/lamps/{lamp_id}`, `DELETE /api/devices/groups/{group_id}`) — 두 엔드포인트만 `data: {객체}`를 반환하여 클라 파싱 예외(`JsonReaderException`) 유발.
- **권장 조치: Option 1 (`data: null`로 통일)** — 작업 분량 약 40분, 다른 5개 단건 DELETE 라우터가 이미 `ApiSingleResponse[None]` 규약을 따르므로 정합성·최소 변경 측면에서 우월.
- **v4.6 Phase 9의 EM DELETE 변경과는 별개 이슈** — Phase 9는 EventMapping 도메인 DELETE 응답 규약을 다루었고, 본건은 Device CRUD 도메인의 단건 DELETE 잔존 비정합. 혼동 주의.

---

## 1. 7개 엔드포인트 검증 결과

| # | 엔드포인트 | response_model | code return data | 실측 응답 data | 클라 보고 | 판정 |
|---|---|---|---|---|---|---|
| 1 | `DELETE /api/devices/cameras/{camera_id}` | `ApiSingleResponse[None]` | `None` | `null` | 정상 | OK (정상) |
| 2 | `DELETE /api/devices/controllers/{controller_id}` | `ApiSingleResponse[None]` | `None` | `null` | 정상 | OK (정상) |
| 3 | `DELETE /api/devices/sensors/{sensor_id}` | `ApiSingleResponse[None]` | `None` | `null` | 정상 | OK (정상) |
| 4 | `DELETE /api/devices/speakers/{speaker_id}` | `ApiSingleResponse[None]` | `None` | `null` | 정상 | OK (정상) |
| 5 | `DELETE /api/devices/enclosures/{enclosure_id}` | `ApiSingleResponse[None]` | `None` | `null` | 정상 | OK (정상) |
| 6 | **`DELETE /api/devices/lamps/{lamp_id}`** | **`ApiSingleResponse[dict]`** | **`{"id": lamp_id, "deleted": True}`** | **`{"id":981,"deleted":true}`** | **실패** | **불일치 confirmed** |
| 7 | **`DELETE /api/devices/groups/{group_id}`** | **`ApiSingleResponse[dict]`** | **`{"id": group_id}`** | **`{"id":11}`** | **실패** | **불일치 confirmed** |

- **client_report_verified**: True (클라 보고와 검증 결과 100% 일치)
- **confirmed_inconsistencies**: 2 / **refuted**: 0

---

## 2. 불일치 원인 (코드 인용)

### 2.1 `lamps.py:409-455` — 단건 DELETE만 dict 반환

```python
# app/routers/lamps.py:409
@router.delete("/{lamp_id}", response_model=ApiSingleResponse[dict])

# lines 451-455
return ApiSingleResponse(
    success=True,
    message="Lamp 삭제 성공",
    data={"id": lamp_id, "deleted": True}   # ← 다른 5개와 다름
)
```

- 도입 커밋: `73d74ea feat: Add Lamp Device and EventMappingLamp APIs`
- Lamp 기능 추가 시 Camera/Controller/Sensor/Speaker/Enclosure가 이미 확립한 `data=None` 규약과 정렬되지 않은 채 머지됨.

### 2.2 `device_groups.py:608-654` — 단건 DELETE만 dict 반환

```python
# app/routers/device_groups.py:608
@router.delete("/{group_id}", response_model=ApiSingleResponse[dict])

# lines 650-654
return ApiSingleResponse(
    success=True,
    data={"id": group_id},   # ← 다른 5개와 다름
    message="디바이스 그룹 삭제 성공"
)
```

- 도입 커밋: `26f3125 struct: Add ApiSingleResponse schema, ...`
- ApiSingleResponse 표준화 일제 작업 시 본 핸들러만 `ApiSingleResponse[None]` 대신 `[dict]` 유지 — 누락성 잔존 비정합.

### 2.3 OpenAPI 스키마 영향

- `ApiSingleResponse_dict_`는 `data: object (additionalProperties: true)` — **정의된 DTO 없는 자유형 객체**. C# 클라이언트 `ToApiResponseAsync<bool>`가 단순값으로 역직렬화 시 `JsonReaderException` 발생.
- 나머지 5개는 `ApiSingleResponse_NoneType_` (`data: {"type":"null"}`) — 클라가 안전하게 null 처리.

---

## 3. 권고 옵션 비교

| 항목 | Option 1: `data: null` 통일 (권장) | Option 2: 표준 DTO 도입 | Option 3: 현상유지 |
|---|---|---|---|
| 변경 범위 | lamps.py 1줄+1블록, device_groups.py 1줄+1블록 | 신규 DTO 1종 + 전 단건 DELETE(7개) 일제 변경 | 없음 |
| 클라 영향 | lamps/groups 두 곳만 wire-level 변경 (null로 단순화) | 7개 전 엔드포인트 wire-level 변경 (DTO로 통일) | 클라 방어 코드로 우회 |
| 작업 시간 | **약 40분** (코드+테스트+OpenAPI 회귀) | 약 3~4시간 (DTO/스키마/테스트/문서) | 0분 |
| OpenAPI 명세 정합성 | 5개 기준에 lamps/groups 정렬 — 단일 모델 | 새로운 표준 모델 신설 | 비정합 유지 |
| v4.6 ApiSingleResponse 정책 부합 | High (지배적 패턴과 일치) | High (그러나 표준 재정의 필요) | Low |
| 장기 유지보수 | 우수 (다른 Device 라우터와 동일 규약) | 우수 (DTO 명세화) | 신규 도메인 추가 시 또 재발 위험 |
| Risk | Low (삭제 후 식별자는 message에 보존 가능) | Mid (7개 모두 회귀 테스트 필요) | High (재발/클라 신뢰 저하) |

**권장: Option 1**
- 근거: (a) Camera/Controller/Sensor/Speaker/Enclosure 5개 라우터가 이미 `data: null` 규약 확립, (b) Lamp/DeviceGroup만 정합화하면 끝, (c) 작업 분량 최소·회귀 영향 국소, (d) 삭제 결과 식별자가 필요하면 `message="디바이스 그룹 11 삭제 성공"` 형태로 메시지에 보존 가능.

---

## 4. 작업 분량

| 작업 | 파일 | 변경 | 시간 |
|---|---|---|---|
| Lamp DELETE 정합화 | `app/routers/lamps.py:409,451-455` | decorator → `ApiSingleResponse[None]`, data → `None` | 25분 |
| DeviceGroup DELETE 정합화 | `app/routers/device_groups.py:608,650-654` | decorator → `ApiSingleResponse[None]`, data → `None` | 15분 |
| 회귀 테스트 추가 | `tests/...` | `should_return_data_none_when_lamp_deleted`, `should_return_data_none_when_device_group_deleted` | 포함 |
| OpenAPI 회귀 확인 | — | `openapi.json` 재생성 시 `ApiSingleResponse_NoneType_` 적용 확인 | 포함 |
| **합계** | | | **약 0.7시간 (40분)** |

---

## 5. v4.6 Phase 9 EventMapping DELETE와의 관계 (혼동 방지)

| 구분 | v4.6 Phase 9 EM DELETE | 본 보고 (Device CRUD DELETE) |
|---|---|---|
| 도메인 | EventMapping (이벤트 매핑) | Device CRUD (Camera/Lamp/Sensor/Speaker/Enclosure/Controller/DeviceGroup) |
| 변경 시점 | v4.6 Phase 9 | (Lamp) v4.3 기능 추가 시 / (Group) v4.6 ApiSingleResponse 표준화 시 |
| 현 상태 | EM 도메인 내 통일된 응답 규약 적용 | 5개는 `data: null`, 2개(Lamp/Group)만 `data: dict` |
| 본건과 별개? | **예. 별개 이슈** — EM 도메인은 Phase 9에서 별도 정책으로 정리, 본건은 Device CRUD 도메인의 잔존 비정합 | — |

- 결론: 클라이언트팀이 보고한 7건은 모두 **Device CRUD 도메인** 단건 DELETE. EM 도메인 응답 규약과 혼동해서는 안 됨.

---

## 6. 매니저 영향

- 본건은 **API 응답 계약(Contract)** 정합성 이슈로, 매니저(NATS Publisher, ConfigChangeLog, DB 매니저) 동작에는 영향 없음.
- `log_config_change` 호출은 `before_state`로 식별자를 이미 캡처하므로 응답 본문에 `id`를 노출하지 않아도 감사 추적성 손실 없음.
- NATS `SYNC_DEVICE action=DELETED` 발화는 본건과 독립적으로 정상 동작 중 (클라 보고 부록 확인됨).

---

## 7. 결재 사항

1. **권고안 채택**: Option 1 (`data: null` 통일) 진행 승인 요청
2. **Wire-level Breaking Change 통보**: lamps/groups 응답이 `{...}` → `null`로 단순화됨 — 클라이언트팀에 배포 동기화 사전 공지 필요 (단, 클라 보고서에서도 "어느 쪽이든 일관성만" 요구하므로 영향 최소)
3. **후속 PRD 등록 권장**: `PRD_ApiResponse_Split.md`에 "단건 DELETE는 `ApiSingleResponse[None]` 사용" 규약을 명문화하여 신규 라우터 추가 시 재발 방지
4. **부차 점검 (옵션)**: `servers.py:461`, `server_categories.py:370`이 동일 dict 패턴인지 sweep — 본 보고 범위 외이나 같은 PRD에서 일제 정리 권장

---

## 8. 부록 — 검증 근거

- **실측 명령 (DeviceGroup)**: `POST /api/auth/login → POST /api/devices/groups (created id=11) → DELETE /api/devices/groups/11` → body `{"success":true,"message":"디바이스 그룹 삭제 성공","data":{"id":11},"meta":{...}}` 확인
- **실측 명령 (Lamp)**: lamp_id=981 생성 후 DELETE → `{"data":{"id":981,"deleted":true}}` 확인
- **실측 명령 (Camera/Controller/Sensor/Speaker/Enclosure)**: 각각 id 생성 후 DELETE → 모두 `"data":null` 확인
- **OpenAPI 스키마 확인**: `ApiSingleResponse_NoneType_` (5개) vs `ApiSingleResponse_dict_` (2개) 분리 확인
- **Git blame**: lamps DELETE는 `73d74ea`, device_groups DELETE는 `26f3125` 도입


---

## 📌 §6 P1 후속 sweep (2026-06-22 추가)

클라이언트팀 보고서 v2 (`docs/API_Delete_Response_Inconsistency-report.md` §6)의 P1 명시 endpoint도 일괄 sweep:

| Endpoint | Before | After |
|---|---|---|
| `DELETE /api/integrations/event-mappings/{id}/cameras/{config_id}` | `ApiSingleResponse[dict]` + `"data": {}` | `ApiSingleResponse[None]` + `"data": None` |
| `DELETE /api/integrations/event-mappings/{id}/speakers/{config_id}` | 동일 | 동일 |
| `DELETE /api/integrations/event-mappings/{id}/lamps/{config_id}` | 동일 | 동일 |
| `DELETE /api/reports/templates/{template_id}` | `ApiResponse` + `data={"id":...}` | `data=None` |
| `DELETE /api/servers/{server_id}/metrics` | `ApiSingleResponse[dict]` + `data={...}` | `ApiSingleResponse[None]` + `data=None` |
| `DELETE /api/devices/enclosures/{id}/metrics` | `data={"deleted_count":...}` | `data=None` (count는 message에 보존) |
| `DELETE /api/users/{user_id}` | `{"success": True}` (envelope 위반) | `{success, message, data:None}` |
| `DELETE /api/user-groups/{group_id}` | `{"success": True}` | 동일 envelope 보강 |
| `DELETE /api/user-sessions/user/{user_id}` | `data={"count":...}` | `data=None` (count는 message에) |
| `DELETE /api/user-sessions/me/{session_id}` | `{"success": True}` | envelope 보강 |
| `DELETE /api/user-sessions/{session_id}` | `{"success": True}` | envelope 보강 |

**합계**: P0 4건 (이전 commit) + P1 11건 (본 commit) = **15 endpoint**

## 최종 검증 (2026-06-22)

전체 DELETE endpoint **36개** OpenAPI 응답 검증:
- ✅ `ApiSingleResponse_NoneType_` (data: null 통일): **22개**
- ⚠️ `$ref` 없음 (response_model 미부착, 별도 작업 영역): 14개
- ✅ `ApiSingleResponse_dict_` (자유형 dict 잔존): **0개**

→ 보고서 §6 명시된 dict 패턴 DELETE 응답 **100% 정합 완료**.
