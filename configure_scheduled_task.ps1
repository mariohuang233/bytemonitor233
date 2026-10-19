param(
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][string]$ScriptPath,
    [Parameter(Mandatory = $true)][string]$Mode,
    [Parameter(Mandatory = $true)][string]$RunTime,
    [Parameter(Mandatory = $true)][int]$IntervalMinutes,
    [string]$Weekdays = "0,1,2,3,4",
    [Parameter(Mandatory = $true)][string]$Enabled
)

$ErrorActionPreference = "Stop"
$taskName = "RecruitmentJobMonitor"

if ($Enabled -ne "true") {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "DISABLED"
    exit 0
}

$workingDirectory = Split-Path -Parent $ScriptPath
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument ('"{0}" --run-once' -f $ScriptPath) `
    -WorkingDirectory $workingDirectory

if ($Mode -eq "interval") {
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
}
elseif ($Mode -eq "weekly") {
    $dayNames = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    $selectedDays = @()
    foreach ($index in $Weekdays.Split(",")) {
        if ($index -match "^\d+$" -and [int]$index -ge 0 -and [int]$index -le 6) {
            $selectedDays += $dayNames[[int]$index]
        }
    }
    if ($selectedDays.Count -eq 0) { $selectedDays = @("Monday") }
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $selectedDays -At $RunTime
}
else {
    $trigger = New-ScheduledTaskTrigger -Daily -At $RunTime
}

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

$task = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Output ("ACTIVE|{0}|{1}" -f $task.State, $info.NextRunTime.ToString("s"))
