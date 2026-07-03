"""섹션 데이터 → 풀 HTML (네이비/골드 정형 보고서, 전체 페이지네이션).

PRD: PRD_Report_Master_Redesign
- 표: table-layout:fixed + colgroup(합 100%) + 행단위 사전 페이지네이션(헤더 반복) → 행 잘림/열 오버플로 없음
- 차트: Chart.js (Chromium 렌더), 도넛 중앙텍스트/막대 값라벨
- mode='full': 전체 페이지네이션 / 'compact': 그리드당 2페이지 (검토용)
"""
from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "templates", "reports", "assets")
_ROWS_PER_PAGE = 22
_CANVAS_H = {"doughnut": 62, "vbar": 64, "hbar": 78, "line": 60}
_LEFT_HEADERS = {"장비", "장비명", "조치 내용", "메시지", "이메일", "서버명", "리소스", "카테고리", "IP"}


def _asset(name: str) -> str:
    with open(os.path.join(_ASSETS, name), encoding="utf-8") as f:
        return f.read()


def _j(x):
    return json.dumps(x, ensure_ascii=False)


def _fmt(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def render_report_html(data: dict, mode: str = "full") -> str:
    meta = data["meta"]
    grid_cap = 2 if mode == "compact" else None
    charts_js: list[str] = []

    def chart_cfg(c) -> str:
        labels, values = _j(c["labels"]), _j(c["values"])
        k = c["kind"]
        if k == "doughnut":
            ct = c.get("center") or ["", ""]
            return (f"{{type:'doughnut',data:{{labels:{labels},datasets:[{{data:{values},"
                    f"backgroundColor:PALETTE,borderWidth:2,borderColor:'#fff'}}]}},"
                    f"options:donutOpts('{ct[0]}','{ct[1]}')}}")
        if k == "vbar":
            bg = (f"hourColors({values},{values}.indexOf(Math.max.apply(null,{values})))"
                  if c["id"] == "det_hour" else "gradV('','#3f7bf0','#9cc2fb')")
            return (f"{{type:'bar',data:{{labels:{labels},datasets:[{{data:{values},"
                    f"backgroundColor:{bg},borderRadius:4,maxBarThickness:54}}]}},options:vbarOpts()}}")
        if k == "hbar":
            return (f"{{type:'bar',data:{{labels:{labels},datasets:[{{data:{values},"
                    f"backgroundColor:gradH('','#2f6fed','#74a8fb'),borderRadius:4,barThickness:15}}]}},"
                    f"options:hbarOpts()}}")
        if k == "line":
            return (f"{{type:'line',data:{{labels:{labels},datasets:[{{data:{values},"
                    f"borderColor:'#2f6fed',backgroundColor:'rgba(47,111,237,0.12)',fill:true,"
                    f"tension:0.3,pointRadius:2,pointBackgroundColor:'#2f6fed'}}]}},options:lineOpts()}}")
        return "{}"

    def render_charts(charts) -> str:
        cells = []
        for c in charts:
            charts_js.append(f"makeChart('{c['id']}', {chart_cfg(c)});")
            h = _CANVAS_H.get(c["kind"], 64)
            cells.append(f'<div class="cbox"><div class="cbox-h {c.get("accent","blue")}">{c["title"]}</div>'
                         f'<div class="cbox-b"><div class="chart-wrap" style="height:{h}mm">'
                         f'<canvas id="{c["id"]}"></canvas></div></div></div>')
        return f'<div class="crow">{cells[0]}{cells[1]}</div>' if len(cells) == 2 else "".join(cells)

    def render_cards(cards) -> str:
        cls = "kpis six" if len(cards) > 3 else "kpis"
        out = [f'<div class="{cls}">']
        for c in cards:
            out.append(f'<div class="kpi {c.get("color","blue")}"><div class="num">'
                       f'<span class="big">{_fmt(c["value"])}</span><span class="unit">{c.get("unit","")}</span></div>'
                       f'<div class="lbl">{c["label"]}</div><div class="wm">{c["value"]}</div></div>')
        out.append("</div>")
        return "".join(out)

    def render_summary(lines) -> str:
        items = "".join(f"<li>{x}</li>" for x in lines)
        return ('<div class="summary"><div class="summary-h"><span class="dia">◆</span> 분석 요약</div>'
                f'<ul class="summary-b">{items}</ul></div>')

    def block_height(b) -> float:
        t = b["type"]
        if t == "cards":
            return 66 if len(b["cards"]) > 3 else 38
        if t == "summary":
            return 20 + 7 * len(b["lines"])
        if t == "charts":
            return max(_CANVAS_H.get(c["kind"], 64) for c in b["charts"]) + 20
        return 0

    def render_block(b) -> str:
        if b["type"] == "cards":
            return render_cards(b["cards"])
        if b["type"] == "summary":
            return render_summary(b["lines"])
        if b["type"] == "charts":
            return render_charts(b["charts"])
        return ""

    def cell_html(val, header) -> str:
        s = "" if val is None else str(val)
        if s == "완료":
            return '<td><span class="badge-done">완료</span></td>'
        if s == "미처리":
            return '<td><span class="badge-undone">미처리</span></td>'
        cls = []
        if "일시" in header:
            cls.append("ts-cell")
        if header in _LEFT_HEADERS:
            cls.append("left")
        elif header in ("ID", "번호"):
            cls.append("num-cell")
        return f'<td class="{" ".join(cls)}">{s}</td>' if cls else f"<td>{s}</td>"

    def render_grid_page(g, rows, idx, npages) -> str:
        colg = "<colgroup>" + "".join(f'<col style="width:{p}%">' for p in g["colpct"]) + "</colgroup>"
        ths = "".join(f'<th class="{"left" if h in _LEFT_HEADERS else ""}">{h}</th>' for h in g["columns"])
        body = "".join("<tr>" + "".join(cell_html(v, g["columns"][i]) for i, v in enumerate(row)) + "</tr>" for row in rows)
        capped = grid_cap is not None and npages > grid_cap
        eff = min(npages, grid_cap) if capped else npages
        shown = eff * _ROWS_PER_PAGE
        note = (f'<span class="cap-note">표시 {_fmt(min(shown, g["total"]))}건 · 전체 {_fmt(g["total"])}건</span>'
                if (capped and idx == 0) else "")
        return (f'<div class="tbl-h"><span class="t">{g["title"]} ({idx+1}/{eff})</span>{note}'
                f'<span class="cnt">총 <b>{_fmt(g["total"])}</b> 건</span></div>'
                f'<table class="grid">{colg}<thead><tr>{ths}</tr></thead><tbody>{body}</tbody></table>')

    # ---- pages ----
    pages = []  # {section, sub, group, body}
    for sec in data["sections"]:
        analysis = [b for b in sec["blocks"] if b["type"] != "grid"]
        grids = [b for b in sec["blocks"] if b["type"] == "grid"]
        # analysis 페이지(높이 패킹)
        cur, cur_h, apages = [], 0.0, []
        for b in analysis:
            h = block_height(b)
            if cur and cur_h + h > 232:
                apages.append("".join(render_block(x) for x in cur)); cur, cur_h = [], 0.0
            cur.append(b); cur_h += h
        if cur:
            apages.append("".join(render_block(x) for x in cur))
        for body in apages:
            pages.append({"section": sec["name"], "sub": sec["sub"], "group": "A", "body": body, "no": sec["no"]})
        # grid 페이지
        for g in grids:
            rows = g["rows"]
            chunks = [rows[i:i + _ROWS_PER_PAGE] for i in range(0, len(rows), _ROWS_PER_PAGE)] or [[]]
            ntot = len(chunks)
            use = chunks[:grid_cap] if grid_cap else chunks
            for ci, ch in enumerate(use):
                pages.append({"section": sec["name"], "sub": "상세 데이터", "group": "B",
                              "body": render_grid_page(g, ch, ci, ntot), "no": sec["no"]})

    # within-group 카운터
    gp = defaultdict(list)
    for i, p in enumerate(pages):
        gp[(p["section"], p["group"])].append(i)
    within = {}
    for idxs in gp.values():
        for k, i in enumerate(idxs):
            within[i] = (k + 1, len(idxs))

    sec_first = {}
    for idx, p in enumerate(pages):
        sec_first.setdefault(p["section"], idx + 2)
    total = len(pages) + 1

    # ---- cover ----
    seen, toc = set(), ""
    for p in pages:
        if p["section"] in seen:
            continue
        seen.add(p["section"])
        toc += (f'<li><span class="toc-n">{p["no"]}</span><span class="toc-t">{p["section"]}</span>'
                f'<span class="toc-dot"></span><span class="toc-p">p.{sec_first[p["section"]]}</span></li>')
    cover = f"""<div class="page cover">
  <div class="cover-side"><span>GOP INTEGRATED CONTROL SYSTEM</span></div>
  <div class="cover-top"><span class="doc-no">문서번호 {meta['doc_no']}</span><span class="ctrl-box">관리문서</span></div>
  <div class="cover-mid">
    <div class="cover-sys"><b>GOP</b> 통합 관제 시스템</div><div class="cover-rule"></div>
    <div class="cover-title">{meta['title_spaced']}</div>
    <div class="cover-sub">{meta['subtitle']}</div>
    <div class="period-box"><div class="period-cap">분 석 기 간</div>
      <div class="period-val">{meta['period_start']} — {meta['period_end']}</div></div>
    <div class="info-row">
      <div class="info-cell"><div class="ic-k">보고서</div><div class="ic-v">{meta['report_id']}</div></div>
      <div class="info-cell"><div class="ic-k">유형</div><div class="ic-v">{meta['report_kind']}</div></div>
      <div class="info-cell"><div class="ic-k">기간</div><div class="ic-v">{meta['period_type']}</div></div>
      <div class="info-cell"><div class="ic-k">총 페이지</div><div class="ic-v">{total}장</div></div>
    </div>
  </div>
  <div class="cover-toc"><div class="toc-head">목 차</div><ul class="toc-list two">{toc}</ul></div>
  <div class="cover-foot"><span>GOP 통합관제 · 정형 보고서</span><span>1 / {total}</span></div>
</div>"""

    def sec_header(no, title, sub, lbl):
        return (f'<div class="sec"><div class="sec-bar"></div><div class="sec-no">{no}</div>'
                f'<div class="sec-titles"><div class="sec-title">{title}</div>'
                f'<div class="sec-sub">{sub}</div></div><div class="sec-page">{lbl}</div></div><hr class="sec-rule">')

    body_pages = [cover]
    for idx, p in enumerate(pages):
        g = idx + 2
        w = within.get(idx, (1, 1))
        head = sec_header(p["no"], p["section"], p["sub"], f"{w[0]} / {w[1]}")
        bar = (f'<div class="topbar"><span class="tb-l"><b>{meta["doc_no"]}</b><i>│</i>{p["section"]}</span>'
               f'<span class="tb-r">{g} / {total}</span></div>')
        foot = f'<div class="foot"><span>GOP 통합관제 · 정형 보고서</span><span>{g} / {total}</span></div>'
        body_pages.append(f'<div class="page"><div class="content">{head}{p["body"]}</div>{bar}{foot}</div>')

    css, jslib, chartjs = _asset("report.css"), _asset("charts.js"), _asset("chart.umd.js")
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
            f'<title>{meta["title"]} - {meta["subtitle"]}</title><style>{css}</style></head><body>'
            f'{"".join(body_pages)}'
            f'<script>{chartjs}</script><script>{jslib}'
            f'window.addEventListener("load",function(){{{"".join(charts_js)}window.__READY__=true;}});'
            f'</script></body></html>')


async def render_report_html_async(data: dict, mode: str = "full") -> str:
    """CPU-bound Jinja/문자열 렌더링을 asyncio.to_thread로 오프로드해 이벤트루프 블로킹 방지.

    async 라우터/서비스에서 호출 시 사용. 기존 sync render_report_html 시그니처/동작 완전 유지.
    """
    return await asyncio.to_thread(render_report_html, data, mode)
