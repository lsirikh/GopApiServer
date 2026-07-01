# PRD: 서버 모니터링 API

**작성일**: 2025-11-29
**버전**: 1.1
**목적**: 통제 UI 대시보드의 서버 모니터링 기능 지원을 위한 API 설계

---

## 1. 개요

### 1.1 배경
통제 UI 대시보드에서 서버 모니터링 기능을 구현하기 위해 서버 카테고리 및 인스턴스 정보를 관리하는 API가 필요합니다.

### 1.2 요구사항 요약

**대시보드 UI 요구사항**:
- 서버 카테고리별 요약 정보 (총 개수, 정상/경고/오류 카운트)
- 카테고리 펼침 시 개별 서버 인스턴스 상세 정보 (CPU, RAM, DISK, Network)

**트리 UI 요구사항**:
- 서버 관리 > 카테고리 목록 표시 (Static 구성)

### 1.3 관련 문서

| 문서 | 설명 |
|------|------|
| [GOP_서버모니터링_스키마.md](./GOP_서버모니터링_스키마.md) | DB 스키마 정의 (테이블, Enum, 초기 데이터) |
| [GOP_Restful_Api_연동설계.md](./GOP_Restful_Api_연동설계.md) | 전체 API 연동 설계서 |

---

## 2. API 설계

### 2.1 API 엔드포인트

#### 서버 카테고리 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/servers/categories` | 카테고리 목록 조회 |
| GET | `/api/servers/categories/{id}` | 카테고리 상세 + 하위 서버 목록 |
| POST | `/api/servers/categories` | 카테고리 생성 |
| PATCH | `/api/servers/categories/{id}` | 카테고리 부분 수정 |
| PUT | `/api/servers/categories/{id}` | 카테고리 전체 수정 |
| DELETE | `/api/servers/categories/{id}` | 카테고리 삭제 |

#### 서버 인스턴스 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/servers` | 서버 인스턴스 목록 조회 |
| GET | `/api/servers/{id}` | 서버 인스턴스 상세 조회 |
| POST | `/api/servers` | 서버 인스턴스 생성 |
| PATCH | `/api/servers/{id}` | 서버 인스턴스 부분 수정 |
| PUT | `/api/servers/{id}` | 서버 인스턴스 전체 수정 |
| DELETE | `/api/servers/{id}` | 서버 인스턴스 삭제 |

#### 대시보드 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/servers/summary` | 카테고리별 서버 현황 요약 (대시보드용) |

---

### 2.2 Request/Response 스키마

#### ServerCategoryCreate (카테고리 생성)

```json
{
  "name": "VMS 서버",
  "type_server": "VMS",
  "description": "Video Management System 서버",
  "sort_order": 1
}
```

#### ServerCategoryUpdate (카테고리 수정)

```json
{
  "name": "VMS 서버",
  "description": "Video Management System 서버 (수정)",
  "sort_order": 1
}
```

#### ServerCategoryResponse (카테고리 응답)

```json
{
  "id": 1,
  "name": "VMS 서버",
  "type_server": "VMS",
  "description": "Video Management System 서버",
  "sort_order": 1,
  "created_at": "2025-11-29T10:00:00+09:00",
  "updated_at": "2025-11-29T10:00:00+09:00"
}
```

#### ServerCreate (서버 인스턴스 생성)

```json
{
  "category_id": 1,
  "name": "VMS-ab1120",
  "status": "NORMAL",
  "ip_address": "192.168.1.10",
  "port": 8080,
  "hostname": "vms-server-01",
  "cpu_usage": 45.0,
  "ram_usage": 62.0,
  "disk_usage": 78.0,
  "network_throughput": "125MB/s"
}
```

#### ServerUpdate (서버 인스턴스 수정)

```json
{
  "status": "WARNING",
  "cpu_usage": 85.0,
  "ram_usage": 78.0
}
```

#### ServerResponse (서버 인스턴스 응답)

```json
{
  "id": 1,
  "category_id": 1,
  "name": "VMS-ab1120",
  "status": "NORMAL",
  "ip_address": "192.168.1.10",
  "port": 8080,
  "hostname": "vms-server-01",
  "cpu_usage": 45.0,
  "ram_usage": 62.0,
  "disk_usage": 78.0,
  "network_throughput": "125MB/s",
  "created_at": "2025-11-29T10:00:00+09:00",
  "updated_at": "2025-11-29T12:30:00+09:00"
}
```

---

### 2.3 API 상세

#### GET /api/servers/summary

**설명**: 대시보드용 카테고리별 서버 현황 요약

**Response**:
```json
{
  "success": true,
  "message": "Server summary retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "VMS 서버",
      "type_server": "VMS",
      "total": 2,
      "normal": 2,
      "warning": 0,
      "error": 0,
      "servers": [
        {
          "id": 1,
          "category_id": 1,
          "name": "VMS-ab1120",
          "status": "NORMAL",
          "ip_address": "192.168.1.10",
          "port": 8080,
          "hostname": "vms-server-01",
          "cpu_usage": 45.0,
          "ram_usage": 62.0,
          "disk_usage": 78.0,
          "network_throughput": "125MB/s",
          "created_at": "2025-11-29T10:00:00+09:00",
          "updated_at": "2025-11-29T12:30:00+09:00"
        },
        {
          "id": 2,
          "category_id": 1,
          "name": "VMS-ab1121",
          "status": "NORMAL",
          "ip_address": "192.168.1.11",
          "port": 8080,
          "hostname": "vms-server-02",
          "cpu_usage": 38.0,
          "ram_usage": 55.0,
          "disk_usage": 65.0,
          "network_throughput": "98MB/s",
          "created_at": "2025-11-29T10:00:00+09:00",
          "updated_at": "2025-11-29T12:30:00+09:00"
        }
      ]
    },
    {
      "id": 2,
      "name": "지능형영상 분석 서버",
      "type_server": "AI_ANALYSIS",
      "total": 3,
      "normal": 2,
      "warning": 1,
      "error": 0,
      "servers": [...]
    }
  ]
}
```

#### GET /api/servers/categories

**설명**: 서버 카테고리 목록 조회

**Response**:
```json
{
  "success": true,
  "message": "Server categories retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "VMS 서버",
      "type_server": "VMS",
      "description": "Video Management System",
      "sort_order": 1,
      "created_at": "2025-11-29T10:00:00+09:00",
      "updated_at": "2025-11-29T10:00:00+09:00"
    },
    {
      "id": 2,
      "name": "지능형영상 분석 서버",
      "type_server": "AI_ANALYSIS",
      "description": "AI 기반 영상 분석 서버",
      "sort_order": 2,
      "created_at": "2025-11-29T10:00:00+09:00",
      "updated_at": "2025-11-29T10:00:00+09:00"
    }
  ]
}
```

#### GET /api/servers/categories/{id}

**설명**: 카테고리 상세 + 하위 서버 목록

**Response**:
```json
{
  "success": true,
  "message": "Server category retrieved successfully",
  "data": {
    "id": 1,
    "name": "VMS 서버",
    "type_server": "VMS",
    "description": "Video Management System",
    "sort_order": 1,
    "created_at": "2025-11-29T10:00:00+09:00",
    "updated_at": "2025-11-29T10:00:00+09:00",
    "servers": [
      {
        "id": 1,
        "category_id": 1,
        "name": "VMS-ab1120",
        "status": "NORMAL",
        "ip_address": "192.168.1.10",
        "port": 8080,
        "hostname": "vms-server-01",
        "cpu_usage": 45.0,
        "ram_usage": 62.0,
        "disk_usage": 78.0,
        "network_throughput": "125MB/s",
        "created_at": "2025-11-29T10:00:00+09:00",
        "updated_at": "2025-11-29T12:30:00+09:00"
      }
    ]
  }
}
```

#### POST /api/servers/categories

**설명**: 서버 카테고리 생성

**Request**:
```json
{
  "name": "VMS 서버",
  "type_server": "VMS",
  "description": "Video Management System 서버",
  "sort_order": 1
}
```

**Response**: `201 Created`
```json
{
  "success": true,
  "message": "Server category created successfully",
  "data": {
    "id": 1,
    "name": "VMS 서버",
    "type_server": "VMS",
    "description": "Video Management System 서버",
    "sort_order": 1,
    "created_at": "2025-11-29T10:00:00+09:00",
    "updated_at": "2025-11-29T10:00:00+09:00"
  }
}
```

#### POST /api/servers

**설명**: 서버 인스턴스 생성

**Request**:
```json
{
  "category_id": 1,
  "name": "VMS-ab1120",
  "status": "NORMAL",
  "ip_address": "192.168.1.10",
  "port": 8080,
  "hostname": "vms-server-01",
  "cpu_usage": 45.0,
  "ram_usage": 62.0,
  "disk_usage": 78.0,
  "network_throughput": "125MB/s"
}
```

**Response**: `201 Created`
```json
{
  "success": true,
  "message": "Server created successfully",
  "data": {
    "id": 1,
    "category_id": 1,
    "name": "VMS-ab1120",
    "status": "NORMAL",
    "ip_address": "192.168.1.10",
    "port": 8080,
    "hostname": "vms-server-01",
    "cpu_usage": 45.0,
    "ram_usage": 62.0,
    "disk_usage": 78.0,
    "network_throughput": "125MB/s",
    "created_at": "2025-11-29T10:00:00+09:00",
    "updated_at": "2025-11-29T10:00:00+09:00"
  }
}
```

#### PATCH /api/servers/{id}

**설명**: 서버 인스턴스 부분 수정 (메트릭 업데이트 등)

**Request** (부분 업데이트):
```json
{
  "status": "WARNING",
  "cpu_usage": 85.0,
  "ram_usage": 78.0
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Server updated successfully",
  "data": {
    "id": 1,
    "category_id": 1,
    "name": "VMS-ab1120",
    "status": "WARNING",
    "ip_address": "192.168.1.10",
    "port": 8080,
    "hostname": "vms-server-01",
    "cpu_usage": 85.0,
    "ram_usage": 78.0,
    "disk_usage": 78.0,
    "network_throughput": "125MB/s",
    "created_at": "2025-11-29T10:00:00+09:00",
    "updated_at": "2025-11-29T14:00:00+09:00"
  }
}
```

---

## 3. 상태 판단 기준 (보류)

> **[보류]** 상태 판단 로직은 Nats 브로커를 통해 처리 예정
> - 서버 상태(NORMAL/WARNING/ERROR)는 Nats를 통한 하트비트/상태 메시지로 판단
> - CPU/RAM/DISK 퍼센트는 상태 판단 기준이 아님 (단순 메트릭 표시용)
> - DB API는 상태 저장/조회만 담당

---

## 4. 파일 구조 (예상)

```
app/
├── models/
│   └── server.py          # ServerCategory, Server 모델
├── schemas/
│   └── server.py          # Request/Response 스키마
├── routers/
│   ├── servers.py         # 서버 인스턴스 API
│   └── server_categories.py  # 서버 카테고리 API
└── utils/
    └── enums.py           # EnumServerType, EnumServerStatus 추가
```

---

## 5. 체크리스트

### 5.1 구현 항목

- [ ] Enum 추가 (`EnumServerType`, `EnumServerStatus`)
- [ ] Model 생성 (`ServerCategory`, `Server`)
- [ ] Schema 생성 (Request/Response)
- [ ] Router 생성 (`/api/servers/*`)
- [ ] 초기 데이터 Seed 스크립트
- [ ] 테스트 코드 작성

### 5.2 연동 설계서 업데이트

- [ ] `GOP_Restful_Api_연동설계.md`에 서버 API 섹션 추가
- [ ] 버전 업데이트 (v1.9)

---

## 6. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2025-11-29 | 초기 PRD 문서 작성 |
| v1.1 | 2025-11-29 | DB 스키마 섹션 분리 (GOP_서버모니터링_스키마.md 참조), API 설계에 집중 |

---

**문서 종료**
