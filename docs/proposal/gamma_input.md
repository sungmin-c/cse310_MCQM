# MCQM: Is It the Network or My Laptop?
Real-time video call quality monitoring from packet headers

CSE310 Final Project Proposal
Sungmin Choo · [Teammate name]

---

# The Problem
- Video calls (Meet, Teams, Zoom) are **encrypted** — we cannot read their contents
- When a call stutters, users cannot tell **why**
  - Is it the **network** (packet loss, low bandwidth)?
  - Or the **device** (laptop CPU overloaded)?
- Each app keeps its quality statistics to itself — there is no app-independent view, and no hint on what to fix

**Goal:** estimate call quality from outside the app, find the cause, and check whether the fix worked

---

# Starting Point: vcaml (IMC 2023)
- Looks only at **packet size and arrival timing** (IP/UDP headers), never the encrypted content
- Per 1-second window → statistics → **Random Forest** →
  - frame rate (fps) · bitrate · frame jitter · resolution
- Original results: about **1.5 fps** average error on Meet, Teams, Webex
- **We reproduced it:** 1.49 fps error (paper: 1.50)

**Limits:** offline (after the call), lab data from Linux, no cause, no user-facing tool

---

# What We Add on Top of vcaml
1. **Real-time** — estimate every 1 second during the call, not after it
2. **Real-world accuracy** — measure how well it works on real Windows calls, then **retrain** to improve
3. **Cause diagnosis** — network (loss, bandwidth) vs. device (CPU)
4. **Action + recovery check** — suggest a fix, then verify whether quality recovered
5. **Dashboard + mini widget** — live charts and an always-on-top mini window during the call

---

# Pilot Results: Why This Matters
(one pilot call each — direction check, not final results)

| Pilot | Finding |
|---|---|
| Original model on a real Windows Meet call | fps error **9.09** (vs. 1.33 in the lab) → **retraining needed** |
| Laptop CPU limited to 2 cores | Packets looked normal, but **36 freezes** and **~9× decode time** → packets alone **cannot see** device problems |
| Monitor overhead | about **1.3% CPU**, no change in call quality |

---

# System Overview
Video call (Meet / Teams / Zoom) on the Windows laptop
→ **tshark** captures packet headers
→ 1-second features → **Random Forest** (fps, bitrate, jitter, resolution)
→ **Quality judge** (good / fair / poor per metric)
→ **Cause diagnosis** using packets + OS metrics (CPU)
→ **Suggested action** → **Recovery check**
→ WebSocket → **Web dashboard** + **Mini widget** (Picture-in-Picture)

All processing runs locally on our own laptop and only captures our own traffic.

---

# Evaluation Plan
**Apps, in order:** Google Meet (~30 calls) → Microsoft Teams web (~15) → Zoom (~15)

**Ground truth:** Chrome WebRTC statistics (Meet, Teams) · Zoom statistics window (approximate)

**Controlled problems we inject:** packet loss · bandwidth limit · CPU limit

| Question | Metric |
|---|---|
| How accurate is the estimate? | fps / bitrate error, before vs. after retraining |
| Can we find the cause? | precision / recall, with vs. without OS metrics |
| Do we detect recovery? | seconds to detect recovery, false "recovered" rate |
| Is the monitor lightweight? | CPU usage, call quality with monitor on vs. off |

---

# Timeline & Roles
| When | Milestone |
|---|---|
| Oct (done) | Reproduced vcaml, real-time pipeline, pilots |
| Late Oct | Teams pilot, widget prototype, Meet data collection |
| Early Nov | Teams + Zoom collection, retraining, recovery check |
| Mid Nov | Evaluation, Android design note |
| Nov 24 | Feature freeze |
| **Dec 2** | **Final demo** |

**Sungmin:** capture, ML, diagnosis, experiments · **[Teammate]:** web dashboard, mini widget

---

# Risks & Honest Limits
| Risk | Backup plan |
|---|---|
| Model stays inaccurate after retraining | Report the gap itself as a finding (same as the vcaml paper's real-world drop) |
| Teams web ground truth not available | Use approximate ground truth, label results "estimate only" |
| Live demo fails | Replay recorded calls |

**Limits:** small sample (one phone as call partner), injected problems are artificial, the "fix" in experiments = removing the injected problem

---

# Summary
- vcaml showed call quality can be read from **encrypted packets**
- We make it **real-time**, measure it on **real Windows calls**, and go further:
  **find the cause → suggest a fix → confirm recovery**
- Final demo: a live call degrades, the widget names the cause, we fix it, the widget shows **"Recovered"**

Thank you — questions welcome
