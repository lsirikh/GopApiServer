# 명세서(GOP_Restful_Api_연동설계.md) 최신화 감사 리포트

- **감사 일시**: 2026-08-04
- **방법**: 멀티에이전트 워크플로우 9에이전트(8 영역 병렬 + 종합), 245 엔드포인트·코드 전수 대조
- **대상**: `GOP_Restful_Api_연동설계.md` (16,700줄+ CRLF) vs 실제 코드(진실 소스)
- **판정**: **대체로 최신**. 단 "코드가 명세를 앞선" 3개 지점에서 계약 붕괴. 총 갭 **23건**(P0 4·P1 14·P2 5).

---

## 적용 완료 (커밋 반영)

| 항목 | 위치 | 조치 |
|---|---|---|
| ✅ P0 PUT detection 계약 | §6.1.5 | 요청 예시에서 `device_id`/`action_reported` 삭제(코드 `extra='forbid'`→422 유발) |
| ✅ P0 PUT malfunction 계약 | §6.2 | 요청 예시 `device_id` 삭제 |
| ✅ P0 PUT connection 계약 | §6.3 | 요청 예시+필드표 `device_id` 삭제 + PUT 불변 노트 |
| ✅ P1 EnumLogoutReason | §4(632) | `SELF_LOGOUT`(코드부재) → `DUPLICATE`(코드존재) |
| ✅ P1 EnumConfigResourceType | §4(750) | 17종→21종 + `LAMP`·`EVENT_MAPPING_LAMP`·`SUPPRESSION_SCHEDULE`·`SETTINGS` 추가 |
| ✅ P1 SESSION_REVOKED | §12.2 | 에러코드 표에 `401 SESSION_REVOKED` 행 추가 |

---

## 잔여 실행목록 (체계적 후속)

### P0 (계약 누락)
| # | 섹션 | 조치 |
|---|---|---|
| 1 | §10.4.1 + 상세 신설 | `POST /api/reports/generations/{id}/cancel` **완전 미문서**(reports:delete, PENDING/GENERATING만 취소, 종료상태 400). 표+상세절+§12/13 부록 추가 |

### P1 (필드·enum·인가 누락)
| # | 섹션 | 조치 |
|---|---|---|
| 2 | §9.2.2 | 로그인 Request Body에 선택 `client_id` + `X-Client-Id` 헤더 우선 규칙(1~64자 `[A-Za-z0-9._:-]`, invalid 무시, allow+self_replace 동일 client_id 교체) — 현재 ChangeLog에만 존재 |
| 3 | §9.5.2/9.5.3 | user-sessions 응답에 `login_id`·`role` 추가(코드는 반환, 명세 예시 누락) |
| 4 | §9.5.2/9.5.3 | `forced_by` 계약 불일치 — 명세는 `forced_by:null` 기재하나 코드 `_session_to_response` 미반환. **택1(코드 소유자 결정)**: 명세에서 제거 or 코드에 추가 |
| 5 | §9 신설 소절 | **중앙 권한 매트릭스 집행** 문서화: `enforce_matrix`+`PERMISSION_MAP`, token 모드만, ADMIN bypass, 401/403, `MATRIX_DENY_MODE`(off/observe/enforce)+public allowlist. PERMISSION_MAP 전항목 module:verb 부록 |
| 6 | §9.4.7·부록 | `EnumPermissionModule` 8종→**12종**(+ `map`/`broadcast`/`setup_system`/`setup_feature`). setup_system은 이미 §9.8 인가에 사용 중(자기모순) |
| 7 | §7.3 integrations 쓰기 | 인가 명시: `integrations:edit\|delete` 요구하나 **integrations가 EnumPermissionModule 미포함 → 비-ADMIN 부여불가 = 사실상 ADMIN 전용**. ★코드-명세 정합 이슈(코드측 enum 추가 검토 권고) |
| 8 | file-groups/thumbnails 쓰기 | 동일 — `files` 모듈 미포함으로 ADMIN 전용. 인가 컬럼+코드 정합 권고 |
| 9 | §6.1 말미/§6 공통 | `SYNC_DETECTION` 발행 계약 서브섹션(UPDATE/DELETE만, INSERT 미발행, `all.sync.detection`, from=DBApi). 현재 ChangeLog+bro커명세만 |
| 10 | §8.6.2 | GET metrics 파라미터 `start_date→start_time`, `end_date→end_time`(코드·§287 규약과 일치, 현재 명세 자기모순). 필터 기준 `created_at` 각주 |
| 11 | §8.6.4 | DELETE metrics `before_date`→`older_than_days`(int, 기본30, ge=1), 응답 `data:null`+message. 파라미터·응답형 전부 불일치(Enclosure 패턴 오복사) |
| 12 | §4 신설 4.10 | `EnumSuppression*` 4종 정식 정의 블록(TargetType/Side/EventScope/Status). §6.8 필드표의 "§4 참조" dangling 해소 |
| 13 | §6.8.6 | Error 목록에 `400`(대상 device/group id 미존재) 추가 |
| 14 | §10.4.1+부록 | `DELETE /api/reports/generations/{id}`(ChangeLog v5.4만), `GET .../detail.csv?type=`(ChangeLog v6.0만) 정식 표·부록 등재 |

### P2 (서술 보강)
| # | 섹션 | 조치 |
|---|---|---|
| 15 | §8.6(13661)+예시 | collected_at '저장' 서술 정정(코드는 UtcDateTime=UTC 저장), naive datetime 예시(offset 없는 `...000000`)를 `+09:00` 표기로 통일 |
| 16 | §6.8 필드표 | `recurrence_rule`(Phase2 미사용) 행 추가 |

---

## 반영 잘 된 것 (covered — 손댈 것 없음)
세션설정 5키(§9.8) · event_suppression 전체(bulk-delete·멀티타깃) · admin photo(§9.3) · detection_sync ChangeLog · proxy(§8.8) · tracking(§11) · datetime 전역규약(§3.4) · device polymorphic nested · frame_width/height.

---

## 최대 갭 3
1. **PUT replace 3종** — 명세 예시대로 호출 시 422(능동적 오문서) → **적용 완료**.
2. **중앙 권한 매트릭스 집행 미문서** — enforce_matrix/PERMISSION_MAP + integrations/files 인가 공백(#5~8).
3. **reports 생성 라이프사이클 3종** — cancel 완전 미문서, DELETE/detail.csv ChangeLog만(#1,14).
