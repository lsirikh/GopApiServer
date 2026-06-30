# 멀티세션 협업 조율판 (Session Coordination Board)

> **목적**: 동시에 도는 두 작업 세션이 **같은 파일 충돌 없이** 협업하도록 소유권·경계·확장훅을 못박는다.
> 두 세션 모두 작업 시작 전 이 파일을 읽고, 경계를 바꾸려면 여기 먼저 갱신한다.
> **갱신**: 2026-06-30 / 브랜치: `feature/tracking-gis-ingest` (공유) / HEAD at write: `59711cd`

---

## 워크스트림 2개

| WS | 내용 | PRD | 소유 세션 |
|---|---|---|---|
| **WS-A: RBAC 베이스** | 휴면 require_perm/optional + 27 부착 + 활성화 가이드 | PRD_GOP_Server_RBAC_Enforcement | **세션 #1 (RBAC)** — 완료·동결 |
| **WS-B: 권한그룹 시간 스케쥴링** | user_group_grants + 유효권한 계산 + 부여 API + sweep | PRD_Permission_Group_Scheduling | **세션 #2 (Scheduling)** — 착수 예정 |

> WS-B 는 §3.7대로 WS-A 휴면 게이트에 **올라탐**(별도 게이트 없음, 같은 AUTH_MODE 플립으로 동시 활성).

---

## 파일 소유권 (충돌 방지 — 이 경계 지키면 git 충돌 0)

| 파일/영역 | 소유 | 규칙 |
|---|---|---|
| **`app/routers/auth.py`** | **WS-B 단독** | ★ WS-A는 **동결**(커밋 `c49f0a4`/`require_perm_optional` 안정). WS-B가 FR-02 `effective_permissions` 확장을 **여기서 단독** 수행. WS-A는 편집 금지 |
| `app/models/` (신규 `user_group_grants`) | WS-B | 신규 파일 — 충돌 없음 |
| `app/migrations/` (신규 grants) | WS-B | 신규 파일 |
| `app/routers/users.py` (`/grants` API) | WS-B | ※ WS-A의 `b2f80c8`(비번변경 세션무효화) 이미 커밋됨 — 그 위에서 append만 |
| `app/main.py` (sweep lifespan) | WS-B | lifespan 배선 |
| `requirements.txt` (APScheduler) | WS-B | |
| 27 write 라우터 데코레이터 | **동결** | WS-A `9a6624c` 부착 완료. 둘 다 추가 부착 시 조율 필요 |
| `docs/prds/GUIDE_RBAC_Activation_*` · `CONTRACT_*` | WS-A | 활성화/계약 문서 |
| `app/utils/init_sample_data.py` (그룹 시드) | **조율 필요** | 역할명 그룹 정렬 ↔ grants 시드. 편집 전 여기 표시 |
| `docs/memory/session-context.md` | 공유(append) | 각자 자기 섹션만, 작은 커밋 |

---

## 확장 훅 (WS-B가 auth.py에서 쓸 것)

WS-A가 추출해둔 헬퍼(`app/routers/auth.py`)를 WS-B가 그대로 재사용:
- `_resolve_role_group(db, user)` — 역할명 그룹(`UserGroup.name==role`) 1순위 + group_id 폴백.
- `_role_group_allows(group, module, verb)` — 매트릭스 판정(bool).

WS-B 권장 구현(§3.2):
```python
def effective_permissions(db, user, now):
    # role 매트릭스(_resolve_role_group) ∪ 현재 유효 grant들의 group 매트릭스
    # require_perm / require_perm_optional 둘 다 이 결과로 _role_group_allows 판정
```
→ require_perm/optional 의 ADMIN bypass·휴면(public 무집행) 동작은 **유지**. grant 합집합만 추가.

---

## 라이브 권한그룹 현황 (2026-06-30 실측, WS-B 참고)

역할명 그룹 **이미 생성됨**(WS-A의 `name==role` 해석과 정합):
`id10=ADMIN · 11=MAINTAINER · 12=OPERATOR · 13=VIEWER · 14=GUEST(역할 enum엔 없음)`.
구 팀명 그룹(1 운영팀·2 관제팀·3 유지보수팀)은 group_id 폴백용 — 역할명 그룹 있으면 미발동.

⚠️ **미해결 정책**(PM 결정 대기): OPERATOR 매트릭스가 cameras/devices/events `edit=false` → P5 활성화 시 운영자 장비/이벤트 생성·수정 403. 의도 확인 필요(WS-A 가이드 §6).

---

## 커밋 규율 (같은 브랜치 공유)

- 편집 전 `git pull --rebase` (또는 최신 HEAD 확인).
- 작은·단일 논리 커밋. 커밋 메시지에 `[WS-A]`/`[WS-B]` 태그 권장.
- 구조/행동 분리(Tidy First).

---

## 현재 상태 (live)

- WS-A: 휴면 RBAC 배포 완료(Swagger 5.2.0 라이브, `v5.2-deployed`). 활성화(P5)는 클라 Bearer 동시배포 게이트. **추가 완료(2026-06-30)**: 명세서 본문 v5.2 동기화(`36379e3`, 5중싱크 5/5) + **FR-SV-09 종결(`de4266d`)** — `app/routers/user_groups.py` POST/PUT/DELETE/GET-members 에 `require_admin` 부착(권한그룹 관리 ADMIN 전용 통일). ★WS-B 알림: user_groups.py 데코레이터만 변경(핸들러 본문·grants 무관, 충돌 없음). P6 audit append-only는 `trg_audit_logs_immutable`(v51)로 **이미 DB레벨 충족**.
- WS-B: PRD Approved + plan. **FR-01~07 코드 완료(2026-06-30)** — 스케쥴링 전체 31 로컬 테스트 passed, 회귀 0:
  - ✅ **FR-01** `UserGroupGrant` 모델 + `v56` (`728e537`)
  - ✅ **FR-02** `auth.py` `_effective_allows` 요청시점 만료집행 (`fc3accb`, NFR-01 검증)
  - ✅ **FR-03/05** 부여 API `app/routers/grants.py`(prefix `/api`, users.py 무접촉) + `grant_service.grant_status` (`4c3b641`)
  - ✅ **FR-04** sweep `main.py` lifespan APScheduler(방어적) + `requirements.txt` (`985097f`)
  - ✅ **FR-06/07** `effective_permissions_payload` + `GET /api/auth/me/permissions` + 로그인 grant 병합 (`37cce4e`)
  - 경계 준수: `auth.py`·`main.py`·`requirements.txt`·신규파일만. 27 데코레이터·`init_sample_data.py`·`users.py` 미편집.
  - ⏭ **WS-A 조율 필요 1건**: FR-06 NATS `permissions_changed` 통지(grant 만료/변경) — **WS-A NATS publisher/ACL 소유**라 미구현. 서버는 매 요청 authoritative(FR-02)라 정합성은 보장, NATS는 즉시성 최적화. WS-A 발행 헬퍼 시그니처 공유해주면 grants.py 생성/회수 + sweep에 thin publish 추가 예정.
  - ⏭ 배포(미실행): 5중싱크 ②③④(명세서·도커 재빌드·컨테이너) + `v56` 마이그레이션 psql 적용. **AUTH_MODE 플립은 클라 Bearer 동시배포 게이트(WS-A와 공통)** — 스케쥴링 집행도 이 플립으로 함께 활성.
