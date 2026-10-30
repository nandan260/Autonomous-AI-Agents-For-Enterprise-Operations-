import json
from datetime import datetime
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_database_url
from .models import ApprovalRequest, Base, Employee, ITAssetRecord, OnboardingTask, TrainingTaskRecord
from ..services.mock_external_apis import (
    SYNTHETIC_EMPLOYEES,
    MockHRMS,
    MockLaptopAPI,
    MockSoftwareAPI,
    uid,
)

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        db_url = get_database_url()
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def SessionLocal() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _SessionLocal()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def seed_initial_data(session: Session) -> None:
    """Pre-load rich synthetic demo employees and onboarding tasks if empty."""
    existing_count = session.query(Employee).count()
    if existing_count > 0:
        return

    print("[Database] Seeding synthetic employees and demo records...")
    for emp_data in SYNTHETIC_EMPLOYEES:
        emp = Employee(
            employee_id=emp_data["id"],
            employee_name=emp_data["name"],
            email=emp_data["email"],
            department=emp_data["department"],
            role=emp_data["role"],
            joining_date=emp_data["joiningDate"],
            salary=emp_data.get("salary", "₹18,00,000 CTC"),
            manager=emp_data.get("manager", "Priya Sharma"),
            buddy=emp_data.get("buddy", "Rohan Verma"),
            team=emp_data.get("team", "Platform Team"),
            desk=MockHRMS.get_desk(emp_data["department"]),
            avatar=emp_data.get("avatar", "EP"),
            avatar_color=emp_data.get("avatarColor", "#6366f1"),
            onboarding_status="in_progress",
        )
        session.add(emp)
        session.flush()

        # Seed standard onboarding tasks
        tasks = [
            ("document_verification", "completed" if emp_data["id"] == "EMP-2024-001" else "pending"),
            ("it_provisioning", "completed" if emp_data["id"] == "EMP-2024-001" else "pending"),
            ("team_allocation", "completed" if emp_data["id"] == "EMP-2024-001" else "pending"),
            ("training", "in_progress" if emp_data["id"] == "EMP-2024-001" else "pending"),
        ]
        for task_name, status in tasks:
            session.add(
                OnboardingTask(
                    employee_id=emp_data["id"],
                    task_name=task_name,
                    status=status,
                )
            )

        # Seed IT asset record
        laptop = MockLaptopAPI.select_spec(emp_data["department"])
        softwares = MockSoftwareAPI.get_software_list(emp_data["department"])
        session.add(
            ITAssetRecord(
                employee_id=emp_data["id"],
                email_account=emp_data["email"],
                laptop_model=laptop["model"],
                laptop_specs=json.dumps(laptop),
                laptop_ticket_id=f"HW-{uid(6)}",
                master_ticket_id=f"TKT-IT-{uid(6)}",
                software_licenses=json.dumps(softwares),
                status="provisioned",
            )
        )

        # Seed Day 1 Training Tasks
        day1_tasks = MockHRMS.get_day1_tasks(emp_data["department"])
        for i, t in enumerate(day1_tasks[:5]):
            session.add(
                TrainingTaskRecord(
                    employee_id=emp_data["id"],
                    title=t["title"],
                    category=t.get("type", "Orientation"),
                    priority=t.get("priority", "medium"),
                    status="Completed" if (emp_data["id"] == "EMP-2024-001" and i < 2) else "Pending",
                )
            )

    # Seed demo approval requests
    demo_approvals = [
        {
            "approval_id": "APP-IT-101",
            "employee_id": "EMP-2024-002",
            "agent": "IT Provisioning Agent",
            "approval_type": "IT Access",
            "title": "Hardware & Systems Access Sign-Off",
            "description": "IT Manager sign-off required for Sneha Patel (Product Designer) — MacBook Air M2, Wacom Tablet, Figma Pro & Slack Pro.",
            "checklist": json.dumps([
                "Hardware procurement verified",
                "Role-appropriate permissions assigned",
                "MFA enrollment link dispatched",
                "Security training acknowledged",
            ]),
            "status": "Pending",
        },
        {
            "approval_id": "APP-TM-102",
            "employee_id": "EMP-2024-003",
            "agent": "Team Allocation Agent",
            "approval_type": "Team Allocation",
            "title": "Manager Confirmation — Rahul Gupta",
            "description": "Reporting manager (Deepa Krishnan) confirmation for Financial Planning & Analysis team assignment, buddy pairing, and Day 1 schedule.",
            "checklist": json.dumps([
                "Team capacity verified",
                "Buddy availability confirmed (Meera Nair)",
                "Desk allocation inspected (4th Floor North Wing)",
                "Day 1 calendar 1-on-1 scheduled",
            ]),
            "status": "Pending",
        },
        {
            "approval_id": "APP-DOC-103",
            "employee_id": "EMP-2024-004",
            "agent": "Document Verification Agent",
            "approval_type": "Document Review",
            "title": "HR Compliance Review — Divya Nair",
            "description": "HR Specialist approval for degree certificate and experience documents verification.",
            "checklist": json.dumps([
                "Aadhaar & PAN identity confirmed",
                "Educational degree validated",
                "Signed offer letter verified",
                "Bank details penny-drop test verified",
            ]),
            "status": "Pending",
        },
    ]

    for app in demo_approvals:
        session.add(
            ApprovalRequest(
                approval_id=app["approval_id"],
                employee_id=app["employee_id"],
                agent=app["agent"],
                approval_type=app["approval_type"],
                title=app["title"],
                description=app["description"],
                checklist=app["checklist"],
                status=app["status"],
            )
        )

    session.commit()
    print("[Database] Seeding completed successfully.")


def init_db() -> None:
    """Create all tables and seed initial demo data."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_initial_data(session)
    finally:
        session.close()
