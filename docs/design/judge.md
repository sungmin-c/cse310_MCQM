# judge.py 설계 (T3, 2026-10-16, Claude) — 구현은 T3b(Codex)

## 역할
추정값(fps, bitrate, frameHeight, frame_jitter) 1초 행 → 지표별 등급 `good|fair|poor|unknown` + 종합. diagnosis(원인)와 별개: judge는 "품질이 어떤가", diagnosis는 "왜".

## 입출력 (SCHEMA v1.2 `judgement` 초안, 팀원 확인 대기)
```python
judge(est: dict, vca: str, state: JudgeState) -> dict
# est: {"fps": float, "bitrate": float(bps), "frameHeight": float, "frame_jitter": float(ms)} 일부 NaN/None 허용
# return: {"fps": "good", "bitrate": "fair", "frameHeight": "poor", "frame_jitter": "good",
#          "overall": "poor",            # 지표 중 최악. unknown은 제외 (전부 unknown이면 unknown)
#          "validated": bool}            # Meet=True 가능, Teams=정답 경로 확인 전 False, Zoom=False ("모델 추정값")
```
`JudgeState`: 지표별 최근 raw 등급 deque(maxlen=2) + 통화 초반 기준선. **상태는 호출자가 보관**(서버 세션당 1개), 함수는 순수에 가깝게.

## 규칙
1. **절대 기준(fps, frame_jitter)** — [가정] 값, W3 수집 후 보정:
   - fps: ≥24 good, 15–24 fair, <15 poor (Meet 공칭 30)
   - frame_jitter(ms): <30 good, 30–60 fair, ≥60 poor
2. **상대 기준(bitrate, frameHeight)** — P1에서 모델이 학습 범위 밖이라 bitrate 약 6배 과소, 높이 정확도 0%였다. 절대 임계값은 오판정을 만든다. 통화 시작 후 `base_len`초(정상 구간 중앙값)를 기준선으로 삼아 비율로 판정: ≥0.8 good, 0.5–0.8 fair, <0.5 poor. 기준선이 없으면 `unknown`. 재학습 후 절대 기준으로 교체 검토.
3. **히스테리시스**: 등급이 바뀌려면 같은 새 등급이 연속 2틱 (경계 깜빡임 억제). 악화는 즉시, 회복은 2틱 [가정].
4. **경계**: 임계값 값 자체는 위쪽 등급 (fps=24 → good).
5. NaN/None/음수 → `unknown` (예외 던지지 않음). `validated=False`면 overall 옆에 UI가 "추정" 표기.

## 테스트 표 (tests/test_judge.py)
| 케이스 | 기대 |
|---|---|
| fps 30/24/23.9/15/14.9/0 | good/good/fair/fair/poor/poor |
| **단조성**: fps 내림차순 스윕에서 등급이 한 번도 좋아지지 않음 (jitter는 오름차순 스윕에서 안 좋아짐) | 위반 0 |
| 히스테리시스: good→poor 1틱 튐 후 복귀 | 악화 즉시 반영, 회복은 2틱 뒤 |
| 기준선 없음 + bitrate 입력 | bitrate=unknown, overall은 나머지로 |
| 모든 입력 NaN | overall=unknown, 예외 없음 |
| vca="zoom" | validated=False |
| 합성 스트림(`server/dummy_stream.py`) 재생 | SCHEMA 계약 테스트 통과 |

## 열린 질문 (사용자)
- 임계값 근거: ITU-T G.1070 등 표준을 쓸지, 우리 수집 데이터 분위수로 정할지. 권장: W3 전 [가정]값으로 시작, 수집 후 분위수로 보정하고 발표에 "표준 대비" 한 줄 추가.
