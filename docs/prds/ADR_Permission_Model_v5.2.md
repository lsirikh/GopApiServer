# ADR — 권한 모델 단순화 (Role = ADMIN 특권 + 기능권한 = 그룹)

- **상태**: Accepted (차장님 결정 2026-06-30, "리스크 최소안")
- **작성**: WS-A (RBAC) / **구현 분담**: WS-A·WS-B (아래 §6)
- **연관**: PRD_GOP_Server_RBAC_Enforcement / PRD_Permission_Group_Scheduling / 조율판 R8·R9
- **적용 안전성**: 현재 `AUTH_MODE=public`(휴면) → 본 변경은 **행동 무변(집행 0)**, `AUTH_MODE=token` 플립 시 함께 활성. 무위험 점진 적용.

---

## 1. 결정 (두괄식)

| 항목 | 결정 |
|---|---|
| **role(등급)** | **ADMIN만 특권** (require_perm bypass + `require_admin` 25곳 + 마지막ADMIN 가드). 비-ADMIN role(OPERATOR/VIEWER/MAINTAINER)은 **정보 라벨**(권한 효력 0). **role enum 4종 유지**(변경 안 함 = 리스크 최소) |
| **기능 권한** | **사용자에게 배정된 그룹 매트릭스 ∪ 유효 grant** (R9 중앙 enforcer 그대로). 모듈/verb 판정은 100% 매트릭스(=미들웨어, R8) |
| **`name==role` 자동해석** | **폐기** — 권한을 role 이름으로 자동 유도하지 않음. 권한은 **명시 배정(group_id) + grant**에서만 |
| **시드** | **최소**: ADMIN 그룹 + admin 부트스트랩 사용자. 그 외 그룹은 ADMIN이 **필요시 생성·배정** |
| **비-ADMIN 부트스트랩** | 그룹 배정 전 **권한 0**(안전·명시). "사용자 생성 시 그룹 배정 필수"로 운영 보완 |

> 핵심: **"ADMIN은 role로 특권, 그 외 모든 권한은 그룹"**. 프리셋/커스텀 이분법·`kind` 컬럼 불필요(차장님 단순화안 채택).

---

## 2. 배경 / 문제

- 기존: role(등급) ↔ 동명 권한그룹(`name==role`, 10~14) 자동연결 = 암묵 "프리셋". 위험:
  - **임시 등급상승**: grant로 "OPERATOR" 프리셋을 VIEWER에 부여 가능(필터 없음).
  - **오삭제/이름변경**: 프리셋 rename/삭제 시 해당 등급 전원 권한 붕괴(문자열 매칭 취약).
  - **종류 구분자 부재**: preset/custom이 데이터에 없음.
- 차장님 단순화안: "프리셋/커스텀 굳이? ADMIN 그룹만 두고 필요시 생성." → 채택.

## 3. 왜 role(ADMIN)은 못 없애나 (제약 인정)

실측: role 특수처리 **35곳**(`require_admin` 25 엔드포인트 + `role=="ADMIN"` 직접분기 10), `account_users.role` **NOT NULL**. ADMIN 권력은 그룹 매트릭스가 아니라 role 하드코딩에서 나옴 → ADMIN은 role로 남긴다(순수 그룹화는 25곳 리팩토링=대공사라 비채택). **= "ADMIN 특권 role + 나머지 그룹" 하이브리드를 의도적으로 수용.**

## 4. R8/R9와의 관계 (정합 + 1건 재조정)

- ✅ **정합**: R9 중앙 enforcer(`app/security/matrix_enforcer.py`) + R8 "매트릭스=미들웨어, 코드 특별취급 0" 은 본 ADR의 "기능권한=매트릭스"와 동일 방향. **enforcer 유지**.
- 🔧 **재조정 1건**: R8 메모 "OPERATOR 권한변경=`POST /user-groups/12/permissions`(group 12=OPERATOR-named)" 는 `name==role` 가정. ADR 적용 후:
  - role-named 그룹(10~14)은 **자동연결을 잃고 "그냥 일반 그룹"**이 됨(편의상 기본 그룹으로 남겨도 됨).
  - "OPERATOR 사용자의 권한 변경" = 그 사용자들이 **배정된 그룹**(group_id/grant)의 매트릭스 편집. group 12를 계속 쓰려면 OPERATOR 사용자에게 group_id=12 배정.

## 5. 결과 / 영향

- **유지(불변)**: `require_admin` 25곳·ADMIN bypass·마지막ADMIN 가드(전부 role 기반) / R9 enforcer / grant 스케쥴링 / 휴면(public 무집행).
- **변경**: `auth.py` `_resolve_role_group`/`_effective_allows`의 권한 원천 = `name==role` → **배정 그룹(group_id) + grant**. (effective_permissions_payload 동일.)
- **시드**: `init_sample_data.py` 역할명 그룹 자동시드 → ADMIN 그룹 + admin 사용자 최소화(나머지 옵션).
- **재현성**: 차장님 static-seed 원칙 충족 위해 **최소 시드(ADMIN)는 유지**(환경 3종 일관).

## 6. 구현 분담 (조율판 R10에 등재)

| 작업 | 담당 | 파일/경계 |
|---|---|---|
| `_resolve_role_group` 권한원천 `name==role`→`group_id` + grant 로 변경 | **WS-B** | `app/routers/auth.py` (WS-B 락) + `app/security/*` enforcer |
| role 비-ADMIN 라벨화 확정(코드상 특별취급 0 확인) | **WS-B** | enforcer / auth.py |
| 시드 최소화(ADMIN 그룹 + admin) | **조율** | `init_sample_data.py` (편집 전 조율판 표시) |
| 명세서/가이드 반영(권한모델 §) + 본 ADR | **WS-A** | spec doc · GUIDE · ADR |
| `require_admin` 25곳 | **불변(유지)** | role 기반 그대로 |

## 7. 대안 (비채택)

- **A. role→ADMIN/USER 2종 단순화**: 가장 깔끔하나 enum 변경 + 마이그레이션 + 35곳 영향 → **리스크 높음, 후속 검토로 보류**.
- **B. `kind`(ROLE_PRESET/CUSTOM) 구분자 도입**: 프리셋 유지 전제 → 차장님 "프리셋 불필요"로 폐기.
- **C. require_admin 전부 권한기반 리팩토링**: 대공사, 비채택.

---

**요약**: role은 ADMIN만 특권으로 남기고, 기능 권한은 전부 "배정 그룹 + grant 매트릭스"로. `name==role` 자동해석만 폐기. 휴면 상태라 무위험 점진 적용 — 코드 변경은 WS-B(auth.py/enforcer), 시드는 조율, 문서는 WS-A.
