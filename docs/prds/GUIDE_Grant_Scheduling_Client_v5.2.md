# 클라(Dotnet.Monitoring) 권한그룹 스케쥴링 연동 가이드 — v5.2

- **작성**: WS-B (권한그룹 시간 스케쥴링) / 2026-06-30
- **대상**: Dotnet.Monitoring / Ironwall.Dotnet.Libraries / Dotnet.Rtsp.Viewer.Ui (api-test-server 소비 3종)
- **연관**: PRD_Permission_Group_Scheduling · ADR_Permission_Model_v5.2 · CONTRACT_GOP_Server_v5.2(세션/강제로그아웃) · GOP_Restful_Api_연동설계 §9.9/§9.2.6
- **전제**: 현재 `AUTH_MODE=public`(집행 휴면). 클라 Bearer 동시배포 + `AUTH_MODE=token` 플립 시 함께 활성.

---

## 0. 한 줄 요약

권한은 **role 이름이 아니라 서버가 내려주는 매트릭스(modules)** 로 판단하고, **`valid_until` 도달/NATS 통지 시 재조회**한다. 버튼·메뉴 게이팅은 보조이며, **실제 허용은 서버 응답(200/403)이 최종**이다.

---

## 1. 권한 모델 (ADR v5.2) — 클라가 반드시 알 것

| 항목 | 내용 | 클라 영향 |
|------|------|----------|
| **role** | **ADMIN만 특권**(전권). OPERATOR/VIEWER/MAINTAINER 는 **정보 라벨**(권한 효력 0) | role 이름으로 권한 추론 **금지**. ADMIN만 "전권" 가정 가능 |
| **기능 권한** | **배정 그룹 매트릭스 ∪ 유효 grant** | `permissions.modules[모듈][동사]` 로만 판정 |
| **`name==role` 자동연결** | **폐기** | "OPERATOR면 OPERATOR 권한" 같은 가정 금지 |
| **미배정 비-ADMIN** | 권한 0 | 그룹 미배정 사용자는 아무 것도 못 함(로그인은 됨) |

모듈 키: `devices·events·reports·cameras·users·user_groups·audit_logs·servers·map·broadcast·setup_system·setup_feature`
동사: `view·edit·delete·control`(control=cameras 전용)

---

## 2. 권한 스냅샷 수신 — 2개 경로

### 2.1 로그인 응답 (`POST /api/auth/login`)
```jsonc
"data": {
  "access_token": "...", "refresh_token": "...", "session_id": "...",
  "user": {
    "id": 1, "login_id": "operator01", "role": "OPERATOR", "group_id": 12,
    "permissions": {
      "modules": { "events": {"view": true, "edit": true}, "cameras": {"view": true, "control": true} },
      "device_groups": [1, 2, 3],
      "valid_until": "2026-07-01T14:00:00+09:00"   // 가장 임박한 grant 만료(없으면 null=상시)
    }
  }
}
```

### 2.2 재조회 (`GET /api/auth/me/permissions`, Bearer 필요)
```jsonc
"data": {
  "modules": { ... },
  "device_groups": [ ... ],
  "valid_until": "2026-07-01T14:00:00+09:00",   // null=상시
  "server_time": "2026-06-30T13:05:00+09:00"    // 시계 보정 기준
}
```

---

## 3. 클라 구현 패턴 (3중 방어)

```
[로그인] → permissions + valid_until 캐시, (server_time - localNow) = clockSkew 저장
   │
   ├─ 타이머: valid_until 도달(보정시각 기준) → GET /me/permissions 재조회
   ├─ NATS: permissions_changed 수신 → GET /me/permissions 재조회
   │
[화면] 메뉴/버튼 = 캐시 modules 로 게이팅(보조 UX)
[동작] 실제 write = 서버 응답 권위: 200 성공 / 403 = 권한만료·부족 → 캐시 갱신 + 재안내
```

- **① 서버 authoritative**: 모든 write 는 서버 매트릭스가 최종 차단. 클라 캐시가 stale 해도 만료 권한 호출은 403 → 보안 OK.
- **② 클라 재조회**: `valid_until` 타이머 + NATS 통지로 캐시 신선도 유지(UX).
- **③ 시계 보정**: 폐쇄망 NTP 편차 대비. `server_time` 으로 `clockSkew` 계산, 만료 판정은 `localNow + clockSkew` 사용.

> ⚠️ `valid_until` 은 "가장 임박한 grant 만료"다. 한 사용자가 grant 여러 개면 가장 이른 시각 → 그 시점에 재조회하면 나머지는 자동 반영.

---

## 4. NATS `permissions_changed` 통지 (R1)

- **subject**: `sensorway.{unit}.account.{user_id}.permissions.changed` (per-user)
- **발행 시점**: grant 생성(`GRANT_CREATED`) / 회수(`GRANT_REVOKED`) / 만료 sweep(`GRANT_EXPIRED`)
- **서명**: HMAC-SHA256(REVOKE_SIGNING_KEY) — 강제로그아웃과 동일 검증(CONTRACT_GOP_Server_v5.2 §3)
- **게이트**: 서버 `NATS_REVOKE_ENABLED` (현재 off → 미발행). 활성화는 강제로그아웃과 동시 운영
- **클라 동작**: 본인 user_id subject 구독 → 수신 시 `GET /me/permissions` 재조회(페이로드 자체는 트리거 용도, 권위는 재조회 응답)

---

## 5. 관리(ADMIN) — 부여/회수 UI 용 API

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/users/{user_id}/grants` | 부여: `{group_id, valid_from, valid_until?}` (`valid_until` 생략=상시) |
| GET | `/api/users/{user_id}/grants` | 사용자 부여 목록 + `status`(ACTIVE/PENDING/EXPIRED/REVOKED) |
| DELETE | `/api/grants/{grant_id}` | 회수(soft) |

- 시각은 KST(+09:00) ISO 권장. `valid_until <= valid_from` 또는 과거 `valid_until` → 422.
- 외부 수리기사 예: `POST /users/{id}/grants {group_id: 정비그룹, valid_from:"오늘13:00", valid_until:"내일14:00"}` → 내일 14:00 자동 무효.

---

## 6. 활성화 전 체크리스트 (클라팀)

- [ ] 모든 ApiService(Device/Event/Camera)에 **Bearer 토큰 부착**(`AUTH_MODE=token` 플립과 동시 배포 — 미부착 시 전원 401)
- [ ] 403 응답 핸들링: 권한만료·부족 → `GET /me/permissions` 재조회 + 사용자 안내
- [ ] `valid_until` 타이머 + (활성 시)NATS 구독으로 캐시 갱신
- [ ] role 기반 하드코딩 게이팅 제거 → `permissions.modules` 기반으로 전환
- [ ] `server_time` 기반 시계 보정 적용
