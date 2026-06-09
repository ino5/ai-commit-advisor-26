from datetime import date, datetime

from pgvector.sqlalchemy import Vector

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
    last_synced_commit_hash: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    programs: Mapped[list["Program"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    git_commits: Mapped[list["GitCommit"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    standard_terms: Mapped[list["StandardTerm"]] = relationship(back_populates="project", cascade="all, delete-orphan")


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
