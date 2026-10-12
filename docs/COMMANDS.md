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

## 개발 서버
| 목적 | 명령 | 확인 |
|---|---|---|
| 더미 스트림 (SCHEMA v1) | `uv run server/dummy_stream.py` (`--app kakao_voice --mode whatif` 등) | 터미널에 `dummy stream: ws://localhost:8000/ws` 출력 |
| 대시보드 | `npm --prefix dashboard run dev` | 브라우저에서 Vite 주소 열기 |
