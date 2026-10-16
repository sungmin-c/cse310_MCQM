# T8b — diagnosis v1 구현 (설계: docs/design/diagnosis_v1.md)
단계별로 커밋한다. **1단계는 W3(10/27) 전 필수**라 가장 먼저 한다.

## 1단계 — `call_core_pct` (브랜치 `ml/t8b-diag-v1`, `ml/t1-tshark-live` 위에서 분기)
1. `capture/tshark_live.py`에 순수 함수 `core_util(percpu, cores)` 추가: `percpu` 리스트 중 `cores`(int 집합) 위치 값의 평균. `cores`가 비었거나 None이면 전체 평균.
2. `OsSampler`: 매 초 통화 프로세스(`CALL_PROCS`)의 `cpu_affinity()` 합집합을 구하고(`psutil.Error`면 그 프로세스 건너뜀) `psutil.cpu_percent(None, percpu=True)`와 함께 `core_util`로 계산. os.csv **마지막 열**에 `call_core_pct` 추가(소수 1자리). 시작 시 percpu도 한 번 미리 호출(첫 값 0 방지, 기존 `cpu_percent(None)`처럼).
3. os.csv를 읽는 곳(`scripts/overhead_ab.py`, `scripts/pilot_live.py compare` 등)이 열 이름으로 읽어 안 깨지는지 확인. 위치로 읽는 곳이 있으면 이름으로 바꾼다.
4. 테스트(`tests/test_tshark_live.py`): `core_util([100,100,10,10], {0,1}) == 100`, `core_util([100,100,10,10], None) == 55`, 빈 집합 → 55. psutil 없이 통과.
5. `uv run --no-sync pytest tests/ -q` 전체 통과(기준 39 passed + 1 skipped 이상).

## 2단계 — `Diagnoser` v1 + `scripts/diag_eval.py` (같은 브랜치, T4와 무관)
- 설계 문서 "규칙" 0·4, `update(..., device=None, flow=None)`, `CAUSES`에 `device_cpu`, `last_signals["call_core_pct"]`. 테스트 표 전부 추가, **기존 diagnosis 테스트 13개는 수정 없이 통과**.
- `scripts/diag_eval.py`: 설계 문서 "평가" 절. W3 자료가 없으니 합성 CSV로 실행만 확인하는 테스트 1개.

## 3단계 — T4 tick 연결 (T4 커밋·PASS 뒤, `ml/t4-ws` 위)
- **작업 위치 (10/16 밤 준비 완료)**: `..\mcqm-wt-T8b`, 브랜치 `ml/t8b-diag-v1` HEAD `2dd55ea` = ①② + T4(`431faef`). 새 브랜치 만들지 않는다.
- Codex 샌드박스는 git 쓰기·Python 실행이 막혀 있다 → **파일 수정만** 하고 `data/ai_runs/codex_notes.md`에 `[T8b] ③ 완료: <바꾼 파일>` 한 줄. pytest·커밋·push는 Claude 리뷰 루프가 한다.
- 대상: `server/app.py`의 `build_tick`(현재 `diagnoser.update(w, seq_loss=None)`), Replay `--os` 파싱, Live `sample_os`. 흐름 키는 `process_lines`가 원본 필드를 넘기지 않으니 창별 `(ip.src, udp.srcport)` 바이트 집계를 추가해야 한다(`scripts/diag_eval.py:run_call`의 방식과 같게, 경계 패킷은 다음 창).
- 창마다 수신 영상 패킷의 `(ip.src, udp.srcport)` 바이트 합 최대를 `flow`로, 2초 이내 최근 OS 샘플을 `device`로 `Diagnoser.update`에 넘긴다. Replay는 `--os` CSV(열이 없으면 `device=None`).
- Live는 T4 `server/app.py`가 psutil을 따로 계산한다(10/16 미커밋 기준 `:237` 근처) → 거기서도 1단계 `core_util`을 재사용해 `device.call_core_pct`를 채운다. 계산을 새로 짜지 않는다.
- (1단계 확인 결과, Claude 10/16) os.csv를 위치로 읽는 코드는 없다. T4 Replay도 `csv.DictReader`라 마지막 열 추가는 안전.

완료 기준 = 단계별 테스트 통과 + 새 의존성 없음 + dashboard/·vcaml/ 변경 없음. 보고에 실측(실제 psutil affinity 값, 2코어 고정 시 ≥ 85 근처인지)은 "미확인"으로 적는다 — W3 S0-4에서 사용자가 확인.
