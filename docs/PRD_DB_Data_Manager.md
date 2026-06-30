# PRD: DB 데이터 제어 프로그램

## 1. 개요

### 1.1 목적
SQLite 데이터베이스의 테이블 데이터를 안전하게 관리(조회, 삭제)할 수 있는 Web UI 기반 관리 도구

### 1.2 대상 사용자
- 개발자
- 데이터베이스 관리자
- QA 테스터

### 1.3 개발 환경
- Python 3.11+
- SQLite 데이터베이스
- sqlite-web (Web UI 도구)
- Docker & Docker Compose
- 웹 브라우저 (Chrome, Firefox, Edge 등)

## 2. 기능 요구사항

### 2.1 Web UI 접근 (FR-001)
**설명**: 웹 브라우저를 통해 SQLite 데이터베이스 관리 화면 접근

**접근 방법**:
- URL: `http://localhost:8080`
- Docker 컨테이너 자동 시작 시 함께 실행

**화면 구성**:
- 좌측: 테이블 목록 (8개 테이블)
  - controllers
  - sensors
  - cameras
  - detection_events
  - malfunction_events
  - connection_events
  - action_events
  - event_mappings
- 중앙: 선택한 테이블의 데이터 표시
- 상단: SQL 쿼리 실행 영역

**동작**:
- 테이블 클릭 시 데이터 자동 조회
- 실시간 레코드 수 표시
- 페이지네이션 지원

### 2.2 테이블 데이터 조회 (FR-002)
**설명**: 선택한 테이블의 데이터를 조회하고 탐색

**기능**:
- 테이블 선택 시 전체 데이터 표시
- 컬럼명 클릭으로 정렬
- 검색 필터 기능
- 레코드 수 표시

**동작**:
- 테이블 클릭 → SELECT * FROM table_name 실행
- 결과를 그리드 형태로 표시
- 페이지당 100개 레코드 표시 (설정 가능)

### 2.3 SQL 쿼리 실행 (FR-003)
**설명**: 사용자 정의 SQL 쿼리를 직접 실행

**기능**:
- SQL 쿼리 입력 텍스트 영역
- SELECT, DELETE, UPDATE 쿼리 지원
- 쿼리 실행 결과 표시

**예시 쿼리**:
```sql
-- 테이블 전체 삭제
DELETE FROM controllers;

-- 조건부 삭제
DELETE FROM sensors WHERE status = 'DEACTIVATED';

-- 데이터 조회
SELECT * FROM detection_events WHERE created_at > '2025-01-01';
```

**동작**:
- 쿼리 입력 후 "Execute" 버튼 클릭
- 결과 또는 영향받은 행 수 표시
- 에러 발생 시 에러 메시지 표시

### 2.4 데이터베이스 정보 (FR-004)
**설명**: 데이터베이스 전체 정보 표시

**표시 정보**:
- DB 파일 경로: `/app/data/gop.db`
- DB 파일 크기
- 총 테이블 수: 8개
- 각 테이블별 레코드 수
- 마지막 수정 시간

## 3. 비기능 요구사항

### 3.1 보안 (NFR-001)
- **내부 네트워크만 접근**: localhost:8080 (외부 노출 금지)
- **읽기 전용 모드 옵션**: 필요 시 --read-only 플래그 사용 가능
- **주의**: 개발/테스트 환경용, 프로덕션에서는 인증 필요

### 3.2 성능 (NFR-002)
- 페이지 로딩: 1초 이내
- 쿼리 실행: 대부분 1초 이내
- 대용량 테이블: 페이지네이션으로 처리

### 3.3 사용성 (NFR-003)
- **직관적 UI**: 클릭만으로 테이블 조회
- **SQL 편집기**: 문법 하이라이팅
- **결과 표시**: 테이블 형태로 깔끔하게 표시
- **반응형 디자인**: 다양한 화면 크기 지원

### 3.4 안정성 (NFR-004)
- DB 파일 공유 접근 (SQLite 동시성 제한 고려)
- 트랜잭션 자동 처리
- 에러 발생 시 명확한 메시지 표시
- Docker 컨테이너 자동 재시작

## 4. 기술 스택

### 4.1 Core
- **sqlite-web**: 경량 SQLite 웹 브라우저
- Python 3.11+ (sqlite-web 의존성)
- Flask (sqlite-web 내부 사용)

### 4.2 Database
- SQLite 3.x
- DB 파일: `./data/gop.db`
- 동일 DB를 FastAPI와 공유

### 4.3 Docker
- Docker Compose 3.8+
- 독립 서비스로 실행
- 볼륨 마운트: `./data` 공유

## 5. Docker 구조

### 5.1 서비스 구성
```yaml
services:
  api_server-fastapi:     # 기존 FastAPI 서버
    ports: "8000:8000"
    volumes: ./data:/app/data

  db-admin:               # 새로운 sqlite-web 서비스
    image: coleifer/sqlite-web
    ports: "8080:8080"
    volumes: ./data:/data
    command: /data/gop.db --host 0.0.0.0 --port 8080
```

### 5.2 접근 URL
- FastAPI 서버: `http://localhost:8000`
- DB 관리 UI: `http://localhost:8080`

## 6. 데이터 모델

### 6.1 대상 테이블
1. **controllers** - 관제기 정보
2. **sensors** - 센서 정보
3. **cameras** - 카메라 정보
4. **detection_events** - 탐지 이벤트
5. **malfunction_events** - 고장 이벤트
6. **connection_events** - 연결 이벤트
7. **action_events** - 조치 이벤트
8. **event_mappings** - 이벤트 매핑

### 6.2 관계
- sensors → controllers (FK: controller_id)
- 삭제 시 외래 키 제약 조건 고려 필요

## 7. 사용 시나리오

### 7.1 기본 사용 흐름 - 데이터 조회
```
1. 사용자: Docker Compose 실행 (docker-compose up -d)
2. 시스템: FastAPI + DB Admin 서비스 시작
3. 사용자: 브라우저에서 http://localhost:8080 접속
4. 시스템: SQLite Web UI 표시, 테이블 목록 로딩
5. 사용자: 'controllers' 테이블 클릭
6. 시스템: SELECT * FROM controllers 실행, 데이터 표시
7. 사용자: 데이터 확인 후 다른 테이블 탐색
```

### 7.2 데이터 삭제 시나리오
```
1. 사용자: http://localhost:8080 접속
2. 사용자: 상단 "Query" 탭 클릭
3. 사용자: SQL 입력: DELETE FROM sensors WHERE status = 'DEACTIVATED';
4. 사용자: "Execute" 버튼 클릭
5. 시스템: 쿼리 실행, "3 rows affected" 표시
6. 사용자: 'sensors' 테이블 클릭하여 삭제 확인
```

### 7.3 테이블 전체 삭제 시나리오
```
1. 사용자: http://localhost:8080 접속
2. 사용자: Query 탭에서 SQL 입력: DELETE FROM action_events;
3. 사용자: Execute 클릭
4. 시스템: "150 rows deleted" 메시지 표시
5. 사용자: 테이블 클릭하여 빈 테이블 확인
```

## 8. 제약 사항

### 8.1 기술적 제약
- Docker 환경 필수
- SQLite 데이터베이스만 지원
- 기존 FastAPI와 동일한 DB 파일 공유 (./data/gop.db)
- SQLite 동시성 제한 (쓰기 작업 시 주의)

### 8.2 기능적 제약
- **인증 없음**: 개발/테스트 환경용
- 외부 노출 금지 (localhost만 접근)
- 삭제된 데이터는 복구 불가 (백업 권장)

## 9. 향후 확장 가능성

### 9.1 Phase 2 (선택적)
- **인증 추가**: Basic Auth 또는 토큰 기반 인증
- **읽기 전용 모드**: 데이터 조회만 가능
- **백업 기능**: UI에서 백업 생성/복원
- **감사 로그**: 모든 쿼리 실행 기록

### 9.2 Phase 3 (선택적)
- **데이터 Import/Export**: CSV, JSON 형식 지원
- **통계 대시보드**: 테이블별 통계 시각화
- **쿼리 히스토리**: 실행한 쿼리 저장/재실행

## 10. 테스트 계획

### 10.1 기능 테스트
- [ ] Docker Compose 서비스 시작 확인
- [ ] http://localhost:8080 접근 확인
- [ ] 8개 테이블 모두 표시되는지 확인
- [ ] SELECT 쿼리 실행 테스트
- [ ] DELETE 쿼리 실행 테스트
- [ ] 페이지네이션 동작 확인

### 10.2 통합 테스트
- [ ] FastAPI와 동시 접근 테스트
- [ ] DB 파일 공유 문제 없는지 확인
- [ ] 동시 쓰기 작업 테스트

### 10.3 사용성 테스트
- [ ] UI 반응성 확인
- [ ] SQL 문법 하이라이팅 확인
- [ ] 에러 메시지 명확성 확인

## 11. 배포 계획

### 11.1 배포 파일
- `docker-compose.yml` (db-admin 서비스 추가)
- `Docs/PRD_DB_Data_Manager.md` (문서)

### 11.2 실행 방법
```bash
# Docker Compose 시작
docker-compose up -d

# 브라우저에서 접속
http://localhost:8080

# 종료
docker-compose down
```

### 11.3 필요 조건
- Docker 및 Docker Compose 설치
- SQLite DB 파일 존재 (./data/gop.db)
- 포트 8080 사용 가능

## 12. 문서화

### 12.1 사용자 문서
- PRD 문서 (본 문서)
- Docker Compose 설정 설명
- 주의 사항 및 보안 경고

### 12.2 운영 문서
- 포트 설정 방법
- 볼륨 마운트 설명
- 트러블슈팅 가이드

## 13. 승인 기준

### 13.1 기능 완성
- [x] PRD 작성 완료
- [ ] 프로그램 구현 완료
- [ ] 모든 테이블 삭제 기능 작동
- [ ] 에러 처리 완료

### 13.2 품질
- [ ] 코드 리뷰 완료
- [ ] 테스트 통과
- [ ] 사용자 피드백 반영

---

**문서 버전**: 1.0
**작성일**: 2025-01-19
**작성자**: Claude Code
**승인자**: (대기 중)
