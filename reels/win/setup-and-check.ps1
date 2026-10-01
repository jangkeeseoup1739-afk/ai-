# 릴스 편집 도구: 설치 + 환경 점검을 한 번에.
#
# 쓰는 법 (PowerShell에 아래 한 줄 붙여넣기):
#   irm https://raw.githubusercontent.com/jangkeeseoup1739-afk/ai-/claude/bold-albattani-2wh4im/reels/win/setup-and-check.ps1 | iex
#
# 중간에 뭐가 실패해도 끝까지 가고, 무슨 일이 있었는지 전부
# 바탕화면의 "릴스-점검결과.txt" 에 적는다. 그 파일을 보내주면 된다.

$ErrorActionPreference = "Continue"
$Branch = "claude/bold-albattani-2wh4im"   # PR 머지 후에는 기본 브랜치로 바꾼다
$Repo   = "jangkeeseoup1739-afk/ai-"

$Desktop = [Environment]::GetFolderPath("Desktop")
if (-not $Desktop) { $Desktop = Join-Path $HOME "Desktop" }
$LogPath = Join-Path $Desktop "릴스-점검결과.txt"
$Lines = New-Object System.Collections.ArrayList

function Log($text) {
    Write-Host $text
    [void]$Lines.Add($text)
    try { $Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8 } catch { }
}
function Step($n, $text) { Log ""; Log "===== $n. $text =====" }
function Have($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

Log "릴스 편집 도구 설치 + 점검"
Log "시작: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "결과는 여기에 저장됩니다: $LogPath"
Log "Windows: $([Environment]::OSVersion.VersionString)"
Log "PowerShell: $($PSVersionTable.PSVersion)"

# ---------------------------------------------------------------- 1. Python
Step 1 "Python 확인"
$Python = $null
foreach ($c in @("python", "py")) {
    if (Have $c) {
        $v = & $c --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 10) {
            $Python = $c; Log "찾음: $c ($v)"; break
        } else { Log "$c 은 쓸 수 없음: $v" }
    }
}
if (-not $Python) {
    Log "Python 이 없거나 3.10 보다 낮습니다. winget 으로 설치를 시도합니다."
    if (Have winget) {
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements 2>&1 | ForEach-Object { Log "  $_" }
        Log "설치 후에는 PowerShell 을 닫고 새로 연 뒤 이 명령을 다시 실행하세요."
    } else {
        Log "winget 도 없습니다. https://www.python.org/downloads/ 에서 직접 설치하고"
        Log "설치 화면 맨 아래 'Add python.exe to PATH' 를 반드시 켜주세요."
        Start-Process "https://www.python.org/downloads/"
    }
    Log ""
    Log "여기서 멈춥니다. Python 을 설치한 뒤 다시 실행해주세요."
    try { Start-Process notepad.exe $LogPath } catch { }
    return
}

# ---------------------------------------------------------- 2. 코드 내려받기
Step 2 "코드 내려받기"
$Root = Join-Path $HOME "ai-"
$local = ""
if ($PSScriptRoot) {                      # iex 로 실행하면 비어 있다
    $maybe = Join-Path $PSScriptRoot "..\doctor.py"
    if (Test-Path $maybe) { $local = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path }
}
if ($local) {
    $Root = $local
    Log "이미 가지고 있는 코드를 씁니다: $Root"
} else {
    $zip = Join-Path $env:TEMP "reels-src.zip"
    $out = Join-Path $env:TEMP "reels-src"
    $url = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
    Log "내려받는 중: $url"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Remove-Item $zip, $out -Recurse -Force -ErrorAction SilentlyContinue
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $out -Force
        $inner = Get-ChildItem $out -Directory | Select-Object -First 1
        if (-not $inner) { throw "압축 안에 폴더가 없습니다" }
        Remove-Item $Root -Recurse -Force -ErrorAction SilentlyContinue
        Move-Item $inner.FullName $Root
        Log "풀었습니다: $Root"
    } catch {
        Log "내려받기 실패: $_"
        Log "인터넷 연결이나 회사 방화벽을 확인해주세요."
        try { Start-Process notepad.exe $LogPath } catch { }
        return
    }
}

# --------------------------------------------------------- 3. ffmpeg / yt-dlp
Step 3 "ffmpeg / yt-dlp"
if (Have winget) {
    foreach ($pkg in @(@("ffmpeg", "Gyan.FFmpeg"), @("yt-dlp", "yt-dlp.yt-dlp"))) {
        if (Have $pkg[0]) { Log "$($pkg[0]): 이미 있음" }
        else {
            Log "$($pkg[0]) 설치 중..."
            winget install --id $pkg[1] -e --accept-source-agreements --accept-package-agreements 2>&1 |
                Select-Object -Last 3 | ForEach-Object { Log "  $_" }
        }
    }
    Log "(방금 설치한 것은 PowerShell 을 새로 열어야 PATH 에 잡힙니다)"
} else {
    Log "winget 이 없어 건너뜁니다. Microsoft Store 에서 '앱 설치 관리자' 를 설치하면 됩니다."
}

# ------------------------------------------------------------ 4. 가상환경
Step 4 "파이썬 가상환경 + 패키지"
$Venv = Join-Path $HOME ".pycapcut"
$VenvPy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Log "만드는 중: $Venv"
    & $Python -m venv $Venv 2>&1 | ForEach-Object { Log "  $_" }
}
if (-not (Test-Path $VenvPy)) {
    Log "가상환경을 만들지 못했습니다. 위 메시지를 확인해주세요."
    try { Start-Process notepad.exe $LogPath } catch { }
    return
}
& $VenvPy -m pip install --upgrade pip 2>&1 | Select-Object -Last 2 | ForEach-Object { Log "  $_" }
$req = Join-Path $Root "reels\requirements.txt"
if (-not (Test-Path $req)) {
    Log "코드를 찾지 못했습니다: $req"
    Log "2번 단계(코드 내려받기)가 실패했습니다. 위 메시지를 확인해주세요."
    try { Start-Process notepad.exe $LogPath } catch { }
    return
}
Log "설치 중: $req"
& $VenvPy -m pip install -r $req 2>&1 | Select-Object -Last 6 | ForEach-Object { Log "  $_" }

# -------------------------------------------------------------- 5. 점검
Step 5 "환경 점검"
Push-Location $Root
try {
    $report = & $VenvPy -m reels doctor 2>&1
    foreach ($line in $report) { Log "$line" }
} catch {
    Log "점검을 돌리지 못했습니다: $_"
} finally {
    Pop-Location
}

Log ""
Log "끝: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "이 파일($LogPath) 내용을 전부 복사해서 보내주세요."
try { Start-Process notepad.exe $LogPath } catch { Log "메모장을 열지 못했습니다. 바탕화면에서 직접 열어주세요." }
