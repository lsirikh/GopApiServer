"""마스터 보고서 데이터 빌더 — DB에서 전 도메인을 제네릭 섹션 구조로 변환.

PRD: PRD_Report_Master_Redesign
- 정형(STANDARD): enabled_components=None → 전 섹션/컴포넌트 포함
- 비정형(CUSTOM): enabled_components=set(...) → 해당 컴포넌트만 (기존 report_templates.components 재사용)

섹션 블록 타입: cards | summary | charts | grid (report_html_renderer가 소비)
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.utils import report_labels as L

_NAME_RE = re.compile(r"\]\s*(.+?)\s*\(number:")
_ZONE_RE = re.compile(r"-\s*([A-Za-z])\s*\d+")


def _parse_name(name_device: str, desc: str) -> str:
    if name_device:
        return name_device
    m = _NAME_RE.search(desc or "")
    return m.group(1).strip() if m else "(미상)"


def _zone_of(loc: str, name: str) -> str:
    loc = (loc or "").strip()
    if loc:
        z = loc.split("-", 1)[0].strip()
        if z:
            return z
    m = _ZONE_RE.search(name or "")
    return f"{m.group(1).upper()}구역" if m else "미지정"


def build_report_meta(generation) -> dict:
    """ReportGeneration → 표지/헤더 메타. report_service·preview 공통 사용."""
    is_custom = getattr(generation, "report_type", None) == "CUSTOM"
    kind = "비정형" if is_custom else "정형"
    return {
        "doc_no": f"GOP-RPT-{generation.id}",
        "title": generation.title,
        "title_spaced": " ".join(f"{kind}보고서"),
        "subtitle": " ".join("통합운영분석보고서"),
        "system": "GOP 통합 관제 시스템",
        "period_start": generation.start_date.strftime("%Y.%m.%d"),
        "period_end": generation.end_date.strftime("%Y.%m.%d"),
        "period_type": generation.period_type,
        "report_id": f"#{generation.id}",
        "report_kind": f"{kind} (선택 섹션)" if is_custom else f"{kind} (전 섹션)",
    }


def _chart(cid, dom, title, kind, labels, values, center=None, accent="blue") -> dict:
    return {"type": "chart", "cid": cid, "id": dom, "title": title, "kind": kind,
            "labels": labels, "values": values, "center": center, "accent": accent}


def _grid(cid, title, columns, colpct, rows, total) -> dict:
    return {"type": "grid", "cid": cid, "title": title, "columns": columns,
            "colpct": colpct, "rows": rows, "total": total}


def build_master_data(
    db: Session,
    start: datetime,
    end: datetime,
    meta: dict,
    enabled_components: Optional[set[str]] = None,
    severity_filter: Optional[list[str]] = None,
) -> dict:
    """전 도메인 데이터를 수집해 {meta, sections} 구조로 반환.

    v5.4 P1-3: severity_filter 실적용 — system_events 4개 쿼리에 severity IN (…) 조건 부착.
    - 화이트리스트 검증 (CRITICAL/ERROR/WARNING/INFO/DEBUG) → SQL injection 차단.
    """
    p = {"start": start, "end": end}

    def q(sql: str, params: dict | None = None) -> list:
        return list(db.execute(text(sql), {**p, **(params or {})}).all())

    def scalar(sql: str) -> int:
        r = db.execute(text(sql), p).scalar()
        return int(r or 0)

    EV = "e.created_at >= :start AND e.created_at < :end"
    CC = "created_at >= :start AND created_at < :end"

    # v5.4 P1-3: severity_filter 화이트리스트 검증 + system_events 쿼리 조건 조립
    _valid_sev = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
    _safe_sev = [s.upper() for s in (severity_filter or []) if isinstance(s, str) and s.upper() in _valid_sev]
    SEV_FILTER = f" AND severity::text IN ({', '.join(repr(s) for s in _safe_sev)})" if _safe_sev else ""

    det_total = scalar(f"select count(*) from detection_events d join events e on e.id=d.id where {EV}")
    mal_total = scalar(f"select count(*) from malfunction_events m join events e on e.id=m.id where {EV}")
    act_total = scalar(f"select count(*) from action_events where {CC}")
    dev_total = scalar("select count(*) from devices")
    sys_total = scalar(f"select count(*) from system_events where {CC}{SEV_FILTER}")
    cfg_total = scalar(f"select count(*) from config_change_logs where {CC}")
    aud_total = scalar(f"select count(*) from audit_logs where {CC}")
    usr_total = scalar("select count(*) from account_users")
    ses_total = scalar("select count(*) from user_sessions")
    log_total = scalar(f"select count(*) from user_login_logs where {CC}")
    srv_total = scalar("select count(*) from servers")

    sections: list[dict] = []

    # ── 1. 종합 요약 ──
    sections.append({"no": 1, "name": "종합 요약", "sub": "현황 분석", "blocks": [
        {"type": "cards", "cid": "SUMMARY_CARD", "cards": [
            {"label": "장비", "value": dev_total, "unit": "대", "color": "blue"},
            {"label": "탐지 이벤트", "value": det_total, "unit": "건", "color": "navy"},
            {"label": "장애 이벤트", "value": mal_total, "unit": "건", "color": "red"},
            {"label": "조치 이벤트", "value": act_total, "unit": "건", "color": "green"},
            {"label": "시스템 이벤트", "value": sys_total, "unit": "건", "color": "amber"},
            {"label": "사용자", "value": usr_total, "unit": "명", "color": "teal"},
        ]},
        {"type": "summary", "cid": "SUMMARY_CARD", "lines": [
            f"분석 기간 {start:%Y-%m-%d} ~ {end:%Y-%m-%d} — 전 도메인 통합 운영 보고서",
            f"이벤트 총계: 탐지 {det_total:,}건 · 장애 {mal_total:,}건 · 조치 {act_total:,}건",
            f"자산: 장비 {dev_total:,}대 · 서버 {srv_total}대 · 사용자 {usr_total}명",
            f"운영 로그: 시스템 {sys_total:,}건 · 설정 변경 {cfg_total:,}건 · 감사 {aud_total:,}건 · 로그인 {log_total:,}건",
        ]},
    ]})

    # ── 2. 장비 현황 ──
    dev_status = [(L.label(L.STATUS, r[0]), int(r[1])) for r in q("select status, count(*) from devices group by status order by 2 desc")]
    dev_type = [(L.label(L.DEVICE_CATEGORY, r[0]), int(r[1])) for r in q("select category_device, count(*) from devices group by category_device order by 2 desc")]
    dev_rows = [[r[0], r[1], L.label(L.DEVICE_CATEGORY, r[2]), r[3], r[4] or "",
                 L.label(L.STATUS, r[5]), "사용" if r[6] else "미사용"]
                for r in q("select id, name_device, category_device, type_device, version, status, is_enable from devices order by id")]
    sections.append({"no": 2, "name": "장비 현황", "sub": "자산 현황", "blocks": [
        {"type": "charts", "charts": [
            _chart("DEVICE_STATUS_PIE", "dev_status", "장비 상태 분포", "doughnut", [x[0] for x in dev_status], [x[1] for x in dev_status], center=[f"{dev_total}", "대"]),
            _chart("DEVICE_TYPE_BAR", "dev_type", "유형별 장비 현황", "vbar", [x[0] for x in dev_type], [x[1] for x in dev_type]),
        ]},
        _grid("DEVICE_GRID", "장비 목록", ["ID", "장비명", "유형", "타입", "버전", "상태", "사용"],
              [7, 26, 12, 17, 12, 13, 13], dev_rows, dev_total),
    ]})

    # ── 3. 탐지 이벤트 ──
    det_raw = q(f"""select e.id, to_char(e.created_at,'YYYY-MM-DD HH24:MI'), coalesce(d.name_device,''),
        dt.result::text, coalesce(dt.action_reported,'False'), coalesce(s.geolocation->>'location',''),
        (select count(*) from action_events a where a.from_event_id=e.id), coalesce(e.device_description,'')
        from detection_events dt join events e on e.id=dt.id
        left join devices d on d.id=e.device_id left join sensors s on s.id=e.device_id
        where {EV} order by e.created_at desc""")
    by_type, by_zone, by_hour = Counter(), Counter(), Counter()
    det_done, det_rows = 0, []
    for r in det_raw:
        name = _parse_name(r[2], r[7]); zone = _zone_of(r[5], name)
        tko = L.label(L.DETECTION, r[3]); done = str(r[4]).lower() == "true" or int(r[6] or 0) > 0
        det_done += done; by_type[tko] += 1; by_zone[zone] += 1; by_hour[int(str(r[1])[11:13])] += 1
        det_rows.append([r[0], tko, name, zone, r[1], "완료" if done else "미처리"])
    type_dist, zone_dist = by_type.most_common(), by_zone.most_common()
    hourly = [by_hour.get(h, 0) for h in range(24)]
    sections.append({"no": 3, "name": "탐지 이벤트 현황", "sub": "현황 분석", "blocks": [
        {"type": "summary", "cid": "EVENT_SUMMARY_PIE", "lines": [
            f"탐지 이벤트 {det_total:,}건 · 조치 완료율 {round(det_done/det_total*100,1) if det_total else 0}% ({det_done:,}/{det_total:,})",
            (f"최다 유형: {type_dist[0][0]} ({type_dist[0][1]:,}건) · 최다 구역: {zone_dist[0][0]} ({zone_dist[0][1]:,}건)" if type_dist else "데이터 없음"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_SUMMARY_PIE", "det_type", "탐지유형별 분포", "doughnut", [x[0] for x in type_dist], [x[1] for x in type_dist], center=[f"{det_total:,}", "건"]),
            _chart("EVENT_ZONE_PIE", "det_zone", "구역별 분포", "doughnut", [x[0] for x in zone_dist], [x[1] for x in zone_dist], center=[f"{det_total:,}", "건"], accent="amber"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_DAILY_BAR", "det_hour", "시간대별 탐지 분포", "vbar", [f"{h:02d}시" for h in range(24)], hourly),
        ]},
        _grid("EVENT_DETECTION_GRID", "탐지 이벤트 목록", ["번호", "탐지 유형", "장비", "구역", "발생 일시", "조치"],
              [9, 17, 24, 13, 22, 15], det_rows, det_total),
    ]})

    # ── 4. 장애 이벤트 ──
    mal_raw = q(f"""select e.id, to_char(e.created_at,'YYYY-MM-DD HH24:MI'), m.reason::text,
        coalesce(d.name_device,''), coalesce(s.geolocation->>'location',''),
        (select count(*) from action_events a where a.from_event_id=e.id), coalesce(e.device_description,'')
        from malfunction_events m join events e on e.id=m.id
        left join devices d on d.id=e.device_id left join sensors s on s.id=e.device_id
        where {EV} order by e.created_at desc""")
    mal_reason, mal_rows = Counter(), []
    for r in mal_raw:
        name = _parse_name(r[3], r[6]); rko = L.label(L.FAULT, r[2]); mal_reason[rko] += 1
        mal_rows.append([r[0], rko, name, _zone_of(r[4], name), r[1], "완료" if int(r[5] or 0) > 0 else "미처리"])
    mal_dist = mal_reason.most_common()
    sections.append({"no": 4, "name": "장애 이벤트 현황", "sub": "현황 분석", "blocks": [
        {"type": "summary", "cid": "EVENT_MALFUNCTION_GRID", "lines": [
            f"장애 이벤트 {mal_total:,}건 발생",
            (f"최다 장애 유형: {mal_dist[0][0]} ({mal_dist[0][1]:,}건)" if mal_dist else "장애 없음"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_MALFUNCTION_BAR", "mal_reason", "장애 유형별 분포", "hbar", [x[0] for x in mal_dist], [x[1] for x in mal_dist]),
        ]},
        _grid("EVENT_MALFUNCTION_GRID", "장애 이벤트 목록", ["번호", "장애 유형", "장비", "구역", "발생 일시", "조치"],
              [9, 18, 26, 13, 22, 12], mal_rows, mal_total),
    ]})

    # ── 5. 조치 이벤트 ──
    act_rows = [[r[0], r[1], L.label(L.ACTION_TYPE, r[2]), r[3] or "", r[4] or ""]
                for r in q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), type_event, content, \"user\" from action_events where {CC} order by created_at desc")]
    sections.append({"no": 5, "name": "조치 이벤트 현황", "sub": "상세 데이터", "blocks": [
        _grid("EVENT_ACTION_GRID", "조치 이벤트 목록", ["번호", "조치 일시", "유형", "조치 내용", "조치자"],
              [8, 18, 13, 46, 15], act_rows, act_total),
    ]})

    # ── 6. 시스템 / 운영 로그 ──
    sys_sev = [(L.label(L.SEVERITY, r[0]), int(r[1])) for r in q(f"select severity, count(*) from system_events where {CC}{SEV_FILTER} group by severity order by 2 desc")]
    sys_daily = q(f"select to_char(date_trunc('day',created_at),'MM-DD'), count(*) from system_events where {CC}{SEV_FILTER} group by 1 order by 1")
    # v6.1: title 컬럼 추가
    sys_rows = [[r[0], r[1], L.label(L.SYSTEM_EVENT, r[2]), L.label(L.SEVERITY, r[3]), r[4], r[5]]
                for r in q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), type_event::text, severity::text, coalesce(title,''), coalesce(message,'') from system_events where {CC}{SEV_FILTER} order by created_at desc")]
    sections.append({"no": 6, "name": "시스템 / 운영 로그", "sub": "현황 분석", "blocks": [
        {"type": "charts", "charts": [
            _chart("SYSTEM_SEVERITY_BAR", "sys_sev", "심각도별 분포", "vbar", [x[0] for x in sys_sev], [x[1] for x in sys_sev]),
            _chart("SYSTEM_TREND_LINE", "sys_trend", "시스템 이벤트 추이", "line", [str(r[0]) for r in sys_daily], [int(r[1]) for r in sys_daily]),
        ]},
        _grid("SYSTEM_EVENT_GRID", "시스템 이벤트 목록", ["번호", "발생 일시", "유형", "심각도", "제목", "메시지"],
              [7, 16, 15, 12, 20, 30], sys_rows, sys_total),
    ]})

    # ── 7. 설정 변경 이력 ──
    # v6.1: actor_name, actor_ip, resource_name, description 확장
    cfg_rows = [[r[0], r[1], r[2], r[3], L.label(L.CONFIG_RESOURCE, r[4]),
                 (r[5] or r[6] or ""), L.label(L.CONFIG_ACTION, r[7]), r[8]]
                for r in q(f"""select id, to_char(created_at,'YYYY-MM-DD HH24:MI'),
                    coalesce(actor_name, '(system)'), coalesce(actor_ip, ''),
                    resource_type::text, coalesce(resource_name, ''), coalesce(cast(resource_id as text), ''),
                    action::text, coalesce(description, '')
                    from config_change_logs where {CC} order by created_at desc""")]
    sections.append({"no": 7, "name": "설정 변경 이력", "sub": "상세 데이터", "blocks": [
        _grid("SYSTEM_CONFIG_GRID", "설정 변경 이력",
              ["번호", "변경 일시", "행위자", "IP", "리소스 유형", "리소스명", "액션", "변경설명"],
              [6, 13, 12, 12, 14, 15, 10, 18], cfg_rows, cfg_total),
    ]})

    # ── 8. 감사 로그 ──
    # v6.1: actor_login_id 폴백
    aud_rows = [[r[0], r[1], L.label(L.AUDIT_ACTION, r[2]), L.label(L.RESULT, r[3]), L.label(L.AUDIT_RESOURCE, r[4]), r[5]]
                for r in q(f"""select id, to_char(created_at,'YYYY-MM-DD HH24:MI'),
                    action_type, action_status, resource_type,
                    coalesce(actor_name, actor_login_id, '(system)')
                    from audit_logs where {CC} order by created_at desc""")]
    sections.append({"no": 8, "name": "감사 로그", "sub": "상세 데이터", "blocks": [
        _grid("SYSTEM_AUDIT_GRID", "감사 로그", ["번호", "발생 일시", "액션", "상태", "리소스", "행위자"],
              [8, 18, 18, 14, 20, 22], aud_rows, aud_total),
    ]})

    # ── 9. 사용자 현황 ──
    usr_role = [(L.label(L.ROLE, r[0]), int(r[1])) for r in q("select role, count(*) from account_users group by role order by 2 desc")]
    log_daily = q(f"select to_char(date_trunc('day',created_at),'MM-DD'), count(*) from user_login_logs where {CC} group by 1 order by 1")
    log_result = [(L.label(L.RESULT, r[0]), int(r[1])) for r in q(f"select result, count(*) from user_login_logs where {CC} group by result order by 2 desc")]
    usr_rows = [[r[0], r[1] or "", r[2] or "", L.label(L.ROLE, r[3]), r[4] or ""]
                for r in q("select id, login_id, name, role, email from account_users order by id")]
    log_rows = [[r[0], r[1], r[2] or "", L.label(L.LOGIN_ACTION, r[3]), L.label(L.RESULT, r[4]), r[5] or ""]
                for r in q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), login_id, action, result, ip_address from user_login_logs where {CC} order by created_at desc")]
    # v6.1: account_users LEFT JOIN
    ses_rows = [[r[0], r[2] or f"(uid:{r[1]})", r[3], r[4], r[5], r[6]]
                for r in q("""select s.id, s.user_id, coalesce(u.login_id,''), coalesce(u.name,''),
                    coalesce(s.ip_address,''),
                    to_char(s.created_at,'YYYY-MM-DD HH24:MI'),
                    to_char(s.expires_at,'YYYY-MM-DD HH24:MI')
                    from user_sessions s left join account_users u on u.id = s.user_id
                    order by s.created_at desc""")]
    sections.append({"no": 9, "name": "사용자 현황", "sub": "현황 분석", "blocks": [
        {"type": "charts", "charts": [
            _chart("USER_ROLE_PIE", "usr_role", "역할별 사용자 분포", "doughnut", [x[0] for x in usr_role], [x[1] for x in usr_role], center=[f"{usr_total}", "명"]),
            _chart("USER_LOGIN_RESULT_PIE", "usr_result", "로그인 결과 분포", "doughnut", [x[0] for x in log_result], [x[1] for x in log_result], center=[f"{log_total:,}", "건"], accent="green"),
        ]},
        {"type": "charts", "charts": [
            _chart("USER_LOGIN_TREND_LINE", "usr_login", "일별 로그인 추이", "line", [str(r[0]) for r in log_daily], [int(r[1]) for r in log_daily]),
        ]},
        _grid("USER_GRID", "사용자 목록", ["ID", "로그인 ID", "이름", "역할", "이메일"], [8, 20, 18, 18, 36], usr_rows, usr_total),
        _grid("USER_LOGIN_GRID", "로그인 이력", ["번호", "발생 일시", "로그인 ID", "액션", "결과", "IP"], [8, 18, 20, 14, 14, 26], log_rows, log_total),
        _grid("USER_SESSION_GRID", "세션 목록", ["ID", "로그인 ID", "사용자명", "IP", "생성 일시", "만료 일시"],
              [8, 15, 15, 15, 22, 25], ses_rows, ses_total),
    ]})

    # ── 10. 서버 현황 ──
    srv_status, srv_rows = Counter(), []
    for r in q("select s.id, s.name, s.status::text, coalesce(c.name,'') from servers s left join server_categories c on c.id=s.category_id order by s.id"):
        st = L.label(L.STATUS, r[2] or "미상"); srv_status[st] += 1
        srv_rows.append([r[0], r[1] or "", st, r[3]])
    sections.append({"no": 10, "name": "서버 현황", "sub": "자산 현황", "blocks": [
        {"type": "charts", "charts": [
            _chart("SERVER_STATUS_PIE", "srv_status", "서버 상태 분포", "doughnut", list(srv_status.keys()), list(srv_status.values()), center=[f"{srv_total}", "대"]),
        ]},
        _grid("SERVER_GRID", "서버 목록", ["ID", "서버명", "상태", "카테고리"], [8, 34, 20, 38], srv_rows, srv_total),
    ]})

    if enabled_components is not None:
        sections = _filter_sections(sections, enabled_components)

    return {"meta": meta, "sections": sections}


async def build_master_data_async(
    db: AsyncSession,
    start: datetime,
    end: datetime,
    meta: dict,
    enabled_components: Optional[set[str]] = None,
    severity_filter: Optional[list[str]] = None,
) -> dict:
    """AsyncSession 버전 — build_master_data와 동일 로직/결과.

    v6.0 Phase 3: reports.py 라우터 async 전환에 대응해 신설.
    - db.execute(text(...)) → await db.execute(text(...))
    - 나머지(Row 처리, dict 조립, _filter_sections)는 sync 버전과 동일.
    - severity_filter 화이트리스트 검증 유지 (SQL injection 차단).
    """
    p = {"start": start, "end": end}

    async def q(sql: str, params: dict | None = None) -> list:
        result = await db.execute(text(sql), {**p, **(params or {})})
        return list(result.all())

    async def scalar(sql: str) -> int:
        result = await db.execute(text(sql), p)
        r = result.scalar()
        return int(r or 0)

    EV = "e.created_at >= :start AND e.created_at < :end"
    CC = "created_at >= :start AND created_at < :end"

    # v5.4 P1-3: severity_filter 화이트리스트 검증 + system_events 쿼리 조건 조립
    _valid_sev = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
    _safe_sev = [s.upper() for s in (severity_filter or []) if isinstance(s, str) and s.upper() in _valid_sev]
    SEV_FILTER = f" AND severity::text IN ({', '.join(repr(s) for s in _safe_sev)})" if _safe_sev else ""

    det_total = await scalar(f"select count(*) from detection_events d join events e on e.id=d.id where {EV}")
    mal_total = await scalar(f"select count(*) from malfunction_events m join events e on e.id=m.id where {EV}")
    act_total = await scalar(f"select count(*) from action_events where {CC}")
    dev_total = await scalar("select count(*) from devices")
    sys_total = await scalar(f"select count(*) from system_events where {CC}{SEV_FILTER}")
    cfg_total = await scalar(f"select count(*) from config_change_logs where {CC}")
    aud_total = await scalar(f"select count(*) from audit_logs where {CC}")
    usr_total = await scalar("select count(*) from account_users")
    ses_total = await scalar("select count(*) from user_sessions")
    log_total = await scalar(f"select count(*) from user_login_logs where {CC}")
    srv_total = await scalar("select count(*) from servers")

    sections: list[dict] = []

    # ── 1. 종합 요약 ──
    sections.append({"no": 1, "name": "종합 요약", "sub": "현황 분석", "blocks": [
        {"type": "cards", "cid": "SUMMARY_CARD", "cards": [
            {"label": "장비", "value": dev_total, "unit": "대", "color": "blue"},
            {"label": "탐지 이벤트", "value": det_total, "unit": "건", "color": "navy"},
            {"label": "장애 이벤트", "value": mal_total, "unit": "건", "color": "red"},
            {"label": "조치 이벤트", "value": act_total, "unit": "건", "color": "green"},
            {"label": "시스템 이벤트", "value": sys_total, "unit": "건", "color": "amber"},
            {"label": "사용자", "value": usr_total, "unit": "명", "color": "teal"},
        ]},
        {"type": "summary", "cid": "SUMMARY_CARD", "lines": [
            f"분석 기간 {start:%Y-%m-%d} ~ {end:%Y-%m-%d} — 전 도메인 통합 운영 보고서",
            f"이벤트 총계: 탐지 {det_total:,}건 · 장애 {mal_total:,}건 · 조치 {act_total:,}건",
            f"자산: 장비 {dev_total:,}대 · 서버 {srv_total}대 · 사용자 {usr_total}명",
            f"운영 로그: 시스템 {sys_total:,}건 · 설정 변경 {cfg_total:,}건 · 감사 {aud_total:,}건 · 로그인 {log_total:,}건",
        ]},
    ]})

    # ── 2. 장비 현황 ──
    _dev_status_raw = await q("select status, count(*) from devices group by status order by 2 desc")
    dev_status = [(L.label(L.STATUS, r[0]), int(r[1])) for r in _dev_status_raw]
    _dev_type_raw = await q("select category_device, count(*) from devices group by category_device order by 2 desc")
    dev_type = [(L.label(L.DEVICE_CATEGORY, r[0]), int(r[1])) for r in _dev_type_raw]
    _dev_rows_raw = await q("select id, name_device, category_device, type_device, version, status, is_enable from devices order by id")
    dev_rows = [[r[0], r[1], L.label(L.DEVICE_CATEGORY, r[2]), r[3], r[4] or "",
                 L.label(L.STATUS, r[5]), "사용" if r[6] else "미사용"]
                for r in _dev_rows_raw]
    sections.append({"no": 2, "name": "장비 현황", "sub": "자산 현황", "blocks": [
        {"type": "charts", "charts": [
            _chart("DEVICE_STATUS_PIE", "dev_status", "장비 상태 분포", "doughnut", [x[0] for x in dev_status], [x[1] for x in dev_status], center=[f"{dev_total}", "대"]),
            _chart("DEVICE_TYPE_BAR", "dev_type", "유형별 장비 현황", "vbar", [x[0] for x in dev_type], [x[1] for x in dev_type]),
        ]},
        _grid("DEVICE_GRID", "장비 목록", ["ID", "장비명", "유형", "타입", "버전", "상태", "사용"],
              [7, 26, 12, 17, 12, 13, 13], dev_rows, dev_total),
    ]})

    # ── 3. 탐지 이벤트 ──
    # v6.0-report_progress_perf: 통계는 GROUP BY SQL로 이관 (파이썬 66k iter 제거).
    #   by_type, by_hour, done_count는 전체 대상 정확도 유지.
    #   by_zone은 sensors.geolocation approximation (파이썬 정규식 name-based zone은 SQL 이관 복잡).
    # 상세 rows는 LIMIT 500 (사용자 결정 Y: PDF 상위 500 + CSV 다운로드로 전량 보전).
    _type_raw = await q(f"""select dt.result::text, count(*)
        from detection_events dt join events e on e.id=dt.id
        where {EV} group by dt.result order by 2 desc""")
    type_dist = [(L.label(L.DETECTION, r[0]), int(r[1])) for r in _type_raw]

    _zone_raw = await q(f"""select coalesce(nullif(split_part(s.geolocation->>'location', '-', 1), ''), '미지정') as zone,
        count(*)
        from detection_events dt join events e on e.id=dt.id
        left join sensors s on s.id = e.device_id
        where {EV} group by zone order by 2 desc""")
    zone_dist = [(str(r[0]), int(r[1])) for r in _zone_raw]

    _hour_raw = await q(f"""select extract(hour from e.created_at)::int as h, count(*)
        from detection_events dt join events e on e.id=dt.id
        where {EV} group by h""")
    _hour_map = {int(r[0]): int(r[1]) for r in _hour_raw}
    hourly = [_hour_map.get(h, 0) for h in range(24)]

    det_done = await scalar(f"""select count(*) from detection_events dt join events e on e.id=dt.id
        where {EV} and (dt.action_reported::text = 'True'
                       or exists (select 1 from action_events a where a.from_event_id = e.id))""")

    # 상세 rows — 상위 500 (최근순). 전체는 별도 CSV 다운로드로 100% 보전.
    _det_rows_raw = await q(f"""select e.id, to_char(e.created_at,'YYYY-MM-DD HH24:MI'), coalesce(d.name_device,''),
        dt.result::text, coalesce(dt.action_reported,'False'), coalesce(s.geolocation->>'location',''),
        (select count(*) from action_events a where a.from_event_id=e.id), coalesce(e.device_description,'')
        from detection_events dt join events e on e.id=dt.id
        left join devices d on d.id=e.device_id left join sensors s on s.id=e.device_id
        where {EV} order by e.created_at desc limit 500""")
    det_rows = []
    for r in _det_rows_raw:
        name = _parse_name(r[2], r[7]); zone = _zone_of(r[5], name)
        tko = L.label(L.DETECTION, r[3]); done = str(r[4]).lower() == "true" or int(r[6] or 0) > 0
        det_rows.append([r[0], tko, name, zone, r[1], "완료" if done else "미처리"])
    sections.append({"no": 3, "name": "탐지 이벤트 현황", "sub": "현황 분석", "blocks": [
        {"type": "summary", "cid": "EVENT_SUMMARY_PIE", "lines": [
            f"탐지 이벤트 {det_total:,}건 · 조치 완료율 {round(det_done/det_total*100,1) if det_total else 0}% ({det_done:,}/{det_total:,})",
            (f"최다 유형: {type_dist[0][0]} ({type_dist[0][1]:,}건) · 최다 구역: {zone_dist[0][0]} ({zone_dist[0][1]:,}건)" if type_dist else "데이터 없음"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_SUMMARY_PIE", "det_type", "탐지유형별 분포", "doughnut", [x[0] for x in type_dist], [x[1] for x in type_dist], center=[f"{det_total:,}", "건"]),
            _chart("EVENT_ZONE_PIE", "det_zone", "구역별 분포", "doughnut", [x[0] for x in zone_dist], [x[1] for x in zone_dist], center=[f"{det_total:,}", "건"], accent="amber"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_DAILY_BAR", "det_hour", "시간대별 탐지 분포", "vbar", [f"{h:02d}시" for h in range(24)], hourly),
        ]},
        _grid("EVENT_DETECTION_GRID", "탐지 이벤트 목록", ["번호", "탐지 유형", "장비", "구역", "발생 일시", "조치"],
              [9, 17, 24, 13, 22, 15], det_rows, det_total),
    ]})

    # ── 4. 장애 이벤트 ──
    # v6.0-report_progress_perf: 통계는 SQL GROUP BY, 상세 rows는 LIMIT 500.
    _mal_reason_raw = await q(f"""select m.reason::text, count(*)
        from malfunction_events m join events e on e.id=m.id
        where {EV} group by m.reason order by 2 desc""")
    mal_dist = [(L.label(L.FAULT, r[0]), int(r[1])) for r in _mal_reason_raw]

    _mal_rows_raw = await q(f"""select e.id, to_char(e.created_at,'YYYY-MM-DD HH24:MI'), m.reason::text,
        coalesce(d.name_device,''), coalesce(s.geolocation->>'location',''),
        (select count(*) from action_events a where a.from_event_id=e.id), coalesce(e.device_description,'')
        from malfunction_events m join events e on e.id=m.id
        left join devices d on d.id=e.device_id left join sensors s on s.id=e.device_id
        where {EV} order by e.created_at desc limit 500""")
    mal_rows = []
    for r in _mal_rows_raw:
        name = _parse_name(r[3], r[6]); rko = L.label(L.FAULT, r[2])
        mal_rows.append([r[0], rko, name, _zone_of(r[4], name), r[1], "완료" if int(r[5] or 0) > 0 else "미처리"])
    sections.append({"no": 4, "name": "장애 이벤트 현황", "sub": "현황 분석", "blocks": [
        {"type": "summary", "cid": "EVENT_MALFUNCTION_GRID", "lines": [
            f"장애 이벤트 {mal_total:,}건 발생",
            (f"최다 장애 유형: {mal_dist[0][0]} ({mal_dist[0][1]:,}건)" if mal_dist else "장애 없음"),
        ]},
        {"type": "charts", "charts": [
            _chart("EVENT_MALFUNCTION_BAR", "mal_reason", "장애 유형별 분포", "hbar", [x[0] for x in mal_dist], [x[1] for x in mal_dist]),
        ]},
        _grid("EVENT_MALFUNCTION_GRID", "장애 이벤트 목록", ["번호", "장애 유형", "장비", "구역", "발생 일시", "조치"],
              [9, 18, 26, 13, 22, 12], mal_rows, mal_total),
    ]})

    # ── 5. 조치 이벤트 ──
    # v6.0-report_progress_perf: 상세 rows LIMIT 500 (CSV 다운로드로 전량 보전).
    _act_raw = await q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), type_event, content, \"user\" from action_events where {CC} order by created_at desc limit 500")
    act_rows = [[r[0], r[1], L.label(L.ACTION_TYPE, r[2]), r[3] or "", r[4] or ""]
                for r in _act_raw]
    sections.append({"no": 5, "name": "조치 이벤트 현황", "sub": "상세 데이터", "blocks": [
        _grid("EVENT_ACTION_GRID", "조치 이벤트 목록", ["번호", "조치 일시", "유형", "조치 내용", "조치자"],
              [8, 18, 13, 46, 15], act_rows, act_total),
    ]})

    # ── 6. 시스템 / 운영 로그 ──
    _sys_sev_raw = await q(f"select severity, count(*) from system_events where {CC}{SEV_FILTER} group by severity order by 2 desc")
    sys_sev = [(L.label(L.SEVERITY, r[0]), int(r[1])) for r in _sys_sev_raw]
    sys_daily = await q(f"select to_char(date_trunc('day',created_at),'MM-DD'), count(*) from system_events where {CC}{SEV_FILTER} group by 1 order by 1")
    # v6.1: title 컬럼 추가. v6.0-report_progress_perf: LIMIT 500.
    _sys_rows_raw = await q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), type_event::text, severity::text, coalesce(title,''), coalesce(message,'') from system_events where {CC}{SEV_FILTER} order by created_at desc limit 500")
    sys_rows = [[r[0], r[1], L.label(L.SYSTEM_EVENT, r[2]), L.label(L.SEVERITY, r[3]), r[4], r[5]]
                for r in _sys_rows_raw]
    sections.append({"no": 6, "name": "시스템 / 운영 로그", "sub": "현황 분석", "blocks": [
        {"type": "charts", "charts": [
            _chart("SYSTEM_SEVERITY_BAR", "sys_sev", "심각도별 분포", "vbar", [x[0] for x in sys_sev], [x[1] for x in sys_sev]),
            _chart("SYSTEM_TREND_LINE", "sys_trend", "시스템 이벤트 추이", "line", [str(r[0]) for r in sys_daily], [int(r[1]) for r in sys_daily]),
        ]},
        _grid("SYSTEM_EVENT_GRID", "시스템 이벤트 목록", ["번호", "발생 일시", "유형", "심각도", "제목", "메시지"],
              [7, 16, 15, 12, 20, 30], sys_rows, sys_total),
    ]})

    # ── 7. 설정 변경 이력 ──
    # v6.1: actor_name/actor_ip/resource_name/description 확장. v6.0-report_progress_perf: LIMIT 500.
    _cfg_raw = await q(f"""select id, to_char(created_at,'YYYY-MM-DD HH24:MI'),
        coalesce(actor_name, '(system)'), coalesce(actor_ip, ''),
        resource_type::text, coalesce(resource_name, ''), coalesce(cast(resource_id as text), ''),
        action::text, coalesce(description, '')
        from config_change_logs where {CC} order by created_at desc limit 500""")
    cfg_rows = [[r[0], r[1], r[2], r[3], L.label(L.CONFIG_RESOURCE, r[4]),
                 (r[5] or r[6] or ""), L.label(L.CONFIG_ACTION, r[7]), r[8]]
                for r in _cfg_raw]
    sections.append({"no": 7, "name": "설정 변경 이력", "sub": "상세 데이터", "blocks": [
        _grid("SYSTEM_CONFIG_GRID", "설정 변경 이력",
              ["번호", "변경 일시", "행위자", "IP", "리소스 유형", "리소스명", "액션", "변경설명"],
              [6, 13, 12, 12, 14, 15, 10, 18], cfg_rows, cfg_total),
    ]})

    # ── 8. 감사 로그 ──
    # v6.1: actor_login_id 폴백. v6.0-report_progress_perf: LIMIT 500.
    _aud_raw = await q(f"""select id, to_char(created_at,'YYYY-MM-DD HH24:MI'),
        action_type, action_status, resource_type,
        coalesce(actor_name, actor_login_id, '(system)')
        from audit_logs where {CC} order by created_at desc limit 500""")
    aud_rows = [[r[0], r[1], L.label(L.AUDIT_ACTION, r[2]), L.label(L.RESULT, r[3]), L.label(L.AUDIT_RESOURCE, r[4]), r[5]]
                for r in _aud_raw]
    sections.append({"no": 8, "name": "감사 로그", "sub": "상세 데이터", "blocks": [
        _grid("SYSTEM_AUDIT_GRID", "감사 로그", ["번호", "발생 일시", "액션", "상태", "리소스", "행위자"],
              [8, 18, 18, 14, 20, 22], aud_rows, aud_total),
    ]})

    # ── 9. 사용자 현황 ──
    _usr_role_raw = await q("select role, count(*) from account_users group by role order by 2 desc")
    usr_role = [(L.label(L.ROLE, r[0]), int(r[1])) for r in _usr_role_raw]
    log_daily = await q(f"select to_char(date_trunc('day',created_at),'MM-DD'), count(*) from user_login_logs where {CC} group by 1 order by 1")
    _log_result_raw = await q(f"select result, count(*) from user_login_logs where {CC} group by result order by 2 desc")
    log_result = [(L.label(L.RESULT, r[0]), int(r[1])) for r in _log_result_raw]
    _usr_rows_raw = await q("select id, login_id, name, role, email from account_users order by id")
    usr_rows = [[r[0], r[1] or "", r[2] or "", L.label(L.ROLE, r[3]), r[4] or ""]
                for r in _usr_rows_raw]
    _log_rows_raw = await q(f"select id, to_char(created_at,'YYYY-MM-DD HH24:MI'), login_id, action, result, ip_address from user_login_logs where {CC} order by created_at desc limit 500")
    log_rows = [[r[0], r[1], r[2] or "", L.label(L.LOGIN_ACTION, r[3]), L.label(L.RESULT, r[4]), r[5] or ""]
                for r in _log_rows_raw]
    # v6.1: account_users LEFT JOIN. v6.0-report_progress_perf: LIMIT 500.
    _ses_rows_raw = await q("""select s.id, s.user_id, coalesce(u.login_id, ''), coalesce(u.name, ''),
        coalesce(s.ip_address, ''),
        to_char(s.created_at,'YYYY-MM-DD HH24:MI'),
        to_char(s.expires_at,'YYYY-MM-DD HH24:MI')
        from user_sessions s left join account_users u on u.id = s.user_id
        order by s.created_at desc limit 500""")
    ses_rows = [[r[0], r[2] or f"(uid:{r[1]})", r[3], r[4], r[5], r[6]]
                for r in _ses_rows_raw]
    sections.append({"no": 9, "name": "사용자 현황", "sub": "현황 분석", "blocks": [
        {"type": "charts", "charts": [
            _chart("USER_ROLE_PIE", "usr_role", "역할별 사용자 분포", "doughnut", [x[0] for x in usr_role], [x[1] for x in usr_role], center=[f"{usr_total}", "명"]),
            _chart("USER_LOGIN_RESULT_PIE", "usr_result", "로그인 결과 분포", "doughnut", [x[0] for x in log_result], [x[1] for x in log_result], center=[f"{log_total:,}", "건"], accent="green"),
        ]},
        {"type": "charts", "charts": [
            _chart("USER_LOGIN_TREND_LINE", "usr_login", "일별 로그인 추이", "line", [str(r[0]) for r in log_daily], [int(r[1]) for r in log_daily]),
        ]},
        _grid("USER_GRID", "사용자 목록", ["ID", "로그인 ID", "이름", "역할", "이메일"], [8, 20, 18, 18, 36], usr_rows, usr_total),
        _grid("USER_LOGIN_GRID", "로그인 이력", ["번호", "발생 일시", "로그인 ID", "액션", "결과", "IP"], [8, 18, 20, 14, 14, 26], log_rows, log_total),
        _grid("USER_SESSION_GRID", "세션 목록", ["ID", "로그인 ID", "사용자명", "IP", "생성 일시", "만료 일시"],
              [8, 15, 15, 15, 22, 25], ses_rows, ses_total),
    ]})

    # ── 10. 서버 현황 ──
    srv_status, srv_rows = Counter(), []
    _srv_raw = await q("select s.id, s.name, s.status::text, coalesce(c.name,'') from servers s left join server_categories c on c.id=s.category_id order by s.id")
    for r in _srv_raw:
        st = L.label(L.STATUS, r[2] or "미상"); srv_status[st] += 1
        srv_rows.append([r[0], r[1] or "", st, r[3]])
    sections.append({"no": 10, "name": "서버 현황", "sub": "자산 현황", "blocks": [
        {"type": "charts", "charts": [
            _chart("SERVER_STATUS_PIE", "srv_status", "서버 상태 분포", "doughnut", list(srv_status.keys()), list(srv_status.values()), center=[f"{srv_total}", "대"]),
        ]},
        _grid("SERVER_GRID", "서버 목록", ["ID", "서버명", "상태", "카테고리"], [8, 34, 20, 38], srv_rows, srv_total),
    ]})

    if enabled_components is not None:
        sections = _filter_sections(sections, enabled_components)

    return {"meta": meta, "sections": sections}


def _filter_sections(sections: list[dict], enabled: set[str]) -> list[dict]:
    """비정형: enabled_components에 포함된 컴포넌트만 남기고 빈 섹션 제거."""
    out = []
    for sec in sections:
        kept = []
        for b in sec["blocks"]:
            t = b["type"]
            if t == "grid":
                if b["cid"] in enabled:
                    kept.append(b)
            elif t == "charts":
                ch = [c for c in b["charts"] if c["cid"] in enabled]
                if ch:
                    kept.append({"type": "charts", "charts": ch})
            elif t == "cards":
                if b["cid"] in enabled:
                    kept.append(b)
            elif t == "summary":
                kept.append(b)  # 임시: 섹션에 내용 있으면 유지, 없으면 아래에서 제거
        # summary만 남은 섹션은 제거
        non_summary = [b for b in kept if b["type"] != "summary"]
        if non_summary:
            out.append({**sec, "blocks": kept})
    # 섹션 번호 재부여
    for i, sec in enumerate(out, 1):
        sec["no"] = i
    return out
