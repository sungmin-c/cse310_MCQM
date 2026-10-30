# MCQM — Project Overview (for another AI) — as of 2026-10-25

> Purpose: one file that tells the whole story so far, in the order of our proposal talk.
> Sources: `docs/PROJECT_SPEC.md` (v7), `docs/PROGRESS.md`, `docs/PROJECT_LOG.md`, `docs/HANDOFF.md`, `docs/MEETING_1022.md`, `docs/design/*`, `docs/SCHEMA.md`.
> Tags: **[confirmed]** measured/run · **[assumed]** not yet verified · **[planned]**. Never present [assumed] as fact.

## 0. Basics
- **MCQM = Multi-layer Call Quality Monitor.** CSE310 Final Project (SUNY Korea), 2-person team.
- Core question: *"On a Windows desktop, using only packet headers and OS metrics (no app internals), how accurately can we estimate video-call quality in real time, tell whether a drop is caused by the network or the device (CPU), and confirm quality recovered after a suggested action?"*
- Team: **Sungmin** (Windows) — Python/ML backend, capture, diagnosis, experiments. **Teammate** (Mac) — React dashboard + mini widget; does not work on Python/ML.
- Dates: Proposal talk 2026-10-26 (5–10 min) · feature freeze **11/24** · **Final demo 12/2** (~12 min) · report ~12/12 [assumed].
- Hardware: Windows 11 laptop (Core Ultra 5 125H, 16 GB RAM, low free memory) = receiving side; call partner = Sungmin's Galaxy S20.

## 1. Solo project: vcaml in one minute
- **vcaml** (noise-lab, IMC 2023): estimates WebRTC video quality **without decrypting** — only IP/UDP header info (packet size, inter-arrival time) per 1-second window → features (LSTATS/TSTATS) → **Random Forest** → fps, bitrate, frame jitter, resolution (frameHeight).
- Two input modes: `ip-udp-ml` (headers only, our main) and `rtp-ml` (adds RTP headers). Apps: Meet, Teams, Webex. Ground truth: Chrome `webrtc-internals`.
- Paper: ~1.50 fps MAE. **Our reproduction [confirmed]:** Meet 1.334 / Teams 1.812 / Webex 1.328 (avg 1.491); 50 vcaml tests pass.
- Limits: offline batch (after the call), trained on Linux Chrome + emulated network conditions, quality only (no cause), no user-facing tool. The paper itself failed in-lab → real-world transfer (Meet FPS MAE 12.41, Table 5).
- The solo repo is read-only; the team repo uses fork `sungmin-c/vcaml` (branch `mcqm`) as a submodule. Upstream has no LICENSE → no code copying.

## 2. Existing industry solutions and their limits (doc review only, 2026-10-25)
| | In-call, for users | For IT admins |
|---|---|---|
| Google Meet | "Troubleshooting & help" panel: CPU load, network stability, suggested actions, feedback on their effect | Meet Quality Tool (jitter, loss, RTT, CPU; 30-day history) |
| Microsoft Teams | Call health panel (RTT, loss, bitrate…; refresh every 15 s) | Call Quality Dashboard (Good/Poor classes), Real-Time Analytics for in-progress meetings (automatic with Teams Premium) |
| Zoom | Statistics window (we used it in pilot P4: fps, resolution, latency, jitter, loss; no export) | Zoom Dashboard (MOS 1–5, alerts incl. CPU) |
| Webex | not reviewed | Control Hub + ThousandEyes (network path, Webex desktop app only) |

Limits (our framing — **not** "nobody does this"):
1. **Inside one app only** — each uses the vendor's internal data; no common monitor across apps.
2. **Different in every app** — raw numbers vs. hints; deeper views need admin rights, sometimes licenses.
3. **Accuracy can't be checked from outside** — we found no published hit rate for cause hints in the docs we reviewed; nothing independent confirms recovery after the user acts.
- → Research question: can this be done **from outside the app, for any app**, and **how accurately**?
- Be honest: Meet already shows CPU load and suggests actions to users. We did not test these products (documentation review only). Sources: `SCRIPT_ChatGPT.md` → "출처".

## 3. What vcaml makes possible
- A monitor **outside the app**, on the user's own laptop, with **no vendor cooperation** and **no decryption** (own traffic, headers only).
- Per-second numbers for any app sending UDP video.
- Cheap: 4 models + diagnosis, p95 **36 ms** per tick on in-lab data [confirmed]; p95 126 ms on a real call on battery [confirmed] — both within a 1-second budget.
- → The missing piece for an **app-independent, real-time** monitor that does not depend on vendor data.
- Dashboard/widget status: not yet in the repo (`dashboard/` does not exist as of 10/25); teammate's progress unconfirmed → say "being built, not yet connected".

## 4. Our project: from outside the app, for any app, with measured accuracy
vcaml says *how good*; MCQM adds *why* and *did it recover*. Priorities:
- **P0** Real-time pipeline (tshark → 1-s window → RF) + accuracy vs. ground truth + **retraining** (Meet)
- **P0** Cause diagnosis `none | loss | bandwidth | device_cpu` + evidence + confidence, combining packets with **OS metrics**
- **P1** **Action suggestion + recovery verification** (guidance only; user acts; no auto-repair)
- **P1** React dashboard + **mini widget** (same dashboard in Chrome Document Picture-in-Picture, always on top)
- **P1** Teams (Chrome web client) · **P2** Zoom, overhead repeats, Android 4-layer design doc (no implementation) · **P3** What-if sliders
- Out of scope: mobile accuracy claims, Kakao, Flutter overlay dev, hotspot capture, 0–100 MOS score, auto-repair, fixed-delay diagnosis, Teams/Zoom desktop-app ground truth.

### How we got here (direction history)
- **v5 (10/13) mobile-first:** PCAPdroid streaming worked (~100% delivery), Flutter overlay on S20 worked, but **Clumsy cannot impair hotspot-forwarded phone traffic** (WinDivert NETWORK layer sees only the laptop's own packets) → no controlled impairment on phone traffic.
- **v6 (10/14, professor meeting):** desktop (Windows) first; 12/2 = desktop MVP; Android = design only; web dashboard, no native app. Mobile work archived (`overlay/`, branch `ml/overlay-spike`).
- **v7 (10/22):** order **Meet → Teams (web) → Zoom**, calls 30/15/15; added action + recovery check and the PiP mini widget.

## 5. Current plan and pilot results
### System
```
Meet/Teams (Chrome) or Zoom desktop  ← partner: S20
 → tshark (headers only, own laptop) → server/features.py (vcaml FeatureExtractor, 1-s windows; identical to batch, rtol 1e-9)
 → RF estimator (→ retrained after W3) → judge.py (good/fair/poor per metric)
 + psutil 1 Hz (CPU%, call-process CPU, call_core_pct, mem%)
 → diagnosis.py v1 → action text + recovery decision
 → FastAPI WebSocket (ws://localhost:8000/ws, 1 tick/s) → React dashboard + PiP widget
```
- Modes: Live, Replay (demo fallback), What-if (P3). Contract: `docs/SCHEMA.md` + `docs/schema/sample.jsonl`; v1.2 (judgement, device, `device_cpu`) awaits teammate approval.
- Judge [assumed thresholds]: fps ≥24 good / 15–24 fair / <15 poor; jitter <30 / 30–60 / ≥60 ms; bitrate & height relative to call baseline (≥0.8 / 0.5–0.8 / <0.5); hysteresis (worsen now, recover after 2 ticks).
- Diagnosis v1 rule order: flow-switch → rebuild baseline; bandwidth; RTP loss (seq_loss ≥ 1.5%); jitter; **device_cpu if call_core_pct ≥ 85% [assumed]**; IP/UDP loss rule; none. `device=None` disables device_cpu → the "packets only vs. packets+OS" ablation is one switch.
- `call_core_pct` = mean utilization of the cores the call process may use (affinity); needed because with Chrome pinned to 2 cores, total CPU looked like only 23%.
- Code status [confirmed]: tshark capture, judge, WS server, diagnosis v1 merged to main (PR #9), pytest 197 passed. Live path on real calls not yet verified.

### Pilots (W1, 10/15, **one call each** — direction checks)
| Pilot | Result | Meaning |
|---|---|---|
| P1 accuracy (Meet, 196 s) | fps MAE **9.09** (lab 1.33); bitrate 331 vs 1932 kbps (~6× low); height 0% correct | Capture is fine (packet bitrate 2111 kbps ≈ truth); model out of range (training median 125 kbps, height 180–360 vs ours 1.9 Mbps, 1280). Same as paper's 12.41 → **retrain** |
| P2 CPU (Chrome pinned to 2 cores) | Packets & received fps normal (27.7–29.7), but **36 freezes**, decode 6.6 → 57 ms (~9×), sent fps 16.5 → 3.5; `qualityLimitationReason` stayed `none` | **Packets can't see device problems** → need OS metrics; device truth = freeze/decode time/sent fps. Core pinning works better than busy loops |
| P3 overhead (on/off ×3) | Monitor **~1.3% CPU**, no call-metric difference | Monitor is light |
| P4 Zoom | Server-relayed UDP (~1.9 Mbps); stats window has fps but no export | Zoom truth = approximate; Meet model also off on Zoom |
- Synthetic diagnosis test (in-lab traces with software-injected impairments, v0.1): bandwidth recall 0.95–1.00; loss 0.56–0.94 with RTP sequence numbers but 0.03–0.18 with IP/UDP only; normal false alarms 1–4%; fixed delay is invisible on the receive side (97% "none").
- Fix found: tshark lost RTP decoding on P2P ports > 49152 → added `--enable-heuristic rtp_udp` (verification pending, S0-3).

### Schedule
| Week | Plan |
|---|---|
| W2 10/20–26 | ✅ code merged. Open: W3 pre-checks S0, Teams pilot (T9), widget PiP spike (T11, teammate), action/recovery design (T10), proposal talk |
| W3 10/27–11/2 | Meet ~30 calls (N0 none, L3/L10 loss, B1000/B300 bandwidth, C2/C2L CPU), retraining starts |
| W4 11/3–9 | Teams ~15 calls, recovery logic, widget shows action/recovery |
| W5 11/10–16 | Zoom ~15 calls, evaluation tables |
| W6 11/17–23 | Android design doc, README, static demo + recording; **freeze 11/24** |
| W7 11/24–12/1 | 2 rehearsals (Replay fallback); **demo 12/2** |
- One call = 380 s: warm 0–150, baseline 150–210, **impair 210–300**, recovery 300–380. Injected condition = label; removing it = the experimental "action".
- Tools: Clumsy (drop), clumsy2 (bandwidth, not yet verified), `scripts/cpu_load.py --pin 2` (CPU).

## 6. Final demo: content and goal
- **Live demo:** normal call → inject loss or CPU limit → widget shows **cause + confidence + action** → problem removed → **"Recovered"**. Fallback: Replay + recording.
- **Results to show:** fps/bitrate error before vs. after retraining; diagnosis precision/recall + confusion matrix with vs. without OS metrics; recovery-detection delay and false "recovered" rate; monitor overhead; Android 4-layer design summary.
- **Success =** retraining shrinks the Windows gap (or we explain why not, as a negative result); OS metrics clearly lift `device_cpu` recall over packets-only; recovery detected within seconds with few false positives.
- Final talk (~12 min): problem 2 → method 2 → **live demo 5** → results 2 → limits 1.

## Rules and open items
- Rules: don't state unverified things as fact; no ground truth → `validated: false` ("model estimate"); diagnosis is an estimate with confidence; capture own laptop traffic only; actions are guidance only; recovery evaluation measures *detection speed/accuracy*, not real-world advice effectiveness.
- Unverified: Teams web ground truth; PiP over full-screen call; whether Clumsy drops are visible to tshark (S0-1 — biggest risk); clumsy2; retrained accuracy; recovery N/T seconds (T10); SCHEMA v1.2 teammate approval.
- Limits: small sample, one phone partner, artificial impairments, Linux→Windows transfer, action = removing injection.

## Key files
`docs/PROJECT_SPEC.md` (spec v7) · `docs/PROGRESS.md` (results, decisions Q1–Q23) · `docs/PROJECT_LOG.md` (history) · `docs/HANDOFF.md` (who does what) · `docs/design/{judge,diagnosis_v1,ws_protocol,w3_collection,schema_v1.2_proposal}.md` · `docs/SCHEMA.md` · `docs/COMMANDS.md` · `docs/proposal/PROPOSAL_DECK.md`
