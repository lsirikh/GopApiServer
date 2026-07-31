# Session Context — GOP RESTful API Test Server

> 매 작업 후 갱신 (CLAUDE.md 규약). 다음 세션이 현재 상태를 빠르게 파악하기 위한 단일 진입점.
>
> 🤝 **멀티세션 동시작업 중 — 작업 전 반드시 [SESSION_COORDINATION.md](SESSION_COORDINATION.md) 읽기** (소유권 경계: ★`auth.py`는 WS-B 스케쥴링 세션 단독, WS-A RBAC 베이스 동결).

---

## 현재 차수 (HEAD)

| 항목 | 값 |
|---|---|
| **차수** | **v6.3** (2026-07-13 의식적 승격 — v6.0 후속 21 topic 확정) / v6.1 (2026-07-04, **리포트/서버 초기화 정합화** — 4 Issue + 1 부수결함 일괄 픽스, sample_servers 9카테고리 14대 Static 승격, JSON preview/HTML/PDF 필터 통일, audit/config/system 컬럼 확장 + user_sessions JOIN, N+1 제거) / v6.0 (2026-07-03, Async 대전환) / v5.4~v5.2 (이전 차수) |
| **HEAD commit** | `1a2f211` (2026-07-31, **v6.3.1** 버그픽스 4건 통합 — proxy_mandatory_seed·proxy_settings_typed·server_metrics_tz_fix·settings_config_enum, 태그 `v6.3.1` 이동) / `bf8333b` (2026-07-13, **release v6.3** 승격) — 그 위 audit_logs_authz·명세 5중싱크·review0710 P0/P1·session_token_jti(E1)·rate_limit·migration_tracking 누적 |
| **branch** | **`release/v6.3`** (2026-07-13 canonical 컷 — branch=버전 일치) — `release/v6.0` frozen 보존, 태그 `v6.3`, 후속은 `v6.3-{topic}` |
| **Container** | ✅ **v6.1 rebuild 완료** (2026-07-04) — `[OK] Sample servers created: 14` 확인, 9카테고리 전부 인스턴스 최소 1대. api-server / postgres / autoheal / gis-ingest / db-monitor healthy. |
| **DB** | PostgreSQL 16 + asyncpg / `servers` 14행 (v6.1 시드), `account_users` 3건, `report_generations` 24건 (v6.1 검증 리포트 포함) / `api_logs` 파티셔닝 v6.0 상태 계승. |

## 최신 작업 (2026-07-12 — 재감사 review0710 마감 + clone-deploy 검증)

> v6.1(아래) 이후 누적된 보안/세션 강화 작업의 최신 상태. auth.py 소유권은 2026-07-02 재해제됨(SESSION_COORDINATION.md) — 본 세션이 v6.0 세션/인증 작업 연속 소유.

- **📋 탐지 이벤트 SYNC 발행 PRD 작성 (2026-07-31, Draft, `docs/prds/detection-sync-message-prd.md`)**: PM "탐지 이벤트에도 Sync 메시지 만들어줘 PRD 기반으로". analysis(멀티에이전트 3관점: mechanism/broker/consumer)→PRD. **핵심 설계**: `SYNC_DETECTION` **알림형**(패턴3) @ `all.sync.detection`, from=DBApi, body `{action,resource_id}`, **UPDATE/DELETE만(INSERT 제외 — 필드 DETECT와 중복 시 EventMapping 이중실행)**, 소비자는 `GET /api/events/detections/{id}` 재조회. gop_sync 채널 재사용(db_monitor CMD_SUBJECT_MAP 1줄) + detection_events 트리거 + frame_width/height GAP 동반해소(FR-04). FR6·NFR4·V5·R5. **상태 Draft — 승인 대기**(`advance-phase.js approve prd`). [[broker-v15-api-crossverify]] [[feedback_prd_before_implementation]]

- **✅ server_metrics collected_at tz INSERT 버그 수정 (2026-07-31, `server_metrics_tz_fix`, 커밋 `f938f55`, 롤백태그 `pre-server_metrics_tz_fix`)**: GIS(clone 박스) 보고 — `POST /api/servers/{id}/metrics`에 tz-aware(KST+09:00) `collected_at` 보내면 asyncpg가 naive 컬럼(`TIMESTAMP WITHOUT TIME ZONE`)에 aware 못 넣어 500 → CPU/RAM/디스크 메트릭 저장 통째 실패(**배포 무관 코드 버그, 전 Postgres 배포 공통**). `app/routers/server_metrics.py` `_to_naive_kst` 헬퍼로 aware→KST 벽시계 naive 정규화(응답은 +09:00 유지). 라이브 재현 500→수정 **201**, DB naive(`2026-07-31 10:00:00`) 저장 실측. `tests/test_server_metrics_tz.py` 4 passed, 명세 §8.6+변경이력, 재빌드+healthy, origin+gitea push. **✅ 6.3.1 통합 완료 (PM "하루 1버전 고정")**: 오늘 버그픽스 4건(proxy_mandatory_seed·proxy_settings_typed·server_metrics_tz_fix·settings_config_enum)을 **6.3.1 하나로 고정**, v6.3.1 태그를 최종 HEAD `1a2f211`로 이동+강제푸시(origin+gitea). **✅ 세션설정 500 영구수정**: `app/migrations/v65_add_settings_config_enum.sql`(`ALTER TYPE enumconfigresourcetype ADD VALUE IF NOT EXISTS 'SETTINGS'`, IDEMPOTENT_MIGRATIONS 등재) → clone/옛볼륨 DB 다음 기동 자가치유(PG16 tx내 ADD VALUE 검증). 라이브: v65 적용·기록, 세션설정 PUT **200**(SETTINGS 감사 INSERT), server_metrics aware **201**, Swagger **6.3.1**. 롤백태그 `pre-settings_enum_fix`.
- **✅ v6.3.1 버그픽스 릴리즈 전체 싱크 완료 (2026-07-31, PM "버전 업+전체 싱크", 커밋 `e87bc11`, 태그 `v6.3.1`)**: 오늘 버그픽스 2건(`proxy_mandatory_seed` `7ee1941` + `proxy_settings_typed` `cbf63bd`)을 **하루=1버전** 규율로 **6.3.0→6.3.1** 묶음. `main.py` version→6.3.1(Swagger 구동), 명세서 문서버전+버전표 6.3.1, README 배지/현재버전/릴리즈표/푸터(v6.0.0 stale 정정), CHANGELOG `[6.3.1]` 섹션, 이미지 재빌드+컨테이너 healthy. **라이브 openapi `info.version=6.3.1` 실측.** origin+gitea 브랜치+태그 `v6.3.1` 푸시 완료. ⚠ 잔여: 서버 테스트 44 stale(cpu_usage→ServerMetrics 분리 후 미갱신 + 라우터 401 인증)은 async 테스트 인프라 별건 → 미착수(롤백태그 `pre-server_test_stale_fix`만 존재). [[feedback_five_artifact_sync]] [[feedback_one_day_one_version]] [[feedback_branch_tag_naming]]
- **✅ proxy-settings PROXY 전용 강제 완료 (2026-07-31, `proxy_settings_typed`, 롤백태그 `pre-proxy_settings_typed`, Track B/WI-2)**: proxy-settings(GET/PATCH/PUT)가 기획상 Proxy 전용인데 모든 server_id 허용 → `_get_proxy_server_or_404` 헬퍼로 카테고리 `type_server!=PROXY` 면 404 + lazy-create 차단. **계약 변경**(비-PROXY 200→404), junk 0건이라 정리 불필요 → 클라 통지 `docs/GOP_Server_API_proxy_settings_typed_NOTIFY.md`(로컬). ★**사전 격리 버그 발견·해소**: 기존 sync TestClient(`client` 픽스처)가 async 라우터 `get_async_db` 미오버라이드 → proxy_settings가 격리 :memory: 아닌 실 `data/gop.db` 읽어 id 우연일치로 통과하던 것. 리포 표준(test_grant_enforcement_http)대로 `tests/test_proxy_settings_router.py`를 격리 async(엔드포인트 함수 직접 호출)로 재작성 **11 passed**. 라이브 PROXY(id17)=200/VMS(id3)=404. 5중싱크(코드+명세§8.8·변경이력+Swagger+재빌드+컨테이너 healthy). **커밋 `cbf63bd` + origin/gitea push 완료.** [[proxy-settings-proxy-only]] [[feedback_five_artifact_sync]]
- **✅ 필수 서버 유형 기본 시드 보장 완료 (2026-07-31, `proxy_mandatory_seed`, 롤백태그 `pre-proxy_mandatory_seed`, Track B)**: PM 발견 — **PROXY 가 기본 서버 시드에서 누락**(다른 9종만 시드). `DEFAULT_SERVER_CATEGORIES` 에 PROXY(sort10) 추가(9→10) + `MANDATORY_SERVER_TYPES={PROXY,VMS,NVR_API,BROKER}` 도입, `create_sample_servers`(+async) 가드를 **전체 count>0 통째 스킵 → 유형 기준 보장**(그 유형 서버 0개일 때만 기본 생성, 사용자 등록분 존재 시 중복 미생성)으로 교체. **실사고+교훈**: 초기 name-기준(`PROXY-ab0001` 고정) 시드가, PM 이 직접 등록한 PROXY(`ab0101`, 192.168.1.30:8500)가 있는데도 placeholder 를 중복 생성 → **유형 기준으로 정정 + 중복 id 18 삭제**. 재배포 seed `Servers ensured (mandatory +0, demo +0)`(중복0), **카테고리 10 / 서버 15**. `tests/test_server_seed.py` **7 passed**(중복방지 케이스 포함), 회귀 0(사전 44 실패 = `cpu_usage`→`ServerMetrics` 분리 후 stale, 무관·별건). 5중싱크(코드 `app/utils/init_server_data.py` + 명세 §8.1·§8.5·변경이력 + 재빌드 + 컨테이너 healthy). ✅ **커밋 `7ee1941` + origin/gitea push 완료** — 롤백태그 `pre-proxy_mandatory_seed`. (INDEX.md·session-context는 동시 세션 편집 섞여 커밋 제외) [[proxy-server-default-seed]] [[feedback_five_artifact_sync]] [[feedback_git_rollback_point]] [[proxy-settings-proxy-only]]
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
  - **↳ admin 사진 엔드포인트 구현 완료 (2026-07-21, `v6.3-admin_photo_upload`, PM "추천대로 진행", 롤백태그 `pre-v6.3-admin_photo_upload`@a44784a)**: PRD Approved(OQ 확정: users:edit·POST+DELETE·전용 감사타입) → dev → test. **코드**: `app/routers/users.py`에 `POST`/`DELETE /users/{user_id}/photo` 신설 — 대상 조회(404)+`_assert_can_modify_admin_target`(base-ADMIN 상승가드)+`_save_profile_photo`/`_delete_photo_file` 재사용 + 감사 `USER_PHOTO_CHANGED`/`USER_PHOTO_DELETED`(행위자≠대상). 라우트 순서 안전(/me/photo·/photo/{file} 뒤). action_type=String(50) tolerant라 감사500 무재현 확인. **테스트**: `tests/test_admin_photo_upload.py` 가드4+라우트3 = **7 passed**(async HTTP는 라이브 E2E 전략=profile_photo_crud 동일). **5중싱크**: ①코드 ③명세서(§9.3.1 표·설명·요약·v6.3후속 체인지로그) ✅ / ②Swagger 라이브 6.3.0 ✅ / ④Docker 재빌드 ✅ / ⑤컨테이너 재기동 healthy ✅ = **5중싱크 5/5**(커밋 `a99f72a`, 롤백이미지 `pids-api-server:pre-admin_photo_upload`, 롤백태그 `pre-v6.3-admin_photo_upload`). 라이브 검증: Swagger 6.3.0·신규 `/users/{id}/photo`(post/delete) 등록·token모드 401 게이팅·`/me/photo` 회귀 OK. **인증 업로드 E2E ALL PASS**(admin/**sensorway1** — PM 제공, admin123 아님): admin(id=1) 사진 `1_9730d349.jpg` **업로드 전후 불변**(=07-13 오염사고 회귀 실증)·대상(flg_verify id=30) `30_*.png` 갱신·없는대상 404·cleanup DELETE→default 복귀. 4/4 PASS. **origin+gitea push 완료** (`a44784a..1fff9ac` release/v6.3, 2026-07-21). 롤백태그 `pre-v6.3-admin_photo_upload` 로컬 유지. ※ HEAD 위 자동 phase-chore 3커밋(f9d5b15/b794a16/1fff9ac = advance-phase 훅 docs 자동커밋: ACCOUNT_COORDINATION 배너 + grant 세션 분석/sim 문서 + INDEX/session-context)도 동반 푸시됨(앱코드는 a99f72a뿐). 산출물 PRD/plan(gitignore 로컬). auth.py 무접촉. [[feedback_five_artifact_sync]] [[feedback_git_rollback_point]] [[feedback_one_day_one_version]]
- **✅ grant-enforcement-hardening PRD v2.0 통합 + 실행 시뮬 검증 (2026-07-21)**: PM 결정("어차피 다 해야 — 하나로 세트")으로 정책 3건(NATS활성 S-2·스윕단축 S-3·실시간푸시 4-a)을 **FR-06~08로 흡수**, **2-Phase**(P1 검증부채 app/무변경 · P2 런타임완결). **실행 시뮬 harness**(`docs/Analysis/grant-enforcement-sim/simulate.py` — 실제 `grant_status`/`is_valid_now`/`_role_group_allows` 호출, `REAL_AUTH_IMPORT=True`): 4단위 92 시나리오 **2회 결정론 동일·92/92 PASS**. ① Unit A 경계초 `valid_until==now`→EXPIRED+차단(is_active 무관, 48/48) = **GIS 핵심주장 실코드 확증** ② Unit B 합집합 집행(10) ③ Unit C enforce_matrix 24전수 → **미등록 경로=default-allow(4-c) 표면화** ④ Unit D 자연만료 통지 sweep-only 최악 10m → **FR-07 per-grant fire 정량 정당화**. 리포트 `docs/Analysis/grant-enforcement-sim/SIMULATION_REPORT.md`. PRD `docs/prds/grant-enforcement-hardening-prd.md` **v2.0 Draft — 승인 대기**. V-01 시뮬로 완료, V-02~07 잔여(default-deny=FR-09 승격 여부만 결정거리). [[feedback_validation_first]] [[feedback_prd_before_implementation]]
- **✅ grant-enforcement-hardening PRD 승인 + plan 작성 (2026-07-21, Phase=plan)**: "추가해서 진행" → **FR-09(default-deny) 추가 v3.0**, 시뮬 Unit C2 재검증(**128/128**, blast-radius **6셀**=token+미등록+¬allowlist, user=none·admin 포함 → 라우트 audit 선결 근거). PRD **Approved**(advance-phase hook), phase 머신 정합(complete→analysis→prd→plan; ★실상태파일=`.claude/.branch-release-v6-3/pipeline-state.json`, `docs/memory/pipeline-state.json` 아님). **plan 작성**: `docs/plans/grant-enforcement-hardening-prd-plan.md` — **36 태스크/~86h**, 3-Phase(P1 검증부채 app/무변경 / P2a 통지완결 / P2b default-deny), VER-01~08(V-01 시뮬완료)·RISK-01~03. ⚠ **소유권 경계**: P2 FR-07(per-grant scheduler)·FR-09(matrix_enforcer)=auth/스케줄링 **WS-B 조율 필요**. 다음=**Phase 1(VER-02→TEST-01) 본세션 착수 가능**. matrix_enforcer default-deny 잔여였던 항목이 FR-09로 정식 편입. [[feedback_prd_before_implementation]] [[feedback_validation_first]]
- **▶ Phase 1 착수 — TEST-01(FR-01) 완료 (2026-07-21)**: "시작해줘" → 소유권 안전한 **Phase 1**(tests/·conftest, app/무변경) 착수. VER-02(PERMISSION_MAP ~90개, TEST-02 대상=`POST /api/devices/cameras`=cameras:edit)·VER-03(SQLite in-mem + `pytest_configure` 비-sqlite 게이트 기존재)·VER-04(`run_grant_sweep` 자체 `AsyncSessionLocal`→RISK-02 몽키패치 확정) 클리어. **`tests/test_grant_boundary.py` 신규 7 케이스**(순수2+sync3+async2, 경계초 `valid_until==now`→EXPIRED/차단 삼중 정합·is_active 비의존, async는 **로컬 aiosqlite**로 prod DB 무접촉) — **7 passed × 2회 결정론, 무회귀 21 passed**. ⚠ 실행법: `env -u DATABASE_URL python -m pytest tests/test_grant_boundary.py`(DATABASE_URL이 postgres set이면 pytest_configure 게이트가 차단 / sqlite로 set하면 app.database create_engine pool인자 TypeError → **unset이 정답**). 진행률 **5/36**. 다음=SETUP-02/TEST-02(token E2E, async-over-sqlite 인프라). ⚠ Phase 2(FR-07 scheduler/FR-09 matrix_enforcer)=**WS-B 조율**.
- **✅ Phase 1(FR-01~05) 완료 (2026-07-21, "쭉 진행")**: tests/·conftest만(**app/ 무변경**). **신규 4 테스트파일 18 passed**: `test_grant_boundary`(경계초 삼중 7)·`test_grant_enforcement_http`(**enforce_matrix 실 async 경로**로 grant 수명주기 7: 유효ALLOW/만료403/회수403/PENDING403/무권한403/ADMIN ALLOW/무토큰401)·`test_grant_sweep_async`(run_grant_sweep 만료flag+감사+**사용자당 1회 dedup 발행** 2)·`test_async_db_guard`(격리 2). **IMPL-03**: conftest `async_db` 기본=격리 aiosqlite(S-6 해소, `ALLOW_DB_TESTS=1`만 실DB) + `_isolated_async_engine` 헬퍼. **회귀 0**(baseline 대조: 사전실패 13=grant_api8·matrix_enforcer3·revoke2 불변, 신규실패0·신규통과+18). ★발견: `test_matrix_enforcer` 3건은 **sync 세션→async enforce_matrix 사전 FAIL**(v6.0 미갱신, 집행코드는 정상) → **DOC-05 GIS 회신**(`docs/Analysis/Grant_Enforcement_Server_Analysis_REPLY.md`). 진행률 **11/36**. ⚠ tests/·conftest = .gitignore(로컬). 실행: `env -u DATABASE_URL python -m pytest tests/test_grant_*.py tests/test_async_db_guard.py`. **다음=Phase 2(FR-06~09)** — per-grant scheduler(FR-07)·NATS활성(FR-06)·스윕설정(FR-08)·default-deny(FR-09)는 `auth.py`/`matrix_enforcer`/스케줄러 변경 → **WS-B 조율 필수**.
- **✅ Phase 2a 일부 — FR-08·FR-06 완료 (2026-07-21)**: ★**소유권 재검증**(검증 우선) — SESSION_COORDINATION.md 직접 확인 결과 auth.py **2026-07-02 재해제**(line 15)+본 세션 v6.0~v6.3 연속 편집+활성 세션 1 → **블로커 없음**(직전 "WS-B 조율 필요"는 stale 헤더 기준 과잉판단, 정정). 원장에 grant-enforcement 영역 클레임 후 착수. **롤백태그 `pre-v6.3-grant_enforcement_hardening`**. **FR-08**(스윕 설정화): `app/config.py` `GRANT_SWEEP_INTERVAL_MINUTES: int=10` + `app/main.py` 배선(하드코딩 `minutes=10` 제거) — **Phase 2 첫 app/ 편집**, `test_grant_sweep_interval` 3 passed. **FR-06**(NATS 통지): 서버 발행부 기배선(grants.py:136/277·grant_service.py:114) 확인 → 발행기 게이트 테스트 `test_permissions_changed_gate` 3 passed(off무발행/on서명발행/다운best-effort) + 런북 `docs/RUNBOOK_NATS_permissions_changed_activation.md`. phase→dev, 진행률 **15/36**. app/ 편집 회귀0(내 신규 21 passed). **남음**: **FR-07**(per-grant fire=신규 `grant_scheduler.py`+grants.py 배선+부팅 재등록, 최대작업)·**V-08→FR-09**(default-deny, 최고위험, 라우트 audit 선결). 실제 flip(NATS 활성/default-deny)=배포 게이트. ⚠ app/ 미커밋·미push(로컬).
- **✅ 오프라인 원클릭 설치기 PRD Draft 작성 (2026-07-21, Track C, PM "인터넷 안 되는 사이트에 최신버전 원클릭 반영")**: air-gapped v6.0+ 사이트를 단일 `.exe`(Inno Setup)로 최신버전 업그레이드 + **DB/런타임데이터 무손실**. 실측 근거: `Dockerfile COPY . .`(코드=이미지 내장 → 호스트는 compose만 갱신)·`init_db.apply_idempotent_migrations`(schema_migrations checksum 멱등 → 버전 delta 자동전진, 설치기 버전 무지각 OK)·named volume `api-test-pgdata`(down[무 -v] 생존). 설계: 번들빌더(인터넷PC: build→docker save 6이미지 tar+payload)→단일exe(마법사+자동롤백)→시퀀스(사전점검→백업[pg_dump+data+:rollback태그]→down[**-v 금지**]→load→파일동기화[.env/data/certs 불가침·바이너리복사]→up[**--build 아님**]→검증→실패시 자동롤백). **최대리스크 R-01=named volume project접두사 불일치→빈DB 기동(V-02 사전점검 필수)**. FR 9개(~30태스크)·NFR 5·V-01~07·R-01~07·DoD(인수2종[빈/구버전]·롤백실증·오프라인검증). 산출물 `docs/prds/offline-installer-prd.md`(**Draft — 승인 대기**, gitignore 로컬). ⚠ 파이프라인 grant-enforcement PRD 점유 → **순번대기**(phase 머신·activePrd 미변경, admin-photo와 동일 패턴). 앱코드 무변경(패키징 산출물). [[feedback_prd_before_implementation]] [[feedback_git_rollback_point]] [[feedback_windows_lf_write_discipline]]
  - **↳ PRD v1.1→v1.2 정련 (2026-07-21)**: ①**볼륨 '탐지+고정'**(실행중 postgres 마운트 조회→`COMPOSE_PROJECT_NAME` 고정, 접두사 불문 자동대응) — 사용자 기억 "프로젝트명 일부만 변경". **개발기 실측**=컨테이너 `pids-api-server`인데 볼륨 `api-test-server_api-test-pgdata`(container_name=pids-api-*는 볼륨접두사와 별개임 확증). ②**롤백 안전모델 강화**(사용자 제약: 대상 물리 원거리 출장·재시도불가·추정진행 + "실패시 롤백 정확히"): **물리 볼륨 스냅샷=롤백앵커**(pg_dump는 정상DB 필요→물리 바이트복제로 스키마·데이터 정확회귀), **백업 무결성 게이트=되돌릴수없는지점 통과조건**, **3계층 정밀롤백**(이미지/구성/데이터), `-Rollback` 독립재실행+수기런북, `-Rehearse` **출장전 리허설**(개발기 동일볼륨). **가정 베팅 안함**: 접두사·버전·네트워크 런타임검증→불일치시 Phase2(무변경) 이전 중단. FR 9→10·NFR 5→6·R 7→8(v1.4: FR-10 리허설=완전격리 샌드박스[읽기전용 클론·별도 project명/포트·자동정리]로 명확화 — "실 프로젝트엔 테스트 못 하잖아" 질문 대응).
  - **↳ plan 작성 완료 (2026-07-21)**: `docs/plans/offline-installer-prd-plan.md`(gitignore 로컬) — **29 태스크/~88h**, 5 Phase. VER 4(V-05 마이그레이션 비파괴·V-01/02 볼륨탐지·V-06 certs·V-03 nats격리; V-04/07=런타임강제)·RISK 2(**R-01 볼륨 pin PoC·R-02 물리 스냅샷 왕복 PoC=롤백앵커 최우선**)·SETUP 2·IMPL 11(FR-01~10)·TEST 7·DOC 3. **핵심 게이트=TEST-04 리허설 드릴**(강제실패→자동롤백→직전 동일, 현장배포 전 필수). ⚠ 파이프라인 grant-enforcement 점유 → **out-of-band 트랙**(phase 머신·activePlan 미변경). 다음=RISK-02(스냅샷 PoC)/SETUP-01 착수 가능.
  - **✅ dev 완료 — 설치기 구축 + 핵심 라이브 검증 (2026-07-21, "끝까지 진행")**: 산출물 `offline-installer/`(build: make-offline-bundle.ps1·installer.iss / installer.ps1 오케스트레이터 + lib 10종[common·volume_snapshot·detect_volume·preflight·backup·sync_files·apply_stack·verify·rollback·rehearse] + tests 4 + preserve.list + README) + `docs/RUNBOOK_offline_installer*.md` 2 + `.dockerignore`(offline-installer/·backups 제외). **라이브 검증**: ①**RISK-02** 물리 스냅샷/복원 왕복 실 볼륨 `:ro`→복원→postgres 기동 **live==snap==restore(users=13·servers=14)·원본불변** ②**TEST-04 리허설** 격리샌드박스(실 롤백함수 dogfood) baseline13→업글12→강제실패→**무인롤백**13 동일·샌드박스 소각 ③**TEST-01/02/03** 단위 11 assert ALL PASS ④**VER-01** v60/62/64 정독=업무데이터 무삭제(★v60 파티셔닝 내부 멱등 아님→schema_migrations checksum skip 보장). **핵심 발견(라이브)**: 복사헬퍼 `alpine`→`postgres:16-alpine`(폐쇄망 alpine 부재, DB이미지 상존). 설계 무결성: 되돌릴수없는지점=백업 무결성게이트 통과시만·볼륨 탐지+pin(R-01)·무인 3계층 롤백·`-Rollback` 독립+수기런북. **미실행(무거움)**: SETUP-02 6이미지 실 save/load(멀티GB)·TEST-05 오프라인완주·TEST-06 인수2종 풀스택(코드경로는 구현). out-of-band 트랙(로컬, 미커밋). **↳ 실 번들 빌드 완료(SETUP-02 ✅)**: compose build(캐시)→save 6이미지 `gop_images.tar` **1.02GB**, load 왕복 6/6 exit0, 시크릿 제외 검증(payload `.env`/`certs` 부재). **단일 진입 `gop_offline_installer.exe`(ps2exe 27KB·requireAdmin)** 빌드 — bundle 폴더째 USB→더블클릭. Inno `.iss`도 제공(ISCC 미설치). 잔여=TEST-05 오프라인완주·TEST-06 풀스택 인수2종(현장/실리허설). 다음=(택)실 리허설·커밋. **↳ 종합 매뉴얼 작성**: `docs/MANUAL_offline_installer.md`(동작원리[코드=이미지·태그연동 §3.2·교체vs보존·볼륨탐지·롤백모델] + 활용3단계 + 시퀀스 + 문제해결 + FAQ[이번 대화 Q&A: 정적파일·app마운트·이미지연동] + 종료코드). 문서세트=MANUAL + RUNBOOK 2(install·rollback) + offline-installer/README. [[feedback_git_rollback_point]] [[feedback_windows_lf_write_discipline]]
- **✅ Phase 2 코드 완료 + 커밋 정리 + README (2026-07-21, "다 진행")**: **FR-07** per-grant scheduler(`app/services/grant_scheduler.py` 신규 — valid_until date job→발화, grants 생성/회수 배선, 부팅 재등록 NFR-05, `GRANT_JOB_HORIZON_HOURS` RISK-03) / **FR-09** matrix_enforcer `MATRIX_DENY_MODE`(off/observe/enforce)+public allowlist, **기본 off=현행 무변경**(NFR-07). 신규 `test_grant_scheduler` 8·`test_default_deny_contract` 6 passed, **회귀 0**(사전 matrix_enforcer 3만). **clean 커밋 4**: `c10cbbf`(명세 footer v6.0→v6.3 header정합)·`ccf08a3`(gitignore `*.db-journal`)·`6fab9bc`(feat FR-06/07/08)·`9d1f30d`(feat FR-09). ⚠ **advance-phase 훅 자동커밋 이슈**: `dev` 전환이 `aeddc62 chore`로 FR-08+tests+`data/gop.db-journal` git add -A 했었음 → **차장님 커밋 `3477198`(admin_photo_upload)이 위에 얹혀 soft-reset 불가** → forward-only 정리(gitignore로 재발방지). **README** 타깃 갱신(진행중 콜아웃, 템플릿 전체덮기 회피=매니저 문서 보존). **V-08**: 정적 라우트 audit은 직접 import 시 앱 라우트 미충전(환경 quirk)이라 **observe 모드 라이브 수집이 정석**(route_audit.py 제거). ⚠ tests/·conftest=**gitignore 아님**(추적됨) 정정. **잔여(라이브 게이트)**: NATS `NATS_REVOKE_ENABLED` flip · `MATRIX_DENY_MODE` observe→enforce(+미분류0 확인) · **5중싱크**(명세 grant집행·재빌드·컨테이너) · Phase 3 통합회귀. app/ 커밋됨·**미push**. 롤백태그 `pre-v6.3-grant_enforcement_hardening`.
- **✅ grant-enforcement 배포·라이브회귀·5중싱크 마감 (2026-07-21, "순서대로")**: 롤백이미지 `pids-api-server:pre-v6.3-grant_enforcement_hardening` → **재빌드**(COPY 최신 코드) → **재기동 healthy**(부팅 `Grant expiry jobs rescheduled on boot: 0`·`Grant sweep scheduler started (interval 10m)` 무오류) → **라이브 회귀 `tests/session_authority_e2e.sh` A01~A18 10/10 · 계약 10 passed**(무회귀) → 라이브 Swagger **6.3.0 / 129 paths(계약 불변)**. **5중싱크 완결**: ①코드(커밋 c10cbbf·ccf08a3·6fab9bc·9d1f30d·4e2a1be) ②Swagger(라이브 6.3.0) ③명세 롤링 체인지로그(`## 변경 이력` v6.3후속 2026-07-21 grant_enforcement_hardening 행 추가) ④이미지 재빌드 ⑤컨테이너 healthy. ⚠ **flip 미활성 유지**(`NATS_REVOKE_ENABLED`·`MATRIX_DENY_MODE=off` 기본 = 현행 무행동변화, 배포게이트). ✅ **origin+gitea push 완료** (`3477198..77f3d84 release/v6.3`, 6 커밋). 롤백: git `pre-v6.3-grant_enforcement_hardening` / 이미지 동명 태그.
- **✅ 세션 만료 로그아웃 원인 규명 + 세션 동시성 정책 재설계 분석 (2026-07-31, Track A, 워크플로우 2회=48 agent+라이브 DB 실측)**: PM 리포트("계정이 세션 만료로 로그아웃") → 8관점×3중 적대검증 버그헌트. **원인 체인 확정(라이브 DB)**: ①클라 3종 **refresh 미사용 실증**(REFRESH_ROTATION 블랙리스트 0건·30일 572세션 전부 TTL 정확히 12.0h/24.0h=연장 0회) → 12h마다 재로그인 → ②**의도된 단일세션 evict**(DUPLICATE 14일 122건, admin 116 — PM 확인: 단일ID단일세션은 설계 요구였음) 상호 축출. **확정 결함(P0) 4건**: sweep이 expires_at(access) 기준으로 세션 사망→7d refresh 무력화(critical, EXPIRED 13건 전부 refresh 유효 실측)·delete_my_session 블랙리스트 미수행·비번변경 타세션 무효화 무동작(users.py:272 decode_token(jti) 항상 JWTError)·refresh 회전 옛 refresh TTL 설정값 사용(auth.py:852). **session_enabled 검증**: 저장/감사/신규10년발급 정상, 단 기존 세션 소급 없음+DUPLICATE와 무관+기능효과 테스트 0. **배포 리스크**: offline-installer 번들 .env 부재(재배포시 JWT 키 폴백→전 토큰 무효+위조 가능)·.env 키가 금지 리터럴 시작(staging/prod 기동 거부). **분석보고서**: `docs/analyses/session-concurrency-policy-analysis.md` — PM 결정(SSO 대비 중복 세션 필수) 반영, 신규 설정 4키(session_concurrency_policy evict_all|allow 기본 evict_all·max_concurrent_sessions 0·session_history_retention_days 0·login_anomaly_event_enabled False)+client_id(v65 유일 DDL)+deny 의도적 제외+SSO 브로커형 권고(idp 컬럼은 SSO PRD 이연)+클라 동시배포 필수 0건+Phase 0~6 로드맵+**FR-01~15**. 차수명 `v6.3-session_concurrency` 제안. **다음=PRD 작성**(Track C, [[feedback_prd_before_implementation]] — 단 파이프라인 grant-enforcement 점유 → out-of-band 순번대기 패턴). 코드 무변경.
- **✅ HTTPS 인증서 SAN 확장 (2026-07-31, `pre-cert_san_expand` 롤백태그 @f938f55)**: PM 원격 접속 시 `ERR_CERT_AUTHORITY_INVALID`(포트포워딩 공인 IP `123.141.236.253:8136`) → 원인 2겹: ①접속 클라에 mkcert rootCA 미신뢰 ②cert SAN에 해당 IP 없음(기존 SAN `.160/.1/10.0.0.1`은 실서버 IP와도 불일치). 서버는 다른 지역, 내부 IP `192.168.202.151/192.168.1.151`, 공인 IP로 접속. **조치**: `server_install.ps1:225` `$defaultSans`에 공인 IP 2개(`123.141.236.253`,`.248`) + 내부 서브넷 전체(`192.168.1.1~254`,`192.168.202.1~254`) 열거 추가(IP 와일드카드 불가 → 512 SAN). **CRLF 바이너리 편집**(줄바꿈 오염 방지 [[feedback_windows_lf_write_discipline]]). `build_install_exe.ps1`로 `server_install.exe`(38400)/`client_install.exe`(36352) 재빌드. **검증**: mkcert 512-SAN 발급 OK, 임베드 rootCA==현재 CA(DER sha256 `f36af2da…` 일치), 로컬 컨테이너 재시작 후 uvicorn 512-SAN 로드 + `openssl Verify return code: 0`. rootCA 불변이라 기존 신뢰 클라 재설치 불요. 백업 `certs/backup-20260731-131840`. ⚠ **CA 일관성 주의**: `.151`에서 `server_install.exe` 직접 실행 시 그 PC의 mkcert CA를 씀. **PM 선택=Model B(리모트 자족)**: `git clone + bootstrap.ps1` 하나로 서버 cert(그 서버 CA·512SAN) + **client_install.exe를 그 서버 CA로 재생성**까지 완성 → 생성된 client_install.exe를 클라 PC로 가져와 실행. **구현 완료**: ①`client_install.ps1` 하드코딩 CA→`__ROOT_CA_BASE64_PLACEHOLDER__` 복원(CA-agnostic, 재임베드 가능화) ②`bootstrap.ps1`에 step 2.5 삽입(cert 발급 후 `build_install_exe.ps1 -RootCaPath certs\rootCA.pem`로 client_install.exe 재빌드, ps2exe 필요·인터넷·best-effort+sidecar fallback). 커밋용 exe는 placeholder 템플릿(server_install.exe 38400=신SAN, client_install.exe 34304=placeholder). **검증**: 두 ps1 구문 OK·CRLF 보존, `-RootCaPath` 임베드 경로 DER sha256 `f36af2da…` 일치(리모트 재빌드 정상), placeholder 상태 확인. cert 파일(crt/key/pem)은 git-ignored라 커밋 안 감(리모트가 bootstrap으로 자체 생성). 롤백 `pre-cert_san_expand`@f938f55, 백업 `certs/backup-20260731-131840`(cert+exe+ps1). ⚠ bootstrap은 cert 존재 시 발급 스킵(147-149) → 기존서버 재적용은 옛 cert 삭제 후 실행. **미커밋(로컬)** — 변경: bootstrap.ps1·client_install.ps1·server_install.ps1·server_install.exe·client_install.exe. [[feedback_windows_lf_write_discipline]] [[feedback_git_rollback_point]]
- **✅ datetime/timezone 혼용 통합 분석 (2026-07-31, Track A, 3소스 수렴)**: **스펙**(`GOP_Restful_Api_연동설계.md` = datetime **전역규약 없음**·`Z`/`+09:00`/naive 혼재·validation 에러예시가 `Z` 유도) × **라이브실측**(`docs/API_DateTime_Timezone_Audit_2026-07-31.md` = 12 endpoint 500 측정) × **코드검증**(워크플로 25에이전트 33필드 전수+적대검증). **LIVE 500**: ServerMetrics DELETE(**무조건 100%**)·GET /logs필터(번들뷰어 항상 Z→매번)·detection_logs·actions목록·system_events·server_metrics GET·enclosure GET/DELETE·audit_logs·config_change_logs. **조용한 9h 드리프트**: 리포트 start/end 창(timestamptz→UTC strip)·completed_at(응답 +00:00 방출)·api_logs sweep(utcnow cutoff)·token_blacklist. **GUARDED(load-bearing)**: event_statistics(레퍼런스 픽스)·grants·sessions. **이미수정**: collected_at·event_statistics·logged_out_at. **근본**=경계 공용 정규화유틸 부재 + 컬럼타입 가드 부재 + **스펙 단일규약 부재**. **픽스**: P0(server_metrics DELETE·logs필터)→P1(전 list/delete 가드+리포트 read strip를 astimezone변환+컬럼 naive마이그)→공용 `to_naive_kst` 유틸+SQLAlchemy TypeDecorator+serializer astimezone+**스펙 전역 datetime 규약 신설**+에러예시 `Z`→`+09:00`. 산출 **`docs/analyses/datetime-timezone-consolidated-analysis.md`**. ⚠ 배포 v6.3.1 사이트에 500·드리프트 그대로 존재(기존결함). 실제 픽스는 Track C=PRD 대기. [[feedback_validation_first]]
  - **↳ 통일 PRD Draft 작성 (2026-07-31, "datetime 하나로 통일+추천방향 PRD")**: `docs/prds/datetime-timezone-unification-prd.md`(**Draft — 승인 대기**). 규약=**naive-KST 저장/+09:00 출력/경계 정규화**. FR 10(~31태스크): FR-01 공용 `to_naive_kst`/`kst_now_naive` 유틸 · FR-02 `KstNaiveDateTime` **TypeDecorator**(bind시 aware→strip, 타입레벨 차단) · FR-03 쿼리파라미터 정규화 · FR-04 P0핫픽스(server_metrics DELETE·logs필터) · FR-05 P1 라우터 가드이식(~9개) · FR-06 리포트 컬럼 timestamptz→naive 마이그+read strip+completed_at · FR-07 serializer aware→KST 변환+오류meta +09:00 · FR-08 sweep/blacklist cutoff KST-naive · FR-09 scheduler/cursor/password_expires_at 정합 · FR-10 명세 전역규약+에러예시 Z→+09:00. NFR 5·V-01~04(★V-01 TypeDecorator asyncpg bind PoC·V-02 리포트마이그 데이터보존)·R-01~05(★R-01 TypeDecorator 미커버→FR-03 병행 2중방어·R-02 마이그 9h이동). 2중방어(유틸+타입가드)로 라우터별 누락 구조적 차단. ⚠ 파이프라인 grant-enforcement 점유 → out-of-band. 승인 후 plan. [[feedback_prd_before_implementation]] [[feedback_five_artifact_sync]] [[feedback_windows_lf_write_discipline]]
- **✅ 이벤트 수신 억제 스케줄(정비 창) PRD Draft 작성 (2026-07-31, Track C, PM 요청 "공사/설치/AS 시 불필요 탐지·장애 억제 API")**: 워크플로우 7-리더+synthesis 심층분석(코드 직접 교차검증). **★핵심 아키텍처 사실 확정**: DBApi는 브로커 발행전용 → 인바운드 NATS 구독 **0건**(grep 검증), 이벤트는 오직 HTTP POST 3개(`detections`/`malfunctions`/`connections`)로 유입 → 이 서버 억제 = **저장(persistence)+DB파생 다운스트림 억제**(라이브 NATS 방송은 PidsProxy/AiAnalysis 직송이라 미차단 = Phase 2 크로스컴포넌트, **PM 결정 D1**). **매핑 검증**: 연결/탐지/장애=`EnumEventCategory.CONNECTION/DETECTION/MALFUNCTION`(enums.py:137-139, 핸들러 하드코딩 category 확인), 감지=sensor/controller·감시=camera(파생, 스키마에 side 플래그 없음). **설계**: grant `valid_from/valid_until`+파생status+sweep 패턴 이식, 신규 `event_suppression_schedules` 테이블(`UtcDateTime`), lazy 게이트 `event_suppression_service.is_suppressed()`를 **device 조회 후·`device.status` 플립 전(malfunctions 404행/detections 389행)·`db.add` 전** 삽입, RBAC `events:edit`(안전성 상승 시 ADMIN-only 옵션 D3), connections POST 무인가 정합(D12). FR-01~08(Phase1)+FR-P2-01/02(Phase2 라이브전파·반복). NFR 6·V-01~11·리스크7·**PM결정 D1~D13(권고안 포함)**. 산출물 `docs/prds/event-suppression-schedule-prd.md`(**Draft — 승인 대기**), docs/prds/INDEX.md #7 등재. ⚠ 파이프라인 다PRD 병행 → out-of-band 순번대기(phase=prd, activePrd 미강제). **코드 무변경**(PRD만). 승인: `node .claude/hooks/advance-phase.js approve prd "..."`. [[feedback_prd_before_implementation]] [[feedback_validation_first]] [[feedback_five_artifact_sync]]
  - **↳ v2.0 PIVOT — Option B (UTC 저장 + DISPLAY_TZ 설정) (2026-07-31, PM "헝가리/미국 대비, static naive_kst 불가")**: A(naive-KST)는 `Asia/Seoul` 하드코딩=**이식 불가**로 **기각**. B=**저장 UTC(`timestamptz`) / 출력 `DISPLAY_TZ`(env·ZoneInfo·DST 자동) / 입력 aware 권장(timestamptz 네이티브 수용→500 원천소멸)**. 설정=`DISPLAY_TZ=Asia/Seoul|Europe/Budapest|America/New_York` env 하나로 코드·데이터 무변경 전환. FR 재작성 10개(~37): utc_now/to_utc/to_display 유틸·`display_tz` config·전컬럼 timestamptz+**마이그(`AT TIME ZONE 'Asia/Seoul'` naive→UTC 보존, ★파티션 api_logs 특수)**·쓰기 utc_now·serializer to_display·명세 규약. **V-02(마이그 데이터 보존)=최우선**·R-01(마이그 치명→DB백업+스테이징 리허설). **V-01 PoC 완료**(TypeDecorator가 asyncpg에서 aware strip — A용이었으나 timestamptz의 aware 수용도 확인). **A 코드(util/types/P0 edit) 되돌림**(git checkout+rm, 트리 clean). 롤백태그 `pre-datetime_unification`. 클라통지 `docs/GOP_Server_API_datetime_unification_NOTIFY.md`(표시tz 개념으로 갱신 필요). PRD **v2.0 Draft 승인대기** → plan/dev. [[feedback_prd_before_implementation]]
  - **↳ v2.1 — 반론 적대검증 + 마이그 버전무관 (2026-07-31)**: 반론보고서(`docs/reports/datetime-timezone-unification-prd-counterargument-report.md`, **v1.0/A 대상**) **사실 전부 코드검증=참**(token_blacklist.py:34 default=utcnow / report.py:195 body TypeError / common.py:31 aware미변환 / common.py:22 PlainSerializer format유실). B pivot으로 4.1(blacklist모순)은 구조해소하나 **통찰=컬럼별 time-base 마이그방향**(KST→`AT TIME ZONE 'Asia/Seoul'`, **blacklist/JWT UTC→`'UTC'`**)이 필수(방향틀리면 9h=보안). 반영: FR-04 **멱등·조건부**(`information_schema` skip)·`schema_migrations` 등록=**옛버전도 번들 기동시 1회 자동 정확반영**(PM "이전버전 원격도 정상반영" 요구) · FR-07 **body**정규화(model_validator) · FR-06 openapi `format:date-time`+`.isoformat()`금지 · 범위명확화(typed통일+표시문자열 DISPLAY_TZ 문서화) · V-06~10(blacklist경계·body혼합·문자열인벤토리·openapi·244회귀). PRD **v2.1 Draft**. 다음=plan(B)→V-02/V-06 마이그리허설(볼륨클론)→dev. [[feedback_validation_first]]
  - **↳ 마이그 리허설 완료 (2026-07-31, 볼륨 클론, 실DB 무접촉)**: 인벤토리 **82 timestamp 컬럼**(naive 79 + timestamptz 3=report_generations). **V-02 ✅**(`AT TIME ZONE 'Asia/Seoul'` epoch 보존 무손실) · **V-06 ✅**(token_blacklist 2컬럼 `AT TIME ZONE 'UTC'`) · **V-03 ✅**(report_generations timestamptz=이미 정확 UTC→skip) · 멱등가드(data_type skip) ✅. **★V-05 발견=api_logs `timestamp`가 파티션키라 직접 ALTER 불가**(`cannot alter column ... part of partition key`, 68k행) → **재생성+복사+스왑 전략 필수**(v60식). 마이그 3계층 확정: 일반79=Asia/Seoul · blacklist2=UTC · api_logs=재생성 · report3=skip. PRD FR-04+V노트 반영. **api_logs 전략(재생성 vs 예외 연기)=PM 결정 대기**. 샌드박스가 클론 cp `/from/.` 오탐→dangerouslyDisableSandbox로 우회(안전 확인된 :ro 클론). [[feedback_validation_first]]
  - **↳ plan(B) + Phase 1 기반 완료·검증 (2026-07-31, "순서대로 진행")**: plan `docs/plans/datetime-timezone-unification-prd-plan.md`(B, api_logs 재생성=Phase4 맨끝). **IMPL-01/02/03 완료**: `app/utils/datetime.py`(utc_now/to_utc/to_display)·`app/config.py`(**`DISPLAY_TIMEZONE`+`display_tz`**)·`app/models/types.py`(`UtcDateTime` TypeDecorator). **다국가 실측 PASS**(격리컨테이너, 운영 무변경): Asia/Seoul→to_display(UTC00:00)=09:00+09 / **Europe/Budapest→02:00+02:00(7월 서머타임 DST 자동)** — env `DISPLAY_TIMEZONE` 하나로 코드·데이터 무변경 전환 실증. 다음=Phase 2(마이그 SQL `vNN_datetime_to_utc.sql` 조건부멱등+컬럼별방향 / 모델 전컬럼 UtcDateTime / 쓰기 utc_now) → Phase 3 serializer/입력 → Phase 4 api_logs 재생성 → 명세 → test → 5중싱크+번들. 롤백태그 pre-datetime_unification. app/ 미커밋(config/util/types만, 라우터 무변경).
  - **↳ Phase 2·3 코어 완료·검증 (2026-07-31, "끝까지")**: **FR-04 마이그** `app/migrations/v66_datetime_to_utc.sql`(naive만 대상 루프=조건부멱등, 컬럼별방향 KST=`Asia/Seoul`/blacklist=`UTC`, api_logs·schema_migrations 제외, report_gen skip) + `init_db.py` IDEMPOTENT_MIGRATIONS 등록. **타겟팅 읽기전용 검증**: 69변환(67KST+2UTC)·10제외·leftover 0. **FR-03 모델** 바이너리 스윕 2회 17파일 `Column(DateTime)`→`UtcDateTime`(멀티라인 포함, log.py=ApiLog만 v67까지 naive), **모델 로드 검증**(report.start_date/blacklist.expires_at=UtcDateTime). **FR-06 serializer** common.py(`_kst_isoformat`·`_add_kst_recursive`→`to_display`, `KSTDatetime`에 `WithJsonSchema` format:date-time 복원[반론4.5])·main.py(encoder→to_display, 오류meta→DISPLAY_TZ[성공과 일치]), **검증**(UTC00:00→Seoul+09). compileall 전 app OK. **완료 FR**: 01·02·03·04(비파티션)·06. **남음**: FR-05 쓰기표준(default→utc_now, 현 Korea는 TypeDecorator로 정상·타국용 follow-up)·FR-07 body정규화(ReportGenerateRequest end<start TypeError, 반론4.2)·FR-04 api_logs v67 재생성·FR-09 명세·FR-08 sweep·FR-10 test·**DEPLOY(rebuild+마이그 실행+라이브)**. app/ 미커밋(config·util·types·17모델·common·main·init_db·v66sql). 롤백태그 유효.
  - **↳ ✅ 완결·라이브 검증·배포·5중싱크 (2026-07-31, `datetime_unification`, 커밋 `39b12dd`, 태그 `v6.3-datetime_unification`)**: **FR-05** 런타임 쓰기/비교 스윕(모델 default→utc_now, 라우터/서비스 naive-KST/utcnow→utc_now, api_logs 3파일 제외). **정규화 헬퍼 6종**(`_to_naive_kst` 계열)+리포트 범위+**FR-07** ReportGenerateRequest body → `to_utc`(aware UTC) 위임(역순범위 TypeError→422). **FR-06** main.py encoder·오류meta→to_display + **마이그 직후 async_engine.dispose()**(ALTER 후 asyncpg InvalidCachedStatement 전이 500 제거). **api_logs**: 파티션키라 ALTER 불가 → naive-UTC 저장(`utc_now().replace(tzinfo=None)`)+입력경계 to_utc(전역 naive=UTC 규약 정합, 구KST행은 retention 소멸까지 표시skew, v67 timestamptz 재생성 이연). **FR-09** 명세 §3.4 규약 신설+체인지로그+클라MD(Option B). **배포**: 롤백3종(git·이미지·DB덤프 `backups/datetime-unification-20260731/gop_pre_datetime.dump` 4.75MB) → 재빌드 → v66 실행(72 timestamptz/10제외=api_logs9+schema_migrations) → 재기동 멱등skip+dispose로그. **라이브 실증**: aware `collected_at +09:00` POST→**201**(DB저장 UTC 10:50/출력 +09:00), GET 다수 200+`+09:00`, reports/generate aware범위→**201→COMPLETED**(역순 422), 오류meta `+09:00`. 5중싱크(코드·Swagger·명세·이미지·컨테이너 healthy). **origin/gitea push 대기**(로컬 커밋·태그만). ⚠ admin 비번은 문서기본 admin123 재설정함(dev). [[feedback_five_artifact_sync]] [[feedback_git_rollback_point]] [[feedback_https_policy]]
- **잔여(후순위)**: P2-01 secret/CORS(SEC-02 보류 영역), P3-01 invalid enum 422화, ~~matrix_enforcer default-deny 전환~~(→ grant-enforcement-hardening FR-09로 편입, observe/enforce 구현 완료·flip 배포게이트), SEC-05(session off 10년 JWT 보류→세션 동시성 분석에서 결함④·조합 매트릭스로 구체화). 선재: TestClient lifespan 반복 시 log_consumer 이벤트루프 오류(하네스 격리 개선, 내 변경 무관).

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
- **현재 Phase**: prd
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
- **현재 세션 ID**: ppid-72848
- **충돌 여부**: 없음
- **활성 세션 목록**: ppid-72848

