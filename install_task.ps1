# Legt die Windows-Aufgabe "M365 Dub Downloader" an: alle 3 Stunden
# Download neuer Dubs -> Whisper-Transkripte -> Upload zu Spreaker.
# Ausfuehren:  powershell -ExecutionPolicy Bypass -File "S:\Downloads\Dub Downloader\install_task.ps1"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $dir "run_dubs.bat"
New-Item -ItemType Directory -Force -Path "$dir\_logs" | Out-Null
$act = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"`"$bat`" run >> `"$dir\_logs\task_output.log`" 2>&1`"" -WorkingDirectory $dir
$trg = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 3)
$set = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
       -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 12)
Register-ScheduledTask -TaskName "M365 Dub Downloader" -Action $act -Trigger $trg -Settings $set `
       -Description "YouTube-Dubs (Sticky Man Explained) laden, transkribieren und zu Spreaker hochladen" -Force | Out-Null
Write-Host "Fertig: Aufgabe 'M365 Dub Downloader' laeuft ab jetzt alle 3 Stunden (erster Start in 2 Minuten)." -ForegroundColor Green
Read-Host "Enter zum Schliessen"
