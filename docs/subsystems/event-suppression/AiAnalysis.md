# AiAnalysis — 이벤트 억제(정비 창) 연동 안내

> ## 📄 이 문서는 통합본으로 이동했습니다
>
> **→ [INTEGRATION.md](INTEGRATION.md#33-aianalysis) — 이벤트 억제 서브시스템 통합 연동 가이드**
>
> 여러 서브시스템을 함께 담당하는 개발자를 위해 팀별 문서 7종을 하나로 합쳤습니다.

- **AiAnalysis 담당 절**: [INTEGRATION.md §3.3](INTEGRATION.md#33-aianalysis)
- **공통 계약(전 팀 필독)**: [§2](INTEGRATION.md#2-공통-계약-전-팀-필독) —
  REST 엔드포인트 · 필드 사전 · 시간대 규약 · 장비 ID · 억제 판정 규칙 · 202 응답 ·
  **NATS `SYNC_EVENT_SUPPRESSION`** · **fail-safe 규범**
- **AiAnalysis 체크리스트**: [INTEGRATION.md §5](INTEGRATION.md#5-통합-체크리스트)

**AiAnalysis 요약**: 202 처리 · AI 탐지 발행 skip(Phase 2)

---

⚠ **이 파일은 더 이상 갱신하지 않습니다.** 내용이 통합본과 다르면 **INTEGRATION.md 가 우선**입니다.
사본 드리프트를 막기 위해 마스터는 하나만 유지합니다.
