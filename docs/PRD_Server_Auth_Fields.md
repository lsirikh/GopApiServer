# PRD: Server 인증 정보 필드 추가

**문서 버전**: v1.1
**작성일**: 2026-01-07
**작성자**: Claude Code Assistant
**상태**: Draft

---

## 목차

1. [개요](#1-개요)
2. [변경 설계](#2-변경-설계)
3. [API 스펙 변경](#3-api-스펙-변경)
4. [구현 계획](#4-구현-계획)
5. [변경 이력](#5-변경-이력)

---

## 1. 개요

### 1.1 목표

Server 모델에 `user_name`, `user_password` 필드를 추가하여 서버 접속 인증 정보를 저장합니다.

### 1.2 추가 필드

| 필드 | 타입 | NULL | 설명 |
|------|------|------|------|
| `user_name` | VARCHAR(100) | O | 접속 사용자명 |
| `user_password` | VARCHAR(200) | O | 접속 비밀번호 |

---

## 2. 변경 설계

### 2.1 Model 변경

```python
# app/models/server.py
class Server(Base):
    __tablename__ = "servers"

    # 기존 필드...

    # ===== NEW: 인증 정보 =====
    user_name = Column(String(100), nullable=True)
    user_password = Column(String(200), nullable=True)
```

### 2.2 Schema 변경

```python
# app/schemas/server.py

class ServerCreate(BaseModel):
    # 기존 필드...
    user_name: Optional[str] = None
    user_password: Optional[str] = None

class ServerUpdate(BaseModel):
    # 기존 필드...
    user_name: Optional[str] = None
    user_password: Optional[str] = None

class ServerResponse(BaseModel):
    # 기존 필드...
    user_name: Optional[str] = None
    user_password: Optional[str] = None  # 그대로 반환
```

---

## 3. API 스펙 변경

### 3.1 Response 예시

```json
{
  "id": 1,
  "category_id": 1,
  "name": "VMS-Server-01",
  "status": "NORMAL",
  "ip_address": "192.168.1.100",
  "port": 8080,
  "hostname": "vms-01",
  "user_name": "admin",
  "user_password": "password123",
  "cpu_usage": 45.5,
  "ram_usage": 60.2,
  "disk_usage": 70.0,
  "network_throughput": "125MB/s",
  "created_at": "2026-01-07T10:00:00.000Z",
  "updated_at": "2026-01-07T10:00:00.000Z"
}
```

---

## 4. 구현 계획

| 순서 | 작업 | 파일 |
|------|------|------|
| 1 | Model 필드 추가 | `app/models/server.py` |
| 2 | Schema 필드 추가 | `app/schemas/server.py` |
| 3 | 테스트 | `tests/` |

---

## 5. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.1 | 2026-01-07 | 간소화: user_password Response 포함 |
| v1.0 | 2026-01-07 | 초안 작성 |

---

**문서 종료**
