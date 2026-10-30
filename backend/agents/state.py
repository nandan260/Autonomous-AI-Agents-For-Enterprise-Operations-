from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    """Unified LangGraph state for the multi-agent employee onboarding system."""

    # Core Identifiers (Member 1)
    employee_id: str
    employee_name: str
    department: str
    designation: str
    joining_date: str
    upload_folder: str

    # Agent 1: Document Verification & Registration (Member 2)
    documents_verified: bool
    doc_issues: list
    doc_results: list
    employee_email: str
    employee_profile: dict
    needs_human_review: bool

    # Agent 2: IT Provisioning (Member 3)
    it_provisioned: bool
    it_assets: dict

    # Agent 3: Team Allocation (Member 3)
    team_allocated: bool
    team_info: dict
    manager_name: str
    buddy_name: str

    # Agent 4: Training & Orientation (Member 4)
    training_assigned: bool
    training_tasks: list
    orientation_schedule: dict

    # Cross-cutting Workflow State
    audit_log: list
    pending_approvals: list


def create_initial_state(
    employee_id: str = "",
    employee_name: str = "",
    department: str = "Engineering",
    designation: str = "Software Engineer",
    joining_date: str = "",
    upload_folder: str = "",
) -> AgentState:
    """Return a complete AgentState with safe defaults."""
    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "department": department,
        "designation": designation,
        "joining_date": joining_date,
        "upload_folder": upload_folder,
        "documents_verified": False,
        "doc_issues": [],
        "doc_results": [],
        "employee_email": "",
        "employee_profile": {},
        "needs_human_review": False,
        "it_provisioned": False,
        "it_assets": {},
        "team_allocated": False,
        "team_info": {},
        "manager_name": "",
        "buddy_name": "",
        "training_assigned": False,
        "training_tasks": [],
        "orientation_schedule": {},
        "audit_log": [],
        "pending_approvals": [],
    }
