from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import false, func, or_
from sqlalchemy.orm import Session

from src.db.models import (
    AnalysisRun,
    AIInvocationLog,
    CodeReviewResult,
    CommitFile,
    Developer,
    DocumentChunk,
    GitCommit,
    Program,
    ProgramCommitMapping,
    ProgramImplementationStatus,
    PLBriefingHistory,
    Project,
    ProjectDeveloper,
    ProjectChatMessage,
    ProjectChatSession,
    ResourceMetricSnapshot,
    RiskFinding,
    StandardTerm,
    VectorItem,
)


@dataclass(frozen=True)
class ProjectDeleteImpact:
    project_id: int
    project_name: str
    program_count: int = 0
    git_commit_count: int = 0
    commit_file_count: int = 0
    mapping_count: int = 0
    analysis_run_count: int = 0
    implementation_status_count: int = 0
    risk_finding_count: int = 0
    code_review_count: int = 0
    resource_metric_snapshot_count: int = 0
    pl_briefing_count: int = 0
    ai_invocation_log_count: int = 0
    chat_session_count: int = 0
    chat_message_count: int = 0
    document_chunk_count: int = 0
    vector_item_count: int = 0
    standard_term_count: int = 0
    project_developer_count: int = 0
    developer_count: int = 0

    @property
    def project_owned_total(self) -> int:
        return (
            self.program_count
            + self.git_commit_count
            + self.commit_file_count
            + self.mapping_count
            + self.analysis_run_count
            + self.implementation_status_count
            + self.risk_finding_count
            + self.code_review_count
            + self.resource_metric_snapshot_count
            + self.pl_briefing_count
            + self.ai_invocation_log_count
            + self.chat_session_count
            + self.chat_message_count
            + self.document_chunk_count
            + self.vector_item_count
            + self.standard_term_count
            + self.project_developer_count
        )


@dataclass(frozen=True)
class ProjectResetImpact:
    project_id: int
    project_name: str
    preserved_program_count: int = 0
    preserved_standard_term_count: int = 0
    preserved_project_developer_count: int = 0
    git_commit_count: int = 0
    commit_file_count: int = 0
    mapping_count: int = 0
    analysis_run_count: int = 0
    implementation_status_count: int = 0
    risk_finding_count: int = 0
    code_review_count: int = 0
    resource_metric_snapshot_count: int = 0
    pl_briefing_count: int = 0
    ai_invocation_log_count: int = 0
    chat_session_count: int = 0
    chat_message_count: int = 0
    document_chunk_count: int = 0
    vector_item_count: int = 0

    @property
    def resettable_total(self) -> int:
        return (
            self.git_commit_count
            + self.commit_file_count
            + self.mapping_count
            + self.analysis_run_count
            + self.implementation_status_count
            + self.risk_finding_count
            + self.code_review_count
            + self.resource_metric_snapshot_count
            + self.pl_briefing_count
            + self.ai_invocation_log_count
            + self.chat_session_count
            + self.chat_message_count
            + self.document_chunk_count
            + self.vector_item_count
        )


def _project_program_ids(db: Session, project_id: int) -> list[int]:
    return [int(row[0]) for row in db.query(Program.id).filter(Program.project_id == project_id).all()]


def _project_commit_ids(db: Session, project_id: int) -> list[int]:
    return [int(row[0]) for row in db.query(GitCommit.id).filter(GitCommit.project_id == project_id).all()]


def _project_chat_session_ids(db: Session, project_id: int) -> list[int]:
    return [int(row[0]) for row in db.query(ProjectChatSession.id).filter(ProjectChatSession.project_id == project_id).all()]


def _project_chunk_ids(db: Session, project_id: int) -> list[int]:
    return [int(row[0]) for row in db.query(DocumentChunk.id).filter(DocumentChunk.project_id == project_id).all()]


def _mapping_project_filter(program_ids: list[int], commit_ids: list[int]):
    filters = []
    if program_ids:
        filters.append(ProgramCommitMapping.program_id.in_(program_ids))
    if commit_ids:
        filters.append(ProgramCommitMapping.commit_id.in_(commit_ids))
    return or_(*filters) if filters else false()


def _clear_external_project_graph(project_id: int) -> None:
    try:
        from src.services.neo4j_graph_service import clear_project_graph

        clear_project_graph(project_id)
    except Exception:
        # Project reset/delete must not fail because the optional graph read model is unavailable.
        return


def get_project_delete_impact(db: Session, project_id: int) -> ProjectDeleteImpact | None:
    project = db.get(Project, project_id)
    if project is None:
        return None

    program_ids = _project_program_ids(db, project_id)
    commit_ids = _project_commit_ids(db, project_id)
    chat_session_ids = _project_chat_session_ids(db, project_id)
    chunk_ids = _project_chunk_ids(db, project_id)

    return ProjectDeleteImpact(
        project_id=int(project.id),
        project_name=project.name,
        program_count=db.query(Program).filter(Program.project_id == project_id).count(),
        git_commit_count=db.query(GitCommit).filter(GitCommit.project_id == project_id).count(),
        commit_file_count=(
            db.query(CommitFile)
            .filter(
                or_(
                    CommitFile.commit_id.in_(commit_ids) if commit_ids else false(),
                    CommitFile.git_commit_id.in_(commit_ids) if commit_ids else false(),
                )
            )
            .count()
        ),
        mapping_count=(
            db.query(ProgramCommitMapping)
            .filter(_mapping_project_filter(program_ids, commit_ids))
            .count()
        ),
        analysis_run_count=db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).count(),
        implementation_status_count=(
            db.query(ProgramImplementationStatus)
            .filter(ProgramImplementationStatus.program_id.in_(program_ids) if program_ids else false())
            .count()
        ),
        risk_finding_count=db.query(RiskFinding).filter(RiskFinding.project_id == project_id).count(),
        code_review_count=db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).count(),
        resource_metric_snapshot_count=(
            db.query(ResourceMetricSnapshot).filter(ResourceMetricSnapshot.project_id == project_id).count()
        ),
        pl_briefing_count=db.query(PLBriefingHistory).filter(PLBriefingHistory.project_id == project_id).count(),
        ai_invocation_log_count=db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).count(),
        chat_session_count=db.query(ProjectChatSession).filter(ProjectChatSession.project_id == project_id).count(),
        chat_message_count=(
            db.query(ProjectChatMessage)
            .filter(ProjectChatMessage.session_id.in_(chat_session_ids) if chat_session_ids else false())
            .count()
        ),
        document_chunk_count=db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).count(),
        vector_item_count=(
            db.query(VectorItem).filter(VectorItem.chunk_id.in_(chunk_ids) if chunk_ids else false()).count()
        ),
        standard_term_count=db.query(StandardTerm).filter(StandardTerm.project_id == project_id).count(),
        project_developer_count=db.query(ProjectDeveloper).filter(ProjectDeveloper.project_id == project_id).count(),
        developer_count=db.query(func.count(Developer.id)).scalar() or 0,
    )


def get_project_reset_impact(db: Session, project_id: int) -> ProjectResetImpact | None:
    project = db.get(Project, project_id)
    if project is None:
        return None

    program_ids = _project_program_ids(db, project_id)
    commit_ids = _project_commit_ids(db, project_id)
    chat_session_ids = _project_chat_session_ids(db, project_id)
    chunk_ids = _project_chunk_ids(db, project_id)

    return ProjectResetImpact(
        project_id=int(project.id),
        project_name=project.name,
        preserved_program_count=db.query(Program).filter(Program.project_id == project_id).count(),
        preserved_standard_term_count=db.query(StandardTerm).filter(StandardTerm.project_id == project_id).count(),
        preserved_project_developer_count=(
            db.query(ProjectDeveloper).filter(ProjectDeveloper.project_id == project_id).count()
        ),
        git_commit_count=db.query(GitCommit).filter(GitCommit.project_id == project_id).count(),
        commit_file_count=(
            db.query(CommitFile)
            .filter(
                or_(
                    CommitFile.commit_id.in_(commit_ids) if commit_ids else false(),
                    CommitFile.git_commit_id.in_(commit_ids) if commit_ids else false(),
                )
            )
            .count()
        ),
        mapping_count=(
            db.query(ProgramCommitMapping)
            .filter(_mapping_project_filter(program_ids, commit_ids))
            .count()
        ),
        analysis_run_count=db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).count(),
        implementation_status_count=(
            db.query(ProgramImplementationStatus)
            .filter(ProgramImplementationStatus.program_id.in_(program_ids) if program_ids else false())
            .count()
        ),
        risk_finding_count=db.query(RiskFinding).filter(RiskFinding.project_id == project_id).count(),
        code_review_count=db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).count(),
        resource_metric_snapshot_count=(
            db.query(ResourceMetricSnapshot).filter(ResourceMetricSnapshot.project_id == project_id).count()
        ),
        pl_briefing_count=db.query(PLBriefingHistory).filter(PLBriefingHistory.project_id == project_id).count(),
        ai_invocation_log_count=db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).count(),
        chat_session_count=db.query(ProjectChatSession).filter(ProjectChatSession.project_id == project_id).count(),
        chat_message_count=(
            db.query(ProjectChatMessage)
            .filter(ProjectChatMessage.session_id.in_(chat_session_ids) if chat_session_ids else false())
            .count()
        ),
        document_chunk_count=db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).count(),
        vector_item_count=(
            db.query(VectorItem).filter(VectorItem.chunk_id.in_(chunk_ids) if chunk_ids else false()).count()
        ),
    )


def reset_project_analysis_data(db: Session, project_id: int) -> ProjectResetImpact | None:
    impact = get_project_reset_impact(db, project_id)
    if impact is None:
        return None

    program_ids = _project_program_ids(db, project_id)
    commit_ids = _project_commit_ids(db, project_id)
    chat_session_ids = _project_chat_session_ids(db, project_id)
    chunk_ids = _project_chunk_ids(db, project_id)

    if chat_session_ids:
        db.query(ProjectChatMessage).filter(ProjectChatMessage.session_id.in_(chat_session_ids)).delete(
            synchronize_session=False
        )
    if chunk_ids:
        db.query(VectorItem).filter(VectorItem.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
    if program_ids or commit_ids:
        db.query(ProgramCommitMapping).filter(_mapping_project_filter(program_ids, commit_ids)).delete(
            synchronize_session=False
        )
    if program_ids:
        db.query(ProgramImplementationStatus).filter(ProgramImplementationStatus.program_id.in_(program_ids)).delete(
            synchronize_session=False
        )
    if commit_ids:
        db.query(CommitFile).filter(
            or_(CommitFile.commit_id.in_(commit_ids), CommitFile.git_commit_id.in_(commit_ids))
        ).delete(synchronize_session=False)

    db.query(RiskFinding).filter(RiskFinding.project_id == project_id).delete(synchronize_session=False)
    db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).delete(synchronize_session=False)
    db.query(ResourceMetricSnapshot).filter(ResourceMetricSnapshot.project_id == project_id).delete(
        synchronize_session=False
    )
    db.query(PLBriefingHistory).filter(PLBriefingHistory.project_id == project_id).delete(synchronize_session=False)
    db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectChatSession).filter(ProjectChatSession.project_id == project_id).delete(synchronize_session=False)
    db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).delete(synchronize_session=False)
    db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).delete(synchronize_session=False)
    db.query(GitCommit).filter(GitCommit.project_id == project_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.id == project_id).update(
        {
            Project.last_synced_commit_hash: None,
            Project.last_synced_at: None,
        },
        synchronize_session=False,
    )
    db.commit()
    _clear_external_project_graph(project_id)
    return impact


def delete_project(db: Session, project_id: int) -> ProjectDeleteImpact | None:
    impact = get_project_delete_impact(db, project_id)
    if impact is None:
        return None

    program_ids = _project_program_ids(db, project_id)
    commit_ids = _project_commit_ids(db, project_id)
    chat_session_ids = _project_chat_session_ids(db, project_id)
    chunk_ids = _project_chunk_ids(db, project_id)

    if chat_session_ids:
        db.query(ProjectChatMessage).filter(ProjectChatMessage.session_id.in_(chat_session_ids)).delete(
            synchronize_session=False
        )
    if chunk_ids:
        db.query(VectorItem).filter(VectorItem.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
    if program_ids or commit_ids:
        db.query(ProgramCommitMapping).filter(_mapping_project_filter(program_ids, commit_ids)).delete(
            synchronize_session=False
        )
    if program_ids:
        db.query(ProgramImplementationStatus).filter(ProgramImplementationStatus.program_id.in_(program_ids)).delete(
            synchronize_session=False
        )
    if commit_ids:
        db.query(CommitFile).filter(
            or_(CommitFile.commit_id.in_(commit_ids), CommitFile.git_commit_id.in_(commit_ids))
        ).delete(synchronize_session=False)

    db.query(RiskFinding).filter(RiskFinding.project_id == project_id).delete(synchronize_session=False)
    db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).delete(synchronize_session=False)
    db.query(ResourceMetricSnapshot).filter(ResourceMetricSnapshot.project_id == project_id).delete(
        synchronize_session=False
    )
    db.query(PLBriefingHistory).filter(PLBriefingHistory.project_id == project_id).delete(synchronize_session=False)
    db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectChatSession).filter(ProjectChatSession.project_id == project_id).delete(synchronize_session=False)
    db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).delete(synchronize_session=False)
    db.query(StandardTerm).filter(StandardTerm.project_id == project_id).delete(synchronize_session=False)
    db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).delete(synchronize_session=False)
    db.query(GitCommit).filter(GitCommit.project_id == project_id).delete(synchronize_session=False)
    db.query(Program).filter(Program.project_id == project_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)
    db.commit()
    _clear_external_project_graph(project_id)
    return impact
