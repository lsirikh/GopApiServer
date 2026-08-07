# PRD — Role 축소 (ADMIN/USER) + 등급 그룹 → Preset Group 정리

- **작성일**: 2026-07-02
- **상태**: Approved
- **버전**: v1.0
- **차수 대상**: v5.3 Phase 2
- **언어/프레임워크**: Python 3.11 / FastAPI (SQLAlchemy + PostgreSQL 16)
- **요청 배경**: 차장님 지시 (2026-07-02) — "Admin과 User로만 남기고 기존 나눈 등급은 다 없애던지 아니면 preset 권한 그룹으로 넘기는 게 좋지 않아?"
- **연관 차수**: v5.3 Legacy User Removal (Legacy User 삭제 = AccountUser 통일) → v5.3 Phase 2 Role Simplification (역할 스키마 단순화 = 개념 완성)
- **연관 잔존**: v5.2 R10① `name==role` 자동해석 폐기 정책의 스키마 완성

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-07-02 | v1.0 | 초안 작성 | 차장님 지시 대응 (개념 오염 근본 해결) | EnumUserRole + DB role 컬럼 값 + UserGroup 5건 rename + Swagger + 명세 |
| 2026-07-02 | 1.0 | 사용자 승인 | "차장님 지시 대응 v5.3 Phase 2 진행 — role 축소 + Preset 그룹" | 상태 Draft → Approved |

---

## 1. 개요

### 목적

`EnumUserRole` (현행 5종: ADMIN / MAINTAINER / OPERATOR / VIEWER / GUEST)을 **2종**(ADMIN / USER)으로 축소하고, 기존 4개 등급 그룹(MAINTAINER/OPERATOR/VIEWER/GUEST)을 **Preset 권한 그룹**으로 rename하여 "role은 특권 라벨(ADMIN 여부)만, 권한 원천은 그룹 매트릭스"라는 v5.2 R10① 정신을 스키마 레벨에서 완성한다.

### 배경 및 동기

#### 현재 구조의 개념 오염

**Enum 5종과 등급 그룹 5건의 이름 겹침**:

```
EnumUserRole          UserGroup.name (등급)
├── ADMIN         ↔   "ADMIN"       (id=10)
├── MAINTAINER    ↔   "MAINTAINER"  (id=11)
├── OPERATOR      ↔   "OPERATOR"    (id=12)
├── VIEWER        ↔   "VIEWER"      (id=13)
└── GUEST         ↔   "GUEST"       (id=14)
```

**v5.2 R10① 이전** — 자동해석: role="OPERATOR"면 name="OPERATOR" 등급 그룹 자동 조회 → **role과 그룹이 사실상 하나**로 취급됨.

**v5.2 R10① 이후** — 자동해석 폐기 + group_id 명시 배정 강제. 하지만:
- `EnumUserRole` 값이 여전히 5종
- 등급 그룹 5건이 이름 그대로
- role은 사실상 ADMIN 특권 판정에만 사용, 나머지 4종은 **라벨링 잔재**

#### 문제

| 문제 | 영향 |
|---|---|
| **개념 모호성** | .NET 클라 / GIS 팀 / 운영자가 "role과 그룹 이름 왜 같지?" 혼란 |
| **관리 실수 여지** | role만 바꾸고 group_id 안 바꾸는 실수 (자동해석 폐기 후엔 무효, 개념 오해) |
| **확장성 제약** | 새 등급 필요 시 EnumUserRole 수정 + DB enum 마이그레이션 (비파괴적 아님) |
| **UI 이중 개념** | 관리 UI에 role 드롭다운(5) + 그룹 배정 UI (5+3) — 개념 겹침 |
| **v5.2 R10① 정신 불완전 반영** | "role은 라벨" 정책이 스키마엔 잔재 (원칙과 스키마 불일치) |

#### 해결 방향

1. **`EnumUserRole` 축소**: 5종 → **2종** (ADMIN / USER)
   - `ADMIN`: 특권 라벨 (bypass 판정)
   - `USER`: 일반 사용자 라벨 (권한은 group_id로만)
2. **등급 그룹 4건 rename**: preset 개념으로 이관
   - `MAINTAINER` → `Preset - 유지보수자`
   - `OPERATOR` → `Preset - 운영자`
   - `VIEWER` → `Preset - 조회자`
   - `GUEST` → **삭제** (사용자 0명)
3. **`ADMIN` 등급 그룹(id=10) 삭제**: ADMIN은 bypass라 그룹 매트릭스 무의미 (admin 사용자의 group_id는 NULL로)
4. **팀 그룹 3건 유지**: 운영팀 / 관제팀 / 유지보수팀 (그대로)

### Phase 0 사전 조사 결과 (근거)

| 조사 항목 | 결과 | 위험도 |
|---|---|:---:|
| `require_role(...)` 사용처 | **1건만** (`auth.py:95` = `require_admin = require_role("ADMIN")`) | 🟢 None |
| `if role == "OPERATOR/VIEWER/MAINTAINER/GUEST"` 조건 | **0건** | 🟢 None |
| JWT payload `role` 값 사용 | 값 전달만 (login/refresh 응답 + user 정보) — 로직 조건 없음 | 🟢 Low |
| GUEST 등급 그룹 배정 사용자 | **0명** | 🟢 삭제 가능 |
| UserGroupGrant (v5.2 스케쥴링) | 0건 | 🟢 영향 없음 |
| DB 실 데이터 (admin 외 role) | 7건 사용 중 (모두 group_id로 그룹 명시 배정됨) | 🟢 이주 안전 |
| 예시/시드 문자열 | init_db.py, init_sample_data.py, audit_logs.py, schemas/audit_log.py | 🟡 갱신 필요 |
| 명세서 role 언급 | 22건 | 🟡 갱신 필요 |
| tests/ role 사용 | test_account_auth.py 다수 (`role="VIEWER"` 등) — .gitignore 로컬만 | 🟡 별도 정리 |

**결론**: 로직 breaking 없음. 데이터 마이그레이션 + 시드 코드 정리 + 명세 갱신이 주요 작업.

---

## 2. 요구사항

### 기능 요구사항 (Functional Requirements)

| ID | 요구사항 | 우선순위 | 예상 태스크 수 |
|----|---------|---------|--------------|
| **FR-RS-01** | `EnumUserRole` 축소 — 5종 → 2종 (`ADMIN`, `USER`) | High | ~2개 |
| **FR-RS-02** | DB 마이그레이션 v57 — `account_users.role` 값 UPDATE (`MAINTAINER`/`OPERATOR`/`VIEWER`/`GUEST` → `USER`) + Enum 축소 검증 | High | ~2개 |
| **FR-RS-03** | 등급 그룹 rename 마이그레이션 — 4건 (`MAINTAINER`→`Preset - 유지보수자`, `OPERATOR`→`Preset - 운영자`, `VIEWER`→`Preset - 조회자`, `GUEST`→**DELETE**) + `ADMIN` 등급 그룹(id=10) 삭제 + admin 사용자 group_id NULL 업데이트 | High | ~3개 |
| **FR-RS-04** | `init_db.py` — 등급 그룹 시드 코드 정정 (5건 → 3 Preset, ADMIN/GUEST 제외) + `ensure_role_permission_groups()` 함수명/주석 정리 | High | ~2개 |
| **FR-RS-05** | `init_sample_data.py` — 시드 사용자 role 값 정정 (`OPERATOR/VIEWER/MAINTAINER` → `USER`) + group_id 배정 유지 | Mid | ~2개 |
| **FR-RS-06** | `audit_logs.py`, `schemas/audit_log.py` 예시 문자열 정정 — before/after 예시 `{"role": "OPERATOR"}` → `{"role": "USER"}` | Low | ~1개 |
| **FR-RS-07** | 명세서 `GOP_Restful_Api_연동설계.md` — role 언급 22건 정정 + v5.3 Phase 2 헤더/푸터/변경 이력 행 | High | ~2개 |
| **FR-RS-08** | Swagger schema 정합 — `EnumUserRole` enum 값 2종만 노출 확인 | High | ~1개 |
| **FR-RS-09** | .NET/GIS 클라 팀 안내서 — `docs/GOP_Server_API_v5.3 Phase 2_Role_Simplification_NOTIFY.md` 신설 (변경 내용 + 클라 대응 가이드 + 마이그레이션 시각화) | High | ~2개 |
| **FR-RS-10** | reverse migration SQL — `v57_role_simplification_reverse.sql` 사전 작성 (롤백 대비) | High | ~1개 |
| **FR-RS-11** | 실측 검증 매트릭스 — admin login + gop_maint/op/viewer login (role=USER로 정정 후) + Bearer 토큰 + `/api/auth/me` + 기존 그룹 매트릭스 유지 확인 | High | ~3개 |
| **FR-RS-12** | Container rebuild + Image + Swagger 5-sync + 안전점 태그 (`pre-role-simplification` + `v5.3 Phase 2-final-stable`) | High | ~2개 |

**합계**: 예상 태스크 ~23개, 실 작업 시간 ~4~5h.

### 비기능 요구사항 (Non-Functional Requirements)

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-RS-01 | 무회귀 (권한 실효) | 마이그레이션 후 각 사용자의 **실 유효 권한 매트릭스 100% 유지** (group_id 그대로, preset 그룹 이름만 변경) | before/after `effective_permissions_payload` 매트릭스 diff — 8 사용자 각각 검증 |
| NFR-RS-02 | 무회귀 (API 응답) | 30 라우터 응답 형식/코드 유지 (AUTH_MODE=public에서 무영향) | 회귀 pytest + 실 API curl 스팟 검사 (v5.3과 동일 매트릭스) |
| NFR-RS-03 | 로그인 무영향 | admin login 200 + USER 라벨 사용자 login 200 + JWT payload `role` 값 `ADMIN`/`USER`만 노출 | curl 로그인 + JWT decode 검증 |
| NFR-RS-04 | Swagger 정합 | `components.schemas.EnumUserRole.enum` = `["ADMIN", "USER"]` 확정 | `curl /openapi.json` + Python 검증 |
| NFR-RS-05 | 롤백 안전 | reverse migration SQL로 Enum + 데이터 + 그룹 이름 완전 복원 가능 | 롤백 dry-run 검증 (별도 DB에서) |
| NFR-RS-06 | 이력 보존 | 마이그레이션 audit_log에 ROLE_CHANGED / GROUP_RENAMED 기록 남김 | audit_logs 조회로 이력 확인 |

---

## 3. 기술 설계

### 3.1 아키텍처 결정 및 이유

**결정**: **옵션 A** (role 축소 + 등급 그룹 → Preset rename, admin 등급 그룹 + GUEST 등급 그룹 삭제)

**대안 비교** (2026-07-02 재차 검토):

| 대안 | 장점 | 단점 | 선정 |
|---|---|---|:---:|
| A. role 2종 + Preset 그룹 rename (본 PRD) | 하위호환 최선, 개념 명확, 관리자 편의 유지 | preset 그룹 이름 UI 노출 변경 | ✅ |
| B. role 2종 + 등급 그룹 완전 삭제 | 최대 단순 | 관리자가 그룹 매번 만들어야 함, 운영 부담 | ✗ |
| C. 현행 유지 + 문서 명확화만 | 무변경 | 개념 오염 지속, GIS/클라 팀 회신 어려움 | ✗ |
| D. role 3종 (ADMIN/POWER/USER) | 중간 지점 | 여전히 라벨 오염, 왜 3종인지 근거 부족 | ✗ |

### 3.2 데이터 모델

**Before (v5.3 현재)**:

```
account_users
├── role: EnumUserRole (5종)
│     ├── ADMIN
│     ├── MAINTAINER   ← 라벨 잔재
│     ├── OPERATOR     ← 라벨 잔재
│     ├── VIEWER       ← 라벨 잔재
│     └── GUEST        ← 라벨 잔재
└── group_id: FK → user_groups.id

user_groups (8건)
├── 1  운영팀        (팀)
├── 2  관제팀        (팀)
├── 3  유지보수팀    (팀)
├── 10 ADMIN         (등급, 삭제 대상)
├── 11 MAINTAINER    (등급, rename)
├── 12 OPERATOR      (등급, rename)
├── 13 VIEWER        (등급, rename)
└── 14 GUEST         (등급, 삭제 대상, 사용자 0명)
```

**After (v5.3 Phase 2)**:

```
account_users
├── role: EnumUserRole (2종)   ← 축소
│     ├── ADMIN                (특권 판정용)
│     └── USER                 (일반, 권한은 group_id로만)
└── group_id: FK → user_groups.id (그대로)

user_groups (6건)
├── 1  운영팀              (팀, 유지)
├── 2  관제팀              (팀, 유지)
├── 3  유지보수팀          (팀, 유지)
├── 11 Preset - 유지보수자 ← rename (id 유지, 배정 사용자 유지)
├── 12 Preset - 운영자    ← rename (id 유지, 배정 사용자 유지)
└── 13 Preset - 조회자    ← rename (id 유지, 배정 사용자 유지)

삭제된 그룹:
├── 10 ADMIN  → admin 사용자 group_id를 NULL로 (bypass라 무관)
└── 14 GUEST  → 사용자 0명이라 안전 삭제
```

**Migration SQL** (`app/migrations/v57_role_simplification.sql`):

```sql
BEGIN;

-- 1. role 값 이주 (admin 외 → USER)
UPDATE account_users
SET role = 'USER'
WHERE role IN ('MAINTAINER', 'OPERATOR', 'VIEWER', 'GUEST');

-- 검증 1: role 값이 ADMIN/USER만 남아있는지
DO $$
DECLARE
  invalid_cnt INTEGER;
BEGIN
  SELECT count(*) INTO invalid_cnt
  FROM account_users
  WHERE role NOT IN ('ADMIN', 'USER');
  IF invalid_cnt > 0 THEN
    RAISE EXCEPTION 'role 값에 ADMIN/USER 이외 % 건 존재', invalid_cnt;
  END IF;
END $$;

-- 2. 등급 그룹 rename (id 유지)
UPDATE user_groups SET name = 'Preset - 유지보수자',
                       description = '표준 프리셋 — 유지보수자 권한 매트릭스 (참고 배정용)'
WHERE id = 11;
UPDATE user_groups SET name = 'Preset - 운영자',
                       description = '표준 프리셋 — 운영자 권한 매트릭스 (참고 배정용)'
WHERE id = 12;
UPDATE user_groups SET name = 'Preset - 조회자',
                       description = '표준 프리셋 — 조회자 권한 매트릭스 (참고 배정용)'
WHERE id = 13;

-- 3. admin 사용자 group_id를 NULL로 (ADMIN은 bypass라 그룹 매트릭스 무의미)
UPDATE account_users SET group_id = NULL WHERE role = 'ADMIN';

-- 4. ADMIN 등급 그룹 삭제 (id=10)
DELETE FROM user_groups WHERE id = 10 AND name = 'ADMIN';

-- 5. GUEST 등급 그룹 삭제 (id=14, 사용자 0명 확인)
DO $$
DECLARE
  guest_users INTEGER;
BEGIN
  SELECT count(*) INTO guest_users FROM account_users WHERE group_id = 14;
  IF guest_users > 0 THEN
    RAISE EXCEPTION 'GUEST 그룹(id=14)에 % 명 배정됨 — 삭제 불가', guest_users;
  END IF;
END $$;
DELETE FROM user_groups WHERE id = 14 AND name = 'GUEST';

-- 6. 검증: user_groups 6건 확정
DO $$
DECLARE
  grp_cnt INTEGER;
BEGIN
  SELECT count(*) INTO grp_cnt FROM user_groups;
  IF grp_cnt != 6 THEN
    RAISE EXCEPTION 'user_groups 6건 기대 vs 실제 %', grp_cnt;
  END IF;
END $$;

COMMIT;
```

**Reverse Migration** (`app/migrations/v57_role_simplification_reverse.sql`):

```sql
-- v5.3 Phase 2 롤백용 — Enum 5종 + 등급 그룹 5건 재생성
-- ⚠ 주의: admin 외 사용자의 role 값은 원 값 복원 불가 (USER로 통일됨) — 일괄 VIEWER로 재설정

BEGIN;

-- 1. 등급 그룹 재생성 (ADMIN + GUEST 복원)
INSERT INTO user_groups (id, name, description, permissions, is_active, created_at, updated_at)
VALUES
  (10, 'ADMIN',   '권한 등급 — 관리자(전체)', '{}'::jsonb, true, NOW(), NOW()),
  (14, 'GUEST',   '권한 등급 — 게스트',       '{}'::jsonb, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. Preset 그룹을 원 이름으로 복원
UPDATE user_groups SET name = 'MAINTAINER', description = '권한 등급 — 유지보수자'
WHERE id = 11 AND name LIKE 'Preset%';
UPDATE user_groups SET name = 'OPERATOR', description = '권한 등급 — 운영자'
WHERE id = 12 AND name LIKE 'Preset%';
UPDATE user_groups SET name = 'VIEWER', description = '권한 등급 — 조회자'
WHERE id = 13 AND name LIKE 'Preset%';

-- 3. role 값 복원 (USER → VIEWER, admin 유지)
UPDATE account_users SET role = 'VIEWER' WHERE role = 'USER';

-- 4. admin 사용자 group_id 복원 (10)
UPDATE account_users SET group_id = 10 WHERE role = 'ADMIN';

COMMIT;

-- ★ 참고: 원 role 값 복원은 실 데이터 손실이므로 별도 백업이 필요할 수도 있음.
--          운영 시 실제 원 role 값을 별도 log 테이블에 백업 권장.
```

### 3.3 EnumUserRole 축소 코드

**Before** (`app/utils/enums.py:359~371`):

```python
class EnumUserRole(str, Enum):
    """User role enumeration (5종) — PRD: PRD_Account_Design.md Section 3.2"""
    ADMIN = "ADMIN"
    MAINTAINER = "MAINTAINER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"
    GUEST = "GUEST"
```

**After**:

```python
class EnumUserRole(str, Enum):
    """User role enumeration (2종) — v5.3 Phase 2 (2026-07-02 role 축소)

    v5.2 R10① 정신 완성: role은 특권 라벨만, 실 권한은 group_id로.
    - ADMIN: 시스템 관리자 (require_admin bypass, 매트릭스 무관)
    - USER : 일반 사용자 (권한은 배정 group_id 매트릭스 + 유효 grant 합집합)

    ★ Legacy 4종(MAINTAINER/OPERATOR/VIEWER/GUEST)은 Preset 권한 그룹으로 이관:
       user_groups 테이블의 "Preset - 유지보수자/운영자/조회자" 참조.
    """
    ADMIN = "ADMIN"
    USER = "USER"
```

### 3.4 auth.py 확인 사항 (변경 없음)

- `require_role(*roles)` 팩토리 — 유지 (일반화 인프라)
- `require_admin = require_role("ADMIN")` — 그대로 작동
- `_resolve_role_group(user)` — group_id만 사용 (v5.2 R10①) — 그대로 작동
- ADMIN 사용자는 `group_id=NULL`이지만 bypass로 통과
- `USER` 사용자는 `group_id`로 배정된 그룹 매트릭스 사용 (Preset 또는 팀)

### 3.5 시드 코드 정정

**`app/utils/init_db.py:59~88`**:

```python
def ensure_role_permission_groups(db: Session):
    """Preset 권한 그룹(3건)을 idempotent 보장한다 — v5.3 Phase 2 (role 축소).

    v5.3 Phase 2 변경:
    - ADMIN 등급 그룹 제거 (bypass라 매트릭스 무의미)
    - GUEST 등급 그룹 제거 (사용자 0명)
    - MAINTAINER/OPERATOR/VIEWER → "Preset - {한글명}"으로 rename
    """
    presets = {
        "Preset - 유지보수자": {...},  # id=11 유지
        "Preset - 운영자":    {...},   # id=12 유지
        "Preset - 조회자":    {...},   # id=13 유지
    }
    # ... (idempotent upsert 로직)
```

**`app/utils/init_sample_data.py:153~165`**:

```python
# Before: role="OPERATOR" / "VIEWER" / "MAINTAINER"
# After: role="USER" (권한은 group_id로만)
{"login_id": "operator1", "name": "김운영", "role": "USER",   "group_id": 12, ...},
{"login_id": "monitor1",  "name": "박관제", "role": "USER",   "group_id": 2,  ...},
{"login_id": "maintainer1","name":"정유지", "role": "USER",   "group_id": 11, ...},
```

### 3.6 API 응답 형식 (변경 없음)

- `POST /api/auth/login` 응답의 `data.user.role`은 `"ADMIN"` 또는 `"USER"`만 노출
- 기존 `.NET` 클라의 role 값 처리는 값만 다름 (조건 코드 없다고 조사됨)
- `data.user.permissions` 매트릭스는 그룹에서 산출되므로 형식 동일

---

## 4. 범위

### In Scope

- `EnumUserRole` 축소 (5종 → 2종)
- DB 마이그레이션 v57 (role UPDATE + user_groups rename/DELETE)
- `init_db.py` / `init_sample_data.py` 시드 정정
- audit_logs 예시 문자열 정정
- 명세서 v5.3 Phase 2 갱신
- Swagger 정합 검증
- .NET/GIS 팀 안내서 (`GOP_Server_API_v5.3 Phase 2_Role_Simplification_NOTIFY.md`)
- 실측 검증 매트릭스
- Container rebuild + 안전점 태그 + Gitea/origin push
- reverse migration SQL

### Out of Scope

- `require_role` 함수 자체 제거 (일반화 인프라라 유지)
- `require_admin` 사용처 변경 (그대로 동작)
- 팀 그룹 3건 (운영팀/관제팀/유지보수팀) — 변경 없음
- UserGroupGrant (v5.2 스케쥴링) — 사용 안 하므로 무영향
- AUTH_MODE=token 전환 — 별도 차수 (v5.5+)
- require_perm 활성화 — 별도 차수
- 클라 UI 화면 재설계 — 클라 팀 책임

---

## 5. 의존성 및 전제 조건

- **Phase 0 조사 완료** (2026-07-02): require_role 1건, role 조건 0건, GUEST 0명, UserGroupGrant 0건, 로직 breaking 없음 확인 ✅
- **v5.3-final-stable** (Legacy User 삭제 완료) — role 관련 인프라가 AccountUser 단일 통일
- **v5.2 R10① 정책 적용됨** — `_resolve_role_group`이 group_id만 사용 → role 축소해도 로직 무변경
- **AUTH_MODE=public 유지** — 이주 시 응답 무영향 (v5.3과 동일 조건)
- **UserGroupGrant 미사용** (0건) — grant 데이터 이주 불필요
- **`SESSION_COORDINATION.md`** — auth.py 편집 미필요 (Enum + 시드 코드만 변경) → WS-B와 충돌 없음

---

## 5-A. 검증 필요 항목 (Verification Prerequisites)

| ID | 검증 항목 | 검증 방법 | 확인 여부 |
|----|---------|---------|---------|
| V-RS-01 | `require_role` 사용처 = 1건 (auth.py:95만) | grep 실행 완료 | ✅ 확정 |
| V-RS-02 | `if role == "..."` 조건 코드 = 0건 | grep 실행 완료 | ✅ 확정 |
| V-RS-03 | GUEST 등급 그룹 배정 사용자 = 0명 | SQL 실행 완료 | ✅ 확정 |
| V-RS-04 | UserGroupGrant 데이터 = 0건 | SQL 실행 완료 | ✅ 확정 |
| V-RS-05 | 명세서 role 언급 22건 | grep 실행 완료 | ✅ 확정 |
| V-RS-06 | .NET 클라의 role 값 조건 코드 (외부) | 클라 팀 확인 요청 | 미확인 (별도) |
| V-RS-07 | tests/ role 사용 대응 방침 | .gitignore로 로컬만 — 별도 정리 결재 필요 | 미확정 |

---

## 5-B. 인과 결합 분석 (Causal Coupling Analysis)

| 수정 항목 | 영향 받는 다른 플로우 | 대응 방안 |
|---|---|---|
| `EnumUserRole` 축소 | JWT payload 발행 시 role 값 | admin 외 모두 "USER" 통일 (마이그레이션 v57) |
| `account_users.role` UPDATE | 로그인 응답 `data.user.role` | 값이 USER로 바뀌지만 클라 로직 조건 없음 (V-RS-02 확정) |
| `user_groups.name` rename | `_resolve_role_group` 조회 | group_id로만 조회하므로 이름 무영향 |
| ADMIN 등급 그룹 삭제 (id=10) | admin 사용자의 group_id | NULL로 UPDATE → ADMIN은 bypass라 무관 |
| GUEST 등급 그룹 삭제 (id=14) | 사용자 0명이므로 무영향 | 검증 후 DELETE |
| 시드 코드 정정 | 신규 down -v 후 재시드 | 자동 반영 (기존 데이터 무영향) |
| 명세 v5.3 Phase 2 | .NET 클라 통합 문서 참조 | NOTIFY 문서로 통지 |

**핵심 인과 사슬**:

```
Phase 1 (안전점) → Phase 2 (Enum 축소 + 시드 정정) → Phase 3 (DB 마이그레이션 v57)
     ↑                    ↑                              ↑
안전점 태그          코드 변경 + rebuild              데이터 UPDATE (권한 실효 무변경)
                                                    → Phase 4 (실측 검증) → Phase 5 (통지)
```

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|---|
| .NET 클라의 role 값 조건 코드 존재 | 낮음 | 중간 | V-RS-06 사전 확인 요청. 발견 시 클라 팀에 사전 통지 |
| DB 마이그레이션 실패 (Enum 축소 트랜잭션 오류) | 낮음 | 중간 | BEGIN/COMMIT + 검증 DO block + reverse SQL 사전 준비 |
| admin 사용자 group_id NULL 후 조회 문제 | 매우 낮음 | 낮음 | ADMIN bypass 로직으로 무관 확인. 실측 검증에 포함 |
| Preset 그룹 rename 후 UI 표기 혼란 | 낮음 | 낮음 | NOTIFY 문서에 rename 매트릭스 명시 |
| tests/test_account_auth.py role="VIEWER" 다수 | 중간 | 낮음 | .gitignore라 CI 미영향. 로컬 실행 시 skip 처리 |
| 명세 22건 정정 누락 | 중간 | 중간 | grep으로 누락 여부 확인 (완료 기준 포함) |
| GIS 팀 후속 문의 | 중간 | 낮음 | NOTIFY 문서에 FAQ 섹션 포함 |

---

## 7. 완료 기준 (Definition of Done)

- [ ] 모든 FR 구현 완료 (FR-RS-01 ~ FR-RS-12)
- [ ] NFR 검증 통과 (NFR-RS-01 ~ NFR-RS-06)
- [ ] `EnumUserRole` = `["ADMIN", "USER"]` 확정
- [ ] DB `account_users.role` 값 = `ADMIN`/`USER`만 확정
- [ ] `user_groups` 6건 (팀 3 + Preset 3) 확정, ADMIN/GUEST 그룹 삭제 확정
- [ ] 8 사용자 모두 login 200 + JWT payload role 값 `ADMIN` 또는 `USER`만 확정
- [ ] 각 사용자의 effective_permissions 매트릭스 before/after 100% 동일 확정
- [ ] Swagger `EnumUserRole.enum` = `["ADMIN", "USER"]` 확정
- [ ] 명세서 v5.3 Phase 2 (헤더/푸터/변경 이력 행) 갱신 + role 22건 정정
- [ ] CHANGELOG `[v5.3 Phase 2]` 섹션 신설
- [ ] `docs/GOP_Server_API_v5.3 Phase 2_Role_Simplification_NOTIFY.md` 신설
- [ ] 안전점 태그 `pre-role-simplification` + `v5.3 Phase 2-final-stable` 신설 + Gitea/origin push
- [ ] `session-context.md` v5.3 Phase 2 갱신
- [ ] `SESSION_COORDINATION.md` v5.3 Phase 2 마감 통지

---

## 부록 A. 실행 순서 (Phase별)

```
Phase 0 — 사전 조사 (완료 ✅)
  └─ V-RS-01~05 확정. Phase 1 진입 가능.
       ↓
Phase 1 — 안전점 + reverse SQL 사전 작성 (~15분)
  ├─ git tag pre-role-simplification
  ├─ SETUP-02 v57_role_simplification_reverse.sql 작성
  └─ SETUP-03 마이그레이션 시나리오 dry-run (별도 DB 권고 or skip)
       ↓
Phase 2 — 코드 변경 (~1h)
  ├─ IMPL-01 EnumUserRole 축소 (enums.py)
  ├─ IMPL-02 init_db.py — ensure_role_permission_groups → Preset 그룹 3건
  ├─ IMPL-03 init_sample_data.py — role="USER" 통일
  ├─ IMPL-04 audit_logs.py / schemas/audit_log.py 예시 정정
  └─ IMPL-05 grep 검증 — Legacy role 참조 코드 0건 확정
       ↓
Phase 3 — DB 마이그레이션 (~30분)
  ├─ IMPL-06 v57_role_simplification.sql 작성 + 실 적용
  ├─ IMPL-07 role 값 = ADMIN/USER 확정 검증
  ├─ IMPL-08 user_groups 6건 확정 검증 (ADMIN/GUEST 삭제)
  └─ IMPL-09 admin group_id NULL 확정 + 실 사용자 매트릭스 유지 확정
       ↓
Phase 4 — 실측 검증 (~30분)
  ├─ TEST-01 8 사용자 login 200 + JWT payload role 검증
  ├─ TEST-02 effective_permissions before/after diff 0 (각 사용자)
  ├─ TEST-03 라이브 API 스팟 검사 (14 endpoint 200 유지)
  ├─ TEST-04 Container rebuild + healthy + Swagger EnumUserRole 확정
  └─ TEST-05 최종 grep 검증
       ↓
Phase 5 — 5-sync + 통지 (~1h)
  ├─ DOC-01 명세 v5.3 Phase 2 헤더/푸터/변경 이력 + role 22건 정정
  ├─ DOC-02 CHANGELOG [v5.3 Phase 2] 섹션
  ├─ DOC-03 NOTIFY 문서 신설 (GIS/.NET 팀 안내서)
  ├─ DOC-04 v5.3 Phase 2-final-stable 태그 + Gitea/origin push
  ├─ DOC-05 session-context.md v5.3 Phase 2 갱신
  └─ DOC-06 SESSION_COORDINATION.md v5.3 Phase 2 마감
```

---

## 부록 B. NOTIFY 문서 개요 (`GOP_Server_API_v5.3 Phase 2_Role_Simplification_NOTIFY.md`)

.NET/GIS 팀 안내서 필수 포함 항목:

1. **배경** — v5.2 R10① 정신 완성 + 개념 오염 근본 해결
2. **변경 요약 표** — Before/After 매트릭스
3. **Enum 축소** — 5종 → 2종 (ADMIN/USER)
4. **user_groups rename 매트릭스** — 3 팀 유지 + 4 등급 → 3 Preset + 2 삭제
5. **클라 영향 요약** — 대부분 영향 없음 + role 조건 코드 확인 요청
6. **JWT payload 변경 예시** — Before/After 비교
7. **role 값 조건 코드 조사 요청 (V-RS-06)** — .NET 3 프로젝트 grep 예시
8. **DB 직접 접근 코드 (있으면)** — `where role IN (...)` 등 확인
9. **관리 UI 안내** — role 드롭다운 2종, 그룹 배정 UI에 Preset 그룹 노출
10. **FAQ** — "왜 Preset이라 부르나?" / "기존 사용자 권한은 유지되나?" / "언제 배포?"
11. **롤백 절차** — 긴급 시 `git reset --hard pre-role-simplification` + reverse SQL
12. **참조 자료** — PRD / Plan / 명세 v5.3 Phase 2 / CHANGELOG / 안전점 태그 / commit / Gitea

---

**문서 버전**: v1.0 / **최종 수정**: 2026-07-02 / **상태**: **Draft** (사용자 승인 대기)
