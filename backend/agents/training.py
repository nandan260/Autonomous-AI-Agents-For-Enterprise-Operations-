from .state import AgentState
from ..db.models import TrainingTaskRecord
from ..db.session import SessionLocal
from ..services.audit import log_activity
from ..services.mock_external_apis import MockHRMS


def training_agent(state: AgentState) -> AgentState:
    """Agent 4: Assigns learning curriculum, Day 1 orientation checklist, and compliance modules."""
    employee_id = state.get("employee_id", "EMP-TEMP")
    employee_name = state.get("employee_name", "Jane Doe")
    department = state.get("department", "Engineering")

    audit_log = list(state.get("audit_log") or [])

    audit_log.append(f"[Training & Orientation] Generating learning path for {employee_name} ({department})")
    log_activity(employee_id, f"Training curriculum assignment initiated for {employee_name}", "Training", "info")

    courses = MockHRMS.get_courses(department)
    audit_log.append(f"  ↳ Assigned {len(courses)} department courses: {', '.join(courses)}")

    day1_tasks = MockHRMS.get_day1_tasks(department)
    audit_log.append(f"  ↳ Enrolled employee in {len(day1_tasks)} Day 1 orientation checklist items")

    session = SessionLocal()
    try:
        # Clear any prior unstarted tasks and insert clean list
        session.query(TrainingTaskRecord).where(TrainingTaskRecord.employee_id == employee_id).delete()
        for t in day1_tasks:
            session.add(
                TrainingTaskRecord(
                    employee_id=employee_id,
                    title=t["title"],
                    category=t.get("type", "Orientation"),
                    priority=t.get("priority", "medium"),
                    status="Pending",
                )
            )
        session.commit()
    except Exception as e:
        session.rollback()
        audit_log.append(f"[Training DB Error] {e}")
    finally:
        session.close()

    log_activity(
        employee_id,
        f"Training modules & orientation schedule confirmed ({len(courses)} courses)",
        "Training",
        "success",
    )
    audit_log.append("  ↳ Orientation schedule synced with employee calendar")

    return {
        **state,
        "training_assigned": True,
        "training_tasks": day1_tasks,
        "audit_log": audit_log,
    }
