from datetime import datetime
from ..db.models import AuditLog
from ..db.session import SessionLocal


def log_activity(
    employee_id: str,
    action: str,
    agent: str = "Orchestrator",
    status: str = "info"
) -> None:
    """Record an audit trail entry for an employee onboarding process."""
    session = SessionLocal()
    try:
        entry = AuditLog(
            employee_id=employee_id,
            agent=agent,
            action=action,
            status=status,
            timestamp=datetime.utcnow(),
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[Audit Log Error] Failed to write log: {e}")
    finally:
        session.close()
