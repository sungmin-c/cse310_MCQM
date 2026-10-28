# T8b 구현 인계 (2026-10-16, Codex)

상태: **1·2단계 구현 사본과 패치 준비, 원본 브랜치에는 미적용. 테스트 실행 미확인.**

## T4 확인
- `mcqm-wt-T4` HEAD `1ed0fd9`는 T3b 병합이다. T4 구현은 미커밋 상태이며 `31243bf`도 포함되지 않았다.
- `data/ai_runs/claude_review_state.txt`의 `T4=`는 비어 있고 PASS 기록이 없다. T4 기록은 pytest 시작 전 Python 접근 거부를 명시한다.
- 따라서 브리프의 3단계(T4 tick 연결)는 선행 조건 미충족으로 대기한다. T4 파일은 수정하지 않았다.

## 준비된 변경
- 기준: `ml/t1-tshark-live`의 `31243bf`. 작업 사본: `data/ai_runs/T8b-work/`.
- `data/ai_runs/T8b_01.patch`: `core_util`, 통화 프로세스 affinity 합집합의 CPU 사용률, percpu priming, OS CSV 마지막 `call_core_pct` 열. `_group_cpu()` 호출 형태 유지.
- `data/ai_runs/T8b_02.patch`: `Diagnoser(device, flow)`, CPU 규칙, 2창 연속 흐름 전환 시 재수집, `diag_eval.py`, 회귀 테스트.
- 기존 diagnosis 테스트 13개는 그대로 두었다. 합성 CPU 통화의 dev/test 분리, OS 샘플의 과거 방향 2초 정렬, packet-only 절제 실험, dump의 보조정답을 검증하는 테스트도 추가했다.
- CPU 투표가 남아도 현재 OS 값이 없으면 `device_cpu`를 출력하지 않는다. 흐름 전환 후 재수집 창도 시간 라벨이 있으면 평가 분모에 넣는다.
- `overhead_ab.py`는 수집기를 직접 import하며 OS CSV 위치 인덱스를 사용하지 않는다. `pilot_live.py compare`는 OS CSV를 읽지 않는다. 새 열 때문에 바꿀 호출자는 없었다.

## 검증 결과와 제약
- 두 패치 각각 T1 worktree에서 `git apply --check` 통과. 이는 패치 적용 가능성 확인이며 실행 테스트가 아니다.
- 새 브랜치 생성은 `.git/refs/heads/ml/t8b-diag-v1.lock: Permission denied`로 실패했다. commit·push·PR은 하지 못했다.
- `uv run --no-sync python -m pytest ...`는 수집 시작 전에 실패했다. 기본 uv cache도 접근 불가여서 repo의 cache로 바꿨지만, 공유 `.venv`의 원본 Python(`AppData/Local/Programs/Python/Python313/python.exe`) 실행이 접근 거부된다. Python trampoline을 검사할 수 없다는 메시지가 나온다. 환경 재설치·의존성 변경은 하지 않았다.
- 기존 13개 테스트, 신규 테스트, 전체 회귀 모두 실행 결과 **미확인**. 실제 affinity·2코어 고정 시 ≥85 여부·W3 성능도 **미확인**.

## 사용자 권한 세션에서 재개
repo 루트 PowerShell에서 실행한다. 기존 브랜치가 생겼다면 새로 만들지 않고 해당 브랜치를 사용한다.

```powershell
$repoRoot = (Get-Location).Path
git -C ..\mcqm-wt-T1 switch -c ml/t8b-diag-v1
if ($LASTEXITCODE -ne 0) { throw '브랜치 생성 실패: 상태 확인 후 재개' }
git -C ..\mcqm-wt-T1 apply "$repoRoot/data/ai_runs/T8b_01.patch"
if ($LASTEXITCODE -ne 0) { throw '1단계 패치 적용 실패' }
$env:UV_PROJECT_ENVIRONMENT = "$repoRoot/.venv"
Push-Location ..\mcqm-wt-T1
uv run --no-sync pytest tests/ -q
if ($LASTEXITCODE -ne 0) { Pop-Location; throw '1단계 테스트 실패' }
# 통과 후
git add capture/tshark_live.py tests/test_tshark_live.py
git commit -m "feat(capture): sample CPU utilization on call affinity cores"
if ($LASTEXITCODE -ne 0) { Pop-Location; throw '1단계 커밋 실패' }
Pop-Location
git -C ..\mcqm-wt-T1 apply "$repoRoot/data/ai_runs/T8b_02.patch"
if ($LASTEXITCODE -ne 0) { throw '2단계 패치 적용 실패' }
Push-Location ..\mcqm-wt-T1
uv run --no-sync pytest tests/ -q
if ($LASTEXITCODE -ne 0) { Pop-Location; throw '2단계 테스트 실패' }
# 통과 후
git add server/diagnosis.py scripts/diag_eval.py tests/test_diagnosis.py tests/test_diag_eval.py
git commit -m "feat(diagnosis): add device CPU rules and W3 evaluation"
Pop-Location
```

각 pytest가 실패하면 뒤의 commit 명령을 실행하지 않고 수정한다. 통과 후 Claude 리뷰를 받는다. 패치·사본은 git 제외 경로에 있으므로 검토·적용 전 보존한다.

W3 자료가 생긴 뒤, 적용한 worktree 루트에서:

```powershell
uv run --no-sync python scripts/diag_eval.py --split test
uv run --no-sync python scripts/diag_eval.py --split test --no-device
```

기본 입력은 `data/w3/log.csv`, `data/pilot/w3_<id>_{pkts,os}.csv`, 선택적 `data/w3/w3_<id>_dump.json`이다. `--log`, `--packets-dir`, `--dump-dir`, `--out`, `--dst`로 바꿀 수 있다. 상태 `ok`·`no_truth`만 조건별 ID 순 교대 분리하며 기본은 test다. 과거 OS CSV에 `call_core_pct`가 없으면 CPU 판정을 하지 않는다. 출력은 클래스별 P/R, confusion matrix(기존 cause도 열로 유지), 정상 오탐률, 검출 통화 수와 검출된 통화의 지연 중앙값, 효과가 관측된 CPU 창의 재현율 및 창별 CSV다. dump가 없거나 관련 통계가 없으면 보조정답은 평가 불가로 남긴다.

## 3단계 후속 지점
T4 커밋·Claude PASS 후 T8b를 통합한다. `server/app.py`의 `build_tick`에 device·flow를 전달하고 Live OS 수집 및 Replay `--os` 파싱에 새 열을 연결한다. 기존 2초 freshness 처리는 재사용한다. 현재 T4 `process_lines(feature_emit=...)`에는 원본 송신 IP·포트 전달이 없어 영상 패킷 창별 바이트 합계와 RTP 순번 집계를 경계 패킷보다 먼저 emit하도록 연결해야 한다. `--enable-heuristic rtp_udp`가 T4 자체 Live 명령에도 들어가는지 확인한다. v1.2 계약은 아직 팀원 승인 전이므로 확정하지 않는다.
