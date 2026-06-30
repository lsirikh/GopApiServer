# PRD: 보고서 PDF 한글 깨짐 수정

**문서 버전**: 1.0
**작성일**: 2026-02-12
**상태**: Draft

---

## 1. 문제 정의

`GET /api/reports/generations/{generation_id}/download`로 생성된 PDF 파일의 **한글 텍스트가 깨져서** 출력됩니다.

---

## 2. 근본 원인 분석

### 2.1 핵심 원인: reportlab 한글 폰트 미등록 (pdf_generator.py)

`app/utils/pdf_generator.py`에서 `pdfmetrics`와 `TTFont`를 import하지만 **한글 폰트를 등록하지 않습니다**.

```python
# line 18-19: import만 하고 사용하지 않음
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
```

reportlab의 기본 폰트(Helvetica, Times-Roman, Courier)는 **CJK 문자를 지원하지 않습니다**. 현재 등록된 폰트는 `Symbol`과 `ZapfDingbats`뿐입니다.

**영향 범위** — PDF 내 모든 한글 텍스트:

| 위치 | 코드 (pdf_generator.py) | 한글 포함 내용 |
|------|------------------------|---------------|
| 헤더 - 제목 | line 143 | `generation.title` (예: "주간 운영 보고서") |
| 헤더 - 기간 | line 146 | `"기간: 2026-01-01 ~ 2026-01-31"` |
| 헤더 - 작성자 | line 155 | `"작성: 운영팀 / 홍길동"` |
| 헤더 - 생성일시 | line 158 | `"생성일시: 2026-02-12 ..."` |
| 섹션 제목 | line 174 | `"장비 목록"`, `"탐지 이벤트 목록"` 등 |
| 섹션 내용 | line 178 | 텍스트 요약 본문 |
| 테이블 헤더/데이터 | line 213-215 | 그리드 데이터 (한글 컬럼명, 값) |

### 2.2 부수 원인: matplotlib 한글 폰트 미설정 (chart_generator.py)

`app/utils/chart_generator.py`에서 `matplotlib.rcParams['font.family']`를 설정하지 않습니다. matplotlib 기본 폰트(DejaVu Sans)도 **한글을 지원하지 않으므로** 차트의 레이블/제목이 □□□(tofu)로 표시됩니다.

**영향 범위** — 차트 이미지 내 모든 한글:

| 차트 종류 | 한글 포함 내용 |
|-----------|---------------|
| Pie chart | 레이블 (예: "센서", "카메라"), 제목 |
| Bar chart | X축/Y축 레이블, 제목 |

### 2.3 부수 원인: 다운로드 파일명 인코딩 (reports.py)

```python
# line 521-525
return FileResponse(
    path=generation.pdf_file_path,
    filename=f"{generation.title}.pdf",  # 한글 제목 인코딩 미처리
    media_type="application/pdf"
)
```

`FileResponse`의 `filename`에 한글이 포함되면 일부 브라우저에서 `Content-Disposition` 헤더의 파일명이 깨질 수 있습니다. RFC 5987에 따라 `filename*=UTF-8''...` 형식의 인코딩이 필요합니다.

---

## 3. 시스템 환경

- **OS**: Windows 11
- **사용 가능 한글 폰트**: `C:\Windows\Fonts\malgun.ttf` (맑은 고딕), `malgunbd.ttf` (Bold)
- **reportlab**: PDF 생성 라이브러리
- **matplotlib**: 차트 이미지 생성 라이브러리

---

## 4. 수정 방안

### 4.1 pdf_generator.py — reportlab 한글 폰트 등록

**파일**: `app/utils/pdf_generator.py`

**변경 내용**:
1. 클래스 초기화 시 `malgun.ttf` (맑은 고딕) 폰트를 reportlab에 등록
2. 모든 `ParagraphStyle`의 `fontName`을 등록된 한글 폰트로 변경
3. 테이블 스타일의 `FONTNAME`도 한글 폰트로 변경
4. 폰트 파일이 없는 환경을 대비한 fallback 처리

**구현 방향**:
```
1. 클래스 변수로 FONT_NAME 정의
2. @classmethod _register_fonts() 에서:
   - pdfmetrics.registerFont(TTFont('MalgunGothic', 'malgun.ttf'))
   - pdfmetrics.registerFont(TTFont('MalgunGothicBold', 'malgunbd.ttf'))
   - pdfmetrics.registerFontFamily('MalgunGothic', normal='MalgunGothic', bold='MalgunGothicBold')
   - 실패 시 Helvetica fallback (경고 로그 출력)
3. _get_styles()에서 모든 ParagraphStyle에 fontName='MalgunGothic' 적용
4. _build_table()에서 TableStyle에 FONTNAME='MalgunGothic' 적용
```

### 4.2 chart_generator.py — matplotlib 한글 폰트 설정

**파일**: `app/utils/chart_generator.py`

**변경 내용**:
1. matplotlib의 `rcParams['font.family']`를 한글 폰트로 설정
2. `rcParams['axes.unicode_minus'] = False` (마이너스 기호 깨짐 방지)

**구현 방향**:
```
matplotlib.use('Agg') 직후에:
- plt.rcParams['font.family'] = 'Malgun Gothic'
- plt.rcParams['axes.unicode_minus'] = False
```

### 4.3 reports.py — 다운로드 파일명 인코딩

**파일**: `app/routers/reports.py`

**변경 내용**:
1. `FileResponse`의 `filename`을 ASCII-safe하게 변환
2. `Content-Disposition` 헤더에 RFC 5987 형식의 `filename*` 추가

**구현 방향**:
```
from urllib.parse import quote

encoded_name = quote(f"{generation.title}.pdf")
headers = {
    "Content-Disposition": f"attachment; filename=\"report_{generation_id}.pdf\"; filename*=UTF-8''{encoded_name}"
}
return FileResponse(
    path=generation.pdf_file_path,
    headers=headers,
    media_type="application/pdf"
)
```

---

## 5. 수정 대상 파일 요약

| # | 파일 | 변경 유형 | 설명 |
|---|------|-----------|------|
| 1 | `app/utils/pdf_generator.py` | Bug Fix | 한글 폰트 등록 + 스타일 적용 |
| 2 | `app/utils/chart_generator.py` | Bug Fix | matplotlib 한글 폰트 설정 |
| 3 | `app/routers/reports.py` | Bug Fix | 다운로드 파일명 RFC 5987 인코딩 |

---

## 6. TDD 구현 단계

### Phase 1: pdf_generator.py 한글 폰트 등록
- 1.1 TEST: 폰트 등록 함수 호출 시 MalgunGothic이 등록되는지 검증
- 1.2 TEST: generate_report()로 생성된 PDF bytes가 유효한 PDF인지 검증 (%PDF- 헤더)
- 1.3 TEST: 한글 제목/내용이 포함된 PDF 생성 시 예외 없이 완료되는지 검증
- 1.4 IMPL: _register_fonts() 메서드 구현 + _get_styles() 폰트 적용 + _build_table() 폰트 적용

### Phase 2: chart_generator.py 한글 폰트 설정
- 2.1 TEST: matplotlib rcParams에 한글 폰트가 설정되었는지 검증
- 2.2 TEST: 한글 레이블 포함 차트 생성 시 예외 없이 완료되는지 검증
- 2.3 IMPL: rcParams 한글 폰트 + unicode_minus 설정

### Phase 3: reports.py 다운로드 파일명 인코딩
- 3.1 TEST: 한글 제목 다운로드 시 Content-Disposition 헤더에 filename*=UTF-8'' 포함 검증
- 3.2 TEST: ASCII fallback filename 포함 검증
- 3.3 IMPL: FileResponse headers에 RFC 5987 인코딩 적용

### Phase 4: 통합 검증
- 4.1 VERIFY: 전체 테스트 통과
- 4.2 COMMIT (behavioral): PDF/차트 한글 폰트 수정 + 다운로드 파일명 인코딩

---

## 7. 검증 기준

1. PDF 파일을 열었을 때 한글 텍스트가 정상 표시됨
2. PDF 내 차트 이미지의 한글 레이블이 정상 표시됨
3. 다운로드 파일명이 한글로 정상 표시됨
4. 한글 폰트가 없는 환경에서도 fallback으로 에러 없이 동작함
