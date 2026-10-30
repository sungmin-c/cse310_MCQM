# 예림 작업 지시서 — 10/30(금) ~ 11/1(일), Mac에서 하는 검증
> 작성: Sungmin (10/29). 이 문서만 읽고 시작할 수 있게 썼다. 예림의 Claude는 `YERIM_CLAUDE_GUIDE.md`의 규칙을 먼저 읽는다.
> 시간: 금요일 1시간, 주말 합쳐 최대 3시간. **시간이 모자라면 아래 "우선순위"의 위에서부터 자르지 말고 아래에서부터 자른다.**

## 왜 이 일을 하나
지금 Sungmin은 Windows 노트북에서 Google Meet 통화를 집중 수집한다(캡처·손실/대역폭/CPU 주입은 Windows 전용이라 Mac에서는 못 한다).
그동안 예림 쪽에서 **대시보드가 서버가 보내는 메시지(1초마다 오는 tick)를 제대로 받아 보여 주는지**, **작은 위젯(Chrome의 Picture-in-Picture 창)이 통화 창 위에 뜨는지**를 미리 확인해 두면, 수집이 끝나는 11/2 이후 바로 연결할 수 있다.
용어는 발표 때 쓴 말 그대로다: tick = 1초마다 오는 메시지 1개, 지표 4개 = 프레임레이트·비트레이트·프레임 지터·해상도, 원인 = 손실/대역폭/CPU.

## 이번에 하지 않는 것
- 실제 통화 데이터 수집, Clumsy, 모델 재학습 (Windows·Sungmin)
- Python 서버·테스트 코드 수정 (읽기·실행만)
- 대시보드 기능 추가. **검증하고 결과를 적는 것까지**다. 고치는 건 예림이 결과를 보고 따로 결정한다

## 우선순위 (위가 먼저)
| 순위 | 항목 | 예상 | 언제 |
|---|---|---|---|
| 1 | A0 환경 점검 | 15분 | 금 |
| 2 | A1 대시보드 위치·상태 | 20분 | 금 |
| 3 | A2 계약 검증 (더미 서버 + 예시 JSON) | 25분 | 금 |
| 4 | B1 위젯 PiP 스파이크 (T11) | 60–75분 | 주말 |
| 5 | 질문지 회신 | 10분 | 아무 때나, 늦어도 일요일 |
| 6 | B2 기기 밖 캡처 E7 (선택) | 최대 90분 | 주말, **Sungmin과 시간 맞출 때만** |

## 금요일 (10/30, 1시간)
### A0 환경 점검 (15분)
Claude가 실행하고 결과를 보고서에 적는다.
- [ ] repo 최신 상태: `git fetch --all` 후 `docs/handoff-after-t8b-merge`(또는 main에 병합됐으면 main)에서 새 브랜치 `web/yerim-verify` 생성. 이 문서가 보이는지 확인
- [ ] 버전 기록: macOS, Chrome(**Document PiP는 Chrome 116 이상**), `node -v`, `npm -v`, `uv --version`, `python3 --version`
- [ ] (E7을 할 때만) `tshark -v` 또는 Wireshark 설치 여부
- 막히면: 설치는 예림이 직접 결정한다. Claude는 설치 명령을 제안만 하고 실행하지 않는다.

### A1 대시보드 위치·상태 (20분)
- **현재 repo에는 `dashboard/` 폴더가 없다** (main과 모든 원격 브랜치 확인). 예림 대시보드 코드가 어디 있는지 [확인 필요].
  - [ ] 위치를 보고서에 적는다 (다른 repo / 로컬 폴더 / 아직 없음)
  - [ ] 있으면: `npm ci` → `npm test` 결과(통과/실패 수)를 그대로 적는다. 실행: `npm run dev` 후 어떤 화면이 있는지 한 줄씩
  - [ ] 없으면: "없음"이라고만 적고 A2는 "예시 JSON을 받을 화면이 없어 불가"로 기록. 새로 만들지 않는다 (새로 만들 일이면 Sungmin과 먼저 상의)

### A2 계약 검증 (25분)
계약 파일은 `docs/schema/sample.jsonl`(6줄)과 `docs/SCHEMA.md`다. 둘이 다르면 sample.jsonl이 우선.
- [ ] 더미 서버 실행(별도 터미널): `uv run server/dummy_stream.py` → `dummy stream: ws://localhost:8000/ws` 출력 확인
- [ ] 대시보드가 연결해서 지표 4개와 점수/판정 자리가 1초마다 갱신되는지 (스크린샷 1장)
- [ ] 서버를 껐다 켰을 때 재연결되는지, tick이 3초 이상 안 올 때 "수신 끊김"이 보이는지 (구현 안 됐으면 "미구현"이라고 적는다. 이건 질문지 5번과 같은 문제)
- [ ] `sample.jsonl` 6줄을 전부 `parseMessage`(또는 대응 함수)에 넣어 오류 없는지
- [ ] **제안 단계 필드(서버는 아직 안 보냄)**: `docs/design/schema_v1.2_proposal.md` §2의 예시 JSON(지표별 판정·CPU·원인·근거)과 `docs/design/recovery.md` §3의 `recovery` 예시를 임시 파일로 만들어 대시보드가 깨지지 않고 표시하는지. 못 하면 "화면 없음/미구현"이라고 적는다. 임시 파일은 repo에 넣지 않는다.

## 주말 (10/31–11/1, 합쳐 최대 3시간)
### B1 위젯 PiP 스파이크 = T11 (60–75분)
질문: 작은 위젯 창이 **Meet 통화 창 위에 계속 떠 있는가**. 이미 만들어 둔 대체 위젯 `scripts/widget_proxy.html`을 그대로 쓴다(수정 금지).
1. [ ] 서버(별도 터미널): `uv run server/dummy_stream.py --port 8001` (위젯은 8001 포트에 고정 연결)
2. [ ] Chrome에서 `scripts/widget_proxy.html`을 연다 (`file://`로 안 되면 `window.isSecureContext` 값을 기록하고, 폴더에서 `python3 -m http.server 8080`으로 연다)
3. [ ] [PiP 열기] → PiP 창이 뜨는지, 숫자가 1초마다 바뀌는지 (스크린샷)
4. [ ] 새 Meet 방 하나를 만들어 혼자 입장(meet.new). 카메라 켜기. 아래를 각각 ○/×로 기록:
   - PiP가 Meet 탭 위에 계속 보이는가
   - Meet를 **전체 화면**으로 바꿔도 보이는가
   - 다른 탭으로 옮기거나 다른 창을 클릭해도 유지되는가
   - PiP를 닫고 다시 열면 숫자가 이어지는가
   - PiP 창 크기를 줄이면 글자가 읽히는가
5. [ ] 이 결과는 **Mac Chrome 기준**이다. Windows 결과는 다를 수 있으므로 보고서에 "Windows 재확인 필요"라고 적는다 (Sungmin이 5분 확인).

### 질문지 회신 (10분)
Sungmin이 별도로 보낸 질문지(teammate_questions)에 A/B/C로 답해 `docs/reports/yerim/answers.md`에 그대로 붙인다. 모르면 "?".

### B2 기기 밖 캡처 E7 (선택, 최대 90분) — Sungmin과 같은 시간에 할 수 있을 때만
질문: 노트북 밖(Mac의 핫스팟 쪽)에서 같은 통화를 캡처해도 되는가. **예림은 캡처만 한다. 분석은 Sungmin(Windows)이 한다** (모델 파일이 Mac에 없다).
- [ ] 먼저 확인: Mac이 인터넷을 Wi-Fi가 아닌 다른 경로(유선, USB 연결)로 받을 수 있는가. macOS는 Wi-Fi 연결을 Wi-Fi로 다시 공유할 수 없다 [확인 필요]. 안 되면 여기서 끝, "불가"로 보고
- [ ] 가능하면: 시스템 설정의 인터넷 공유는 **예림이 직접** 켠다 (Claude는 시스템 설정을 바꾸지 않는다). 끝나면 반드시 끈다
- [ ] Sungmin 노트북이 그 핫스팟에 붙고, 둘이 같은 Meet 통화를 시작
- [ ] Wireshark/tshark로 공유 인터페이스(보통 `bridge100`)에서 **Sungmin 노트북의 UDP만** 캡처. 헤더 위주로 `-s 96` 사용. 예: `tshark -i bridge100 -s 96 -f "udp and host <노트북IP>" -w ~/mcqm_e7.pcap -a duration:120`
- [ ] 기록: 패킷 수, 파일 크기, 영상(UDP)이 보이는지. **pcap은 repo에 넣지 않는다**(이미 git 제외). Sungmin에게 따로 전달
- 내 트래픽과 Sungmin 트래픽만 캡처한다. 다른 기기의 트래픽이 섞이면 중단하고 보고.

## 끝났을 때
1. `docs/reports/yerim/REPORT_1030-1101.md`에 `YERIM_CLAUDE_GUIDE.md`의 양식으로 결과 정리
2. **예림이 직접** 보고서만 커밋하고 `web/yerim-verify` 브랜치로 push (main 병합·PR은 하지 않는다)
3. Sungmin에게 "보고서 올렸어" 한 줄. Sungmin은 읽고 PROGRESS에 반영한다

## 막혔을 때
- 20분 이상 막히면 멈추고 보고서에 "막힌 곳 / 해 본 것 / 필요한 것"을 적은 뒤 다음 항목으로 간다.
- 서버/Python 쪽 문제(예: `uv run`이 안 됨)는 고치려 하지 말고 오류 전문을 보고서에 붙인다.
