param(
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][string]$CrawlerPath
)

$arguments = @(
    ('"{0}"' -f $CrawlerPath),
    '--auto',
    '--no-notification'
)

try {
    $process = Start-Process `
        -FilePath $PythonPath `
        -ArgumentList $arguments `
        -WorkingDirectory (Split-Path -Parent $CrawlerPath) `
        -Verb RunAs `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    exit $process.ExitCode
}
catch {
    Write-Error "无法启动管理员采集进程：$($_.Exception.Message)"
    exit 1
}
