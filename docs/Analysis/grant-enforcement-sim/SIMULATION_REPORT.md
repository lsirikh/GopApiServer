# Grant 집행 — PRD 검증 시뮬레이션 리포트

- **작성일**: 2026-07-21
- **대상 PRD**: `docs/prds/grant-enforcement-hardening-prd.md` (v3.0)
- **harness**: `docs/Analysis/grant-enforcement-sim/simulate.py`
- **로그**: `docs/Analysis/grant-enforcement-sim/logs/unit{A,B,C,C2,D}_run{1,2}.log` + `summary_run{1,2}.log`
- **관련**: GIS `docs/Analysis/Grant_Enforcement_Server_Analysis.md` 검토(전수 인용 100% 일치)의 실행 검증판

---

## 0. 한줄 결론

**PRD의 핵심 설계 전제는 시뮬레이션으로 전부 입증됐다 (128/128 PASS, 2회 결정론 동일).** 특히 GIS 문서와 리뷰가 주장한 **경계초 정합**(`valid_until==now` → 차단 & EXPIRED)이 실제 `grant_status`/`is_valid_now` 호출로 **48개 grant 조합 전수**에서 성립함을 확인했다. **모순 0건** — PRD는 설계상 건전하다. 또한 시뮬은 **4-c(미등록 경로 default-allow)** 를 실측 표면화(→FR-09)하고, **default-deny 전환 blast-radius를 6셀**(token+미등록+¬allowlist, `user=none`·`admin` 포함)로 정량 한정해 "전 라우트 audit 선결"을 근거화했다.

---

## 1. 방법 (충실도)

| 요소 | 방식 | 충실도 |
|---|---|---|
| `grant_status` / `is_valid_now` | **실제 import 호출** (`app.services.grant_service`) | 100% (프로덕션 코드) |
| `_role_group_allows` / `_merge_modules` | **실제 import 호출** (`app.routers.auth`) — `REAL_AUTH_IMPORT=True` | 100% (프로덕션 코드) |
| `_active_grants` 필터 | SQL이라 DB 없이 호출 불가 → **소스 충실 복제** 후 실제 `grant_status`와 **교차검증**(c3) | 복제 + 실코드 대조 |
| `enforce_matrix` 결정 | 소스(`matrix_enforcer.py:100-125`) 복제, 라인 주석 병기 | 복제 + 라인 대조 |
| 시각(now) | **고정** `2026-07-21T12:00:00` 주입 → 결정론(NFR-02 방식 그대로) | — |

- **2회 실행 결정론**: `unitX_run1.log` vs `run2.log` diff 결과 **유일 차이 = 헤더의 `[run1]/[run2]` 태그**. 128개 결과행 전부 동일 → 결정론 입증(sleep·실시간 clock 미사용).

---

## 2. 시나리오 매트릭스 (총 128 — "최대한 많이")

| Unit | 시나리오 | 수 | 무엇을 증명 |
|---|---|---|---|
| **A** 유효성/경계 | `valid_from`{과거·NOW·미래} × `valid_until`{NULL·과거·NOW·미래} × `revoked`{live·revoked} × `is_active`{T·F} **전수 카테시안** | **48** | 경계초 정합(S-1) · is_active 비의존(4-b/NFR-01) · 세 술어 일치 |
| **B** 합집합 | 등급 보유/미보유 × grant{유효·만료·대기·회수·타모듈·비활성그룹·혼합} | **10** | `_effective_allows` 등급 ∪ 유효 grant (FR-02) |
| **C** enforce_matrix | `AUTH_MODE`{public·token} × 등록{T·F} × user{none·admin·nonadmin} × effective{T·F} 전수 | **24** | token 집행/403 · admin bypass · 미등록 default-allow(4-c) |
| **C2** default-deny(FR-09) | 위 + `public_allow`{T·F}(미등록 시) — 현행 대비 셀 diff | **36** | default-deny blast-radius=**6셀**(token+미등록+¬allowlist, user=none·admin 포함) |
| **D** sweep/통지 | is_active 표시성 2 + publish 게이트 2 + 자연만료 지연 6 | **10** | 스윕 표시전용(S-3) · 게이트(S-2) · 실시간 통지 지연(4-a) |

---

## 3. Unit A — 경계초 정합 (핵심)

검사 4종: `c1` status 정확 · `c2` `is_valid_now==(status==ACTIVE)` · `c3` **`active_predicate ⟺ status==ACTIVE`(집행⟺상태)** · `c4` **is_active 비의존**(플립해도 동일).

**결정적 경계 행 (실제 `grant_status` 출력):**

```
[PASS] live from-past   until-NOW   isact=T | status=EXPIRED valid=False is_valid_now=False | c1c2c3c4=1111  <<경계
[PASS] live from-past   until-NOW   isact=F | status=EXPIRED valid=False is_valid_now=False | c1c2c3c4=1111  <<경계
[PASS] live from-NOW    until-NULL  isact=T | status=ACTIVE  valid=True  is_valid_now=True  | c1c2c3c4=1111  <<경계
[PASS] live from-NOW    until-future isact=T| status=ACTIVE  valid=True  is_valid_now=True  | c1c2c3c4=1111  <<경계
[PASS] live from-NOW    until-NOW   isact=T | status=EXPIRED valid=False is_valid_now=False | c1c2c3c4=1111  <<경계
```

- **`valid_until==now` → `EXPIRED` + `valid=False`(차단)** — GIS 문서/리뷰가 주장한 `>`(집행) vs `<=`(상태)의 경계 정합을 **실코드로 확증**. `is_active`가 T든 F든 동일(c4) → 스윕 지연과 무관.
- **`valid_from==now` → 즉시 `ACTIVE`**(좌경계 포함). 
- 48/48 PASS. → **PRD FR-01(경계초 회귀) 은 실제로 통과할 테스트**임이 사전 확인됨.

---

## 4. Unit B — 합집합 집행 (실제 auth 헬퍼)

10/10 PASS. 핵심 행:
- `role 미보유 + 유효 grant(cam:control)` → **allow** (grant가 권한 부여)
- `role 미보유 + 만료 grant(cam:control)` → **deny** (만료 grant의 권한은 **무시** — active 집합서 제외)
- `role 미보유 + 유효 grant지만 그룹 비활성` → **deny** (`_role_group_allows`가 그룹 `is_active` 확인)
- `혼합(만료+유효)` → **allow** (유효분만 반영)
→ **FR-02(집행 합집합)** 의 기대 동작이 실제 헬퍼로 재현됨.

---

## 5. Unit C — enforce_matrix 결정표 (24 전수)

24/24 PASS. **주목 행(★):**

```
[PASS] token reg=True  nonadmin eff=False -> 403(:122)                  ★만료/무권한 차단=403
[PASS] token reg=False none     eff=*     -> ALLOW(default-allow :105)  ★미등록=default-allow(4-c)
[PASS] token reg=False nonadmin eff=*     -> ALLOW(default-allow :105)  ★미등록=default-allow(4-c)
```

- **token + 등록경로 + 비ADMIN + ¬effective → 403** = grant 만료/무권한 시 집행 차단 경로(FR-02 E2E가 겨눌 지점).
- **token + 미등록경로 → 무조건 ALLOW** (토큰 없어도) = **4-c 스코프 주의의 실측**. grant가 열어야 할 경로가 `PERMISSION_MAP` 미등록이면 **누구에게나 허용**. → PRD FR에 "대상 경로 등록 확인(V-02)" + default-deny 검토를 명시할 근거.

---

## 5b. Unit C2 — default-deny 변형 (FR-09 blast-radius)

36/36 PASS. 현행(Unit C, default-allow) 대비 **접근결과가 바뀌는 셀은 정확히 6개**:

```
token reg=False pub_allow=False user=none     eff=* | default-allow → 403(default-deny)  <<CHANGED
token reg=False pub_allow=False user=admin    eff=* | default-allow → 403(default-deny)  <<CHANGED
token reg=False pub_allow=False user=nonadmin eff=* | default-allow → 403(default-deny)  <<CHANGED
```

- 변경은 **오직 `token + 미등록 + ¬public_allowlist`** 셀에서만. public 모드·등록 경로·public-allowlist 경로는 **불변**.
- ⚠ **`user=none`(무토큰)·`user=admin` 도 403** — 미등록·비allowlist 경로는 관리자·헬스체크도 차단. → **미분류 경로 0** 이 default-deny 절대 선결(V-08). FR-09가 라우트 audit + allowlist + **관찰(shadow) 모드** 를 포함하는 이유.
- 검출 기준 = **접근결과(ALLOW/BLOCK-401/BLOCK-403)**, 사유 라벨 차이 무시. ※ 초기 harness가 라벨 기준으로 오검출(30/36) → 결과 기준 교정 후 36/36 (시뮬이 harness 자체 결함도 노출).

---

## 6. Unit D — sweep · 게이트 · 통지 지연

10/10 PASS.
- **Part1(표시성)**: 만료 grant는 `is_active` T/F 무관 **집행차단=True**. `sweep_due`는 `is_active=True`일 때만 True → 스윕은 표시 플래그만 정리(S-3, 보안 무관).
- **Part2(게이트)**: `NATS_REVOKE_ENABLED=False→발행X`, `True→발행O` (nats_revoke_publisher.py:145).
- **Part3(자연만료 통지 지연)** — sweep(10m)이 유일 발행 소스일 때:

| 만료시각 t | sweep-only 통지지연 | per-grant 타이머 |
|---|---|---|
| 0.0m | 0.0m | 0m |
| 0.5m | 9.5m | 0m |
| 3.0m | 7.0m | 0m |
| 7.0m | 3.0m | 0m |
| 9.9m | ≈0.1m | 0m |
| 10.0m | 0.0m | 0m |

→ **최악 10m 지연**. **4-a 정량 확인** → PRD **FR-07(per-grant fire)** 필요성 근거.

---

## 7. PRD 교차검증 (FR별 verdict)

| PRD 항목 | 시뮬 근거(Unit) | Verdict |
|---|---|---|
| FR-01 경계초 회귀(sync+async+status) | A 48/48, 경계행 EXPIRED/차단 | ✅ 전제 확증 — 테스트가 통과할 것 |
| FR-02 token HTTP E2E(허용/만료403/회수403/PENDING/경계) | A(상태) + B(합집합) + C(403 경로) | ✅ 기대 동작 전부 재현 |
| FR-03 async_db 격리 | (시뮬 대상 아님 — 인프라) | ➖ 코드 실행 무관, 별도 검증 |
| FR-04 async sweep 발행 | D Part1/2 (분류+게이트) | ✅ 로직 재현(실 호출은 통합테스트) |
| FR-05 문서 커버리지/회신 | C(4-c 표면화) | ✅ 근거 보강 |
| **FR-06 NATS 활성화(S-2)** | D Part2 게이트 | ✅ 서버측 발행 로직 정상, 활성=배포게이트 |
| **FR-07 실시간 만료 통지(4-a)** | D Part3 지연표 | ✅ sweep-only ≤10m → per-grant 필요 정량화 |
| **FR-08 스윕 주기 설정화(S-3)** | D Part1/3 | ✅ 표시전용 확인, 주기 단축은 지연 상한만 축소 |
| 4-c 미등록 default-allow(스코프) | C ★행 | ⚠ 표면화 → FR-09 로 승격 |
| **FR-09 default-deny 전환** | C2 6셀 CHANGED | ✅ blast-radius 6셀 한정 — user=none·admin 포함 → 라우트 audit(V-08) 선결 근거화 |

**종합**: PRD가 겨눈 모든 집행 전제가 실행으로 확증됐고(모순 0), 시뮬이 4-c를 FR-09로 승격시키며 그 blast-radius를 6셀로 한정했다. → **PRD v3.0 승인 진행 가능**(FR-09는 라우트 audit V-08 게이트).

---

## 8. 재현 방법

```bash
cd C:/workspace_python/api-test-server
python docs/Analysis/grant-enforcement-sim/simulate.py --run 1
python docs/Analysis/grant-enforcement-sim/simulate.py --run 2
# 결정론: diff logs/unitA_run1.log logs/unitA_run2.log  → (헤더 태그 외) 동일
```
> ※ 실행 시 `JWT_SECRET_KEY 기본값` UserWarning 1건 = dev 설정 검증기(무해). 시뮬 결과 무관.
