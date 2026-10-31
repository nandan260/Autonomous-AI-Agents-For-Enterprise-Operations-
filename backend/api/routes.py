import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
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
from ..services.llm_service import extract_info_with_llm
from ..services.mock_external_apis import MockEmailAPI, MockHRMS, SYNTHETIC_EMPLOYEES
from ..services.ocr_service import (
    detect_doc_category,
    extract_text,
    find_document,
    generate_sample_pdf_pack,
)

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
            matched_profile = next((e for e in SYNTHETIC_EMPLOYEES if e["department"].lower() == (department or "Engineering").lower()), None)
            manager_name = matched_profile["manager"] if matched_profile else "Priya Sharma"
            buddy_name = matched_profile["buddy"] if matched_profile else "Rohan Verma"
            team_name = matched_profile["team"] if matched_profile else f"{department} Core Team"
            desk_loc = MockHRMS.get_desk(department)

            emp = Employee(
                employee_id=employee_id,
                employee_name=employee_name,
                email=MockEmailAPI.generate_address(employee_name),
                department=department,
                role=role,
                joining_date=joining_date or datetime.utcnow().strftime("%Y-%m-%d"),
                salary="₹18,00,000 CTC",
                manager=manager_name,
                buddy=buddy_name,
                team=team_name,
                desk=desk_loc,
                avatar=avatar,
                avatar_color="#6366f1",
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
        if completed:
            emp.onboarding_status = "completed"
        elif state.get("is_paused"):
            emp.onboarding_status = "paused_for_approval"
        else:
            emp.onboarding_status = "in_progress"

        tasks = session.scalars(
            select(OnboardingTask).where(OnboardingTask.employee_id == state["employee_id"])
        ).all()
        for t in tasks:
            flag = TASK_FLAGS.get(t.task_name)
            if flag:
                if state.get(flag):
                    t.status = "completed"
                elif state.get("is_paused") and state.get("active_checkpoint", {}).get("task") == t.task_name:
                    t.status = "awaiting_approval"
                elif t.status != "completed":
                    t.status = "pending"
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
    emp_id = payload.employee_id or f"EMP-2024-{uuid.uuid4().hex[:6].upper()}"
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
    emp_id = f"EMP-2024-{uuid.uuid4().hex[:6].upper()}"
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
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            "email": emp.email,
            "department": emp.department,
            "role": emp.role,
            "progress": _calc_progress(tasks),
            "employee": {
                "id": emp.employee_id,
                "employee_id": emp.employee_id,
                "name": emp.employee_name,
                "employee_name": emp.employee_name,
                "email": emp.email,
                "department": emp.department,
                "role": emp.role,
                "joining_date": emp.joining_date,
                "salary": emp.salary,
                "manager": emp.manager,
                "buddy": emp.buddy,
                "team": emp.team,
                "desk": emp.desk,
                "avatar": emp.avatar,
                "avatar_color": emp.avatar_color,
                "status": emp.onboarding_status,
                "onboarding_status": emp.onboarding_status,
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
    file: Optional[UploadFile] = File(None),
    files: Optional[list[UploadFile]] = File(None),
    employee_id: Optional[str] = Form(None),
    doc_type: Optional[str] = Form("auto"),
):
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No files provided for upload")

    emp_id = employee_id or "shared"
    emp_folder = UPLOADS_DIR / emp_id
    emp_folder.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()
    processed = []
    try:
        emp = session.get(Employee, emp_id) if emp_id != "shared" else None
        emp_name = emp.employee_name if emp else "Candidate"

        for up_file in upload_list:
            if not up_file.filename:
                continue
            clean_name = os.path.basename(up_file.filename)
            dest_path = emp_folder / clean_name
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(up_file.file, buffer)

            # OCR Text Extraction using PyMuPDF
            raw_text = extract_text(str(dest_path))

            # Determine category
            if doc_type and doc_type != "auto" and len(upload_list) == 1:
                cat = doc_type
            else:
                cat = detect_doc_category(clean_name, raw_text)

            # Standardize filename to category for easy discovery
            cat_dest = emp_folder / f"{cat}.pdf"
            if str(dest_path) != str(cat_dest):
                try:
                    shutil.copyfile(dest_path, cat_dest)
                except Exception:
                    pass

            # Information extraction & validation
            extraction = extract_info_with_llm(raw_text, emp_name)
            issues = extraction.get("issues") or []

            # Upsert into DocumentRecord
            existing_doc = session.scalars(
                select(DocumentRecord).where(
                    DocumentRecord.employee_id == emp_id,
                    DocumentRecord.doc_name == cat,
                )
            ).first()

            readable = len(raw_text.strip()) > 5
            name_match = extraction.get("name_match", True)
            confidence = extraction.get("confidence", "high")
            detected_type = extraction.get("document_type", cat.replace("_", " ").title())

            meta_json = json.dumps(extraction.get("metadata_fields", {}))

            if not existing_doc:
                session.add(
                    DocumentRecord(
                        employee_id=emp_id,
                        doc_name=cat,
                        doc_type=detected_type,
                        readable=readable,
                        extracted_name=extraction.get("extracted_name") or emp_name,
                        name_match=name_match,
                        confidence=confidence,
                        llm_used=extraction.get("llm_used", False),
                        issues=json.dumps(issues),
                        metadata_fields=meta_json,
                    )
                )
            else:
                existing_doc.doc_type = detected_type
                existing_doc.readable = readable
                existing_doc.extracted_name = extraction.get("extracted_name") or emp_name
                existing_doc.name_match = name_match
                existing_doc.confidence = confidence
                existing_doc.llm_used = extraction.get("llm_used", False)
                existing_doc.issues = json.dumps(issues)
                existing_doc.metadata_fields = meta_json

            processed.append({
                "filename": clean_name,
                "category": cat,
                "doc_type": detected_type,
                "readable": readable,
                "name_match": name_match,
                "confidence": confidence,
                "metadata_fields": extraction.get("metadata_fields", {}),
            })

            log_activity(
                emp_id,
                f"Document '{clean_name}' uploaded & verified as {detected_type} (Match: {name_match})",
                "Document Verification",
                "success" if name_match else "warning",
            )

        session.commit()

        # Fetch full updated document list
        records = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == emp_id)).all())
        updated_docs = [
            {
                "id": r.id,
                "name": r.doc_name,
                "doc_name": r.doc_name,
                "type": r.doc_type,
                "doc_type": r.doc_type,
                "readable": r.readable,
                "extracted_name": r.extracted_name,
                "name_match": r.name_match,
                "confidence": r.confidence,
                "llm_used": r.llm_used,
                "issues": json.loads(r.issues) if r.issues else [],
                "metadata_fields": json.loads(r.metadata_fields) if r.metadata_fields else {},
            }
            for r in records
        ]

        return {
            "status": "success",
            "message": f"Processed {len(processed)} document(s) successfully.",
            "processed": processed,
            "documents": updated_docs,
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/documents/{employee_id}/generate-demo-pack")
def generate_demo_documents(employee_id: str):
    """Generate authentic, valid KYC PDFs for all 4 required document types for the candidate."""
    session = SessionLocal()
    try:
        emp = session.get(Employee, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        emp_folder = UPLOADS_DIR / employee_id
        pack = generate_sample_pdf_pack(emp.employee_name, str(emp_folder))

        doc_type_titles = {
            "aadhar_card": "Aadhaar Card",
            "degree_certificate": "Degree Certificate",
            "offer_letter_signed": "Countersigned Offer Letter",
            "bank_details": "Bank Cheque & Statement",
        }

        for doc_key, pdf_path in pack.items():
            raw_text = extract_text(pdf_path)
            extraction = extract_info_with_llm(raw_text, emp.employee_name)
            issues = extraction.get("issues") or []

            existing_doc = session.scalars(
                select(DocumentRecord).where(
                    DocumentRecord.employee_id == employee_id,
                    DocumentRecord.doc_name == doc_key,
                )
            ).first()

            doc_type_title = doc_type_titles.get(doc_key, "KYC Document")
            meta_json = json.dumps(extraction.get("metadata_fields", {}))

            if not existing_doc:
                session.add(
                    DocumentRecord(
                        employee_id=employee_id,
                        doc_name=doc_key,
                        doc_type=doc_type_title,
                        readable=True,
                        extracted_name=emp.employee_name,
                        name_match=True,
                        confidence="high",
                        llm_used=extraction.get("llm_used", False),
                        issues=json.dumps(issues),
                        metadata_fields=meta_json,
                    )
                )
            else:
                existing_doc.doc_type = doc_type_title
                existing_doc.readable = True
                existing_doc.extracted_name = emp.employee_name
                existing_doc.name_match = True
                existing_doc.confidence = "high"
                existing_doc.llm_used = extraction.get("llm_used", False)
                existing_doc.issues = json.dumps(issues)
                existing_doc.metadata_fields = meta_json

        log_activity(
            employee_id,
            f"All 4 official KYC documents generated and verified for {emp.employee_name}",
            "Document Verification",
            "success",
        )
        session.commit()

        records = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == employee_id).order_by(DocumentRecord.id.desc())).all())
        seen = set()
        unique = []
        for r in records:
            if r.doc_name not in seen:
                seen.add(r.doc_name)
                unique.append(r)

        return [
            {
                "id": r.id,
                "name": r.doc_name,
                "doc_name": r.doc_name,
                "type": r.doc_type,
                "doc_type": r.doc_type,
                "readable": r.readable,
                "extracted_name": r.extracted_name,
                "name_match": r.name_match,
                "confidence": r.confidence,
                "llm_used": r.llm_used,
                "issues": json.loads(r.issues) if r.issues else [],
                "metadata_fields": json.loads(r.metadata_fields) if r.metadata_fields else {},
            }
            for r in unique
        ]
    finally:
        session.close()


@router.get("/documents/{employee_id}")
def get_employee_documents(employee_id: str):
    session = SessionLocal()
    try:
        records = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == employee_id).order_by(DocumentRecord.id.desc())).all())
        seen = set()
        unique = []
        for r in records:
            if r.doc_name not in seen:
                seen.add(r.doc_name)
                unique.append(r)

        return [
            {
                "id": r.id,
                "name": r.doc_name,
                "doc_name": r.doc_name,
                "type": r.doc_type,
                "doc_type": r.doc_type,
                "readable": r.readable,
                "extracted_name": r.extracted_name,
                "name_match": r.name_match,
                "confidence": r.confidence,
                "llm_used": r.llm_used,
                "issues": json.loads(r.issues) if r.issues else [],
                "metadata_fields": json.loads(r.metadata_fields) if r.metadata_fields else {},
            }
            for r in unique
        ]
    finally:
        session.close()


@router.post("/documents/{doc_id}/hr-override")
def hr_override_document(doc_id: int):
    """Allow an authorized HR officer to manually override and sign off on a flagged document."""
    session = SessionLocal()
    try:
        doc = session.get(DocumentRecord, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document record not found")

        doc.confidence = "high"
        doc.name_match = True
        doc.readable = True
        override_note = f"[HR Manual Override]: Sign-off granted by HR Operations at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        doc.issues = json.dumps([override_note])

        meta = json.loads(doc.metadata_fields) if doc.metadata_fields else {}
        meta["hr_manual_override"] = True
        meta["hr_verified_at"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        doc.metadata_fields = json.dumps(meta)

        log_activity(
            doc.employee_id,
            f"HR manual override and sign-off granted for document #{doc.id} ({doc.doc_type})",
            "Document Verification",
            "success",
        )
        session.commit()
        return {
            "status": "success",
            "message": "Document manually verified and approved by HR sign-off.",
            "document": {
                "id": doc.id,
                "name": doc.doc_name,
                "doc_name": doc.doc_name,
                "type": doc.doc_type,
                "doc_type": doc.doc_type,
                "readable": doc.readable,
                "extracted_name": doc.extracted_name,
                "name_match": doc.name_match,
                "confidence": doc.confidence,
                "llm_used": doc.llm_used,
                "issues": json.loads(doc.issues) if doc.issues else [],
                "metadata_fields": json.loads(doc.metadata_fields) if doc.metadata_fields else {},
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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

        # If action is Approved, apply customized allocations
        if payload.action == "Approved":
            if app.approval_type == "IT Access":
                asset = session.query(ITAssetRecord).filter(ITAssetRecord.employee_id == app.employee_id).first()
                if asset:
                    if payload.laptop_model:
                        asset.laptop_model = payload.laptop_model
                    if payload.asset_tag:
                        asset.laptop_ticket_id = payload.asset_tag
                        asset.master_ticket_id = payload.asset_tag
                    if payload.software_licenses:
                        asset.software_licenses = json.dumps(payload.software_licenses)
                    asset.status = "provisioned"

            elif app.approval_type == "Team Allocation":
                emp_alloc = session.get(Employee, app.employee_id)
                if emp_alloc:
                    if payload.reporting_manager:
                        emp_alloc.manager = payload.reporting_manager
                    if payload.peer_buddy:
                        emp_alloc.buddy = payload.peer_buddy
                    if payload.assigned_team:
                        emp_alloc.team = payload.assigned_team
                    if payload.desk_location:
                        emp_alloc.desk = payload.desk_location

            elif app.approval_type == "Document Review":
                # Manual HR override: mark flagged documents as accepted by HR officer
                doc_records = list(session.scalars(select(DocumentRecord).where(DocumentRecord.employee_id == app.employee_id)).all())
                for dr in doc_records:
                    dr.readable = True
                    dr.name_match = True
                    dr.confidence = "high"
                    dr.issues = json.dumps([])

        log_activity(
            app.employee_id,
            f"Human Gate [{app.approval_type}] resolved: {payload.action} by {app.approver}. Notes: {payload.notes or 'None'}",
            app.agent,
            "success" if payload.action == "Approved" else "warning",
        )
        session.commit()

        # If action is Approved, automatically resume and advance the multi-agent pipeline!
        resumed_result = None
        if payload.action == "Approved":
            emp = session.get(Employee, app.employee_id)
            if emp:
                resumed_state = run_onboarding(
                    employee_id=emp.employee_id,
                    employee_name=emp.employee_name,
                    department=emp.department or "Engineering",
                    designation=emp.role or "Software Engineer",
                    joining_date=emp.joining_date or "",
                )
                _save_graph_result(resumed_state)
                report = generate_progress_report(resumed_state)
                is_p = resumed_state.get("is_paused", False)
                resumed_result = {
                    "status": "paused_for_approval" if is_p else "completed",
                    "is_paused": is_p,
                    "paused_reason": resumed_state.get("paused_reason", ""),
                    "active_checkpoint": resumed_state.get("active_checkpoint", {}),
                    "progress": report["progress"],
                    "percent": report["percent"],
                    "stages": [
                        {"id": "doc_verification", "name": "Document Verification", "completed": resumed_state.get("documents_verified", False)},
                        {"id": "it_provisioning", "name": "IT Provisioning", "completed": resumed_state.get("it_provisioned", False), "awaiting_approval": is_p and resumed_state.get("active_checkpoint", {}).get("task") == "it_provisioning"},
                        {"id": "team_allocation", "name": "Team Allocation", "completed": resumed_state.get("team_allocated", False), "awaiting_approval": is_p and resumed_state.get("active_checkpoint", {}).get("task") == "team_allocation"},
                        {"id": "training", "name": "Training & Orientation", "completed": resumed_state.get("training_assigned", False)},
                    ],
                    "audit_trail": resumed_state.get("audit_log", []),
                }

        return {
            "status": "success",
            "approval_id": approval_id,
            "decision": payload.action,
            "pipeline": resumed_result,
        }
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
    emp_id = payload.employee_id or f"EMP-2024-{uuid.uuid4().hex[:6].upper()}"
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
        report = generate_progress_report(final_state)
        is_p = final_state.get("is_paused", False)
        return {
            "status": "paused_for_approval" if is_p else "completed",
            "is_paused": is_p,
            "paused_reason": final_state.get("paused_reason", ""),
            "active_checkpoint": final_state.get("active_checkpoint", {}),
            "employee_id": emp_id,
            "employee_name": payload.employee_name,
            "department": payload.department,
            "progress": report["progress"],
            "percent": report["percent"],
            "stages": [
                {"id": "doc_verification", "name": "Document Verification", "completed": final_state.get("documents_verified", False)},
                {"id": "it_provisioning", "name": "IT Provisioning", "completed": final_state.get("it_provisioned", False), "awaiting_approval": is_p and final_state.get("active_checkpoint", {}).get("task") == "it_provisioning"},
                {"id": "team_allocation", "name": "Team Allocation", "completed": final_state.get("team_allocated", False), "awaiting_approval": is_p and final_state.get("active_checkpoint", {}).get("task") == "team_allocation"},
                {"id": "training", "name": "Training & Orientation", "completed": final_state.get("training_assigned", False)},
            ],
            "audit_trail": final_state.get("audit_log", []),
            "pending_approvals": final_state.get("pending_approvals", []),
        }
    finally:
        session.close()




@router.get("/download-demo-pack-pdf")
def download_demo_pack_pdf():
    pdf_path = os.path.abspath("ALL_TEST_DOCUMENTS_SAMPLE_PACK.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Demo pack PDF not found")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="ALL_TEST_DOCUMENTS_SAMPLE_PACK.pdf",
    )


