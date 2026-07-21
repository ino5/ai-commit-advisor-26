COMMIT_MAPPING_SCHEMA = {
    "type": "object",
    "properties": {
        "related_programs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program_id": {"type": "string"},
                    "relevance_score": {"type": "number", "minimum": 0, "maximum": 100},
                    "implementation_status": {
                        "type": "string",
                        "enum": ["구현완료", "일부구현", "판단불가"],
                    },
                    "reason": {"type": "string"},
                },
                "required": ["program_id", "relevance_score", "implementation_status", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["related_programs"],
    "additionalProperties": False,
}


PAIR_MAPPING_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 100},
        "is_related": {"type": "boolean"},
        "reason": {"type": "string"},
        "implementation_status": {
            "type": "string",
            "enum": ["구현됨", "일부구현", "판단불가"],
        },
    },
    "required": ["relevance_score", "is_related", "reason", "implementation_status"],
    "additionalProperties": False,
}


PROGRAM_IMPLEMENTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "UNKNOWN"],
        },
        "summary": {"type": "string"},
        "completed_features": {"type": "array", "items": {"type": "string"}},
        "incomplete_features": {"type": "array", "items": {"type": "string"}},
        "evidence_commits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "commit_hash": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["commit_hash", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "status",
        "summary",
        "completed_features",
        "incomplete_features",
        "evidence_commits",
    ],
    "additionalProperties": False,
}


CODE_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "commit_analysis": {
            "type": "object",
            "properties": {
                "change_intent": {"type": "string"},
                "impact_scope": {
                    "type": "string",
                    "enum": ["local", "module", "cross-cutting", "unknown"],
                },
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["change_intent", "impact_scope", "risk_level"],
            "additionalProperties": False,
        },
        "bug_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "file": {"type": "string"},
                    "line": {"type": ["integer", "null"]},
                    "issue": {"type": "string"},
                    "recommendation": {"type": "string"},
                },
                "required": ["severity", "file", "line", "issue", "recommendation"],
                "additionalProperties": False,
            },
        },
        "refactoring_suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": ["integer", "null"]},
                    "suggestion": {"type": "string"},
                    "benefit": {"type": "string"},
                },
                "required": ["file", "line", "suggestion", "benefit"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "commit_analysis", "bug_findings", "refactoring_suggestions"],
    "additionalProperties": False,
}


PL_BRIEFING_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "enum": ["PL 주간 점검 브리핑"]},
        "summary": {"type": "string"},
        "priority_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program_id": {"type": "string"},
                    "program_name": {"type": "string"},
                    "reason": {"type": "string"},
                    "owner": {"type": "string"},
                },
                "required": ["program_id", "program_name", "reason", "owner"],
                "additionalProperties": False,
            },
        },
        "meeting_questions": {"type": "array", "items": {"type": "string"}},
        "next_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program_id": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["program_id", "action"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "summary", "priority_items", "meeting_questions", "next_actions"],
    "additionalProperties": False,
}
