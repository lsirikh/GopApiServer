PRD 문서 신설 완료: `c:/workspace_python/api-test-server/docs/PRD_v5.0_Permission_Management.md` (약 12KB, 8섹션 + 부록 2개).

# 구조 요약
1. **배경 & 문제 정의** — v4.8 PUT 차단 정책이 운영 막힘 원인이 된 상황 정리 (DB 직접 UPDATE 우회 강요 → 감사 누락)
2. **결정 (Decision)** — `POST /api/user-groups/{group_id}/permissions` 신설. 4개 대안 비교표 (A:PUT부활 / B:PATCH / **C:POST 채택** / D:PUT별경로)
3. **적용 범위 (Scope)** — 포함 5건, 미포함 5건 (v5.1+ 분리)
4. **API 사양** — 메서드 개요 표, 요청/응답 JSON, 에러 매트릭스 5종 (403/404/422×3), POST=full replace 의미 명시
5. **데이터 모델** — `PermissionsSchema` / `ModulePermission` / `EnumPermissionModule(8종)` / `EnumPermissionVerb(4종)`, JSONB 직렬화(`model_dump(mode="json", exclude_none=True)`)
6. **보안 & 감사** — `require_admin` (endpoint-level), `PERMISSION_CHANGED` 흐름 (before/after diff via `get_changes()`), 위협 모델 표 (T1/T1'/T2/T3/T4/T5 vs 차단 지점)
7. **실측 검증 (2026-06-29)** — 5건 시나리오 결과표 (admin 200 / OPERATOR 403 / super_admin 422 / destroy 422 / "yes" 422), 감사 로그 SQL 적재 확인 (`2026-06-29 10:23:29` 보존), Swagger operationId 확인
8. **잔존 & 로드맵 (v5.1+)** — 잔존 4건(R-1~R-4), v5.1 로드맵 6항목 (단일 트랜잭션, 이력 조회 API, 권한 템플릿, time_restriction enforcement, 2단계 승인, PUT 별칭)

# 부록
- **A**: v4.x 정책 정합 표 (v4.8/v4.9/v4.12 vs v5.0 관계)
- **B**: 명세 본문 반영 메모 (§9.4 표 6→7행 확장, §13.1 부록 링크, 변경 이력 표 v5.0 1행 추가, 헤더/푸터 v4.12 → v5.0 갱신)

# 핵심 포인트 (요청 사양 모두 반영)
- "왜 별도 endpoint 인가" → §1.2 + §2.2 에서 v4.8 Phase 12-7a 영구 정책 + T1 권한 상승 차단 근거 명시
- PermissionsSchema strict 구조 + 422 시나리오 5종 → §4.4 + §7.2 두 곳에서 예시 표 제시
- 감사 로그 PERMISSION_CHANGED before/after diff → §6.2 코드 블록 + §7.3 SQL 확인
- 실측 5건 표 → §7.2 (admin 200 / 비-admin 403 / 미정의 모듈 422 / 미정의 verb 422 / StrictBool truthy 422)
- 외부 세션 작업 흔적 보존 → §7.3 timestamp `2026-06-29 10:23:29` + 푸터 메모

# 컨벤션 준수
- 한국어 마크다운, 백틱 코드 / **굵게** / 표 / NOTE 블록 모두 사용
- 명세 본문 표기 스타일 유지
- IDE 의 MD060 lint 경고는 테이블 pipe spacing 스타일 관련 (compact vs padded) — 프로젝트 기존 PRD 문서들도 동일 compact 스타일을 사용하므로 그대로 유지

# 생성 파일 (절대 경로)
- `c:/workspace_python/api-test-server/docs/PRD_v5.0_Permission_Management.md`