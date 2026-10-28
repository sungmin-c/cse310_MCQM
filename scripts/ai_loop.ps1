# Codex 구현 -> Claude 리뷰 -> Codex 수정 자동 루프 (격리된 git worktree에서만 동작)
# 실행 (repo 루트):  pwsh scripts/ai_loop.ps1 -Id T1 -Branch ml/t1-tshark-live -Brief docs/briefs/T1.md [-Base main]
# 안전: main/원본 작업 폴더는 건드리지 않는다. push 안 함. 결과 확인 후 병합은 사람이 한다.
# 되돌리기: git worktree remove --force ../mcqm-wt-<Id> ; git branch -D <Branch>
param(
  [Parameter(Mandatory)][string]$Id,
  [Parameter(Mandatory)][string]$Branch,
  [Parameter(Mandatory)][string]$Brief,
  [int]$Rounds = 3,
  [string]$Base = 'main',          # worktree를 만들 기준 브랜치·커밋 (아직 main에 없는 커밋 위에서 작업할 때)
  [string]$ImplModel = 'gpt-6.1-sol', [string]$ImplEffort = 'high',
  [string]$ReviewModel = 'opus', [string]$ReviewEffort = 'high'
)
$ErrorActionPreference = 'Stop'
$main = (git rev-parse --show-toplevel).Trim()
$wt   = Join-Path (Split-Path $main) "mcqm-wt-$Id"
$log  = Join-Path $main "data/ai_runs/$Id"          # data/ 는 git 제외
New-Item -ItemType Directory -Force $log | Out-Null

if (-not (Test-Path $wt)) {
  git worktree add $wt -b $Branch $Base | Out-Null
  # data/ 는 git 제외라 worktree에 없다. 모델 pkl만 복사 (junction 만들지 않음: 삭제 사고 방지)
  New-Item -ItemType Directory -Force "$wt/data/models" | Out-Null
  Copy-Item "$main/data/models/*" "$wt/data/models/"
  # 아직 main에 없는 에이전트 문맥 파일을 가져와 별도 커밋으로 둔다 (리뷰 diff 기준점)
  foreach ($f in 'AGENTS.md', '.claude/CLAUDE.md', 'docs/HANDOFF.md', 'docs/briefs', 'docs/design') {
    Copy-Item "$main/$f" "$wt/$f" -Recurse -Force
  }
  git -C $wt add -A; git -C $wt commit -q -m "ctx($Id): agent docs"
}
$base = (git -C $wt rev-parse HEAD~0).Trim()   # 첫 실행 시 ctx 커밋. 재실행이면 현재 HEAD
# 의존성은 원본 .venv 공유 (네트워크 없이 테스트). vcaml은 원본 경로로 editable 설치돼 있음
$env:UV_PROJECT_ENVIRONMENT = Join-Path $main '.venv'
$test = 'uv run --no-sync pytest tests/ -q'

$task = Get-Content (Join-Path $main $Brief) -Raw
$prompt = @"
너는 이 repo의 구현 담당(Codex)이다. AGENTS.md와 docs/HANDOFF.md의 $Id 항목을 따른다.
아래 브리프를 구현하라. 테스트 명령: $test (환경변수 UV_PROJECT_ENVIRONMENT가 이미 설정됨, 네트워크 없음).
하지 말 것: dashboard/·vcaml/ 수정, push, 새 의존성. 끝나면 '변경 / 테스트 / 남은 것' 3줄로 보고.

$task
"@

for ($r = 1; $r -le $Rounds; $r++) {
  Write-Host "== $Id round $r : Codex ($ImplModel/$ImplEffort)"
  $prompt | codex exec -C $wt -m $ImplModel -c "model_reasoning_effort=$ImplEffort" `
      -c "shell_environment_policy.set.UV_PROJECT_ENVIRONMENT='$env:UV_PROJECT_ENVIRONMENT'" `
      --sandbox workspace-write -o "$log/codex_$r.md" - *> "$log/codex_$r.log"
  git -C $wt add -A
  git -C $wt commit -q -m "wip($Id): round $r (codex)" --allow-empty

  Write-Host "== $Id round $r : Claude review ($ReviewModel/$ReviewEffort)"
  $rp = @"
AGENTS.md의 '코드 리뷰 모드'를 따라 'git diff $base HEAD'를 리뷰하라. 수정하지 말 것(읽기와 테스트 실행만).
브리프의 완료 기준을 하나씩 확인하고 '$test'를 실행해 결과를 인용하라.
첫 줄은 정확히 'VERDICT: PASS' 또는 'VERDICT: FIX'. 이후 FIX면 파일:줄 — 문제 — 재현 상황 목록(심각도순, 최대 8개).
브리프:
$task
"@
  $rp | claude -p --model $ReviewModel --effort $ReviewEffort `
      --allowedTools 'Read' 'Grep' 'Glob' 'Bash(git diff:*)' 'Bash(git log:*)' 'Bash(git status:*)' 'Bash(uv run --no-sync pytest:*)' `
      > "$log/review_$r.md" 2> "$log/review_$r.err"
  $verdict = (Get-Content "$log/review_$r.md" -TotalCount 1)
  Write-Host "   $verdict"
  if ($verdict -match 'PASS') { break }
  # 다음 라운드: 리뷰 발견을 Codex 입력으로
  $prompt = "이전 라운드 리뷰 결과(Claude)다. 타당한 항목만 수정하고, 반박할 항목은 근거를 보고에 적어라. 테스트: $test`n`n" + (Get-Content "$log/review_$r.md" -Raw)
}
"verdict=$verdict rounds=$r branch=$Branch worktree=$wt" | Set-Content "$log/summary.txt"
Write-Host "완료. $log/summary.txt"
