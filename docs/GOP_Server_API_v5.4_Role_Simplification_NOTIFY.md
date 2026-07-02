# GOP Server API v5.4 — Role 축소 + Preset Group 정리 통지

- **작성일**: 2026-07-02
- **작성자**: GOP API 서버 팀 (이기호 차장)
- **수신**: .NET 클라 팀 (Dotnet.Monitoring.Solution / Ironwall.Dotnet.Libraries / Dotnet.Rtsp.Viewer.Ui) + GIS 팀
- **관련**: `PRD_Role_Simplification.md` (Approved) / `v5.4-final-stable` 태그
- **연관 이력**: v5.3 Legacy User Removal (`GOP_Server_API_v5.3_Legacy_User_Removal_NOTIFY.md`)

---

## 1. 배경

**차장님 지시 (2026-07-02)**: *"Admin과 User로만 남기고 기존 나눈 등급은 다 없애던지 preset 권한 그룹으로 넘기는 게 좋지 않아?"*

**목적**: v5.2 R10① 정신(*role은 특권 라벨만, 실 권한은 group_id로 명시 배정된 그룹 매트릭스*)의 **스키마 완성**. 개념 오염 근본 해결.

---

## 2. 변경 요약 (한눈에 보기)

| 항목 | Before (v5.3) | After (v5.4) |
|---|---|---|
| **`EnumUserRole`** | 5종 (ADMIN/MAINTAINER/OPERATOR/VIEWER/GUEST) | **2종** (ADMIN/USER) |
| **user_groups** | 8건 (팀 3 + 등급 5) | **6건** (팀 3 + Preset 3) |
| **admin.group_id** | 10 (ADMIN 등급 그룹) | **NULL** (bypass라 무관) |
| **admin 외 role 값** | MAINTAINER/OPERATOR/VIEWER 다양 | **모두 USER** |
| **Swagger version** | 5.3.0 | **5.4.0** |

---

## 3. Enum 축소 상세

### 3.1 Before

```python
class EnumUserRole(str, Enum):
    ADMIN = "ADMIN"
    MAINTAINER = "MAINTAINER"    # ← 삭제
    OPERATOR = "OPERATOR"        # ← 삭제
    VIEWER = "VIEWER"            # ← 삭제
    GUEST = "GUEST"              # ← 삭제
```

### 3.2 After

```python
class EnumUserRole(str, Enum):
    ADMIN = "ADMIN"    # 특권 라벨 (require_admin bypass, 매트릭스 무관)
    USER  = "USER"     # 일반 사용자 (권한은 group_id 매트릭스로만)
```

### 3.3 Swagger 정합

- `components.schemas.EnumUserRole.enum` = **`["ADMIN", "USER"]`** 확정
- `.NET` NSwag 재생성 시 자동으로 2종만 반영됨

---

## 4. user_groups 재정리 매트릭스

| id | Before name | After name | 처리 | 배정 사용자 |
|:---:|---|---|:---:|:---:|
| 1 | 운영팀 | 운영팀 | 유지 | 0 |
| 2 | 관제팀 | 관제팀 | 유지 | 1 (monitor2) |
| 3 | 유지보수팀 | 유지보수팀 | 유지 | 0 |
| **10** | **ADMIN** | ~~삭제~~ | ❌ DROP | admin의 group_id는 NULL로 |
| **11** | MAINTAINER | **Preset - 유지보수자** | 🔄 rename | 1 (gop_maint) |
| **12** | OPERATOR | **Preset - 운영자** | 🔄 rename | 2 (op_tester, gop_op) |
| **13** | VIEWER | **Preset - 조회자** | 🔄 rename | 1 (gop_viewer) |
| **14** | **GUEST** | ~~삭제~~ | ❌ DROP | 0명 |

**핵심**: 
- Preset 그룹의 **id 유지** → 배정된 사용자의 `group_id` 참조 그대로 유지 → **실 권한 매트릭스 100% 유지**
- 이름만 rename → UI 표기 변경만

---

## 5. 클라 영향 요약

### 5.1 실측 결과 (6/6 PASS)

| 시나리오 | 결과 |
|---|:---:|
| admin login (`login_id`/`password` JSON) | ✅ 200, role=ADMIN |
| gop_maint login | ✅ 200, role=USER, group_id=11 (Preset-유지보수자), modules 10건 매트릭스 유지 |
| gop_op / op_tester login | ✅ 200, role=USER, group_id=12 (Preset-운영자) |
| gop_viewer login | ✅ 200, role=USER, group_id=13 (Preset-조회자) |
| monitor2 login | ✅ 200, role=USER, group_id=2 (관제팀), modules 8건 매트릭스 유지 |
| 14 endpoint 응답 코드 (RBAC endpoints) | ✅ 모두 유지 |

### 5.2 대부분 영향 없음 ✅

- **URL/Method/Response schema 100% 유지** — 30 라우터 응답 형식 동일
- **permissions 매트릭스 100% 유지** — group_id는 그대로, 이름만 rename
- **JWT flow 무변경** — access/refresh token 발행 방식 동일
- **AccountUserResponse 유지** — v5.3에서 통일 완료 (Legacy User 삭제)

### 5.3 확인 필요 사항 (V-RS-06) ⚠️

**.NET 클라 코드에 `role` 값 조건이 있으면 확인 필요**:

```bash
# .NET 3 프로젝트에서 다음 grep 실행 요청:
grep -rnE 'role\s*==\s*"(MAINTAINER|OPERATOR|VIEWER|GUEST)"' src/
grep -rnE 'EnumUserRole\.(MAINTAINER|OPERATOR|VIEWER|GUEST)' src/
grep -rnE 'UserRole\.(MAINTAINER|OPERATOR|VIEWER|GUEST)' src/
```

**있으면**: 서버 대응 완료 회신 요청 → 클라 로직 수정 (모두 USER로 통일)
**없으면**: 무영향 확정 (서버 조사 결과와 동일: 로직 조건 코드 0건)

---

## 6. JWT payload / login 응답 변경 예시

### 6.1 Before (v5.3)

```json
POST /api/auth/login
Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "...",
    "user": {
      "id": 82,
      "login_id": "gop_op",
      "role": "OPERATOR",   ← Legacy 값
      "group_id": 12,
      "permissions": {...}
    }
  }
}
```

### 6.2 After (v5.4)

```json
POST /api/auth/login
Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "...",
    "user": {
      "id": 82,
      "login_id": "gop_op",
      "role": "USER",       ← 축소된 값
      "group_id": 12,       ← 그대로 (Preset - 운영자)
      "permissions": {...}  ← 그대로 (매트릭스 유지)
    }
  }
}
```

**주목**: `group_id`와 `permissions` 100% 유지. `role`만 값이 변경됨.

---

## 7. DB 직접 접근 코드 확인 (있으면)

**서버 DB 직접 SELECT하는 코드 (외부 팀에서 사용 시)**:

```sql
-- Before: role IN 조건
SELECT * FROM account_users WHERE role IN ('OPERATOR', 'VIEWER');

-- After: role 대신 group_id로 판정
SELECT au.* FROM account_users au
JOIN user_groups ug ON au.group_id = ug.id
WHERE ug.name LIKE 'Preset%' OR ug.name IN ('운영팀','관제팀','유지보수팀');
```

**단**: 대부분의 클라는 REST API를 통해서만 접근 → 이 항목 무영향.

---

## 8. 관리 UI 안내

### 8.1 사용자 생성/수정 UI

**role 드롭다운**:
- Before: `[ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST]` (5종)
- After: `[ADMIN, USER]` (2종)

**그룹 배정 드롭다운**:
- 표시: 팀 그룹 3건 + Preset 그룹 3건
- 관리자가 명시적으로 `group_id` 배정 (v5.2 R10① 자동해석 폐기)

### 8.2 그룹 관리 UI

- Preset 그룹 3건은 **참고용 프리셋** — 관리자가 배정 편의를 위해 사용
- 관리자가 직접 새 그룹 생성 가능 (기존 팀 그룹 3건과 동일하게 매트릭스 편집)
- Preset 그룹 이름/설명/매트릭스 편집 가능

---

## 9. FAQ

**Q1. 왜 "Preset"이라 부르나?**  
A: "표준 프리셋(preset)" 개념으로 관리자가 배정 편의를 위해 사용하는 참고용 그룹. 팀 그룹(운영팀/관제팀/유지보수팀)과 개념이 겹치지 않도록 구분.

**Q2. 기존 사용자 권한은 유지되나?**  
A: **예, 100% 유지**. `group_id`가 그대로이고 매트릭스도 유지 (그룹 이름만 rename). 실측 6/6 PASS 확인됨.

**Q3. admin 사용자의 `group_id`가 NULL이 됐는데 권한 문제 없나?**  
A: 문제 없음. ADMIN은 `require_admin`/`require_perm`에서 **매트릭스 조회 없이 bypass**. `group_id`는 참고용에 불과.

**Q4. `role="OPERATOR"` 조건 코드가 있으면 어떻게 하나?**  
A: 로그인 응답의 `data.user.role`이 "USER"로 오므로 조건 false가 됨 → 그 분기 코드 실행 안 됨. **로직 재설계 필요** — 또는 `data.user.group_id` 또는 `data.user.permissions`로 판정하도록 변경.

**Q5. 새 등급 필요할 땐?**  
A: 관리자가 새 Preset 그룹 생성 (매트릭스 커스텀) → 사용자 `group_id`로 배정. Enum 수정 불필요.

**Q6. `GUEST` role 사용자가 이미 있는 경우?**  
A: 서버 실측에서 0명 확인 → 삭제 안전 (v5.4 마이그레이션 v57 DO block으로 자동 검증). 있으면 마이그레이션 실패 (안전 기본값).

**Q7. 언제 배포되나?**  
A: 서버 v5.4-final-stable 태그 완료 시점 (2026-07-02). 클라 재배포는 role 조건 코드 확인 후.

---

## 10. 롤백 절차 (긴급 시)

### 10.1 코드 롤백

```bash
git reset --hard pre-role-simplification
docker compose build api-server && docker compose up -d --force-recreate api-server
```

### 10.2 DB 롤백

```bash
# reverse migration (Enum 5종 재정의 + 그룹 이름 복원)
docker exec -i api-test-postgres psql -U gop_user -d gop < app/migrations/v57_role_simplification_reverse.sql
```

**⚠ 주의**: reverse migration은 admin 외 사용자 role을 일괄 "VIEWER"로 재설정 (원 값 복원 불가). 원 값이 필요하면 별도 백업 필수.

---

## 11. 참조

| 항목 | 위치 |
|---|---|
| PRD | `docs/prds/PRD_Role_Simplification.md` (Approved) |
| Plan | `docs/plans/Role_Simplification-prd-plan.md` |
| CHANGELOG | `CHANGELOG.md` `[v5.4]` — 2026-07-02 |
| 명세서 | `GOP_Restful_Api_연동설계.md` v5.4 (변경 이력 v5.4 행) |
| Migration SQL | `app/migrations/v57_role_simplification.sql` + `_reverse.sql` |
| 안전점 태그 | `pre-role-simplification` |
| 마감 태그 | `v5.4-final-stable` |
| Swagger | `info.version = 5.4.0` |

---

## 12. 문의

| 담당 | 채널 |
|---|---|
| GOP API 서버 팀 | 이기호 차장 |
| 명세 관련 | `GOP_Restful_Api_연동설계.md` 참조 |
| role 조건 코드 발견 시 | 즉시 통지 요청 (마이그레이션 롤백 가능) |

---

**문서 버전**: v1.0 / **최종 수정**: 2026-07-02 / **상태**: Final (배포 통지용)
