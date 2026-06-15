from datetime import date, datetime

from pgvector.sqlalchemy import Vector

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base
from src.utils.config import settings


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    git_repo_path: Mapped[str | None] = mapped_column(Text)
    git_remote_url: Mapped[str | None] = mapped_column(Text)
    git_branch: Mapped[str | None] = mapped_column(String(255))
    last_synced_commit_hash: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    programs: Mapped[list["Program"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    git_commits: Mapped[list["GitCommit"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    standard_terms: Mapped[list["StandardTerm"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    project_developers: Mapped[list["ProjectDeveloper"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    resource_metric_snapshots: Mapped[list["ResourceMetricSnapshot"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    pl_briefings: Mapped[list["PLBriefingHistory"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    ai_invocation_logs: Mapped[list["AIInvocationLog"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    chat_sessions: Mapped[list["ProjectChatSession"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    graph_sync_state: Mapped["ProjectGraphSyncState | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ProjectGraphSyncState(Base, TimestampMixin):
    __tablename__ = "project_graph_sync_state"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_graph_sync_state_project_id"),
        Index("ix_project_graph_sync_state_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    repo_head_hash: Mapped[str | None] = mapped_column(String(64))
    db_sync_head_hash: Mapped[str | None] = mapped_column(String(64))
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_mode: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_commit_db_id: Mapped[int | None] = mapped_column(Integer)
    last_mapping_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="graph_sync_state")


class Developer(Base, TimestampMixin):
    __tablename__ = "developers"
    __table_args__ = (
        UniqueConstraint("developer_id", name="uq_developers_developer_id"),
        UniqueConstraint("developer_key", name="uq_developers_developer_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    developer_key: Mapped[str] = mapped_column(String(255), nullable=False)
    developer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    developer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(255))
    skills: Mapped[str | None] = mapped_column(Text)

    programs: Mapped[list["Program"]] = relationship(back_populates="assigned_developer")
    project_memberships: Mapped[list["ProjectDeveloper"]] = relationship(
        back_populates="developer",
        cascade="all, delete-orphan",
    )


class ProjectDeveloper(Base, TimestampMixin):
    __tablename__ = "project_developers"
    __table_args__ = (
        UniqueConstraint("project_id", "developer_id", name="uq_project_developers_project_developer"),
    )
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    developer_id: Mapped[str] = mapped_column(ForeignKey("developers.developer_id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    project_role: Mapped[str | None] = mapped_column(String(255))
    active_yn: Mapped[str] = mapped_column(String(1), default="Y", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="project_developers")
    developer: Mapped["Developer"] = relationship(back_populates="project_memberships")


class Program(Base, TimestampMixin):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[str | None] = mapped_column(String(255))
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    screen_name: Mapped[str | None] = mapped_column(String(255))
    module: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    developer: Mapped[str | None] = mapped_column(String(255))
    developer_id: Mapped[str | None] = mapped_column(ForeignKey("developers.developer_id", ondelete="SET NULL"))
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)
    progress_rate: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(String(100))
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="programs")
    assigned_developer: Mapped["Developer | None"] = relationship(back_populates="programs")
    mappings: Mapped[list["ProgramCommitMapping"]] = relationship(back_populates="program", cascade="all, delete-orphan")
    implementation_status_result: Mapped["ProgramImplementationStatus | None"] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        uselist=False,
    )


class GitCommit(Base, TimestampMixin):
    __tablename__ = "git_commits"
    __table_args__ = (
        UniqueConstraint("commit_hash", name="uq_git_commits_commit_hash"),
        UniqueConstraint("project_id", "commit_hash", name="uq_git_commits_project_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    commit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_email: Mapped[str | None] = mapped_column(String(255))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_merge_commit: Mapped[bool] = mapped_column(default=False, nullable=False)
    mapping_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mapping_analysis_status: Mapped[str | None] = mapped_column(String(50))

    project: Mapped["Project"] = relationship(back_populates="git_commits")
    files: Mapped[list["CommitFile"]] = relationship(
        back_populates="commit",
        cascade="all, delete-orphan",
        foreign_keys="CommitFile.commit_id",
    )
    mappings: Mapped[list["ProgramCommitMapping"]] = relationship(back_populates="commit", cascade="all, delete-orphan")


class CommitFile(Base, TimestampMixin):
    __tablename__ = "commit_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commit_id: Mapped[int] = mapped_column(ForeignKey("git_commits.id", ondelete="CASCADE"), nullable=False)
    git_commit_id: Mapped[int | None] = mapped_column(ForeignKey("git_commits.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str | None] = mapped_column(String(50))
    diff_text: Mapped[str | None] = mapped_column(Text)

    commit: Mapped["GitCommit"] = relationship(back_populates="files", foreign_keys=[commit_id])


class ProgramCommitMapping(Base, TimestampMixin):
    __tablename__ = "program_commit_mappings"
    __table_args__ = (UniqueConstraint("program_id", "commit_id", name="uq_program_commit_mapping"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    commit_id: Mapped[int] = mapped_column(ForeignKey("git_commits.id", ondelete="CASCADE"), nullable=False)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id", ondelete="SET NULL"))
    relevance_score: Mapped[float | None] = mapped_column(Float)
    is_related: Mapped[bool | None] = mapped_column(Boolean)
    implementation_status: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    feedback_is_related: Mapped[bool | None] = mapped_column(Boolean)
    feedback_relevance_score: Mapped[float | None] = mapped_column(Float)
    feedback_implementation_status: Mapped[str | None] = mapped_column(String(100))
    feedback_reason: Mapped[str | None] = mapped_column(Text)
    feedback_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    program: Mapped["Program"] = relationship(back_populates="mappings")
    commit: Mapped["GitCommit"] = relationship(back_populates="mappings")
    analysis_run: Mapped["AnalysisRun | None"] = relationship(back_populates="mappings")


class ProgramImplementationStatus(Base, TimestampMixin):
    __tablename__ = "program_implementation_status"
    __table_args__ = (UniqueConstraint("program_id", name="uq_program_implementation_status_program_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    completed_features: Mapped[list | None] = mapped_column(JSONB)
    incomplete_features: Mapped[list | None] = mapped_column(JSONB)
    evidence_commits: Mapped[list | None] = mapped_column(JSONB)
    commit_hash_signature: Mapped[str | None] = mapped_column(String(64))
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_response: Mapped[dict | None] = mapped_column(JSONB)

    program: Mapped["Program"] = relationship(back_populates="implementation_status_result")


class AnalysisRun(Base, TimestampMixin):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    run_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    analysis_type: Mapped[str | None] = mapped_column(String(100))
    total_count: Mapped[int | None] = mapped_column(Integer)
    processed_count: Mapped[int | None] = mapped_column(Integer)
    failed_count: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="analysis_runs")
    mappings: Mapped[list["ProgramCommitMapping"]] = relationship(back_populates="analysis_run")


class CodeReviewResult(Base, TimestampMixin):
    __tablename__ = "code_review_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_ref: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    commit_analysis: Mapped[dict | None] = mapped_column(JSONB)
    bug_findings: Mapped[list | None] = mapped_column(JSONB)
    refactoring_suggestions: Mapped[list | None] = mapped_column(JSONB)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResourceMetricSnapshot(Base, TimestampMixin):
    __tablename__ = "resource_metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    snapshot_label: Mapped[str | None] = mapped_column(String(255))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    unresolved_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forecasted_delay_program_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_code_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_review_hours_saved: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    estimated_extra_mm_avoidance: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    average_workload_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    average_difficulty_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    developer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    program_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_summary: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="resource_metric_snapshots")


class PLBriefingHistory(Base, TimestampMixin):
    __tablename__ = "pl_briefing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    priority_items: Mapped[list | None] = mapped_column(JSONB)
    meeting_questions: Mapped[list | None] = mapped_column(JSONB)
    next_actions: Mapped[list | None] = mapped_column(JSONB)
    rendered_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_payload: Mapped[dict | None] = mapped_column(JSONB)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="pl_briefings")


class AIInvocationLog(Base, TimestampMixin):
    __tablename__ = "ai_invocation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str | None] = mapped_column(String(100))
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_status: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_length: Mapped[int | None] = mapped_column(Integer)
    response_length: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project | None"] = relationship(back_populates="ai_invocation_logs")


class ProjectChatSession(Base, TimestampMixin):
    __tablename__ = "project_chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ProjectChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ProjectChatMessage.message_index",
    )


class ProjectChatMessage(Base, TimestampMixin):
    __tablename__ = "project_chat_messages"
    __table_args__ = (UniqueConstraint("session_id", "message_index", name="uq_project_chat_messages_session_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("project_chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSONB)
    expanded_queries: Mapped[list | None] = mapped_column(JSONB)
    matched_terms: Mapped[list | None] = mapped_column(JSONB)
    excluded_count: Mapped[int | None] = mapped_column(Integer)
    used_source_count: Mapped[int | None] = mapped_column(Integer)
    insufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    session: Mapped["ProjectChatSession"] = relationship(back_populates="messages")


class RiskFinding(Base, TimestampMixin):
    __tablename__ = "risk_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_yn: Mapped[str] = mapped_column(String(1), default="N", nullable=False)


class StandardTerm(Base, TimestampMixin):
    __tablename__ = "standard_terms"
    __table_args__ = (
        UniqueConstraint("project_id", "korean_term", "english_term", name="uq_standard_terms_project_terms"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    term_type: Mapped[str | None] = mapped_column(String(50))
    korean_term: Mapped[str] = mapped_column(String(255), nullable=False)
    english_term: Mapped[str] = mapped_column(String(255), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    derived_keywords: Mapped[list | None] = mapped_column(JSONB)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship(back_populates="standard_terms")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    vector_items: Mapped[list["VectorItem"]] = relationship(back_populates="chunk", cascade="all, delete-orphan")


class VectorItem(Base, TimestampMixin):
    __tablename__ = "vector_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(255))
    # Dimension is controlled by PGVECTOR_DIMENSION until a production embedding model is selected.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.pgvector_dimension))
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    chunk: Mapped["DocumentChunk"] = relationship(back_populates="vector_items")
