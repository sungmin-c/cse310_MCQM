# 3시간 야간형 큐: ai_loop.ps1(Codex 구현 -> Claude 리뷰 -> Codex 수정)을 작업별로 순서대로 돌린다. 각 작업은 격리 worktree.
# 실행 (repo 루트, 별도 PowerShell 창):  pwsh scripts/run_queue.ps1 [-MaxMinutes 180] [-Rounds 2]
# 안전: push·병합 안 함. main 작업 폴더는 건드리지 않는다. 시간이 지나면 새 작업을 시작하지 않는다(진행 중인 작업은 끝까지).
# 되돌리기: Ctrl+C 로 중단 후  git worktree remove --force ../mcqm-wt-<Id> ; git branch -D <Branch>
param([int]$MaxMinutes = 180, [int]$Rounds = 2)
$ErrorActionPreference = 'Stop'
$start = Get-Date
$base = (git branch --show-current).Trim()            # 지금 브랜치 위에서 작업 (P5 커밋이 main에 없으므로)

# 이 프로세스가 도는 동안만 절전·화면 꺼짐 방지 (시스템 설정은 바꾸지 않는다. 프로세스가 끝나면 자동 해제)
Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[void][Win.Power]::SetThreadExecutionState(0x80000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$queue = @(
  @{ Id = 'T9a'; Branch = 'ml/t9a-teams-app';   Brief = 'docs/briefs/T9a.md' },
  @{ Id = 'T13'; Branch = 'ml/t13-p5-harden';   Brief = 'docs/briefs/T13.md' }
)
foreach ($job in $queue) {
  $elapsed = ((Get-Date) - $start).TotalMinutes
  if ($elapsed -ge $MaxMinutes) { Write-Host "시간 초과($([int]$elapsed)분): $($job.Id) 건너뜀"; continue }
  Write-Host "`n##### $($job.Id) 시작 ($([int]$elapsed)분 경과) #####"
  try {
    pwsh -NoProfile -File scripts/ai_loop.ps1 -Id $job.Id -Branch $job.Branch -Brief $job.Brief -Base $base -Rounds $Rounds
  } catch { Write-Host "$($job.Id) 실패: $_" }
}
Write-Host "`n===== 요약 ====="
foreach ($job in $queue) {
  $f = "data/ai_runs/$($job.Id)/summary.txt"
  if (Test-Path $f) { Write-Host "$($job.Id): $(Get-Content $f)" } else { Write-Host "$($job.Id): 실행 안 됨" }
}
