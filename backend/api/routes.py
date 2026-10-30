import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from ..agents.monitoring import TASKS, generate_progress_report
from ..agents.orchestrator import TASK_IDS, run_onboarding
from ..agents.state import AgentState
from ..config import UPLOADS_DIR
from ..db.models import (
    ApprovalRequest,
    AuditLog,
    DocumentRecord,
    Employee,
    ITAssetRecord,
    OnboardingTask,
    TrainingTaskRecord,
)
from ..db.session import SessionLocal
from ..schemas import (
    ApprovalActionRequest,
    ApprovalItemResponse,
    AuditLogItem,
    AuditLogsResponse,
    EmployeeCreateRequest,
    EmployeeResponse,
    MonitoringReport,
    OnboardingStartRequest,
    OnboardingStatusResponse,
    TrainingTaskUpdate,
)
from ..services.audit import log_activity
from ..services.mock_external_apis import MockEmailAPI, MockHRMS

router = APIRouter(prefix="/api")
TASK_FLAGS = dict(TASKS)


def _ensure_employee(
    employee_id: str,
    employee_name: str,
    department: str = "Engineering",
    role: str = "Software Engineer",
    joining_date: str = "",
) -> Employee:
    session = SessionLocal()
    try:
        emp = session.get(Employee, employee_id)
        if emp is None:
            avatar = "".join([part[0].upper() for part in employee_name.split()[:2]]) or "EP"
            emp = Employee(
                employee_id=employee_id,
                employee_name=employee_name,
                email=MockEmailAPI.generate_address(employee_name),
                department=department,
                role=role,
                joining_date=joining_date or datetime.utcnow().strftime("%Y-%m-%d"),
                avatar=avatar,
                onboarding_status="in_progress",
            )
            session.add(emp)
            session.flush()
            for task_name in TASK_IDS:
                session.add(
                    OnboardingTask(
                        employee_id=employee_id,
                        task_name=task_name,
                        status="pending",
                    )
                )
        else:
            emp.employee_name = employee_name
            emp.department = department
            emp.role = role
            emp.onboarding_status = "in_progress"
        session.commit()
        return emp
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _save_graph_result(state: AgentState) -> None:
    session = SessionLocal()
    try:
        emp = session.get(Employee, state["employee_id"])
        if emp is None:
            return

        completed = all(bool(state.get(flag)) for _, flag in TASKS)
        emp.onboarding_status = "completed" if completed else "in_progress"

        tasks = session.scalars(
            select(OnboardingTask).where(OnboardingTask.employee_id == state["employee_id"])
        ).all()
        for t in tasks:
            flag = TASK_FLAGS.get(t.task_name)
            if flag:
                t.status = "completed" if state.get(flag) else "pending"
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _state_from_db(emp: Employee, tasks: list[OnboardingTask]) -> AgentState:
    flags = {t.task_name: t.status == "completed" for t in tasks}
    pending = [t.task_name for t in tasks if t.status != "completed"]
    return {
        "employee_id": emp.employee_id,
        "employee_name": emp.employee_name,
        "department": emp.department or "Engineering",
        "designation": emp.role or "Software Engineer",
        "joining_date": emp.joining_date or "",
        "documents_verified": flags.get("document_verification", False),
        "it_provisioned": flags.get("it_provisioning", False),
        "team_allocated": flags.get("team_allocation", False),
        "training_assigned": flags.get("training", False),
        "audit_log": [],
        "pending_approvals": pending,
    }


def _calc_progress(tasks: list[OnboardingTask]) -> int:
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.status == "completed")
    return int((done / len(tasks)) * 100)


# ── Onboarding Workflows ────────────────────────────────
@router.post("/onboarding/start", response_model=OnboardingStatusResponse)
def start_onboarding(payload: OnboardingStartRequest) -> OnboardingStatusResponse:
    emp_id = payload.employee_id or f"EMP-2024-{str(uuid.uuid4().int)[:4]}"
    _ensure_employee(
        employee_id=emp_id,
        employee_name=payload.employee_name,
        department=payload.department or "Engineering",
        role=payload.designation or "Software Engineer",
        joining_date=payload.joining_date or "",
    )

    final_state = run_onboarding(
        employee_id=emp_id,
        employee_name=payload.employee_name,
        department=payload.department or "Engineering",
        designation=payload.designation or "Software Engineer",
        joining_date=payload.joining_date or "",
        upload_folder=payload.upload_folder or str(UPLOADS_DIR),
    )
    _save_graph_result(final_state)

    session = SessionLocal()
    try:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        tasks = list(session.scalars(select(OnboardingTask).where(OnboardingTask.employee_id == emp_id)).all())
        report = generate_progress_report(final_state)
        return OnboardingStatusResponse(
            employee_id=emp.employee_id,
            employee_name=emp.employee_name,
            department=emp.department,
            designation=emp.role,
            onboarding_status=emp.onboarding_status,
            documents_verified=final_state.get("documents_verified", False),
            it_provisioned=final_state.get("it_provisioned", False),
            team_allocated=final_state.get("team_allocated", False),
            training_assigned=final_state.get("training_assigned", False),
            pending_approvals=final_state.get("pending_approvals", []),
            monitoring=MonitoringReport.model_validate(report),
        )
    finally:
        session.close()


@router.get("/onboarding/{employee_id}/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(employee_id: str) -> OnboardingStatusResponse:
    session = SessionLocal()
    try:
        emp = session.get(Employee, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        tasks = list(session.scalars(select(OnboardingTask).where(OnboardingTask.employee_id == employee_id)).all())
        state = _state_from_db(emp, tasks)
        report = generate_progress_report(state)
        return OnboardingStatusResponse(
            employee_id=emp.employee_id,
            employee_name=emp.employee_name,
            department=emp.department,
            designation=emp.role,
            onboarding_status=emp.onboarding_status,
            documents_verified=state["documents_verified"],
            it_provisioned=state["it_provisioned"],
            team_allocated=state["team_allocated"],
            training_assigned=state["training_assigned"],
            pending_approvals=state["pending_approvals"],
            monitoring=MonitoringReport.model_validate(report),
        )
    finally:
        session.close()


@router.get("/onboarding/{employee_id}/logs", response_model=AuditLogsResponse)
def get_onboarding_logs(employee_id: str) -> AuditLogsResponse:
    session = SessionLocal()
    try:
        logs = list(
            session.scalars(
                select(AuditLog)
                .where(AuditLog.employee_id == employee_id)
                .order_by(AuditLog.timestamp.desc())
            ).all()
        )
        return AuditLogsResponse(
            employee_id=employee_id,
            logs=[
                AuditLogItem(
                    log_id=e.log_id,
                    employee_id=e.employee_id,
                    agent=e.agent,
                    action=e.action,
                    status=e.status,
                    timestamp=e.timestamp,
                )
                for e in logs
            ],
        )
    finally:
        session.close()


# ── Employees ───────────────────────────────────────────
@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees() -> list[EmployeeResponse]:
    session = SessionLocal()
    try:
        employees = list(session.scalars(select(Employee).order_by(Employee.employee_id.asc())).all())
        results = []
        for emp in employees:
            tasks = list(session.scalars(select(OnboardingTask).where(OnboardingTask.employee_id == emp.employee_id)).all())
            progress = _calc_progress(tasks)
            results.append(
                EmployeeResponse(
                    employee_id=emp.employee_id,
                    employee_name=emp.employee_name,
                    email=emp.email,
                    department=emp.department,
                    role=emp.role,
                    joining_date=emp.joining_date,
                    salary=emp.salary,
                    manager=emp.manager,
                    buddy=emp.buddy,
                    team=emp.team,
                    desk=emp.desk,
                    avatar=emp.avatar,
                    avatar_color=emp.avatar_color,
                    onboarding_status=emp.onboarding_status,
                    progress=progress,
                )
            )
        return results
    finally:
        session.close()


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(payload: EmployeeCreateRequest) -> EmployeeResponse:
    emp_id = f"EMP-2024-{str(uuid.uuid4().int)[:4]}"
    emp = _ensure_employee(
        employee_id=emp_id,
        employee_name=payload.employee_name,
        department=payload.department,
        role=payload.role,
        joining_date=payload.joining_date or datetime.utcnow().strftime("%Y-%m-%d"),
    )
    return EmployeeResponse(
        employee_id=emp.employee_id,
        employee_name=emp.employee_name,
        email=emp.email,
        department=emp.department,
        role=emp.role,
        joining_date=emp.joining_date,
        salary=emp.salary,
        manager=emp.manager,
        buddy=emp.buddy,
        team=emp.team,
        desk=emp.desk,
        avatar=emp.avatar,
        avatar_color=emp.avatar_color,
        onboarding_status=emp.onboarding_status,
        progress=0,
    )


@router.get("/employees/{employee_id}")
def get_employee_detail(employee_id: str):
    session = SessionLocal()
    try:
        emp = session.get(Employee, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        tasks = list(session.scalars(select(OnboardingTask).where(OnboardingTask.employee_id == employee_id)).all())
        it_asset = session.scalars(select(ITAssetRecord).where(ITAssetRecord.employee_id == employee_id)).first()
        docs = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == employee_id)).all())
        training = list(session.scalars(select(TrainingTaskRecord).where(TrainingTaskRecord.employee_id == employee_id)).all())

        return {
            "employee": {
                "id": emp.employee_id,
                "name": emp.employee_name,
                "email": emp.email,
                "department": emp.department,
                "role": emp.role,
                "joining_date": emp.joining_date,
                "manager": emp.manager,
                "buddy": emp.buddy,
                "team": emp.team,
                "desk": emp.desk,
                "status": emp.onboarding_status,
                "progress": _calc_progress(tasks),
            },
            "tasks": [{"name": t.task_name, "status": t.status} for t in tasks],
            "it_assets": {
                "laptop_model": it_asset.laptop_model if it_asset else None,
                "specs": json.loads(it_asset.laptop_specs) if it_asset and it_asset.laptop_specs else None,
                "software": json.loads(it_asset.software_licenses) if it_asset and it_asset.software_licenses else [],
                "master_ticket": it_asset.master_ticket_id if it_asset else None,
            } if it_asset else None,
            "documents": [
                {
                    "name": d.doc_name,
                    "type": d.doc_type,
                    "readable": d.readable,
                    "name_match": d.name_match,
                    "confidence": d.confidence,
                    "llm_used": d.llm_used,
                    "issues": json.loads(d.issues) if d.issues else [],
                }
                for d in docs
            ],
            "training_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category,
                    "status": t.status,
                    "priority": t.priority,
                }
                for t in training
            ],
        }
    finally:
        session.close()


# ── Documents Upload & Verification ─────────────────────
@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    employee_id: Optional[str] = Form(None),
    doc_type: Optional[str] = Form("identity"),
):
    clean_name = os.path.basename(file.filename or f"doc_{uuid.uuid4().hex[:6]}.pdf")
    dest_path = UPLOADS_DIR / clean_name
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "filename": clean_name,
        "saved_path": str(dest_path),
        "size_bytes": os.path.getsize(dest_path),
    }


@router.get("/documents/{employee_id}")
def get_employee_documents(employee_id: str):
    session = SessionLocal()
    try:
        records = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == employee_id)).all())
        return [
            {
                "id": r.id,
                "doc_name": r.doc_name,
                "doc_type": r.doc_type,
                "readable": r.readable,
                "extracted_name": r.extracted_name,
                "name_match": r.name_match,
                "confidence": r.confidence,
                "llm_used": r.llm_used,
                "issues": json.loads(r.issues) if r.issues else [],
            }
            for r in records
        ]
    finally:
        session.close()


# ── Approvals (Human-in-the-Loop) ───────────────────────
@router.get("/approvals", response_model=list[ApprovalItemResponse])
def list_approvals(status: Optional[str] = None) -> list[ApprovalItemResponse]:
    session = SessionLocal()
    try:
        query = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
        if status:
            query = query.where(ApprovalRequest.status == status)
        items = list(session.scalars(query).all())
        results = []
        for app in items:
            emp = session.get(Employee, app.employee_id)
            checklist_items = json.loads(app.checklist) if app.checklist else []
            results.append(
                ApprovalItemResponse(
                    approval_id=app.approval_id,
                    employee_id=app.employee_id,
                    employee_name=emp.employee_name if emp else "Unknown",
                    agent=app.agent,
                    approval_type=app.approval_type,
                    title=app.title,
                    description=app.description,
                    checklist=checklist_items,
                    status=app.status,
                    approver=app.approver,
                    notes=app.notes,
                    created_at=app.created_at,
                )
            )
        return results
    finally:
        session.close()


@router.post("/approvals/{approval_id}/action")
def action_approval(approval_id: str, payload: ApprovalActionRequest):
    session = SessionLocal()
    try:
        app = session.get(ApprovalRequest, approval_id)
        if not app:
            raise HTTPException(status_code=404, detail="Approval request not found")

        app.status = payload.action
        app.approver = payload.approver or "Supervisor"
        app.notes = payload.notes
        app.resolved_at = datetime.utcnow()

        log_activity(
            app.employee_id,
            f"Human Gate [{app.approval_type}] resolved: {payload.action} by {app.approver}. Notes: {payload.notes or 'None'}",
            app.agent,
            "success" if payload.action == "Approved" else "warning",
        )
        session.commit()
        return {"status": "success", "approval_id": approval_id, "decision": payload.action}
    finally:
        session.close()


# ── Training Tasks ──────────────────────────────────────
@router.get("/training/{employee_id}/tasks")
def list_training_tasks(employee_id: str):
    session = SessionLocal()
    try:
        tasks = list(
            session.scalars(
                select(TrainingTaskRecord).where(TrainingTaskRecord.employee_id == employee_id)
            ).all()
        )
        return [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "status": t.status,
                "priority": t.priority,
            }
            for t in tasks
        ]
    finally:
        session.close()


@router.patch("/training/{employee_id}/tasks/{task_id}")
def update_training_task(employee_id: str, task_id: int, payload: TrainingTaskUpdate):
    session = SessionLocal()
    try:
        t = session.get(TrainingTaskRecord, task_id)
        if not t or t.employee_id != employee_id:
            raise HTTPException(status_code=404, detail="Task not found")
        t.status = payload.status
        session.commit()
        log_activity(
            employee_id,
            f"Training task '{t.title}' updated to {payload.status}",
            "Training",
            "info",
        )
        return {"status": "success", "task_id": task_id, "new_status": payload.status}
    finally:
        session.close()


# ── Agent System Status ─────────────────────────────────
@router.get("/agents/status")
def get_agents_status():
    return [
        {"name": "Supervisor Orchestrator", "role": "LangGraph Workflow & Routing", "status": "Active", "type": "Core"},
        {"name": "Document Verification Agent", "role": "OCR & LLM Extraction", "status": "Ready", "type": "Worker"},
        {"name": "IT Provisioning Agent", "role": "Hardware & Systems Access", "status": "Ready", "type": "Worker"},
        {"name": "Team Allocation Agent", "role": "Department & Manager Assignment", "status": "Ready", "type": "Worker"},
        {"name": "Training & Orientation Agent", "role": "LMS & Day 1 Checklist", "status": "Ready", "type": "Worker"},
        {"name": "Monitoring & Audit Agent", "role": "Progress Telemetry & Alerts", "status": "Active", "type": "Observer"},
    ]


# ── Full Pipeline Execution Endpoint ───────────────────
@router.post("/pipeline/run-full")
def run_full_pipeline(payload: OnboardingStartRequest):
    emp_id = payload.employee_id or f"EMP-2024-{str(uuid.uuid4().int)[:4]}"
    _ensure_employee(
        employee_id=emp_id,
        employee_name=payload.employee_name,
        department=payload.department or "Engineering",
        role=payload.designation or "Software Engineer",
        joining_date=payload.joining_date or "",
    )

    final_state = run_onboarding(
        employee_id=emp_id,
        employee_name=payload.employee_name,
        department=payload.department or "Engineering",
        designation=payload.designation or "Software Engineer",
        joining_date=payload.joining_date or "",
        upload_folder=payload.upload_folder or str(UPLOADS_DIR),
    )
    _save_graph_result(final_state)

    session = SessionLocal()
    try:
        emp = session.get(Employee, emp_id)
        tasks = list(session.scalars(select(OnboardingTask).where(OnboardingTask.employee_id == emp_id)).all())
        report = generate_progress_report(final_state)
        return {
            "status": "completed",
            "employee_id": emp_id,
            "employee_name": payload.employee_name,
            "department": payload.department,
            "progress": report["progress"],
            "percent": report["percent"],
            "stages": [
                {"id": "doc_verification", "name": "Document Verification", "completed": final_state.get("documents_verified", False)},
                {"id": "it_provisioning", "name": "IT Provisioning", "completed": final_state.get("it_provisioned", False)},
                {"id": "team_allocation", "name": "Team Allocation", "completed": final_state.get("team_allocated", False)},
                {"id": "training", "name": "Training & Orientation", "completed": final_state.get("training_assigned", False)},
            ],
            "audit_trail": final_state.get("audit_log", []),
            "pending_approvals": final_state.get("pending_approvals", []),
        }
    finally:
        session.close()
