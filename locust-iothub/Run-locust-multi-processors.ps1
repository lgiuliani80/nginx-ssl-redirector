# Test file name
$locustFile = "locustfile.py"
# Web UI port
$webPort = 8089
# Number of logical CPU cores available
$cpuCores = [System.Environment]::ProcessorCount - 2
# List of Locust processes
$locustProcesses = @()

try {
    Write-Host "🔹 Run Locust master on port $webPort"
    $p = Start-Process -PassThru -FilePath "locust" -ArgumentList "-f $locustFile --master --web-port $webPort"
    $locustProcesses += $p

    Start-Sleep -Seconds 5

    Write-Host "🔹 Run $cpuCores worker..."
    for ($i = 1; $i -le $cpuCores; $i++) {
        $p = Start-Process -PassThru -FilePath "locust" -ArgumentList "-f $locustFile --worker --master-host=127.0.0.1"
        $locustProcesses += $p
    }

    Write-Host "✅ Ready! Open http://localhost:$webPort"
    Write-Host "ℹ️ Press CTRL+C to stop and terminate the Locust processes."

    # Keep the script alive
    while ($true) {
        Start-Sleep -Seconds 5
    }
}
finally {
    Write-Host "`n🛑 Stopping, terminating all Locust processes..."
    foreach ($p in $locustProcesses) {
        try {
            Stop-Process -Id $p.Id -Force
        } catch {
            Write-Host "⚠️ Could not terminate PID $($p.Id)"
        }
    }
    Write-Host "✅ All Locust processes terminated."
}