# Session Context — GOP RESTful API Test Server

> 매 작업 후 갱신 (CLAUDE.md 규약). 다음 세션이 현재 상태를 빠르게 파악하기 위한 단일 진입점.
>
> 🤝 **멀티세션 동시작업 중 — 작업 전 반드시 [SESSION_COORDINATION.md](SESSION_COORDINATION.md) 읽기** (소유권 경계: ★`auth.py`는 WS-B 스케쥴링 세션 단독, WS-A RBAC 베이스 동결).

---

## 현재 차수 (HEAD)

| 항목 | 값 |
|---|---|
| **차수** | **v6.3** (2026-07-13 의식적 승격 — v6.0 후속 21 topic 확정) / v6.1 (2026-07-04, **리포트/서버 초기화 정합화** — 4 Issue + 1 부수결함 일괄 픽스, sample_servers 9카테고리 14대 Static 승격, JSON preview/HTML/PDF 필터 통일, audit/config/system 컬럼 확장 + user_sessions JOIN, N+1 제거) / v6.0 (2026-07-03, Async 대전환) / v5.4~v5.2 (이전 차수) |
| **HEAD commit** | `bf8333b` (2026-07-13, **release v6.3** 승격) — 그 위 audit_logs_authz·명세 5중싱크·review0710 P0/P1·session_token_jti(E1)·rate_limit·migration_tracking 누적 |
| **branch** | **`release/v6.3`** (2026-07-13 canonical 컷 — branch=버전 일치) — `release/v6.0` frozen 보존, 태그 `v6.3`, 후속은 `v6.3-{topic}` |
| **Container** | ✅ **v6.1 rebuild 완료** (2026-07-04) — `[OK] Sample servers created: 14` 확인, 9카테고리 전부 인스턴스 최소 1대. api-server / postgres / autoheal / gis-ingest / db-monitor healthy. |
| **DB** | PostgreSQL 16 + asyncpg / `servers` 14행 (v6.1 시드), `account_users` 3건, `report_generations` 24건 (v6.1 검증 리포트 포함) / `api_logs` 파티셔닝 v6.0 상태 계승. |

## 최신 작업 (2026-07-12 — 재감사 review0710 마감 + clone-deploy 검증)

> v6.1(아래) 이후 누적된 보안/세션 강화 작업의 최신 상태. auth.py 소유권은 2026-07-02 재해제됨(SESSION_COORDINATION.md) — 본 세션이 v6.0 세션/인증 작업 연속 소유.

- **재감사 P0 (commit baed794)**: 민감 GET 무인증 노출 차단(config-change-logs/system-events/event-statistics 라우터 가드) + refresh 회전 시 옛 access jti orphan 제거.
- **재감사 P1 (commits 99d0d70·fa641bd·3936414)**:
  - P1-01 logout 폐기를 `revoke_session_family`로 통일(access static TTL→stored exp, logout·refresh·revoke·force_logout 동일 원천).
  - P2-02 `tests/test_public_get_contract.py` — public GET allowlist 계약(구조 introspection + 라이브 무토큰 2xx 미노출). 10 passed.
  - P1-02 api-server를 `nats_external`(nats-core_nats-network) 연결 + `NATS_REVOKE_ENABLED`(기본 false) — dormant 배선.
  - P1-03 종결(무효): aiosqlite는 requirements-test.txt 정위치, DEBUG=release 미재현.
- **clone-deploy 동등성 검증**: 재빌드=git clone 동등 확인. `gop` 52테이블 = 43모델+schema_migrations+8 `api_logs` 런타임파티션. **옛 데이터 잔존 원인 = named volume `api-test-server_api-test-pgdata`(2026-03-16 생성)는 컨테이너/이미지 삭제로 안 지워짐** → 진짜 초기화는 `docker compose down -v`.
- **검증**: 라이브 E2E A01~A18 10/10, logout 재사용 401, P2-02 10/10, 재빌드 후 컨테이너 healthy·nats_external 연결·migrations v61~v64 적용. origin+gitea push 완료.
- **명세서 5중싱크 (commit a58c317, 규칙1·3 지연분 해소)**: `GOP_Restful_Api_연동설계.md` 롤링 항목(`v6.0 후속` 07-04~07→**~12**)에 `[보안 하드닝]` 그룹 추가(session_token_jti·migration_tracking·login_rate_limit·test_reproducibility·review0710 P0·P1) + §4.5 `EnumUserRole` **5종→2종(ADMIN/USER)** 정정 + 폐기역할(MAINTAINER/OPERATOR/VIEWER/GUEST) 필터·예시·권한컬럼 현행화. 
- **audit-logs 인가 강화 (commit ec95eca — 위 별건 해결)**: `audit-logs` GET(목록/상세)이 `get_current_account_user_optional`로 **전 인증 사용자** 열람 가능하던 것을 `require_perm_async("audit_logs","view")`로 강화 → config-change-logs 와 감사도메인 인가 **일관화**. 실측 무토큰 401·ADMIN 200·권한없는 USER **403**(두 엔드포인트 동일), A01~A18 10/10·계약 10 passed. 명세 §9 권한컬럼 + 롤링 체인지로그(`audit_logs_authz`) 동반 갱신(5중싱크).
- **v6.3 승격 + release/v6.3 컷 (2026-07-13)**: v6.0 후속 21 topic 확정 승격, 전 산출물 6.3.0 동기(Swagger/명세/README/main.py desc/CLAUDE.md), `release/v6.3` canonical 컷(release/v6.0 frozen), 태그 `v6.3`. 후속 태그 `v6.3-{topic}`.
- **계정 잠금 정책 완성 (2026-07-13, `v6.3-lockout_policy`, commit a8179a1)**: PM 점검(로그인 실패 안내 부재·자동해제 부재·unlock 재잠금 트랩) 대응. ㉰ 신규 세션설정 `lockout_duration_minutes`(기본30, 0=영구, 1~1440) 자동해제+카운트리셋 / ㉯ 로그인 오답 401 "`N회 중 X회 실패, M회 남음`" 메시지 + 구조화 `error.details`(failed_count/threshold/remaining/locked), 미존재계정·틀린이유 비노출(열거방지) / ㉱ `unlock_user` 카운트·locked_at·lock_reason 리셋. 5중싱크(5코드 + 명세 §9.2.2 실패응답·§9.8 설정필드·v6.3후속 체인지로그 + 재빌드). 실측 자동해제/리셋 통과, A01~A18 10/10·계약 10 passed. **세션 검증 3문 결론**: ①실패안내 없음→추가완료, ②잠금임계 세션설정 매핑 정상, ③session_enabled=false→10년(영속, SEC-05 보류) 확인.
- **✅ 감사 자동잠금/해제 기록 완료 (2026-07-13, `v6.3-audit_auto_lock`, commit 417becd)**: PM 프로세스 지적("구현 직행 말고 PRD")으로 **전 프로세스 준수**(analysis→PRD approved→plan→dev→test). 발견: auth.py `log_action` 0건 — 수동 lock/unlock만 감사되던 비대칭. 구현: auth.py 로그인에 best-effort `_audit_auto` 헬퍼 → **자동잠금 `USER_LOCKED`·자동해제 `USER_UNLOCKED`**(시스템 행위자 `actor_id=None`/`(system)`/`시스템(자동)`, 대상=USER) 기록. 실측 row 생성·정상로그인 audit 미발생(13→13)·best-effort·A01~A18 10/10·계약 10 passed. 5중싱크(auth.py+명세 §9.2.2·v6.3후속 체인지로그+재빌드), origin+gitea push. 산출물 `docs/prds`·`docs/plans`(gitignore=로컬). 프로세스 규율 [[feedback_prd_before_implementation]]. ※ phase 머신은 stale 플랜 IMPL 집계(2/31)로 test 전환 차단 — 실작업 무관 하네스 quirk.
- **✅ 프로필 사진 CRUD 정합화 완료 (2026-07-13, `v6.3-profile_photo_crud`, commit `1e01209`(fix)+`f1fd99f`(docs))**: PM 지적("프로필 사진 CRUD 문제") → Track A 검토(4결함 확인) → Track B 픽스. **①[P0]** `AccountUserSelfUpdate.photo_url` validator 허용 상대경로를 실존하지 않는 `/static/profiles/` → 실제 서빙 경로 `/api/users/photo/` 로 정정 — 서버가 응답에 채우는 default(`/api/users/photo/default.png`)를 클라가 되받아 `PUT /me` 시 **422** 로 거부되던 버그 봉합(서버가 emit 한 값을 서버가 못 받던 자가모순). **②[P1-D]** `DELETE /api/users/me/photo` 신설(파일 제거+photo_url=None→default 복귀, idempotent). **③[P1-U]** `_save_profile_photo` 재업로드 시 옛 파일 orphan 제거(`_delete_photo_file` 헬퍼 — default/외부URL/traversal 방어). **④[P2]** content_type(클라 위조 가능) 대신 Pillow magic-byte `_detect_image_ext` 로 실제 이미지 검증. 파일 2개(`app/schemas/user.py`·`app/routers/users.py`) + 단위테스트 `tests/test_profile_photo_crud.py` **14/14 PASS**(TDD Red→Green). 계정/계약 회귀 무영향(사전실패 4건 = `role=VIEWER` v5.3 레거시·UserGroup, photo 무관). 하네스 정상화 위해 `aiosqlite` 설치(requirements-test.txt 선언분). **5중싱크 완결**: ①코드(2파일+테스트, commit 1e01209) ②Swagger(라이브 6.3.0, `me/photo`=post+delete) ③명세서 §9.3 표·주석·부록+롤링 체인지로그(commit f1fd99f) ④이미지 재빌드(롤백태그 `pids-api-server:pre-profile_photo_crud`) ⑤컨테이너 재기동 healthy. 롤백포인트 git 태그 `pre-v6.3-profile_photo_crud`. **라이브 검증**: OpenAPI Swagger 6.3.0·DELETE summary="본인 프로필 사진 삭제" 확인. ※ 로그인 필요한 기능 스모크(PUT /me·DELETE 실호출)는 **admin123이 라이브 DB에서 거부**(비번 드리프트)로 보류 — 추측 시 잠금 위험이라 미시도, 내 테스트로 누적된 admin failed_count 리셋 원복. ⚠ 별건 관찰: auto-unlock이 `lock_reason` 미클리어(count/is_locked만 리셋) — lockout_policy 잔여(auth.py WS-B 소유). 미push(origin/gitea). [[feedback_profile_photo_storage]]
- **✅ NATS DBApi 발행 정합 완성 (2026-07-13, `v6.3-nats_sync_completion`, commit a1ba737)**: `docs/DBApi_API서버.md`(NATS 발행 명세) 대조 → 발행=**db_monitor/main.py**(gop_sync/gop_event LISTEN→NATS) + **app/db_triggers.py**(pg_notify). **전 프로세스 준수**(analysis→PRD approved→plan→dev→test→report→complete). 5건 정합: ①SYNC_PRESET `camera_id` 추가 ②SYNC_CAMERA_SETTING `resource_id`→`camera_id` ③SYNC_PROXY_SETTING `resource_id`→`server_id`(②③ 실버그: settings.id≠부모id) ④**SYSTEM_EVENT 신설**(system_events INSERT→신규 `gop_event` 채널→`all.event.system` Full-DTO) ⑤**ENCLOSURE_METRICS 신설**(db_monitor 주기 태스크 `ENCLOSURE_METRICS_INTERVAL` 기본10s→`gis.enclosure-metrics`). db_monitor `on_notify` body 통과 일반화. **NATS 실측 6종 subject+body 문서 100% 일치**(SYNC_SERVER 무회귀 포함), db-monitor healthy·오류0. 5중싱크(3코드+명세 v6.3후속 체인지로그+재빌드) + **.NET 클라 통지**(`docs/GOP_Server_API_nats_sync_completion_NOTIFY.md`=gitignore 로컬, 계약변경 요약은 체인지로그). origin+gitea push. **⚠ 계약변경(②③)** 클라팀 전달 조율 필요. 산출물 prd/plan/test/report(gitignore 로컬).
- **✅ Swagger description changelog 제거 (2026-07-13, `refactor(v6.3)`, commit `dac16b6`)**: PM 지적("Swagger changelog 지저분") → `app/main.py` FastAPI description 의 v6.0→v6.3 changelog 블록(주요 업데이트·endpoint 요약·후속 안정화·보안 하드닝) **~60줄 제거**, 현재 버전정보 4줄만 유지(API Version 6.3.0/branch/명세/전체이력 포인터). 코드·API 계약 불변(순수 설명 텍스트 — `git diff -w` 4/60·삭제줄 코드 0). 전체 이력은 명세서 ChangeLog·CHANGELOG.md(2,420줄) 단일소스 보존. ⚠ **CRLF 오염 재발**: Python text-mode write가 전 파일 LF→CRLF 플립(diff 4/60→820/876) → 감지·LF복원·`--amend`·`--force-with-lease`·재빌드로 clean 정정. 규율 [[feedback-windows-lf-write-discipline]]. 재빌드 후 라이브 Swagger 6.3.0·changelog잔재0·description LF 실측, origin+gitea push.
- **✅ GIS 서버측 집행 분석 검토 + 보강 PRD 착수 (2026-07-21, Track A→C)**: GIS 팀 `docs/Analysis/Grant_Enforcement_Server_Analysis.md`(2026-07-20, grant 시간기반 집행) 전수 검토 — **코드 인용 ~30건 실소스 1:1 대조 100% 일치**(라인번호까지), 핵심 판정(요청시점 라이브 계산→만료 시 정확 403 / `is_active` 스윕 비의존 / 경계초 `>`(auth) vs `<=`(grant_service) **정합**) **정확 확인**. 이슈 S-1~S-6 전부 실재. **추가 발견**: ①자연 만료 푸시 ≤10분 — 스윕(`grant_service.py:114`)이 만료 통지 **유일 소스**(S-2+S-3 종합, 문서 미강조) ②유효성 술어 **삼중 인코딩**(`_active_grants`/`_active_grants_async`/`grant_status`) → 경계 회귀는 async까지 assert 필요 ③스코프 경계(`PERMISSION_MAP` 미등록 경로 = token default-allow, `matrix_enforcer.py:105`). **검증 부채 상환 PRD(Draft)**: `docs/prds/grant-enforcement-hardening-prd.md` — FR5(경계초 회귀·token HTTP E2E·async_db 격리+ALLOW_DB_TESTS·async sweep 발행·문서회신), **app/ 런타임 무변경 원칙**, 정책 3건(NATS 활성/스윕단축/실시간푸시)은 Out of Scope 명시. V-04 주의(run_grant_sweep 자체 세션이 test DB 미지향 위험). 승인 대기(`node .claude/hooks/advance-phase.js approve prd "..."`). 프로세스 규율 [[feedback_prd_before_implementation]].
- **✅ Account 협업 원장 검토 + A/B/C 정합 산출물 (2026-07-21, Track A, PM "A B C 순서대로")**: GIS 클라 원장 `docs/Analysis/ACCOUNT_COORDINATION.md`(189줄, 클라측 2세션 living ledger, 07-13 최종) 전수 검토 — 서버 이관 항목 14건을 **실제 v6.3 코드와 1:1 대조**. **판정: ✅12 이미 반영(감사500 `audit_log.py:61/122` str화·구성원해제 `users.py:717-740` model_fields_set·failed_login 리셋 `auth.py:623`·unlock 리셋 `users.py:981-985`·자동해제 `auth.py:477`·실패응답 details `auth.py:539`·GET /grants `grants.py:163`·세션sweep `main.py:302/310`·SUPERSEDED evict `auth.py:572/642`·refresh부활차단 `auth.py:817`·레거시인증제거 `auth.py:34+`·Events통계인가 `event_statistics.py`) · ⚠1 실미해결(관리자 사진 `POST /users/{id}/photo` 부재) · 🟠1 OFF게이트(`NATS_REVOKE_ENABLED=False`)**. 산출물 3종: **(A)** PRD `docs/prds/admin-profile-photo-upload-prd.md`(Draft, gitignore 로컬 — 파이프라인 grant-enforcement PRD 점유로 gate 미강제·순번대기) **(B)** 클라 전달 통지 `docs/GOP_Server_API_Account_Coordination_Reconciliation_NOTIFY.md`(대조표+클라 액션) **(C)** 원장 상단 서버팀 정합 배너+완료분 코멘트. **코드 무변경(Track A/문서), `auth.py` 무접촉(WS-B 동결 준수).** 유일 실작업 후보=admin 사진 엔드포인트(PRD 승인 후 Track C). [[feedback_prd_before_implementation]] [[feedback_profile_photo_storage]] [[feedback_rbac_admin_gate_policy]]
  - **↳ admin 사진 엔드포인트 구현 완료 (2026-07-21, `v6.3-admin_photo_upload`, PM "추천대로 진행", 롤백태그 `pre-v6.3-admin_photo_upload`@a44784a)**: PRD Approved(OQ 확정: users:edit·POST+DELETE·전용 감사타입) → dev → test. **코드**: `app/routers/users.py`에 `POST`/`DELETE /users/{user_id}/photo` 신설 — 대상 조회(404)+`_assert_can_modify_admin_target`(base-ADMIN 상승가드)+`_save_profile_photo`/`_delete_photo_file` 재사용 + 감사 `USER_PHOTO_CHANGED`/`USER_PHOTO_DELETED`(행위자≠대상). 라우트 순서 안전(/me/photo·/photo/{file} 뒤). action_type=String(50) tolerant라 감사500 무재현 확인. **테스트**: `tests/test_admin_photo_upload.py` 가드4+라우트3 = **7 passed**(async HTTP는 라이브 E2E 전략=profile_photo_crud 동일). **5중싱크**: ①코드 ③명세서(§9.3.1 표·설명·요약·v6.3후속 체인지로그) ✅ / ②Swagger 라이브 6.3.0 ✅ / ④Docker 재빌드 ✅ / ⑤컨테이너 재기동 healthy ✅ = **5중싱크 5/5**(커밋 `a99f72a`, 롤백이미지 `pids-api-server:pre-admin_photo_upload`, 롤백태그 `pre-v6.3-admin_photo_upload`). 라이브 검증: Swagger 6.3.0·신규 `/users/{id}/photo`(post/delete) 등록·token모드 401 게이팅·`/me/photo` 회귀 OK. **인증 업로드 E2E 보류**(admin123 드리프트 재확인, 추측 잠금위험 + 공유DB 비번 무단변경 회피 — profile_photo_crud 선례 동일). origin/gitea push 미수행(사용자 확인 대기). 산출물 PRD/plan(gitignore 로컬). auth.py 무접촉. [[feedback_five_artifact_sync]] [[feedback_git_rollback_point]] [[feedback_one_day_one_version]]
- **✅ grant-enforcement-hardening PRD v2.0 통합 + 실행 시뮬 검증 (2026-07-21)**: PM 결정("어차피 다 해야 — 하나로 세트")으로 정책 3건(NATS활성 S-2·스윕단축 S-3·실시간푸시 4-a)을 **FR-06~08로 흡수**, **2-Phase**(P1 검증부채 app/무변경 · P2 런타임완결). **실행 시뮬 harness**(`docs/Analysis/grant-enforcement-sim/simulate.py` — 실제 `grant_status`/`is_valid_now`/`_role_group_allows` 호출, `REAL_AUTH_IMPORT=True`): 4단위 92 시나리오 **2회 결정론 동일·92/92 PASS**. ① Unit A 경계초 `valid_until==now`→EXPIRED+차단(is_active 무관, 48/48) = **GIS 핵심주장 실코드 확증** ② Unit B 합집합 집행(10) ③ Unit C enforce_matrix 24전수 → **미등록 경로=default-allow(4-c) 표면화** ④ Unit D 자연만료 통지 sweep-only 최악 10m → **FR-07 per-grant fire 정량 정당화**. 리포트 `docs/Analysis/grant-enforcement-sim/SIMULATION_REPORT.md`. PRD `docs/prds/grant-enforcement-hardening-prd.md` **v2.0 Draft — 승인 대기**. V-01 시뮬로 완료, V-02~07 잔여(default-deny=FR-09 승격 여부만 결정거리). [[feedback_validation_first]] [[feedback_prd_before_implementation]]
- **잔여(후순위)**: P2-01 secret/CORS(SEC-02 보류 영역), P3-01 invalid enum 422화, matrix_enforcer default-deny 전환(설계 결정), SEC-05(session off 10년 JWT 보류). 선재: TestClient lifespan 반복 시 log_consumer 이벤트루프 오류(하네스 격리 개선, 내 변경 무관).

---

## 이번 세션 (v6.1 — 2026-07-04)

> 사용자 리포트 다운로드 실측 → 4 Issue + 1 부수결함 발견 → 3중 감사 워크플로우로 원인 진단 → 일괄 픽스.

### 감사 결과 (Workflow w8fpw7jid)

| Issue | 결함 | 진단 |
|---|---|---|
| 1 | 사용자 현황 미반영 (JSON vs HTML/PDF 소스 이중화) | Critical — 필터 소스/라벨 소스 불일치 |
| 2 | 세션 목록 user_id=1로만 표시 | High — LEFT JOIN account_users 부재 |
| 3 | 로그인/감사/설정/시스템 로그 미표시 | Critical — 컬럼 노출 결함 (actor_name/resource_name/description/title) |
| 4 | Define 서버 미생성 (servers 0행) | Critical — init_db.py include_samples default False |
| 부수 B | N+1 쿼리 (탐지/장애) | High — 이벤트당 ActionEvent 개별 조회 |

### 픽스 (같은 사이클 통합)

- **Issue 4**: `init_server_data.py` `include_samples` default True로 뒤집기, `DEFAULT_SAMPLE_SERVERS` 14종 상수화 (9카테고리 전부, TRANSCODER/DB_API/NVR_API/SPEAKER_API/ENCLOSURE_API 5종 신규), sync/async 공용 `_build_sample_server_rows` 헬퍼
- **Issue 1(a)**: `ReportServiceAsync._resolve_range` 헬퍼 + 10 도메인 함수에 `start_date/end_date` keyword, 라우터에서 `generation.start_date/end_date` 전달
- **Issue 1(b)**: `L.label` 통일 (ROLE/SEVERITY/DETECTION/FAULT/DEVICE_CATEGORY/CONFIG_RESOURCE/CONFIG_ACTION/AUDIT_ACTION/AUDIT_RESOURCE/LOGIN_ACTION/RESULT/SYSTEM_EVENT/ACTION_TYPE)
- **Issue 1(c)**: event dates off-by-one 픽스 — `[_start.date() … end.date()]` inclusive
- **Issue 2**: `user_sessions LEFT JOIN account_users` → `[ID, 로그인ID, 사용자명, IP, 생성일, 만료일]`
- **Issue 3-a**: audit `COALESCE(actor_name, actor_login_id, '(system)')`
- **Issue 3-b**: config_change 8컬럼 확장 (`행위자, IP, 리소스명, 변경설명` 추가)
- **Issue 3-c**: system_events 6컬럼 확장 (`제목` 추가)
- **부수 B**: N+1 → `WHERE from_event_id.in_(event_ids)` 1회 batch fetch + dict lookup

### 검증 (2026-07-04, JSON preview 실측)
- 리포트 24 생성 → COMPLETED. `SYSTEM_CONFIG_GRID` 56행 8컬럼, `SYSTEM_AUDIT_GRID` 41행 폴백, `SYSTEM_EVENT_GRID` 6컬럼, `USER_GRID` "관리자" 라벨, `USER_SESSION_GRID` "admin/슈퍼사용자" 노출
- Docker startup 로그: `[OK] Sample servers created: 14`
- `SELECT category, count(*)` — 9카테고리 전부 최소 1대 (VMS 2, AI 3, STREAM 2, TRANS 1, BROKER 2, DB_API 1, NVR_API 1, SPEAKER_API 1, ENCLOSURE_API 1)

### 핵심 결정 (v6.1)
- **서버 인스턴스 Static seed 승격** — 이전 v4.6 정책("인스턴스는 옵트인") 명시적 뒤집기. Feedback memory `feedback_static_vs_runtime_seed` 갱신 완료.
- **감사 컬럼 확장 원칙** — nullable 필드는 COALESCE 폴백 필수, 모델에 있는 스냅샷 필드(actor/resource_name/description/title)는 리포트에 모두 노출.
- **필터 윈도우 통일 원칙** — 리포트 뷰 간 데이터 일치가 신뢰성의 기본. period_type→days 매핑 폐기, generation.start_date/end_date 단일 소스.

### 별도 트랙 (다음 사이클)
- config_change_logs actor_id 95% NULL — 서비스 레이어 로깅 헬퍼 감사 필요
- 두 리포트 파이프라인(ReportServiceAsync + build_master_data_async) 단일화 로드맵 — build_master_data_async를 정본으로 승격
- system_events 발화 소스(서버 헬스체크 워커) 미가동 — 별도 인프라 사이클

---

## 이전 세션 (v6.0 — 2026-07-03, Async 대전환 완결)

> v5.4 오전~오후 마감 → v6.0 오후~밤 Async 대전환(P0~P11) → v6.0 후속 6 Phases 밤~새벽 완결. **문제 A 근본 봉합** + Async 100%.

### v6.0 후속 6 Phases (밤~새벽)

1. **Quick Wins** — 저리스크 정합/미세 튜닝
2. **Init async** — 앱 부팅/초기화 경로 async 완전 이관
3. **Report Service async** — 정형/비정형 리포트 서비스 async(+Playwright/Chromium PDF 파이프라인 유지)
4. **A-7 #1 & #6 (batch queue + partitioning)** — `api_logs` 파티셔닝 + batch INSERT 큐 (문제 A 근본 봉합)
5. **RBAC 확대** — ~99 endpoint 매트릭스 등록 완료
6. **최종 검증** — 247/247 시나리오 회귀 PASS

### v6.0 원 P0~P11 (오후~밤, Async 대전환)

- SQLAlchemy 2.x 스타일 + asyncpg + `AsyncSession` 전환
- 41 라우터 async (100%)
- Dual-stack fixtures (pytest + pytest-asyncio) — sync/async 병존 인프라
- selectin_polymorphic 도입 (Device 6종 + Event 3종 상속 계층 로딩)

### v5.4 (오전~오후, 마감분)

- Reports RBAC 부착 (require_perm)
- `.env AUTH_MODE=token` 플립 완료 (클라 Bearer 동시배포 확인 후)
- 문서 A-7 저리스크 4건 정합
- 태그 `release/v5.4` 유지(안전점)

### 핵심 기술 결정 (v6.0)

1. **Dual-stack 원칙** — sync/async 병존. 라우터는 async, 기존 sync 유틸/픽스처 잔존 허용(단계적 이행). pytest는 sync+async fixture 병용.
2. **selectin_polymorphic 필수** — Device 6종(Camera/Lamp/Server/…) + Event 3종 등 상속 계층은 async 로딩 시 `selectin_polymorphic(*)` 강제(N+1 방지 + polymorphic identity 정확성).
3. **asyncpg tz-aware/naive 정합 규칙** — **naive KST 컨벤션**. asyncpg는 tz-aware datetime을 UTC로 변환하나, 서버 전역은 naive KST 유지(app_settings/DB 컬럼 일관). Aware ↔ Naive 경계에서 KST offset 명시 후 tzinfo=None 스트립.

---

## v5.2 (2026-06-30, .NET 이관 PRD 2종) — 이력 아카이브

> .NET 클라팀 이관 서버 PRD 3종(`docs/prds/PRD_GOP_Server_*.md`) 중 실행 2종 완료. 계약 4건 PM 확정.

### 완료 + 커밋 (로컬, tests/는 .gitignore라 미커밋)

- **P1 Force-Logout (Phases 0-5)** — `f00f7ca`(구조: token_blacklist id cross-dialect) + `4ff9a05`(FR-SVF-01~12) + `785c313`(FR-SVF-10 401 SESSION_REVOKED).
  - logout이 access+refresh 패밀리 무효화(구멍 차단) / force_logout last-ADMIN 가드 / sid 클레임(=UserSession.id)·login·refresh session_id / RevokePayload+HMAC 서명 / per-session NATS publisher(게이트 off) / 401 안정코드.
  - 로컬 27건 PASS.
- **P2 Session_Settings (FR-SVS-01~06)** — `73ecc5e`. app_settings + settings_service + GET/PUT /api/settings/session(require_admin) + auth.py 런타임 만료·잠금임계 + ConfigChangeLog 감사 + v55 마이그레이션. 로컬 11건 PASS.
- **전체 회귀 0**: 전체 스위트 174 failed(전부 사전 실패 = pydantic/env, P1+P2 전과 동일 -1) / 2244 passed.

### 확정 계약 4건 (클라 짝 PRD 통지 대상)

1. session_id = JWT `sid`(=UserSession.id) + login/refresh 응답 필드. refresh 시 sid 고정·jti 회전.
2. revoke subject = `sensorway.{unit}.account.{user_id}.session.{session_id}.revoke` (광역 금지).
3. payload = HMAC-SHA256 + 전용 REVOKE_SIGNING_KEY, canonical(sorted·compact·UTF-8·null 명시), reason=EnumLogoutReason.
4. revoked → 401 `error.code=SESSION_REVOKED`(403=권한부족 구분).

---

## 나머지 작업 (다음 세션) ★

> **2026-06-30 추가 세션**: ✅ **D 부분완료**(origin push 완료, **gitea만 인증실패로 잔여**) + ✅ **C 완료**([CONTRACT_GOP_Server_v5.2.md](../prds/CONTRACT_GOP_Server_v5.2.md), 골든벡터 실코드 계산) + ✅ **A 안전분 FR-SV-10 완료**(`b2f80c8`).
>
> ★ **A 실상 재검증(2026-06-30)**: 코드가 세션컨텍스트보다 앞섬. **RBAC 인프라 전부 구축됨**(`require_perm`·`require_admin`·`get_current_account_user_optional`·jti 검사 auth.py). **FR-SV-01**(세션 require_admin 4종 + 벌크 jti)·**FR-SV-05**(enums)·**FR-SV-06**(마지막 ADMIN FOR UPDATE 가드, users.py:529) **이미 구현 확인**. **FR-SV-10 이번 세션 구현**. **남은 핵심=파괴적 부분**: require_perm 8도메인 부착 + 30 라우터 이주(현 `.env AUTH_MODE=public`이라 부착 즉시 Bearer 없는 클라 401). require_perm은 reports.py만 부착됨.

| # | 작업 | 분량/유형 | 비고 |
|---|------|---------|------|
| **A** | **RBAC_Enforcement — 휴면 부착 완료, 활성화만 게이트** | 대형 / plan: [RBAC_Enforcement-prd-plan.md](../plans/RBAC_Enforcement-prd-plan.md) | ✅ **휴면(dormant) RBAC 부착 완료**: `c49f0a4`(구조 헬퍼) → `require_perm_optional` 추가 → `9a6624c`(27 write 데코레이터 부착) + `b2f80c8`(FR-SV-10). `require_perm_optional`=**AUTH_MODE=public 무집행(현 동작 보존)**·token 플립 시 활성. 도메인 회귀 0(사전실패 카운트 전후 동일), 단위 5/5 PASS. ★**P5 활성화=게이트**: 클라(.NET 3종) Bearer 동시배포 확인 후 `.env AUTH_MODE=public→token` 플립(분리 시 전원 401, 롤백=public 복귀). ✅ **P8 FR-SV-09 종결**(`de4266d`: user_groups POST/PUT/DELETE/GET-members require_admin). ✅ **P6 FR-SV-07 DB레벨 이미 충족**(`trg_audit_logs_immutable` v51 트리거 — DELETE/UPDATE 거부, FK익명화 예외); 잔여=export/retention 엔드포인트 + purge(purge는 WS-B sweep 영역). **P7 FR-SV-11(RTSP 마스킹)=반파괴·클라(Rtsp.Viewer.Ui) 조율 게이트로 보류**. |
| **B** | **Force-Logout 활성화 (FR-SVF-08 + 게이트)** | 인프라+조율 | NATS 발행 ACL(서버만 account.> publish, 클라 subscribe-only) + 클라 subject 매칭 확인(V-SVF-05) → 확인 후 `.env NATS_REVOKE_ENABLED=true` + 실 REVOKE_SIGNING_KEY 배포. **계약 §6 B-1~B-3에 명시** |
| ~~**C**~~ | ~~클라 회신용 계약 스냅샷 문서~~ | ✅ **완료** | `docs/prds/CONTRACT_GOP_Server_v5.2.md` — C1 sid / C2 subject / C3 payload+골든벡터 V1·V2 / C4 401 / P2 GET·PUT 스키마. 클라 짝 PRD 통지 + §6 B-1(subject 매칭) 회신 요청 |
| **D** | **푸시** | 소 | ✅ origin(GitHub) push 완료(7건). ⬜ **gitea 잔여** — 인증실패(http://192.168.202.160:3000). 차장님 직접: `! git push gitea feature/tracking-gis-ingest` |
| ~~**E**~~ | ~~배포(5-sync)~~ | ✅ **완료 (5/5)** | 도커 재빌드(`api-server`) + 컨테이너 재기동(healthy) + app_settings 라이브 + Swagger 5.2.0 라이브 + 태그 `v5.2-pre-deploy`/`v5.2-deployed` + 롤백이미지 `pre-v5.2` + **명세서 본문 v5.2 동기화(`36379e3`)**. 5중싱크 전부 충족. |
| **F** | (별도) 사전 테스트 실패 174건 | 별도 결정 | server_schema(pydantic AttributeError)·logs_router·config_change_log·test_config = pydantic 버전/환경 이슈, 본 작업 무관 |

---

## v4.7 + v4.8 차수 핵심 (이번 작업)

### v4.7 (2026-06-21) — Account 분석 + DELETE P0

- **Workflow 13 agent** Account/Auth/Session 전수 조사 (1.15M token / 12분)
- **이슈 113건** (critical 13 / high 38 / medium 39 / low 23) — Verdict **FAIL**
- 평균 완성도 62.5% / OWASP 41점
- DELETE P0 정정 4건: Lamp/DeviceGroup/Server/ServerCategory → `data: null`
- 보고서: `docs/Analysis/Account_Auth_Session_Analysis_v4.6.md` (16KB)
- 보고서: `docs/Analysis/Device_Delete_Response_Verification_v4.6.md` (9KB)
- 안전점: `pre-delete-sweep` @ `a9ef6d6`

### v4.8 (2026-06-22) — DELETE P1 sweep

- 클라이언트팀 보고서 v2 §6 P1 11 endpoint 일괄 정정
- EM 단건 DELETE 3건 (Phase 9 `'data': {}` 정책 정정)
- 일반 단건 DELETE 8건 (Reports/Users/UserGroups/UserSessions ×3/ServerMetrics/EnclosureMetrics)
- envelope 표준화: `{success, message, data:None}` + 정보는 message에 보존
- OpenAPI 전수 검증: dict 잔존 **0건**, NoneType 통일 22개

---

## v4.6 ~ v4.8 git 이력

```
5263317  fix(delete): P1 sweep — 11 endpoint                    ← HEAD / v4.8-final-stable
0b3ea1a  fix(delete): P0 4 endpoint (Lamp + DG + Server + SC)   ← v4.7-final-stable
a9ef6d6  docs(Analysis): Account/Auth/Session 분석              ← pre-delete-sweep
7bbc1be  docs(v4.6): CLAUDE.md 규약 정정 (session-context + INDEX)
3592a9d  docs(v4.6): README v1.9→v4.6 + CHANGELOG.md
536c0b8  feat(v4.6): Phase 10 시드 + pagination 검증
0d74cbc  docs(v4.6): 명세 헤더 정정
bb49462  refactor(v4.6): Camera Preset 단순화
bdf12c1  feat(v4.6): Critical 8건 + Camera Preset
```

---

## 안전점 5단

| 시점 | 태그 | commit |
|---|---|---|
| **v4.8 최종** | `v4.8-final-stable` | (신설) |
| v4.7 최종 | `v4.7-final-stable` | `0b3ea1a` |
| DELETE 작업 직전 | `pre-delete-sweep` | `a9ef6d6` |
| v4.6 최종 | `v4.6-final-stable` | `7bbc1be` |
| v4.5 마감 | `v4.5-final-stable` | `e7a611e` |
| v4.4 마감 | `v4.4-final-stable` | `050cf6d` |

---

## OpenAPI DELETE 전수 검증 (v4.8 완료 시점)

| 분류 | 카운트 |
|---|---|
| ✅ `ApiSingleResponse_NoneType_` (data: null 통일) | **22** |
| ❌ `ApiSingleResponse_dict_` 잔존 | **0** |
| 🟡 $ref 없음 (response_model 미부착) | 14 (v4.9+) |
| 🟡 `Union[dict,None]` events 4건 | (보고서 §6 미명시, 별도) |

---

## v4.9+ 잔존 작업

| 항목 | 분량 | 우선순위 |
|---|---|---|
| **RBAC 의존성 신설** (require_admin/require_role) | 6h | critical (v4.7 Top 권고 #1) |
| **세션 활성 검증** (get_current_account_user) | 6h | critical (Top 권고 #2) |
| **Refresh token type 검증** + rotation/blacklist | 8h | critical (Top 권고 #3) |
| **AuditLog 본문 보강** + 누락 해소 | 10h | high (Top 권고 #4) |
| **비밀번호 정책** + 변경 시 세션 무효화 | 15h | high (Top 권고 #5) |
| FR-11 JWT jti 블랙리스트 (logout 무효화) | 4.5h | 보안 |
| DELETE $ref 없음 14건 response_model 부착 | 별도 PRD | medium |
| Union[dict,None] events 4건 sweep | 30분 | low |
| M04 enclosure-metrics envelope (v4.7 분리됨) | 3h | high |

→ v4.9 ~ v5.0 **보안 강화 차수** 권고 (Top 5 모두 적용 시 ~45h)

---

## 매니저 통합 가이드 단일 진입점

| 정보 | 위치 |
|---|---|
| 빠른 개요 + 시드 명세 | [README.md](../../README.md) (v4.10) |
| 전체 차수 이력 | [CHANGELOG.md](../../CHANGELOG.md) |
| API 명세 | [GOP_Restful_Api_연동설계.md](../../GOP_Restful_Api_연동설계.md) (v4.10) |
| DB 스키마 | [GOP_스키마_전체.md](../GOP_스키마_전체.md) (v2.12) |
| Camera Preset 감시금지구역 | [v46_camera_preset_restricted_zone_guide.md](../v46_camera_preset_restricted_zone_guide.md) |
| **Account/Auth/Session 분석** | [Account_Auth_Session_Analysis_v4.6.md](../Analysis/Account_Auth_Session_Analysis_v4.6.md) |
| **DELETE 응답 검증 보고서** | [Device_Delete_Response_Verification_v4.6.md](../Analysis/Device_Delete_Response_Verification_v4.6.md) |
| docs/ 전체 인덱스 | [INDEX.md](../INDEX.md) |

---

## 최근 작업 흐름

```
2026-06-17  v4.3 마감 — Bulk API 7건 + ActionEvent 1:N
2026-06-18  v4.4 마감 — Phase 1~5 + multi-line Column + user_password 복원
2026-06-19  v4.5 마감 — minimal 6 그룹
            v4.6 마감 — Critical 8건 + Camera Preset + 시드 + pagination
2026-06-21  v4.7 마감 — Account 분석 (FAIL) + DELETE P0 4건
2026-06-22  v4.8 마감 — DELETE P1 sweep 11건 + Phase 8~12-7 (Event 정밀 + 불변성)
2026-06-24  v4.9 진행 — Phase 0 .NET 31건 회신 → Phase 1 Followup PRD → Phase 2~4 Auth/RBAC/Photo (17/17 PASS) → Phase 5 SEC-1 user_password 마스킹 (.NET v4.9 Review 회신, 8/8 PASS)
2026-06-25  v4.10 Phase 1 — SEC-1 마스킹 폐기 / 평문 회귀 (복호화 경로 부재, 차장님 결재 "그냥 평문으로 보내", 6/6 PASS)
            v4.10 Phase 2 — HTTPS 도입 (mkcert 폐쇄망) + Inno Setup rootCA 인스톨러 (6/6 PASS, 차장님 결재 "가장 간단·신뢰·폐쇄망")
            v4.10 Phase 2-add — PS2EXE Lite 인스톨러 2종 (certs/server_install.exe + client_install.exe, 차장님 결재 "두 개로 패키지해서 쉽게 쓸 수 있게")
2026-06-30  권한그룹 스케쥴링 분석 + PRD(Draft)
2026-07-02  v5.3 마감 — Legacy User DROP + AccountUser 통일 (GIS 팀 대응, 14/14 PASS)
2026-07-03  v5.4 마감(오전~오후) — Reports RBAC + AUTH_MODE=token 플립 + 문서 A-7 저리스크 4건
2026-07-03  v6.0 마감(오후~새벽) — Async 대전환 P0~P11 + 후속 6 Phases (Quick Wins / Init async / Report Service async / api_logs partitioning+batch INSERT / RBAC ~99 endpoint 매트릭스 / 최종 검증 247/247 PASS). 문제 A 근본 봉합. Docker autoheal 신설. 태그 v6.0.
```

## 활성 PRD / Plan / Phase

- **활성 브랜치**: `release/v6.0` (tip `61e46fe`, 태그 `v6.0`)
- **활성 PRD**: `docs/prds/grant-enforcement-hardening-prd.md` (**v2.0 Draft — 승인 대기**, 2026-07-21, 시뮬 92/92 검증완료)
- **활성 Plan**: 없음
- **현재 Phase**: analysis
- **Track**: C
- **다음 할 일**: **grant-enforcement-hardening PRD v2.0 승인**(정책 3건 흡수·시뮬 검증 완료) → 승인 시 plan 착수. 유일 결정거리 = default-deny(4-c)를 FR-09로 포함할지. 승인 명령 `node .claude/hooks/advance-phase.js approve prd "..."`
- **핵심 기술결정 (v6.0 확정)**:
  1. Dual-stack 원칙 — sync/async 병존 (단계적 이행)
  2. selectin_polymorphic 필수 — Device 6종 + Event 3종 상속 계층
  3. asyncpg tz-aware/naive 정합 — naive KST 컨벤션 유지

---

## 다음 세션 진입 시 권고

1. 이 파일(`session-context.md`) 읽고 위 **"나머지 작업 (다음 세션)"** 표(A~F) 확인
2. `git log --oneline -8` — v5.2 커밋 4건 확인 (HEAD `73ecc5e`)
3. 우선순위 권고: **D 푸시** + **C 클라 계약 통지** 먼저(소) → **B Force-Logout 활성화**(클라 subject 확인 필요) → **A RBAC 잔여**는 plan부터(대형, 클라 Bearer 동시배포 조율)
4. ★ 본 세션 작업은 **로컬 코드/테스트만** — 배포(E: 도커 재빌드·마이그레이션·태그) 미수행. `tests/`는 `.gitignore`(로컬 검증)
5. CLAUDE.md 매 응답 전 복잡도 판단 (Track A/B/C)

---

**문서 버전**: v6.0 / **최종 업데이트**: 2026-07-03 / **다음 차수 후보**: v6.1 pytest 스위트 async 마이그레이션 (전체 테스트 재작성)

## 세션 상태

- **활성 세션 수**: 1
- **현재 세션 ID**: ppid-55324
- **충돌 여부**: 없음
- **활성 세션 목록**: ppid-55324

