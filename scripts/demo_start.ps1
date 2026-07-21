[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$StartTunnel,
    [switch]$SkipPreflight,
    [switch]$CheckOnly,
    [int]$TimeoutSeconds = 90
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

$repoRoot = Split-Path -Parent $PSScriptRoot
$projectId = 2716
$lmStudioPort = 12345
$chatModelIdentifier = "qwen2.5-coder-7b-instruct"
$chatModelPath = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
$chatContextLength = 8192
$embeddingModelIdentifier = "text-embedding-nomic-embed-text-v1.5"
$embeddingModelPath = "nomic-ai/nomic-embed-text-v1.5-GGUF/nomic-embed-text-v1.5.Q8_0.gguf"
$appHealthUrl = "http://127.0.0.1:8501/_stcore/health"

function Write-Step([string]$Message) {
    Write-Host "`n== $Message ==" -ForegroundColor Cyan
}

function Test-DockerDaemon {
    & docker version --format "{{.Server.Version}}" *> $null
    return $LASTEXITCODE -eq 0
}

function Resolve-LmsExecutable {
    $defaultPath = Join-Path $env:USERPROFILE ".lmstudio\bin\lms.exe"
    if (Test-Path -LiteralPath $defaultPath) {
        return $defaultPath
    }
    $command = Get-Command lms -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    throw "LM Studio CLI(lms)를 찾지 못했습니다. LM Studio 설치와 CLI 경로를 확인하세요."
}

function Read-LmsModels([string]$LmsExecutable) {
    $raw = & $LmsExecutable ps --port $lmStudioPort --json 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }
    try {
        return @(($raw -join "`n") | ConvertFrom-Json)
    }
    catch {
        throw "LM Studio model 상태 JSON을 해석하지 못했습니다: $($_.Exception.Message)"
    }
}

function Wait-ForLmsModels([string]$LmsExecutable, [int]$WaitSeconds) {
    $deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    do {
        $models = Read-LmsModels $LmsExecutable
        if ($null -ne $models) {
            return @($models)
        }
        Start-Sleep -Seconds 1
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "LM Studio server가 port $lmStudioPort 에서 준비되지 않았습니다."
}

function Wait-ForAppHealth([int]$WaitSeconds) {
    $deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    $lastError = "응답 없음"
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $appHealthUrl -TimeoutSec 5
            if ($response.StatusCode -eq 200 -and $response.Content.Trim() -eq "ok") {
                return
            }
            $lastError = "HTTP $($response.StatusCode), body=$($response.Content.Trim())"
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 1
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Docker 8501 health 확인 실패: $lastError"
}

function Resolve-PythonExecutable {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        return $venvPython
    }
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    throw "Quick Tunnel 상태 확인에 사용할 Python을 찾지 못했습니다."
}

if ($CheckOnly -and ($Build -or $StartTunnel)) {
    throw "-CheckOnly는 -Build 또는 -StartTunnel과 함께 사용할 수 없습니다."
}

Push-Location $repoRoot
try {
    Write-Step "Docker daemon 확인"
    if (-not (Test-DockerDaemon)) {
        if ($CheckOnly) {
            throw "Docker daemon이 실행 중이 아닙니다."
        }
        & docker desktop start --timeout 60
        if ($LASTEXITCODE -ne 0 -or -not (Test-DockerDaemon)) {
            throw "Docker Desktop을 시작하지 못했습니다."
        }
    }
    Write-Host "Docker daemon: ready"

    Write-Step "LM Studio server와 model 확인"
    $lmsExecutable = Resolve-LmsExecutable
    $models = Read-LmsModels $lmsExecutable
    if ($null -eq $models) {
        if ($CheckOnly) {
            throw "LM Studio server가 port $lmStudioPort 에서 실행 중이 아닙니다."
        }
        & $lmsExecutable server start --port $lmStudioPort
        if ($LASTEXITCODE -ne 0) {
            throw "LM Studio server 시작에 실패했습니다."
        }
        $models = Wait-ForLmsModels $lmsExecutable $TimeoutSeconds
    }

    $chatModel = @($models | Where-Object { $_.type -eq "llm" -and $_.identifier -eq $chatModelIdentifier }) | Select-Object -First 1
    if ($null -eq $chatModel) {
        if ($CheckOnly) {
            throw "Chat model $chatModelIdentifier 이 로드되지 않았습니다."
        }
        & $lmsExecutable load $chatModelPath --port $lmStudioPort --identifier $chatModelIdentifier --context-length $chatContextLength --yes
        if ($LASTEXITCODE -ne 0) {
            throw "Chat model 로드에 실패했습니다."
        }
        $models = Wait-ForLmsModels $lmsExecutable $TimeoutSeconds
        $chatModel = @($models | Where-Object { $_.type -eq "llm" -and $_.identifier -eq $chatModelIdentifier }) | Select-Object -First 1
    }
    if ($null -eq $chatModel -or [int]$chatModel.contextLength -ne $chatContextLength) {
        $actualContext = if ($null -eq $chatModel) { "missing" } else { [string]$chatModel.contextLength }
        throw "Chat model contextLength가 $actualContext 입니다. 시연 기준 $chatContextLength 로 다시 로드해야 합니다."
    }

    $embeddingModel = @($models | Where-Object { $_.type -eq "embedding" -and $_.identifier -eq $embeddingModelIdentifier }) | Select-Object -First 1
    if ($null -eq $embeddingModel) {
        if ($CheckOnly) {
            throw "Embedding model $embeddingModelIdentifier 이 로드되지 않았습니다."
        }
        & $lmsExecutable load $embeddingModelPath --port $lmStudioPort --identifier $embeddingModelIdentifier --yes
        if ($LASTEXITCODE -ne 0) {
            throw "Embedding model 로드에 실패했습니다."
        }
        $models = Wait-ForLmsModels $lmsExecutable $TimeoutSeconds
        $embeddingModel = @($models | Where-Object { $_.type -eq "embedding" -and $_.identifier -eq $embeddingModelIdentifier }) | Select-Object -First 1
    }
    if ($null -eq $embeddingModel) {
        throw "Embedding model 상태를 확인하지 못했습니다."
    }
    Write-Host "LM Studio: port=$lmStudioPort, chat=$chatModelIdentifier/$chatContextLength, embedding=$embeddingModelIdentifier"

    Write-Step "Docker 8501 앱 확인"
    if (-not $CheckOnly) {
        if ($Build) {
            & docker compose up -d --build app
        }
        else {
            & docker compose up -d app
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Docker app 기동에 실패했습니다."
        }
    }
    Wait-ForAppHealth $TimeoutSeconds
    Write-Host "Streamlit: $appHealthUrl -> ok"

    Write-Step "기존 Quick Tunnel 확인"
    $pythonExecutable = Resolve-PythonExecutable
    & $pythonExecutable scripts\quick_tunnel.py status --timeout 10
    $tunnelStatus = $LASTEXITCODE
    if ($tunnelStatus -ne 0) {
        if ($StartTunnel) {
            if ($CheckOnly) {
                throw "Quick Tunnel이 실행 중이 아니며 -CheckOnly에서는 새 Tunnel을 만들지 않습니다."
            }
            & $pythonExecutable scripts\quick_tunnel.py start --timeout $TimeoutSeconds
            if ($LASTEXITCODE -ne 0) {
                throw "Quick Tunnel 기동에 실패했습니다."
            }
        }
        else {
            Write-Warning "실행 중인 Quick Tunnel이 없습니다. 외부 URL이 필요할 때만 -StartTunnel을 추가하세요."
        }
    }

    if (-not $SkipPreflight) {
        Write-Step "시연 preflight"
        & (Join-Path $PSScriptRoot "demo_preflight.ps1") -ProjectId $projectId
        if ($LASTEXITCODE -ne 0) {
            throw "demo_preflight.ps1 검증에 실패했습니다."
        }
    }

    Write-Step "시연 환경 준비 완료"
    Write-Host "Local URL: http://127.0.0.1:8501/?project_id=$projectId"
    Write-Host "기존 Tunnel이 표시됐다면 해당 URL 뒤에 /?project_id=$projectId 를 붙여 사용하세요."
}
finally {
    Pop-Location
}
