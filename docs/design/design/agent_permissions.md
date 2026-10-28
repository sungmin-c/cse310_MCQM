# 에이전트 권한 설정 (사용자가 직접 적용 — 에이전트가 자기 권한을 못 바꾸게 막혀 있다)

원인: 전역 `defaultMode: "auto"`의 분류기가 worktree commit·push·git 조회를 막는다. 아래 allow 규칙이 있으면 분류기를 거치지 않는다. deny가 항상 우선한다.

## 1. Claude Code — `.claude/settings.local.json` (git 제외 파일. 내용을 통째로 교체)
```json
{
  "env": { "ENABLE_TOOL_SEARCH": "true" },
  "permissions": {
    "allow": [
      "Bash(git *)", "PowerShell(git *)",
      "Bash(gh pr create*)", "Bash(gh pr view*)", "Bash(gh pr list*)", "Bash(gh pr diff*)",
      "PowerShell(gh pr create*)", "PowerShell(gh pr view*)", "PowerShell(gh pr list*)", "PowerShell(gh pr diff*)",
      "Bash(uv run *)", "PowerShell(uv run *)",
      "PowerShell(pwsh *scripts/ai_loop.ps1*)",
      "Read(../mcqm-wt-*/**)", "Edit(../mcqm-wt-*/**)", "Write(../mcqm-wt-*/**)"
    ],
    "deny": [
      "Bash(git push --force*)", "Bash(git push -f*)", "Bash(git reset --hard*)", "Bash(git clean*)", "Bash(git branch -D*)",
      "PowerShell(git push --force*)", "PowerShell(git push -f*)", "PowerShell(git reset --hard*)", "PowerShell(git clean*)", "PowerShell(git branch -D*)",
      "Bash(gh pr merge*)", "PowerShell(gh pr merge*)",
      "Bash(rm *)", "PowerShell(Remove-Item*)",
      "Edit(dashboard/**)", "Edit(vcaml/**)", "Edit(data/in_lab_data/**)", "Edit(data/real_world_data/**)"
    ]
  }
}
```
되돌리기: 파일에서 `permissions` 블록을 지운다.

## 2. Codex — `.codex/config.toml` (git 제외, 통째로 교체)
```toml
approval_policy = "never"          # 승인 요청으로 멈추지 않음 (막히면 실패로 처리)
sandbox_mode = "workspace-write"   # repo 루트 + 아래 writable_roots 안에서만 쓰기

[sandbox_workspace_write]
writable_roots = [
  "C:\\Users\\okggg\\Desktop\\CSE 310\\mcqm-wt-T1",
  "C:\\Users\\okggg\\Desktop\\CSE 310\\mcqm-wt-T3b",
  "C:\\Users\\okggg\\Desktop\\CSE 310\\mcqm-wt-T4",
]
network_access = false

[shell_environment_policy]
inherit = "core"
[shell_environment_policy.set]
ENABLE_TOOL_SEARCH = "true"
```
- 기존 파일의 `ANTHROPIC_BASE_URL = http://127.0.0.1:8787` 줄은 뺐다 (Codex에는 무의미, headroom 프록시용으로 추정 — 미확인). 필요하면 되살린다.
- 프로젝트 `.codex/config.toml`은 Codex가 이 폴더를 "신뢰"할 때만 적용된다. 안 먹으면 처음 실행 시 trust를 승인하거나 같은 값을 `~/.codex/config.toml`에 `[projects."C:\\Users\\okggg\\Desktop\\CSE 310\\cse310_MCQM"]` 아래로 옮긴다 (미확인).
- push에는 네트워크가 필요하다. Codex는 push하지 않고(`network_access=false`) Claude가 push·PR을 맡는다.

## 3. 시작 명령 (플래그 없이)
```
claude --model opus --effort high
codex -m gpt-6.1-sol -c model_reasoning_effort=high
```
