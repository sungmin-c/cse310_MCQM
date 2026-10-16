# COMMANDS — 실행 명령 모음 (OS 중립)

모든 명령은 **팀 repo 루트에서** 실행한다 (`vcaml/config.yaml`의 `data_root: data`가 실행 위치 기준이다).

## 처음 받았을 때
| 목적 | 명령 | 누가 |
|---|---|---|
| repo 받기 (vcaml 포함) | `git clone --recurse-submodules <repo-url>` | 둘 다 |
| 이미 받은 repo에 vcaml 채우기 | `git submodule update --init` | ML |
| Python 환경 | `uv sync` | ML (Web은 불필요) |
| 대시보드 의존성 | `npm --prefix dashboard ci` | Web |

## vcaml Makefile → uv 번역 (Windows에는 make가 없다)
| Makefile | 우리 명령 |
|---|---|
| `make install` | `uv sync` |
| `make download-data` | 사용 안 함. 데이터는 솔로 자료 junction으로 재사용 (`CLAUDE.local.md`) |
| `make train` | `uv run python vcaml/train.py --dataset data/in_lab_data` |
| `make train-rw` | `uv run python vcaml/train.py --dataset data/real_world_data` |
| `make train ARGS='...'` | `uv run python vcaml/train.py --dataset data/in_lab_data --metrics framesReceivedPerSecond --methods ip-udp-ml` |
| `make mlflow-ui` | `uv run mlflow ui --backend-store-uri sqlite:///data/mlruns.db --port 5000` |

학습 주의: 16GB RAM에서는 Chrome 등을 닫고, 절전을 끈 상태에서 조합(metric × method)별로 나눠 실행한다 (솔로 RUN_GUIDE 4-3 참고).

## 테스트
| 대상 | 명령 |
|---|---|
| 우리 Python 테스트 (계약 포함) | `uv run pytest` |
| vcaml 원본 테스트 | `uv run pytest vcaml/tests` |
| 대시보드 | `npm --prefix dashboard test` |

## 실험·측정 스크립트 (in-lab 데이터 필요)
| 목적 | 명령 | 결과 위치 |
|---|---|---|
| 실시간 캡처 (기존 CLI 유지, 구현·서버 import: `capture.tshark_live`) | `uv run --with psutil python scripts/pilot_live.py capture --name p1_meet1 --iface Wi-Fi --duration 200` (`--no-os`면 `--with psutil` 생략 가능) | `data/pilot/<name>_{pkts,est,os}.csv` (`--no-os`면 os 제외) |
| 모니터 on/off 비교 | `uv run --with psutil python scripts/overhead_ab.py --name p3_meet1 --dst <노트북IP>` | `data/pilot/<name>_os.csv`, `_phase.csv`, `_onK_*.csv` |
| CPU 부하 (캡처와 별도 실행) | `uv run python scripts/cpu_load.py --name p2_meet1 --levels 0,50,80,100 --step 60` | `data/pilot/<name>_load.csv` |
| 원인 진단 합성 실험 (IP/UDP만) | `uv run python scripts/diag_synth.py --vca meet --split test` | `data/diag/summary_*.json`, `windows_*.csv` |
| 원인 진단 합성 실험 (RTP 순번 포함) | 위 명령 + `--rtp` | 같은 곳 (`_rtp` 접미사) |
| 진단 규칙 조정용 (dev 세트) | `--split dev` | test 결과는 조정에 쓰지 않는다 |
| 1 tick 처리 시간 (지표 4개 + 진단 + What-if) | `uv run --with psutil python scripts/bench_tick.py --calls 10` | `data/bench/bench_tick.json` |

`bench_tick.py`는 `data/models/meet_{fps,bitrate,frame_jitter,frameHeight}_cv1.pkl`이 필요하다 (솔로 MLflow fold-1 모델 복사본, 경로는 `CLAUDE.local.md`). `psutil`은 메모리 측정용 임시 의존성이다(`--with`, 프로젝트에 추가 안 함).

## 개발 서버
| 목적 | 명령 | 확인 |
|---|---|---|
| 더미 스트림 (SCHEMA v1) | `uv run server/dummy_stream.py` (`--app kakao_voice --mode whatif` 등) | 터미널에 `dummy stream: ws://localhost:8000/ws` 출력 |
| 대시보드 | `npm --prefix dashboard run dev` | 브라우저에서 Vite 주소 열기 |
