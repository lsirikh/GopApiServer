"""Default 프로필 이미지 생성/보장 (v6.0-default_profile_image, 2026-07-07).

정책:
- 프로필 사진이 없는 계정은 응답에서 default 이미지 URL 을 받는다.
- data/profiles/default.png 는 gitignore 대상(개인 사진 폴더)이라 clone 배포엔 없음.
  → startup 에서 없으면 Pillow 로 자동 생성(신규 PC 배포에도 견고).
- 파일명은 고정 'default.png' — 응답 헬퍼/서빙 엔드포인트가 이 이름을 참조.
"""
from __future__ import annotations

import os

DEFAULT_PROFILE_FILENAME = "default.png"


def ensure_default_profile_image(storage_path: str) -> None:
    """storage_path/default.png 가 없으면 생성한다. 실패해도 앱 기동은 계속.

    회색 배경 + 중앙 사람 실루엣(단순 도형)의 중립 아바타.
    Pillow 미설치/오류 시 로그만 남기고 skip(서빙 엔드포인트가 404 대신 안전 처리).
    """
    try:
        os.makedirs(storage_path, exist_ok=True)
        target = os.path.join(storage_path, DEFAULT_PROFILE_FILENAME)
        if os.path.exists(target):
            return

        from PIL import Image, ImageDraw

        size = 256
        bg = (224, 227, 231)      # 연회색 배경
        fg = (150, 157, 165)      # 실루엣 색
        img = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(img)

        # 머리 (원)
        head_r = size * 0.16
        head_cx, head_cy = size / 2, size * 0.38
        draw.ellipse(
            [head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
            fill=fg,
        )
        # 어깨/몸통 (아래쪽 반원 형태 — pieslice 로 근사)
        body_w = size * 0.52
        body_top = size * 0.60
        draw.pieslice(
            [size / 2 - body_w / 2, body_top, size / 2 + body_w / 2, body_top + body_w],
            start=180, end=360, fill=fg,
        )
        img.save(target, format="PNG")
        print(f"[OK] default profile image created: {target}")
    except Exception as e:  # Pillow 미설치/쓰기 실패 등 — 기동 방해 금지
        print(f"[WARN] default profile image 생성 실패(무시): {e}")
