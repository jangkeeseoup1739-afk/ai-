# 릴스 편집 도구 설치 (Windows, PowerShell)
#   powershell -ExecutionPolicy Bypass -File reels\setup-windows.ps1
#
# 관리자 권한은 필요 없습니다. winget이 설치 중 한 번 확인을 물을 수 있습니다.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot   # 저장소 최상위 (reels\ 의 부모)

function Have($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

Write-Host "== 1/3 ffmpeg / yt-dlp ==" -ForegroundColor Cyan
$installed = $false
if (-not (Have winget)) {
    Write-Host "winget이 없습니다. '앱 설치 관리자'를 Microsoft Store에서 설치하거나," -ForegroundColor Yellow
    Write-Host "ffmpeg와 yt-dlp를 직접 받아 PATH에 넣어주세요." -ForegroundColor Yellow
} else {
    if (Have ffmpeg) { Write-Host "  ffmpeg 이미 있음" }
    else {
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        $installed = $true
    }
    if (Have yt-dlp) { Write-Host "  yt-dlp 이미 있음" }
    else {
        winget install --id yt-dlp.yt-dlp -e --accept-source-agreements --accept-package-agreements
        $installed = $true
    }
}

Write-Host "== 2/3 파이썬 가상환경 ==" -ForegroundColor Cyan
if (-not (Have python)) {
    throw "python이 없습니다. https://www.python.org 에서 설치하고 'Add python.exe to PATH'를 켜주세요."
}

$venv = Join-Path $HOME ".pycapcut"
if (-not (Test-Path $venv)) { python -m venv $venv }
$py = Join-Path $venv "Scripts\python.exe"

Write-Host "== 3/3 pycapcut / faster-whisper ==" -ForegroundColor Cyan
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host ""
Write-Host "== 설치 확인 ==" -ForegroundColor Cyan
if (Have ffmpeg) { (ffmpeg -version | Select-Object -First 1) } else { "ffmpeg: 이 창에서는 아직 안 보임" }
if (Have yt-dlp) { "yt-dlp:  $(yt-dlp --version)" }        else { "yt-dlp: 이 창에서는 아직 안 보임" }
& $py -c "import pycapcut; print('pycapcut ok')"
& $py -c "import faster_whisper; print('faster-whisper', faster_whisper.__version__)"

# 저장소 위치를 기준으로 불러온다 (현재 폴더가 어디든 동작하도록)
$probe = @"
import sys
sys.path.insert(0, r'$repo')
from reels import platforms
p = platforms.default_draft_root()
print('캡컷 초안 폴더:', p)
print('  ->', '찾았습니다' if p.is_dir() else '없습니다. 캡컷을 한 번 실행해 프로젝트를 만들어주세요.')
"@
& $py -c $probe

Write-Host ""
if ($installed) {
    Write-Host "winget으로 방금 설치한 것은 PowerShell을 새로 열어야 PATH에 잡힙니다." -ForegroundColor Yellow
}
Write-Host "설치 끝!" -ForegroundColor Green
Write-Host ""
Write-Host "다음 (저장소 폴더에서):" -ForegroundColor Cyan
Write-Host "  & `"$py`" -m reels all -i `"$HOME\Desktop\촬영본.mp4`" --name 릴스_러프컷"
Write-Host "받아쓰기 모델은 처음 실행할 때 한 번 자동으로 내려받습니다 (약 1.5GB)."
