# 세션 동시성 정책(evict) 재설계 분석 리포트

- **분석 일시**: 2026-07-31
- **분석 모드**: Deep (멀티에이전트 워크플로우 2회 — 버그헌트 8관점×3중 적대검증 42 agent + 설계분석 5관점+비평 6 agent, 라이브 DB 실측 병행)
- **분석 범위**: 세션/인증 서브시스템 (auth.py · user_sessions.py · session_sweep/revoke/blacklist/settings 서비스 · 명세서 계약)
- **언어/프레임워크**: Python / FastAPI + SQLAlchemy(dual-stack) + PostgreSQL 16
- **이전 분석**: 최초 분석 (관련: `docs/Analysis/ACCOUNT_COORDINATION.md`, `account-session-authority-prd`)
- **배경 결정**: 단일 ID 단일 세션(현행 evict)은 **의도된 정책**(PM 요구, v5.4 P1-B, NOTIFY §2.3 명문화). SSO 연동 예정에 따라 **중복 세션 허용으로 전환**하되, 필요한 기술적 분화(추가 설정 옵션)를 본 분석에서 도출.

---

## 0. 요약 (결론)

**중복 세션 허용은 서버 단독 배포로 가능하며, 클라 동시배포 필수 항목은 0건이다.** evict를 강제하는 코드는 `auth.py` 로그인 경로 3구간뿐이고, 나머지 인프라(sid 클레임·per-session NATS·강제로그아웃·refresh CAS)는 이미 per-session 지향이라 정책 조건화는 국소적이다. 단, **정책과 무관한 선행 결함 4건(P0)을 먼저 고쳐야** 중복 세션 모델이 보안·실효성 양면에서 성립한다.

| 결정 사항 | 내용 |
|---|---|
| **정책 키** | `session_concurrency_policy` (str enum: `evict_all` \| `allow`) — **기본 `evict_all`=현행 100% 보존**, 운영 전환은 PUT 1회(런타임 flip, 감사 자동) |
| **상한 키** | `max_concurrent_sessions` (int, 기본 0=무제한, 0~20) — allow 전용, 초과 시 evict_oldest 고정 |
| **클라 식별** | `AccountLoginRequest.client_id` 옵션 필드 + `user_sessions.client_id` 컬럼(v65) — allow 모드에서 같은 앱 재로그인은 자기 세션만 교체(self-replace) |
| **선행 결함 4건** | ① sweep이 access 만료 기준으로 세션 사망 → refresh 무력화 ② `delete_my_session` 블랙리스트 미수행 ③ 비밀번호 변경 타세션 무효화 무동작 ④ refresh 회전 블랙리스트 TTL 불일치 |
| **SSO 아키텍처** | 로컬 JWT 발급 유지(브로커형) 권고 — IdP 토큰 직접 검증(B안)은 블랙리스트·sid·NATS 계약 전량 붕괴로 기각. idp 컬럼(idp_subject 등)은 IdP 제품 미정이라 **SSO PRD로 이연** |
| **deny 정책** | **의도적 제외** — 계정 잠금형 DoS(공격자 세션 점유 + 무토큰 사용자의 자기구제 경로 부재) |
| **차수명** | `v6.3-session_concurrency` (pre-태그 필수, 하루 1차수 규율) |

### 증상 원인 체인 (라이브 DB 실증 — PM 질문 회신)

**"refresh 코드가 없어서 만료된 것 아닌가" → 맞음(실증됨).** 단, refresh를 클라에 넣어도 서버 결함 ① 미수정 시 사후(reactive) refresh는 실패한다.

```
클라 3종 refresh 미사용 (30일간 REFRESH_ROTATION 블랙리스트 0건,
  전 세션 TTL이 정확히 12.0h/24.0h — 연장 흔적 0건)
    ↓ access 12h 만료
클라 재로그인
    ↓ 의도된 단일세션 evict (DUPLICATE)
같은 admin 계정을 쓰는 다른 클라 세션 즉시 폐기
    ↓ 401 SESSION_REVOKED
"세션 만료" 표시 → 그 클라도 재로그인 → 상호 축출 반복
```

- 최근 14일 세션 폐기: **DUPLICATE 122건**(admin 116) / EXPIRED 13건 / USER_LOGOUT 1건 — evict 정책은 설계대로 동작 중이며, 문제는 "공유 계정 + 멀티 앱" 운영이 단일세션 전제와 충돌하는 것.
- EXPIRED 13건은 **전부 refresh 토큰이 수일 유효한 상태에서 sweep에 의해 폐기**됨(결함 ①의 실측 증거).

---

## 1. 현황 진단 — 라이브 DB 실측

### 1.1 로그아웃 사유 분포 (2026-07-17~31)

| logout_reason | 건수 | 해석 |
|---|---|---|
| DUPLICATE | 122 (admin 116) | 의도된 단일세션 evict. 세션 생존시간 평균 1분~1시간(상호 축출 핑퐁) |
| EXPIRED | 13 | sweep 처리 — 13건 전부 `refresh_expires_at > logged_out_at` (refresh 유효한데 폐기) |
| USER_LOGOUT | 1 | 정상 로그아웃 |

### 1.2 클라이언트 refresh 미사용 확증

| 증거 | 실측값 |
|---|---|
| `token_blacklist` reason 분포 | DUPLICATE 97건 / LOGOUT 1건 / **REFRESH_ROTATION 0건** (회전 성공 시 반드시 기록됨) |
| 세션 TTL 분포 (30일, 572건) | **정확히 24.0h 295건**(~7/6, 당시 설정 24h) + **정확히 12.0h 277건**(7/6~, 설정 12h) — 비표준 TTL 0건 = refresh 연장 0회 |
| 로그인 빈도 | admin 7일간 67회 (모두 Docker 게이트웨이 IP 172.18/19.0.1 = 호스트측 클라이언트) |

### 1.3 런타임 설정 현황 (app_settings 권위 — .env 24h는 시드 기본값일 뿐)

`session_timeout_hours=12`, `refresh_expiration_days=7`, `session_enabled=true`, `lockout_threshold=5`, `lockout_duration_minutes=30`. `session_enabled` 토글은 2026-07-07 회귀 테스트로 1초간 꺼진 것 외 실운영 사용 이력 없음.

---

## 2. 아키텍처 현황 — 멀티세션 준비도

### 2.1 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 | 멀티세션 판정 |
|---|---|---|---|
| 로그인 evict 블록 | `auth.py:581-591, 643-652` | 같은 계정 활성 세션 전부 폐기 + NATS 발행 | **정책 분기 대상 (유일한 단일세션 강제 지점)** |
| sid 클레임 | `auth.py:610-614` | JWT sid = UserSession.id, refresh 회전에도 불변 | 무변경 — 이미 per-session |
| refresh CAS | `auth.py:834-846` | FOR UPDATE + refresh jti 일치 검사 | 무변경 — per-session 격리 |
| revoke_session_family | `session_revoke_service.py` | access+refresh를 stored exp로 블랙리스트 + 세션 마킹 | 무변경 — 폐기 단일화 서비스 |
| per-session NATS revoke | `nats_revoke_publisher.py` (계약 C2) | 세션 전용 subject 발행 (게이트 OFF) | 무변경 — 클라 구독 로직도 무변경 |
| 강제로그아웃 (단건/벌크/self) | `user_sessions.py` | 세션 단위 폐기 | self(delete_my_session)만 결함 수정 |
| 마지막-ADMIN 가드 | `user_sessions.py:43-78` | 활성 ADMIN 세션 0 방지 | 카운트에 미만료 조건 보강(P1) |
| session sweep | `session_sweep_service.py` (5분) | 만료 세션 마킹 | **판정 기준 수정 필수 (결함 ①)** |
| 런타임 설정 | `settings_service.py` + `routers/settings.py` | app_settings 시드·캐시·감사 | 신규 키 4종 수용 준비 완료 |

### 2.2 단일세션 가정 의존성 — 전수 판정

- **의존 없음(무변경)**: logout(요청 토큰 jti로 자기 세션만), refresh(sid 격리), 벌크 force_logout·lock/reset(원래 전 세션 순회), UserSession 스키마(per-user unique 제약 없음 — DDL blocker 없음), 세션 목록 API(페이지네이션 보유).
- **수정 필요**: §4의 결함 4건 + user_sessions 행 purge 로직 전무(코드 전체에 DELETE 0건 — 이력 무한 누적, retention 설정으로 해소).
- **깨질 테스트**: pytest 0건(DUPLICATE evict 직접 단언 없음), E2E 셸 `session_authority_e2e.sh` A05 1건(정책값 분기 필요). `test_session_settings.py`는 응답 필드 추가로 확장 필요.

---

## 3. 신규 설정 옵션 설계 (핵심 산출물)

### 3.1 런타임 설정 키 4종 (app_settings — `seed_if_empty` 자동 시드, SQL 불필요)

| 키 | 타입 | 기본값 (=현행 보존) | 경계 | 의미 |
|---|---|---|---|---|
| `session_concurrency_policy` | str enum | **`evict_all`** | `evict_all` \| `allow` | evict_all=현행(전 세션 폐기) / allow=공존(SSO 목표). PUT 1회로 flip·롤백, config_change_logs 자동 감사 |
| `max_concurrent_sessions` | int | **0** (무제한) | 0~20 | allow 전용 계정당 활성 세션 상한. 초과 시 **evict_oldest 고정**(created_at 오름차순, reason=DUPLICATE 재사용). evict_all에선 no-op(Swagger 명기). cap>0일 때만 계정 행 FOR UPDATE(동시 로그인 race 차단 — 기본 0이면 락 경합 추가 없음) |
| `session_history_retention_days` | int | **0** (비활성) | 0~3650 | >0이면 `is_active=False AND logged_out_at < cutoff` 이력 행 DELETE sweep(1일 1회). 활성 세션 절대 미대상. 운영 권장 180일 |
| `login_anomaly_event_enabled` | bool | **False** | — | 신규 IP/UA 로그인 성공 시 SystemEvent(SECURITY_ALERT) 발행 — 단일세션이 주던 "로그아웃당함=도난 감지" 신호의 대체 |

기본값이 전부 현행 보존이므로 **코드 배포 직후 동작 변화 0** (조직 규율: MATRIX_DENY_MODE=off, NATS_REVOKE_ENABLED=False 패턴과 동일).

### 3.2 client_id 세션 귀속 (설정이 아닌 스키마/요청 확장)

| 항목 | 설계 |
|---|---|
| 요청 | `AccountLoginRequest.client_id: Optional[str]` — 패턴 `^[A-Za-z0-9._:-]{1,64}$`, 규약값 `central-ui` / `monitoring` / `rtsp-viewer`. **옵셔널이라 기존 클라 하위호환 100%** (미전송=현행 동작이 그 자체로 안전 게이트 — 별도 설정 키 불필요) |
| DB | `user_sessions.client_id VARCHAR(64) NULL` + 부분 인덱스 2종 — **v65 마이그레이션(유일한 DDL)**, `IDEMPOTENT_MIGRATIONS` 등재로 startup 자동 적용 |
| 시맨틱 | **allow 모드에서만** 같은 `(user_id, client_id)` 활성 세션을 self-replace(자기 세션만 교체) — evict_all에선 기록 전용이라 클라가 먼저 보내기 시작해도 무해(배포 순서 자유) |
| SSO 연계 | 이 컬럼이 그대로 OIDC RP client_id 축이 됨 — 재설계 불필요 |

### 3.3 설정 조합 매트릭스 (`session_enabled`은 TTL축, policy×max는 공존축 — 직교)

| policy | max | session_enabled=True (12h/7d) | session_enabled=False (10년) |
|---|---|---|---|
| evict_all | any | **현행** — 로그인마다 전 세션 폐기, max 무시 | 단일 세션 수렴이라 무한 TTL 무해 |
| allow | 0 | **SSO 목표 상태** — 무제한 공존 (결함① 수정 전제) | 세션 영구 공존 누적 → retention 권장 |
| allow | N≥1 | N개 롤링 유지, 초과분 oldest evict | 동일 (항상 자리 확보 — 안전) |
| ~~deny~~ | — | **v1 의도적 제외** (§3.4) | — |

### 3.4 deny 정책 의도적 제외 사유

활성 세션 존재 시 신규 로그인 거부(deny)는 ① 도난 자격증명 1회 로그인 또는 좀비 세션이 정상 사용자 로그인을 차단(토큰 없는 사용자는 `delete_my_session` 호출 불가 → 자기구제 경로 없음), ② `session_enabled=False`(10년 TTL)와 결합 시 사실상 영구 락아웃, ③ SSO 요구("중복 허용")에 존재하지 않는 값. 명세서에 "의도적 제외"로 기록한다.

---

## 4. 선행/동반 수정 결함 4건 (P0 — 정책 flip 전 필수)

| # | 결함 | 위치 | 내용 → 수정안 | 멀티세션에서의 증폭 |
|---|---|---|---|---|
| ① | **sweep이 refresh 무력화** (버그헌트 critical 확정, 3중 검증 통과) | `session_sweep_service.py:23-26, 34-37` + `auth.py:839` | sweep이 `expires_at`(access 만료) 기준으로 `is_active=False` → `/refresh`가 is_active 요구 → access 만료+5분 후 7일 refresh가 401. **수정: 판정식을 `COALESCE(refresh_expires_at, expires_at) < now`로 — sync/async 양쪽** | idle 성향 클라(RTSP Viewer 등) 세션이 12h마다 조용히 죽어 allow 정책 목적 자체가 무효화. 클라에 refresh를 넣어도 사후 갱신이 불가 |
| ② | **delete_my_session 토큰 미폐기** | `user_sessions.py:306-312` | is_active=False 마킹만, 블랙리스트/NATS 없음 → 토큰이 exp까지 유효. **수정: `revoke_session_family_async` + NATS 발행**(DB reason=SELF_LOGOUT 유지, NATS reason=MANUAL 매핑) | allow에서 "내 다른 세션 종료"가 도난 세션 1차 자기방어 수단으로 승격 — 종료해도 토큰이 살아있으면 보안 구멍 상시화 |
| ③ | **비밀번호 변경 타세션 무효화 무동작** | `users.py:270-291` | E1/P1-10 이후 `session.token`은 jti인데 `decode_token()`(JWT 파싱) 호출 → 항상 JWTError → except pass → 블랙리스트 전량 스킵. **수정: stored jti 직접 블랙리스트(`_blacklist_pairs` 방식)** | "비번 변경 시 다른 기기 로그아웃"이 멀티세션의 실제 보안 경계가 됨 |
| ④ | **refresh 회전 블랙리스트 TTL 불일치** | `auth.py:851-860` | 옛 refresh TTL을 stored `refresh_expires_at`이 아닌 설정값(now+7d)으로 계산 — 같은 함수의 옛 access는 stored 사용(864-872), refresh만 비대칭(3줄 수정). session_enabled=False의 10년 refresh가 7일 뒤 블랙리스트에서 청소됨(CAS가 실악용은 차단 — 방어층 소실) | 방어심층 정합 — 폐기 경로 "stored exp 단일 원천" 불변식 완성 |

---

## 5. SSO(OIDC) 대비 설계

### 5.1 중복 세션이 SSO의 전제인 이유

OIDC에서 사용자는 IdP에 1개 세션을 갖고 각 RP(클라 앱)가 개별 code flow로 자기 토큰 세트를 받는다 → **사용자 1명 = 로컬 세션 N개(RP당 1개)가 정상 상태**. 현행 evict_all이면 Central UI가 IdP 로그인하는 순간 Monitoring/RTSP 세션이 즉사 — SSO의 존재 이유(1회 인증, N앱 동시 사용)가 무효화된다. 최근 14일 DUPLICATE 116건은 이 충돌의 사전 증상이다.

### 5.2 아키텍처 권고: 로컬 JWT 발급 유지 (브로커형)

| | A안: 브로커형 (권고) | B안: IdP 토큰 직접 검증 (기각) |
|---|---|---|
| 구조 | OIDC code flow는 로그인 경계에서만, 성공 시 현행 HS256 access+refresh(sid) 발급 | 전 endpoint가 IdP RS256 토큰을 JWKS로 검증 |
| 기존 자산 | jti 블랙리스트·refresh CAS·per-session NATS·last-ADMIN 가드·permissions payload **전부 무변경 재사용** | 블랙리스트 무의미(IdP 토큰 폐기 권한 없음), sid=세션행 매핑 소멸 → 강제로그아웃/세션 UI 전부 재구축 |
| 폐쇄망(GOP) | IdP 단절 시에도 기존 세션 지속 | IdP 의존 — 가용성 취약 |
| 갭 | 로컬 refresh(7d)가 IdP 로그아웃을 초과 생존 → Back-Channel Logout이 공식 해법 | — |

### 5.3 Back-Channel Logout 준비도

| 구성요소 | 상태 |
|---|---|
| 폐기 실행 계층 | **기존 인프라로 충족** — 세션 목록 조회 후 `revoke_session_family` + per-session NATS 반복 호출(벌크 force_logout과 동일 패턴) |
| 조회키 (`idp_subject`/`idp_session_id`) | 부재 → SSO PRD에서 v-next DDL |
| RS256/JWKS 검증 경로 | 부재 → jose 지원, JWKS fetch/캐시 신규 |
| 무인증 endpoint (`POST /api/auth/backchannel-logout`) | 부재 → IdP 서버간 호출용 신규 경로 |

### 5.4 지금 반영 vs SSO PRD 이연

| 지금 (v6.3-session_concurrency) | SSO PRD로 이연 (근거: IdP 제품 미정 — 미정 스키마 선반영 금지) |
|---|---|
| policy enum(boolean 아님 — SSO 때 allow만 켜면 됨) | `user_sessions.auth_source/idp_subject/idp_session_id` 컬럼 |
| `client_id` 스키마+로그인 배선(=RP 식별 축) | `account_users.password_hash` nullable화 + JIT 프로비저닝(기본그룹 매핑 필수 짝) |
| 전 폐기 경로 `revoke_session_family` 단일화(결함 ②③ 수정 포함) | backchannel-logout endpoint + JWKS 검증 |
| sid=UserSession.id 불변 원칙 유지(로컬 sid vs IdP sid 용어 분리 명세화) | `EnumLogoutReason.SSO_LOGOUT`(클라 동기 배포 필요 — C3 계약상 이번 차수 신규 enum 금지) |
| evict 로직을 `session_policy_service`(가칭)로 추출 — SSO 콜백 라우터가 동일 함수 재사용 | `SSO_ENABLED`/`OIDC_*` env 게이트(예약만 가능) |
| 브레이크글라스: 최소 1개 로컬 ADMIN 계정 영구 유지 정책(라스트-ADMIN 가드와 정합) — SSO PRD에서 확정 | |

---

## 6. 클라이언트(.NET 3종) 계약 영향

### 6.1 배포 의존성 판정 — **동시배포 필수 0건**

| 구분 | 항목 |
|---|---|
| 서버 단독 선배포 안전 | 설정 키 4종(additive), client_id 옵션 수용, user-sessions 응답 additive 필드, 결함 4건 수정, 정책 게이트 코드(기본 evict_all) |
| 클라 후속 (비동시) | client_id 전송, `details.reason` 메시지 분기, 세션관리 패널 멀티세션/is_current 표시, **proactive refresh 도입**(만료 전 선제 갱신 — 결함 ① 수정 후엔 reactive도 동작하나 선제가 표준) |
| flip 전제 | 스테이징 회귀 + 클라 3종 실사용 검수(세션 목록 3+행 표시). client_id 전송은 필수 전제 아님(미전송=단순 공존) |

### 6.2 명세서(GOP_Restful_Api_연동설계.md) 갱신 절 — 기존 결락 2건 포함

| 절 | 내용 |
|---|---|
| §9.2.2 login | **동시세션 정책 절 신설** — 현행 evict가 본문에 미기재(ChangeLog v5.4 행에만 존재)된 결락 보정 + client_id 옵션 |
| §4.5 EnumLogoutReason | **스펙-코드 불일치 정정**(기존 결함) — 명세에 DUPLICATE 누락/SELF_LOGOUT만 기재, 코드는 반대. "코드 6종 + SELF_LOGOUT(self-종료 기록값)"으로 정직화 |
| 401 계약 | `details.reason` 정식 필드 승격 + 클라 메시지 표 계약화 — DUPLICATE="다른 곳에서 로그인되어 로그아웃됨" / EXPIRED="세션 만료" / FORCED="관리자 종료" |
| §9.5 user-sessions | client_id/is_current 필드, /me 상세 절 신설 |
| §9.8 settings | 신규 키 4종 표 + 422 규칙 |
| NOTIFY | `GOP_Server_API_session_concurrency_NOTIFY.md` 발행 — 기존 NOTIFY §2.3 "최신 로그인만 유효" 문구 대체, C1(sid)/C2(per-session subject) **무변경 확인** 명시 |
| C3 제약 | NATS reason은 6종 고정(클라 서명 payload 파싱) — **이번 차수 신규 enum 값 0건**, cap-evict/self-replace는 DUPLICATE 재사용 |

---

## 7. 발견된 이슈 / 기술 부채 (버그헌트 42-agent 확정분 통합)

| 심각도 | 위치 | 내용 | 제안 | 예상 공수 |
|---|---|---|---|---|
| Critical | `session_sweep_service.py` + `auth.py:839` | 결함 ① sweep→refresh 무력화 (3중 검증 확정, EXPIRED 13건 전부 refresh 유효 실측) | FR-03 | 2h |
| High | `users.py:270-291` | 결함 ③ 비번 변경 무효화 무동작 (보안 — 증상과는 무관 방향) | FR-04 | 2h |
| High | `user_sessions.py:306-312` | 결함 ② delete_my_session 미폐기 | FR-02 | 2h |
| High | `auth.py:851-860` | 결함 ④ refresh 회전 TTL 비대칭 | FR-09 | 1h |
| High | `auth.py:81` | 계정 잠금 시 유효 세션 즉사가 일반 401로 평탄화(사유 구분 불가 — 클라 "세션 만료" 오인 기여) | 401 details.reason 계약화(FR-05)에 포함 | 1h |
| Medium | `token_blacklist_service.py:79` | add_to_blacklist 내부 commit이 refresh FOR UPDATE 락 조기 해제(단일 이벤트루프라 실발화 저확률 — 검증단 1/3 반박) | 후속 차수: 블랙리스트 commit 지연(flush만) 검토 | 4h |
| Medium | `settings_service.py:106` | 실효 TTL 권위가 DB(12h)로 이관 — .env(24h)와 불일치, 운영 혼선 | 명세 §9.8에 "DB 권위" 명기 | 0.5h |
| 배포 리스크 | `offline-installer/dist/bundle/payload/` | **번들에 .env 부재** — 재배포 시 JWT 키가 기본 리터럴 폴백 → 전 토큰 무효(전원 로그아웃) + 키 공지로 토큰 위조 가능 | payload에 .env 포함(또는 설치기 preserve.list 강제 검증) | 2h |
| 배포 리스크 | `.env` | JWT_SECRET_KEY가 금지 리터럴 'your-secret-key…'로 시작 — staging/prod 승격 시 기동 거부(fail-fast) | 랜덤 키 교체(1회성 전원 재로그인 공지 필요) | 1h |
| 참고 | `docker-compose.yml:146` | autoheal 무통보 재기동 — in-flight 단절을 클라가 "세션 만료"로 표시 가능(현재 RestartCount=0) | 클라 재시도 정책 확인 | — |
| 기각 | timezone/KST 혼용, matrix_enforcer(FR-09 off), JWT 키 재시작 로테이션 | 적대 검증에서 증상 원인 아님 확정 | — | — |

---

## 8. 개선 권고사항 — 롤아웃 로드맵

| Phase | 내용 | 동작 변화 |
|---|---|---|
| **0. 사전 조사** | `pre-v6.3-session_concurrency` git 태그. 비 UI 소비자(nats-dashboard/db_monitor/gis_ingest)의 REST 로그인 사용 여부 교차 확인 → cap 산정·client_id 규약값 확정 | 없음 |
| **1. 결함 수정 4건** | FR-02/03/04/09 (정책 무관 순수 결함 — NOTIFY 통지 후 서버 단독 배포, v6.0-session_authority 전례) | 결함 제거만 |
| **2. 스키마+설정+정책 코드** | v65(client_id+인덱스, startup 자동), 설정 4키 시드, evict 블록 정책 분기+cap evict_oldest, client_id self-replace, last-ADMIN 가드 미만료 조건 보강, is_current, retention sweep(0=무동작) | **0** (기본값 전부 현행 보존) |
| **3. 5중 싱크** | Swagger·명세(§9.2.2 신설/§4.5 정정/§9.5/§9.8/ChangeLog 1행)·NOTIFY 발행·이미지 재빌드·컨테이너 교체 | 없음 |
| **4. 스테이징 검증** | PUT policy=allow 후 회귀: A01~A18(A05 정책 분기) + 신규 pytest(allow 공존/cap evict/동시 로그인 race — Task별 독립 커넥션/retention/AUTH_MODE 양 모드) + HTTPS rootCA 환경 E2E + .NET 3종 동시 접속 실사용 | 스테이징 한정 |
| **5. 운영 flip** | `PUT /api/settings/session {"session_concurrency_policy":"allow"}` — 신규 로그인부터 적용, 롤백=PUT 1회(allow 기간 다중 세션은 다음 로그인 때 일괄 evict됨을 운영 주지) | **중복 세션 허용 개시** |
| **6. 후속·이연** | retention/anomaly 활성(운영 판단), 클라 client_id+reason 분기+refresh 도입, 성공 로그인 rate limit 보강, **SSO PRD 별도 착수** | 점진 |

---

## 9. 다음 단계 제안

### PRD 필요 항목 (신규 기능·아키텍처 변경) → prd 스킬 FR 초안

| FR | 우선순위 | 제목 |
|---|---|---|
| FR-01 | P0 | `session_concurrency_policy` 런타임 설정 + 로그인 evict 블록 정책 분기 |
| FR-02 | P0 | delete_my_session 토큰 폐기 완결 (revoke_session_family_async + NATS) |
| FR-03 | P0 | 세션 sweep 판정을 `COALESCE(refresh_expires_at, expires_at)` 기준으로 (sync/async 양쪽) |
| FR-04 | P0 | 비밀번호 변경 타세션 무효화 복구 (stored jti 직접 블랙리스트) |
| FR-05 | P0 | 명세·계약 정합화 (§9.2.2 신설, §4.5 정정, 401 details.reason 계약화, NOTIFY) |
| FR-06 | P1 | max_concurrent_sessions cap + evict_oldest (cap>0 시 계정 행 FOR UPDATE, UserLoginLog 감사) |
| FR-07 | P1 | client_id 세션 귀속 (v65 + AccountLoginRequest + allow self-replace) |
| FR-08 | P1 | last-ADMIN 가드 미만료 조건 보강 (좀비 세션 오계산 차단) |
| FR-09 | P1 | refresh 회전 옛 refresh TTL을 stored refresh_expires_at으로 통일 |
| FR-10 | P1 | 세션 동시성 테스트 스위트 (공존/cap/race/retention/A05 분기/AUTH_MODE) |
| FR-11 | P2 | is_current 필드 + /me is_active 필터 |
| FR-12 | P2 | session_history_retention_days + 이력 DELETE sweep |
| FR-13 | P2 | login_anomaly_event_enabled — 신규 IP/UA SystemEvent |
| FR-14 | P2 | 성공 로그인 IP rate limit 보강 |
| FR-15 | P3 | SSO env 게이트 예약 (SSO_ENABLED=False 등록만 — 본체는 SSO PRD) |

예상 복잡도: Track C (10+ 파일, 아키텍처 정책 변경) — **PRD 우선 규율 적용 대상**.

### 즉시 처리 가능 항목 (참고)

결함 ②③④는 단독으로도 배포 가능한 순수 버그픽스지만, 같은 차수(FR-02/04/09)로 묶는 것이 하루 1차수·5중 싱크 규율에 부합.

### 테스트 강화 필요

세션 동시성 신규 시나리오는 현재 커버리지 0% — FR-10이 필수 동반. 기존 `test_session_settings.py`는 응답 필드 추가로 확장 필요. `session_enabled` 기능 효과(10년 토큰 발급) 검증도 미존재(이번 분석에서 확인된 공백).
