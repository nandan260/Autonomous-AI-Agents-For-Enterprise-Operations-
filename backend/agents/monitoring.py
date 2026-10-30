from .state import AgentState

TASKS: tuple[tuple[str, str], ...] = (
    ("document_verification", "documents_verified"),
    ("it_provisioning", "it_provisioned"),
    ("team_allocation", "team_allocated"),
    ("training", "training_assigned"),
)

TASK_IDS: tuple[str, ...] = tuple(task_id for task_id, _ in TASKS)


def check_completed_tasks(state: AgentState) -> list[str]:
    """Return task ids whose completion flags are True."""
    return [task_id for task_id, flag in TASKS if bool(state.get(flag))]


def identify_pending_tasks(state: AgentState) -> list[str]:
    """Return task ids that are not yet complete."""
    completed = set(check_completed_tasks(state))
    return [task_id for task_id in TASK_IDS if task_id not in completed]


def identify_pending_approvals(state: AgentState) -> list:
    """Return pending approvals already recorded on shared state."""
    return list(state.get("pending_approvals") or [])


def generate_alerts(state: AgentState) -> list[str]:
    """Build alert messages for incomplete onboarding activities or human gates."""
    employee = state.get("employee_name") or state.get("employee_id") or "unknown"
    alerts = []
    for item in identify_pending_approvals(state):
        alerts.append(f"AWAITING HUMAN APPROVAL: Request #{item} for {employee}")
    for task_id in identify_pending_tasks(state):
        alerts.append(f"ALERT: {task_id} is incomplete for {employee}")
    return alerts


def generate_progress_report(state: AgentState) -> dict:
    """Return a comprehensive onboarding progress report."""
    completed = check_completed_tasks(state)
    pending = identify_pending_tasks(state)
    approvals = identify_pending_approvals(state)
    alerts = generate_alerts(state)
    return {
        "employee_id": state.get("employee_id"),
        "employee_name": state.get("employee_name"),
        "completed_tasks": completed,
        "pending_tasks": pending,
        "pending_approvals": approvals,
        "alerts": alerts,
        "progress": f"{len(completed)}/{len(TASK_IDS)}",
        "percent": int((len(completed) / len(TASK_IDS)) * 100) if TASK_IDS else 100,
    }


def monitoring_agent(state: AgentState) -> AgentState:
    """LangGraph node: monitor progress, check human gates, and append status to the audit log."""
    report = generate_progress_report(state)
    audit_log = list(state.get("audit_log") or [])
    audit_log.append(f"[Monitoring Report] Workflow progress: {report['progress']} ({report['percent']}%)")
    if report["pending_approvals"]:
        audit_log.append(f"  ↳ {len(report['pending_approvals'])} action items require human supervisor approval")
    else:
        audit_log.append("  ↳ All onboarding workflow automation steps completed successfully!")
    return {**state, "audit_log": audit_log}
