# GOP_Restful_Api_연동설계.md v4.5 동기화 가이드 — 매니저 4종

> **차수**: v4.5 (2026-06-18) → 매니저 사본 4곳
> **작성자**: 이기호 차장
> **작성일**: 2026-06-19
> **목적**: v4.6 FR-4 — .NET 사본 4곳 stale 상태 해소

---

## 1. 두괄식 — 왜 동기화 필요한가

DBApi의 마스터 명세서가 v4.3 → v4.4 → v4.5로 3차수 갱신됐는데, .NET 매니저 측 사본 4곳이 **모두 옛 버전**입니다.

| 사본 위치 | 현재 버전 | 일자 | 갭 | 위험도 |
|---|---|---|---|---|
| **`c:\workspace_app\Ironwall.Dotnet.Libraries\Docs\`** | v4.2 | 2026-03-03 | 3개월 + Bulk API 전체 미반영 | 🔴 **Critical** |
| **`c:\source\repos\Dotnet.Rtsp.Viewer.Ui\Docs\`** | v4.3 | 2026-03-04 | v4.4 GAP 14건 + v4.5 PR-A/B/C/D 미반영 | 🟠 High |
| **`c:\workspace_app\Dotnet.Monitoring.Solution\Docs\`** | v1.6 | 2025-11-26 | 7개월 (DB 동기화 위주, REST 의존 적음) | 🟡 Medium |
| `c:\workspace_app\Ironwall.Dotnet.Libraries\Docs\Backup\pre_docs\` | 백업 | - | 손대지 않음 | - |

→ 매니저(GIS/VMS/NVR/Speaker) 4종이 이 사본을 보고 작업하면 **즉시 422/500 실패** 또는 **잘못된 응답 envelope 가정**으로 충돌 발생.

---

## 2. 마스터 파일 (진실의 출처)

```
c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md
```

- **버전**: v4.5 (2026-06-18)
- **git 추적**: ✅ commit `0bd252c`
- **크기**: 521,458 bytes / 15,848 라인
- **변경 이력**: v4.3 (Bulk 7건 신설) → v4.4 (GAP 14건 정정) → v4.5 (PR-A/B/C/D 코드 보강 + Swagger 정합)

---

## 3. 동기화 방법

### 3.1 매니저별 사본 위치 + 책임자

| 매니저 | 사본 위치 | 책임자 (가정) | 우선순위 |
|---|---|---|---|
| **NVRManager / VMS 공통** | `c:\workspace_app\Ironwall.Dotnet.Libraries\Docs\` | NVR 팀 | **즉시** |
| **VMS / 통합상황도** | `c:\source\repos\Dotnet.Rtsp.Viewer.Ui\Docs\` | VMS 팀 | 1순위 |
| **db_monitor / 통합 모니터링** | `c:\workspace_app\Dotnet.Monitoring.Solution\Docs\` | DBApi 팀 (이미 자료 보유) | 2순위 |

### 3.2 동기화 절차

각 사본 위치에서:

```powershell
# 1. 기존 파일 백업 (이력 보존)
$src = "c:\workspace_app\Ironwall.Dotnet.Libraries\Docs\GOP_Restful_Api_연동설계.md"
$backup = "$src.v4.2.bak"
Copy-Item -Path $src -Destination $backup

# 2. 마스터에서 복사
$master = "c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md"
Copy-Item -Path $master -Destination $src -Force

# 3. 검증
Get-Content $src | Select-String "문서 버전" | Select-Object -Last 1
# 출력 기대: "**문서 버전**: v4.5"
```

또는 PowerShell 한 줄:
```powershell
Copy-Item "c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md" "<사본 경로>" -Force
```

### 3.3 검증 체크리스트

동기화 후 각 사본에서 확인:

```powershell
# 푸터 v4.5 확인
(Get-Content "<사본 경로>" -Tail 3) -join "`n"
# 기대 출력:
# **문서 버전**: v4.5
# **최종 업데이트**: 2026-06-18

# 변경 이력 v4.5 행 존재 확인
Select-String -Path "<사본 경로>" -Pattern "v4.5 \| 2026-06-18" | Measure-Object | Select-Object Count
# 기대: Count = 1

# §5.6.9 본문 존재 확인 (DeviceGroup 벌크 해제)
Select-String -Path "<사본 경로>" -Pattern "5.6.9 디바이스 그룹에서 디바이스 벌크 해제" | Measure-Object
# 기대: Count = 1

# §7.3.9 본문 존재 (Camera 벌크 등록)
Select-String -Path "<사본 경로>" -Pattern "7.3.9 카메라 벌크 등록" | Measure-Object
# 기대: Count = 1
```

---

## 4. v4.3 → v4.5 주요 변경 요약 (매니저용)

### 4.1 신규 엔드포인트 7건 (v4.3 신설, v4.4/v4.5 정합화 완료)

| 엔드포인트 | 메서드 | 목적 |
|---|---|---|
| `/api/devices/groups/{group_id}/devices` | DELETE | DeviceGroup 벌크 해제 |
| `/api/integrations/event-mappings/{mapping_id}/cameras/bulk` | POST | Camera 벌크 등록 |
| `/api/integrations/event-mappings/{mapping_id}/cameras` | DELETE | Camera 벌크 해제 |
| `/api/integrations/event-mappings/{mapping_id}/speakers/bulk` | POST | Speaker 벌크 등록 |
| `/api/integrations/event-mappings/{mapping_id}/speakers` | DELETE | Speaker 벌크 해제 |
| `/api/integrations/event-mappings/{mapping_id}/lamps/bulk` | POST | Lamp 벌크 등록 |
| `/api/integrations/event-mappings/{mapping_id}/lamps` | DELETE | Lamp 벌크 해제 |

### 4.2 응답 envelope (v4.5 PR-D 정합)

```json
{
  "success": true,
  "message": "string",
  "data": {
    "mapping_id": 10,
    "created_ids": [701, 702],         // 매핑 row PK (event_mapping_cameras.id), 카메라 PK 아님
    "failed_items": [{ "index", "item", "error" }],
    "skipped_config_ids": [...],       // 이미 매핑된 기존 row PK (멱등)
    "not_found_config_ids": [...],     // FK 미존재 카메라 PK
    "message": "..."
  },
  "meta": {
    "timestamp": "2026-06-18T13:45:00+09:00",   // KST
    "request_id": null                 // X-Request-ID 헤더 시 채워짐
  }
}
```

### 4.3 v4.4 GAP 14건 핵심 (매니저 영향 큰 항목)

1. **`created_ids` / `config_ids`는 매핑 row PK** (`event_mapping_cameras.id`), 카메라 PK 아님 — §7.3.6 단건 DELETE path와 동일 의미
2. **`Request Body 6필드**: `camera_id`, `target_preset_id?`, `home_preset_id?`, `delay_time`, `is_enable`, `priority?` (옛 명세 `config_id, is_active` 2필드는 잘못)
3. **NATS 트리거명**: `trg_sync_eml_ins/del` (옛 `trg_sync_eml_insert/delete` 잘못)
4. **DeviceGroup path**: `/devices` (옛 `/members/bulk` `/members` 잘못)

### 4.4 v4.5 코드 보강 4건 (PR-A/B/C/D)

- **PR-A**: ConfigChangeLog 0건 케이스도 무조건 발행 (감사 가능성)
- **PR-B**: `skipped/not_found_config_ids` 실 분류 활성화 (이전 placeholder)
- **PR-C**: Lamp `color/buzzer_sound/light_mode` Pydantic Enum 전환 → `color="Purple"` 보내면 422 (옛 500)
- **PR-D**: EventMapping 6 핸들러 `response_model=ApiSingleResponse[T]` — Swagger UI에 응답 구조 정확 노출

---

## 5. 자동 생성 코드 (DTO) 재생성 권고

v4.5 명세 동기화 후 .NET 클라이언트 자동 생성 도구 (NSwag / OpenAPI Generator / Swashbuckle) 재실행:

```bash
# Swagger UI에서 OpenAPI JSON 다운로드
curl http://<dbapi-host>:8000/openapi.json > openapi_v45.json

# NSwag로 C# DTO 재생성
nswag openapi2csclient /input:openapi_v45.json /output:GeneratedDtos.cs

# 또는 OpenAPI Generator
openapi-generator-cli generate -i openapi_v45.json -g csharp -o ./generated
```

신규 응답 타입 7건:
- `ApiSingleResponse<DeviceBulkRemoveResponse>`
- `ApiSingleResponse<EventMappingCameraBulkCreateResponse>` (+ Unassign)
- `ApiSingleResponse<EventMappingSpeakerBulkCreateResponse>` (+ Unassign)
- `ApiSingleResponse<EventMappingLampBulkCreateResponse>` (+ Unassign)

---

## 6. v4.6 차수 진행 안내

DBApi 팀이 현재 v4.6 (잔존 GAP 12건 정리) 작업 진행 중:
- **P0** (즉시): JWT 시크릿 + user_password 마스킹 + CORS + .NET 사본 동기화 ← **본 문서가 이 작업**
- **P1**: PR-B 한계 보강 + pytest 11건 정합 + 단건 14건 response_model + dead code + AUTH_MODE
- **P2**: §7.5.7 재채번 + PRD git 추적
- **v4.7 분리**: JWT 회전 (jti 블랙리스트)

→ v4.6 명세 배포 시 (2026-06-23 예정) 본 가이드와 함께 매니저 재공지 예정.

---

## 7. 문의 / 회신

동기화 완료 후 다음 정보로 DBApi 팀에 회신 부탁드립니다:

| 매니저 | 사본 동기화 완료 일자 | 검증 통과 (4 체크) | C# DTO 재생성 완료 |
|---|---|---|---|
| NVRManager (Ironwall.Dotnet.Libraries) | ____-__-__ | ☐ | ☐ |
| VMS (Dotnet.Rtsp.Viewer.Ui) | ____-__-__ | ☐ | ☐ |
| 통합상황도 (Dotnet.Monitoring.Solution) | ____-__-__ | ☐ | ☐ |

회신처: 이기호 차장 (DBApi 팀)

---

**문서 버전**: v1.0
**최종 업데이트**: 2026-06-19
