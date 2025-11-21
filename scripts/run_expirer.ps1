Param(
    [string]$ProjectPath = "C:\Trabajo-local\Domicilio Donatello (Navidad)\Hermez_backend",
    [int]$IntervalSeconds = 60,
    [string]$PythonExe = "python"
)

Write-Host "Iniciando expirador cada $IntervalSeconds s en $ProjectPath..." -ForegroundColor Cyan

try {
    while ($true) {
        try {
            Set-Location -LiteralPath $ProjectPath
            & $PythonExe manage.py expire_quotes_offers | Out-Host
        } catch {
            Write-Warning "Error ejecutando expire_quotes_offers: $_"
        }
        Start-Sleep -Seconds $IntervalSeconds
    }
} finally {
    Write-Host "Expirador detenido" -ForegroundColor Yellow
}
