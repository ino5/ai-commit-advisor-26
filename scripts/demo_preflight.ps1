[CmdletBinding()]
param(
    [string]$AppUrl = "http://127.0.0.1:8501",
    [string]$LlmBaseUrl = "http://127.0.0.1:12345/v1",
    [string]$LlmModel = "qwen2.5-coder-7b-instruct",
    [string]$EmbeddingModel = "text-embedding-nomic-embed-text-v2-moe",
    [int]$ExpectedEmbeddingDimension = 768,
    [int]$ProjectId = 1,
    [string]$SampleRepoPath = "C:\dev\ai-advisor-sample-shop",
    [switch]$SkipLiveModelProbe,
    [switch]$SkipDatabaseProbe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

$script:FailureCount = 0
$script:WarningCount = 0

function Write-Check {
    param(
        [ValidateSet("PASS", "WARN", "FAIL", "INFO")]
        [string]$Status,
        [string]$Message
    )

    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        default { "Cyan" }
    }

    if ($Status -eq "FAIL") {
        $script:FailureCount += 1
    }
    elseif ($Status -eq "WARN") {
        $script:WarningCount += 1
    }

    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-TcpPortReservation {
    param([int]$Port)

    $rows = netsh interface ipv4 show excludedportrange protocol=tcp 2>$null
    foreach ($row in $rows) {
        if ($row -match "^\s*(\d+)\s+(\d+)") {
            $startPort = [int]$Matches[1]
            $endPort = [int]$Matches[2]
            if ($Port -ge $startPort -and $Port -le $endPort) {
                return $true
            }
        }
    }
    return $false
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appHealthUrl = "$($AppUrl.TrimEnd('/'))/_stcore/health"
$llmUri = [Uri]$LlmBaseUrl
$llmPort = $llmUri.Port
$repoHead = $null

Write-Host "AI Commit Advisor 시연 사전 점검" -ForegroundColor White
Write-Host "repo=$repoRoot project_id=$ProjectId app=$AppUrl llm=$LlmBaseUrl" -ForegroundColor DarkGray

$requiredFiles = @(
    (Join-Path $repoRoot "outputs\20260630_0735_ai-use-case-team-share_수정1_로컬.pptx"),
    (Join-Path $repoRoot "outputs\ai-use-case-team-share.pptx"),
    (Join-Path $repoRoot "outputs\20260630_0547_application-preview-summary.pptx")
)

foreach ($requiredFile in $requiredFiles) {
    if (Test-Path -LiteralPath $requiredFile) {
        Write-Check "PASS" "대체 자료 확인: $requiredFile"
    }
    else {
        Write-Check "FAIL" "대체 자료가 없습니다: $requiredFile"
    }
}

if (-not (Test-Path -LiteralPath $SampleRepoPath)) {
    Write-Check "FAIL" "샘플 저장소가 없습니다: $SampleRepoPath"
}
elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Check "FAIL" "git 명령을 찾지 못했습니다."
}
else {
    $isRepo = (& git -C $SampleRepoPath rev-parse --is-inside-work-tree 2>$null).Trim()
    if ($LASTEXITCODE -ne 0 -or $isRepo -ne "true") {
        Write-Check "FAIL" "샘플 경로가 Git 저장소가 아닙니다: $SampleRepoPath"
    }
    else {
        $commitCount = [int]((& git -C $SampleRepoPath rev-list --count HEAD).Trim())
        $repoHead = (& git -C $SampleRepoPath rev-parse HEAD).Trim()
        $worktreeStatus = @(& git -C $SampleRepoPath status --porcelain)
        if ($commitCount -eq 48) {
            Write-Check "PASS" "샘플 저장소 commit 48개, HEAD=$($repoHead.Substring(0, 12))"
        }
        else {
            Write-Check "WARN" "샘플 저장소 commit 수가 기준값 48과 다릅니다: $commitCount"
        }

        if ($worktreeStatus.Count -eq 0) {
            Write-Check "PASS" "샘플 저장소 작업트리가 clean 상태입니다."
        }
        else {
            Write-Check "WARN" "샘플 저장소에 미커밋 변경이 있습니다. 시연 전에 원인을 확인하세요."
        }
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Check "FAIL" "docker 명령을 찾지 못했습니다."
}
else {
    Push-Location $repoRoot
    try {
        $dockerVersion = (& docker info --format "{{.ServerVersion}}" 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $dockerVersion) {
            Write-Check "PASS" "Docker engine 연결: $dockerVersion"
        }
        else {
            Write-Check "FAIL" "Docker engine에 연결할 수 없습니다."
        }

        $postgresStatus = (& docker inspect --format "{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{end}}" ai_commit_advisor_postgres 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $postgresStatus -eq "running/healthy") {
            Write-Check "PASS" "PostgreSQL container: $postgresStatus"
        }
        else {
            Write-Check "FAIL" "PostgreSQL container가 healthy 상태가 아닙니다: $postgresStatus"
        }

        $neo4jStatus = (& docker inspect --format "{{.State.Status}}" ai_commit_advisor_neo4j 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $neo4jStatus -eq "running") {
            Write-Check "PASS" "Neo4j container: $neo4jStatus"
        }
        else {
            Write-Check "FAIL" "Neo4j container가 running 상태가 아닙니다: $neo4jStatus"
        }

        $appStatus = (& docker inspect --format "{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{end}}" ai_commit_advisor_app 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $appStatus -eq "running/healthy") {
            Write-Check "PASS" "Streamlit app container: $appStatus"
        }
        else {
            Write-Check "FAIL" "Streamlit app container가 healthy 상태가 아닙니다: $appStatus"
        }
    }
    finally {
        Pop-Location
    }
}

try {
    $neo4jResponse = Invoke-WebRequest -Uri "http://127.0.0.1:7474" -UseBasicParsing -TimeoutSec 5
    Write-Check "PASS" "Neo4j HTTP endpoint: HTTP $($neo4jResponse.StatusCode)"
}
catch {
    Write-Check "FAIL" "Neo4j HTTP endpoint에 연결할 수 없습니다: $($_.Exception.Message)"
}

if (Test-TcpPortReservation -Port $llmPort) {
    Write-Check "FAIL" "LLM port $llmPort 이 Windows 제외 포트 범위에 포함됩니다. 다른 port를 사용하세요."
}
else {
    Write-Check "PASS" "LLM port $llmPort 은 Windows 제외 포트 범위 밖입니다."
}

try {
    $modelsResponse = Invoke-RestMethod -Uri "$($LlmBaseUrl.TrimEnd('/'))/models" -Method Get -TimeoutSec 8
    $modelIds = @($modelsResponse.data | ForEach-Object { $_.id })
    if ($modelIds -contains $LlmModel) {
        Write-Check "PASS" "Chat model 로드 확인: $LlmModel"
    }
    else {
        Write-Check "FAIL" "Chat model이 로드되지 않았습니다: $LlmModel"
    }

    if ($modelIds -contains $EmbeddingModel) {
        Write-Check "PASS" "Embedding model 로드 확인: $EmbeddingModel"
    }
    else {
        Write-Check "FAIL" "Embedding model이 로드되지 않았습니다: $EmbeddingModel"
    }
}
catch {
    Write-Check "FAIL" "LM Studio models endpoint에 연결할 수 없습니다: $($_.Exception.Message)"
}

if ($SkipLiveModelProbe) {
    Write-Check "INFO" "-SkipLiveModelProbe로 chat/embedding 실제 호출을 건너뜁니다."
}
else {
    try {
        $embeddingPayload = @{
            model = $EmbeddingModel
            input = @("시연 연결 확인")
        } | ConvertTo-Json -Depth 5
        $embeddingBytes = [Text.Encoding]::UTF8.GetBytes($embeddingPayload)
        $embeddingResponse = Invoke-RestMethod `
            -Uri "$($LlmBaseUrl.TrimEnd('/'))/embeddings" `
            -Method Post `
            -Body $embeddingBytes `
            -ContentType "application/json; charset=utf-8" `
            -TimeoutSec 30
        $embeddingDimension = @($embeddingResponse.data[0].embedding).Count
        if ($embeddingDimension -eq $ExpectedEmbeddingDimension) {
            Write-Check "PASS" "Embedding 실제 호출: dimension=$embeddingDimension"
        }
        else {
            Write-Check "FAIL" "Embedding dimension이 예상값과 다릅니다: $embeddingDimension (expected=$ExpectedEmbeddingDimension)"
        }
    }
    catch {
        Write-Check "FAIL" "Embedding 실제 호출이 실패했습니다: $($_.Exception.Message)"
    }

    try {
        $chatPayload = @{
            model = $LlmModel
            messages = @(
                @{ role = "system"; content = "짧게 한국어로 답하세요." },
                @{ role = "user"; content = "연결 확인이라고 답해줘." }
            )
            temperature = 0
            max_tokens = 24
        } | ConvertTo-Json -Depth 8
        $chatBytes = [Text.Encoding]::UTF8.GetBytes($chatPayload)
        $chatResponse = Invoke-RestMethod `
            -Uri "$($LlmBaseUrl.TrimEnd('/'))/chat/completions" `
            -Method Post `
            -Body $chatBytes `
            -ContentType "application/json; charset=utf-8" `
            -TimeoutSec 45
        $chatText = [string]$chatResponse.choices[0].message.content
        if ($chatText.Trim()) {
            Write-Check "PASS" "Chat 실제 호출 응답: $($chatText.Trim())"
        }
        else {
            Write-Check "FAIL" "Chat endpoint가 빈 응답을 반환했습니다."
        }
    }
    catch {
        Write-Check "FAIL" "Chat 실제 호출이 실패했습니다: $($_.Exception.Message)"
    }
}

try {
    $appHealth = Invoke-WebRequest -Uri $appHealthUrl -UseBasicParsing -TimeoutSec 8
    if ($appHealth.StatusCode -eq 200 -and $appHealth.Content.Trim() -eq "ok") {
        Write-Check "PASS" "Streamlit health endpoint: HTTP 200 / ok"
    }
    else {
        Write-Check "FAIL" "Streamlit health 응답이 예상과 다릅니다: HTTP $($appHealth.StatusCode) / $($appHealth.Content.Trim())"
    }
}
catch {
    Write-Check "FAIL" "Streamlit health endpoint에 연결할 수 없습니다: $($_.Exception.Message)"
}

try {
    $remoteService = Get-Service -Name "chromoting" -ErrorAction Stop
    if ($remoteService.Status -eq "Running") {
        Write-Check "PASS" "Chrome 원격 데스크톱 서비스: Running"
    }
    else {
        Write-Check "FAIL" "Chrome 원격 데스크톱 서비스 상태: $($remoteService.Status)"
    }
}
catch {
    Write-Check "FAIL" "Chrome 원격 데스크톱 서비스를 찾지 못했습니다."
}

if ($SkipDatabaseProbe) {
    Write-Check "INFO" "-SkipDatabaseProbe로 시연 프로젝트 DB 검사를 건너뜁니다."
}
elseif (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Check "FAIL" "프로젝트 Python 실행 파일이 없습니다: $pythonPath"
}
else {
    $dbProbe = @'
import json
import sys

from sqlalchemy import func

from src.db.database import SessionLocal
from src.db.models import (
    CodeReviewResult,
    DocumentChunk,
    GitCommit,
    Program,
    Project,
    ProjectChatMessage,
    ProjectChatSession,
    ProjectGraphSyncState,
    VectorItem,
)
from src.rag.embedding_client import EmbeddingClient
from src.utils.config import settings

project_id = int(sys.argv[1])
with SessionLocal() as db:
    project = db.query(Project).filter(Project.id == project_id).one_or_none()
    if project is None:
        raise RuntimeError(f"project not found: {project_id}")

    source_query = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == project_id,
        DocumentChunk.source_type == "source_file",
    )
    embedding_storage_key = EmbeddingClient().embedding_model_name
    vector_count = (
        db.query(func.count(func.distinct(VectorItem.chunk_id)))
        .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
        .filter(
            DocumentChunk.project_id == project_id,
            DocumentChunk.source_type == "source_file",
            VectorItem.embedding_model == embedding_storage_key,
        )
        .scalar()
        or 0
    )
    graph = db.query(ProjectGraphSyncState).filter(ProjectGraphSyncState.project_id == project_id).one_or_none()
    chat = (
        db.query(ProjectChatMessage)
        .join(ProjectChatSession, ProjectChatMessage.session_id == ProjectChatSession.id)
        .filter(ProjectChatSession.project_id == project_id, ProjectChatMessage.role == "assistant")
        .order_by(ProjectChatMessage.created_at.desc())
        .first()
    )
    review = (
        db.query(CodeReviewResult)
        .filter(CodeReviewResult.project_id == project_id)
        .order_by(CodeReviewResult.created_at.desc())
        .first()
    )
    chat_meta = (chat.raw_metadata or {}) if chat else {}
    payload = {
        "project_name": project.name,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "embedding_storage_key": embedding_storage_key,
        "embedding_base_url": settings.embedding_base_url,
        "pgvector_dimension": settings.pgvector_dimension,
        "neo4j_enabled": settings.neo4j_enabled,
        "stored_analysis_head": project.last_synced_commit_hash,
        "program_count": db.query(Program).filter(Program.project_id == project_id).count(),
        "commit_count": db.query(GitCommit).filter(GitCommit.project_id == project_id).count(),
        "analyzed_commit_count": db.query(GitCommit).filter(
            GitCommit.project_id == project_id,
            GitCommit.mapping_analyzed_at.isnot(None),
        ).count(),
        "source_count": source_query.count(),
        "vector_count": vector_count,
        "graph_status": graph.status if graph else None,
        "graph_node_count": graph.node_count if graph else 0,
        "graph_edge_count": graph.edge_count if graph else 0,
        "graph_repo_head": graph.repo_head_hash if graph else None,
        "chat_session_id": chat.session_id if chat else None,
        "chat_source_count": chat.used_source_count if chat else 0,
        "chat_graph_count": len(chat_meta.get("graph_evidence") or []),
        "chat_fallback": chat_meta.get("fallback_used"),
        "chat_validation": chat_meta.get("validation_status"),
        "chat_insufficient": chat.insufficient_evidence if chat else True,
        "review_target": review.target_ref if review else None,
        "review_bug_count": len(review.bug_findings or []) if review else 0,
        "review_status": review.status if review else None,
    }
    print(json.dumps(payload, ensure_ascii=False))
'@

    Push-Location $repoRoot
    try {
        $dbOutput = @($dbProbe | & $pythonPath - $ProjectId 2>&1)
        if ($LASTEXITCODE -ne 0) {
            Write-Check "FAIL" "시연 프로젝트 DB 검사가 실패했습니다: $($dbOutput -join ' ')"
        }
        else {
            $dbState = $dbOutput[-1] | ConvertFrom-Json
            Write-Check "PASS" "시연 프로젝트: $($dbState.project_name) (#$ProjectId)"

            $expectedLlmBaseUrl = $LlmBaseUrl.TrimEnd("/")
            $configuredLlmBaseUrl = ([string]$dbState.llm_base_url).TrimEnd("/")
            if ($dbState.llm_provider -eq "local_openai" -and $dbState.llm_model -eq $LlmModel -and $configuredLlmBaseUrl -eq $expectedLlmBaseUrl) {
                Write-Check "PASS" "앱 LLM 설정: local_openai / $LlmModel / $configuredLlmBaseUrl"
            }
            else {
                Write-Check "FAIL" "앱 LLM 설정이 preflight 대상과 다릅니다: provider=$($dbState.llm_provider), model=$($dbState.llm_model), base_url=$configuredLlmBaseUrl"
            }

            $configuredEmbeddingBaseUrl = ([string]$dbState.embedding_base_url).TrimEnd("/")
            if ($dbState.embedding_provider -eq "local_openai" -and $dbState.embedding_model -eq $EmbeddingModel -and $configuredEmbeddingBaseUrl -eq $expectedLlmBaseUrl -and $dbState.pgvector_dimension -eq $ExpectedEmbeddingDimension) {
                Write-Check "PASS" "앱 embedding 설정: local_openai / $EmbeddingModel / dimension=$($dbState.pgvector_dimension)"
            }
            else {
                Write-Check "FAIL" "앱 embedding 설정이 preflight 대상과 다릅니다: provider=$($dbState.embedding_provider), model=$($dbState.embedding_model), base_url=$configuredEmbeddingBaseUrl, dimension=$($dbState.pgvector_dimension)"
            }

            if ($dbState.neo4j_enabled) {
                Write-Check "PASS" "앱 Neo4j 설정: enabled"
            }
            else {
                Write-Check "FAIL" "앱 Neo4j 설정이 disabled 상태입니다."
            }

            if ($dbState.program_count -eq 8 -and $dbState.commit_count -eq 48) {
                Write-Check "PASS" "저장 분석 데이터: program=8, commit=48"
            }
            else {
                Write-Check "FAIL" "저장 분석 데이터 수가 기준과 다릅니다: program=$($dbState.program_count), commit=$($dbState.commit_count)"
            }

            if ($dbState.analyzed_commit_count -eq $dbState.commit_count) {
                Write-Check "PASS" "Mapping 분석 완료 commit: $($dbState.analyzed_commit_count)/$($dbState.commit_count)"
            }
            else {
                Write-Check "FAIL" "Mapping 분석 미완료 commit이 있습니다: $($dbState.analyzed_commit_count)/$($dbState.commit_count)"
            }

            if ($dbState.source_count -ge 79 -and $dbState.vector_count -eq $dbState.source_count) {
                Write-Check "PASS" "현재 소스 검색 준비: $($dbState.vector_count)/$($dbState.source_count), profile=$($dbState.embedding_storage_key)"
            }
            else {
                Write-Check "FAIL" "현재 소스 검색 준비가 부족합니다: vector=$($dbState.vector_count), source=$($dbState.source_count)"
            }

            if ($dbState.graph_status -eq "completed" -and $dbState.graph_node_count -ge 200 -and $dbState.graph_edge_count -ge 500) {
                Write-Check "PASS" "Knowledge Graph 저장 상태: node=$($dbState.graph_node_count), edge=$($dbState.graph_edge_count)"
            }
            else {
                Write-Check "FAIL" "Knowledge Graph 상태를 확인하세요: status=$($dbState.graph_status), node=$($dbState.graph_node_count), edge=$($dbState.graph_edge_count)"
            }

            $chatEvidenceReady = -not $dbState.chat_insufficient -and $dbState.chat_source_count -ge 6 -and $dbState.chat_graph_count -ge 4
            $chatOutputVerified = -not $dbState.chat_fallback -or $dbState.chat_validation -eq "deterministic_repair"
            if ($chatEvidenceReady -and $chatOutputVerified) {
                Write-Check "PASS" "저장 Project Chat #$($dbState.chat_session_id): source=$($dbState.chat_source_count), graph=$($dbState.chat_graph_count), validation=$($dbState.chat_validation), fallback=$($dbState.chat_fallback)"
            }
            else {
                Write-Check "FAIL" "저장 Project Chat 결과를 확인하세요: session=$($dbState.chat_session_id), source=$($dbState.chat_source_count), graph=$($dbState.chat_graph_count), validation=$($dbState.chat_validation), fallback=$($dbState.chat_fallback)"
            }

            if ($dbState.review_status -eq "completed" -and ([string]$dbState.review_target).StartsWith("2325182") -and $dbState.review_bug_count -ge 1) {
                Write-Check "PASS" "저장 AI Code Review: target=2325182, bug finding=$($dbState.review_bug_count)"
            }
            else {
                Write-Check "FAIL" "저장 AI Code Review 결과를 확인하세요: target=$($dbState.review_target), status=$($dbState.review_status), bug=$($dbState.review_bug_count)"
            }

            if ($repoHead -and $dbState.stored_analysis_head -and $repoHead -ne $dbState.stored_analysis_head) {
                Write-Check "WARN" "저장 Mapping 스냅샷 HEAD와 현재 샘플 저장소 HEAD가 다릅니다. 시연 중 Git 동기화/Mapping 재실행은 누르지 마세요."
            }
            elseif ($repoHead -and $dbState.stored_analysis_head) {
                Write-Check "PASS" "저장 분석 HEAD와 샘플 저장소 HEAD가 일치합니다: $($repoHead.Substring(0, 12))"
            }
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
if ($script:FailureCount -gt 0) {
    Write-Host "사전 점검 실패: FAIL=$($script:FailureCount), WARN=$($script:WarningCount)" -ForegroundColor Red
    exit 1
}

Write-Host "사전 점검 통과: FAIL=0, WARN=$($script:WarningCount)" -ForegroundColor Green
if ($script:WarningCount -gt 0) {
    Write-Host "WARN 항목을 읽고 시연 동선을 그대로 지키세요." -ForegroundColor Yellow
}
exit 0
