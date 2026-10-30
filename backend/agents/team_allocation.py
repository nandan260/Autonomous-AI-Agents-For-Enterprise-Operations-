import json
import uuid
from datetime import datetime

from .state import AgentState
from ..db.models import ApprovalRequest, Employee
from ..db.session import SessionLocal
from ..services.audit import log_activity
from ..services.mock_external_apis import (
    MockHRMS,
    SYNTHETIC_EMPLOYEES,
    uid,
)


def team_allocation_agent(state: AgentState) -> AgentState:
    """Agent 3: Assigns team, desk, reporting manager, buddy, Slack channels, and schedules Day 1."""
    employee_id = state.get("employee_id", "EMP-TEMP")
    employee_name = state.get("employee_name", "Jane Doe")
    department = state.get("department", "Engineering")

    audit_log = list(state.get("audit_log") or [])
    pending = list(state.get("pending_approvals") or [])

    audit_log.append(f"[Team Allocation] Allocating team & organizational hierarchy for {employee_name}")
    log_activity(employee_id, f"Team Allocation initiated for {employee_name}", "Team Allocation", "info")

    # Match or derive manager and buddy based on department
    matched_profile = next((e for e in SYNTHETIC_EMPLOYEES if e["department"].lower() == department.lower()), None)
    manager_name = matched_profile["manager"] if matched_profile else "Priya Sharma"
    buddy_name = matched_profile["buddy"] if matched_profile else "Rohan Verma"
    team_name = matched_profile["team"] if matched_profile else f"{department} Core Team"

    # Desk allocation
    desk_location = MockHRMS.get_desk(department)
    audit_log.append(f"  ↳ Team: {team_name} | Assigned Desk: {desk_location}")

    # Manager & Buddy
    audit_log.append(f"  ↳ Reporting Manager: {manager_name}")
    audit_log.append(f"  ↳ Peer Buddy Assigned: {buddy_name}")

    # Slack Channels
    slack_channels = MockHRMS.get_slack_channels(department)
    audit_log.append(f"  ↳ Joined {len(slack_channels)} Slack channels: {', '.join(slack_channels)}")

    # Day 1 Tasks & Calendar
    day1_tasks = MockHRMS.get_day1_tasks(department)
    audit_log.append(f"  ↳ Generated {len(day1_tasks)} tailored Day 1 tasks & blocked manager 1-on-1 slot")

    team_summary = {
        "team": team_name,
        "desk": desk_location,
        "manager": manager_name,
        "buddy": buddy_name,
        "slack_channels": slack_channels,
        "day1_tasks": day1_tasks,
    }

    session = SessionLocal()
    is_approved = False
    approval_id = f"APP-TM-{uid(4)}"
    try:
        emp = session.get(Employee, employee_id)
        if emp:
            emp.team = team_name
            emp.manager = manager_name
            emp.buddy = buddy_name
            emp.desk = desk_location

        existing_approval = session.query(ApprovalRequest).filter(
            ApprovalRequest.employee_id == employee_id,
            ApprovalRequest.approval_type == "Team Allocation",
        ).first()

        if existing_approval and existing_approval.status == "Approved":
            is_approved = True
            approval_id = existing_approval.approval_id
        elif state.get("team_approved", False):
            is_approved = True
            approval_id = existing_approval.approval_id if existing_approval else approval_id
        else:
            is_approved = False
            if existing_approval:
                approval_id = existing_approval.approval_id
            else:
                session.add(
                    ApprovalRequest(
                        approval_id=approval_id,
                        employee_id=employee_id,
                        agent="Team Allocation Agent",
                        approval_type="Team Allocation",
                        title=f"Manager Confirmation - {employee_name}",
                        description=(
                            f"Reporting Manager ({manager_name}) confirmation required for {employee_name}'s "
                            f"assignment to {team_name}, paired with {buddy_name}."
                        ),
                        checklist=json.dumps([
                            "Employee role matches team requirements",
                            "Department and team bandwidth confirmed",
                            f"Buddy ({buddy_name}) availability verified",
                            "Day 1 calendar 1-on-1 slot acknowledged",
                        ]),
                        status="Pending",
                    )
                )

        session.commit()
    except Exception as e:
        session.rollback()
        audit_log.append(f"[Team Allocation DB Error] {e}")
    finally:
        session.close()

    if not is_approved:
        if approval_id not in pending:
            pending.append(approval_id)
        audit_log.append(f"[HITL CHECKPOINT PAUSE] Pipeline paused: Manager ({manager_name}) confirmation required [Request #{approval_id}]")
        log_activity(
            employee_id,
            f"Pipeline paused at Team Gate ({approval_id}): Waiting for {manager_name} confirmation",
            "Team Allocation",
            "warning",
        )
        return {
            **state,
            "team_allocated": False,
            "is_paused": True,
            "paused_reason": f"Reporting Manager ({manager_name}) Confirmation Required",
            "active_checkpoint": {
                "approval_id": approval_id,
                "agent": "Team Allocation Agent",
                "approval_type": "Team Allocation",
                "task": "team_allocation",
                "title": f"Manager Confirmation - {employee_name}",
                "description": f"Reporting Manager ({manager_name}) confirmation required for {employee_name}'s assignment to {team_name}, paired with {buddy_name}.",
                "manager": manager_name,
                "buddy": buddy_name,
                "team": team_name,
                "desk": desk_location,
                "checklist": [
                    "Employee role matches team requirements",
                    "Department and team bandwidth confirmed",
                    f"Buddy ({buddy_name}) availability verified",
                    "Day 1 calendar 1-on-1 slot acknowledged",
                ],
            },
            "team_info": team_summary,
            "manager_name": manager_name,
            "buddy_name": buddy_name,
            "audit_log": audit_log,
            "pending_approvals": pending,
        }

    # If approved, proceed cleanly!
    audit_log.append(f"  ✅ [CONFIRMED] Reporting Manager ({manager_name}) confirmed team placement [Request #{approval_id}]")
    log_activity(employee_id, f"Team allocation confirmed ({approval_id}) by {manager_name}", "Team Allocation", "success")
    return {
        **state,
        "team_allocated": True,
        "is_paused": False,
        "paused_reason": "",
        "active_checkpoint": {},
        "team_info": team_summary,
        "manager_name": manager_name,
        "buddy_name": buddy_name,
        "audit_log": audit_log,
        "pending_approvals": [p for p in pending if p != approval_id],
    }
