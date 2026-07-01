"""HTML → PDF 변환 (Playwright + Chromium).

PRD: PRD_Report_Master_Redesign
백그라운드 태스크(스레드) 내에서 동기 Playwright로 A4 PDF 바이트를 생성한다.
Chart.js 렌더 완료(window.__READY__) 후 page.pdf 호출.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def html_to_pdf_bytes(html: str, ready_timeout_ms: int = 120_000) -> bytes:
    """완전한 HTML 문서를 A4 PDF 바이트로 렌더링한다.

    Raises:
        RuntimeError: Playwright 미설치 또는 렌더 실패 시.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("playwright가 설치되지 않았습니다. 'pip install playwright' 후 'playwright install chromium'") from e

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load", timeout=ready_timeout_ms)
            try:
                page.wait_for_function("window.__READY__===true", timeout=ready_timeout_ms)
            except Exception as e:  # 차트 렌더 지연/실패해도 본문은 출력
                logger.warning("report render: __READY__ 대기 실패 (차트 일부 누락 가능): %s", e)
            page.wait_for_timeout(600)
            pdf = page.pdf(
                format="A4", print_background=True, prefer_css_page_size=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            browser.close()

    return _compress_pdf(pdf)


def _compress_pdf(pdf: bytes) -> bytes:
    """PyMuPDF로 무손실 재압축(객체스트림 GC + deflate). Chromium 출력 대비 ~85% 축소.

    PyMuPDF 미설치 시 원본을 그대로 반환한다(graceful)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:  # pragma: no cover
        logger.warning("PyMuPDF 미설치 — PDF 재압축 생략")
        return pdf
    try:
        doc = fitz.open(stream=pdf, filetype="pdf")
        out = doc.tobytes(garbage=4, deflate=True, deflate_images=True,
                          deflate_fonts=True, clean=True)
        doc.close()
        return out if out and len(out) < len(pdf) else pdf
    except Exception as e:  # pragma: no cover
        logger.warning("PDF 재압축 실패, 원본 반환: %s", e)
        return pdf
