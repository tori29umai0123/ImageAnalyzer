Set-Location $PSScriptRoot

$Env:PIP_DISABLE_PIP_VERSION_CHECK = 1

if (!(Test-Path -Path "venv")) {
    Write-Output  "create python venv..."
    python -m venv venv
}
.\venv\Scripts\activate

Write-Output "upgrade pip..."
python.exe -m pip install --upgrade pip

Write-Output "Installing deps..."
pip install --upgrade -r requirements.txt

Write-Output "Install completed"
Read-Host | Out-Null ;