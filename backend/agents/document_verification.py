import json
import os
import uuid
from datetime import datetime

from .state import AgentState
from ..config import UPLOADS_DIR
from ..db.models import ApprovalRequest, DocumentRecord, Employee
from ..db.session import SessionLocal
from ..services.audit import log_activity
from ..services.llm_service import extract_info_with_llm
from ..services.ocr_service import extract_text, find_document

REQUIRED_DOCS = [
    "aadhar_card",
    "degree_certificate",
    "offer_letter_signed",
    "bank_details",
]


def document_verification_agent(state: AgentState) -> AgentState:
    """Agent 1: Verifies submitted KYC & educational documents with OCR & LLM."""
    employee_id = state.get("employee_id") or f"EMP-2024-{str(uuid.uuid4().int)[:4]}"
    employee_name = state.get("employee_name") or "Jane Doe"
    upload_folder = state.get("upload_folder") or str(UPLOADS_DIR)
    if not os.path.isdir(upload_folder):
        upload_folder = str(UPLOADS_DIR)

    audit_log = list(state.get("audit_log") or [])
    pending = list(state.get("pending_approvals") or [])
    issues = []
    results = []

    audit_log.append(f"[Document Verification] Starting verification for {employee_name} ({employee_id})")
    log_activity(employee_id, f"Document verification started for {employee_name}", "Document Verification", "info")

    session = SessionLocal()
    try:
        for doc_name in REQUIRED_DOCS:
            doc_path = find_document(upload_folder, doc_name)
            if not doc_path:
                msg = f"Missing document: {doc_name}"
                issues.append(msg)
                res = {
                    "document": doc_name,
                    "document_type": "Unknown",
                    "readable": False,
                    "extracted_name": None,
                    "name_match": False,
                    "confidence": "low",
                    "llm_used": False,
                    "issues": [msg],
                }
                results.append(res)
                session.add(
                    DocumentRecord(
                        employee_id=employee_id,
                        doc_name=doc_name,
                        doc_type="Unknown",
                        readable=False,
                        extracted_name=None,
                        name_match=False,
                        confidence="low",
                        llm_used=False,
                        issues=json.dumps([msg]),
                    )
                )
                continue

            # OCR Text Extraction
            raw_text = extract_text(doc_path)
            if len(raw_text.strip()) < 10:
                msg = f"{doc_name} is blank or unreadable"
                issues.append(msg)
                res = {
                    "document": doc_name,
                    "document_type": "Unknown",
                    "readable": False,
                    "extracted_name": None,
                    "name_match": False,
                    "confidence": "low",
                    "llm_used": False,
                    "issues": [msg],
                }
                results.append(res)
                session.add(
                    DocumentRecord(
                        employee_id=employee_id,
                        doc_name=doc_name,
                        doc_type="Unknown",
                        readable=False,
                        extracted_name=None,
                        name_match=False,
                        confidence="low",
                        llm_used=False,
                        issues=json.dumps([msg]),
                    )
                )
                continue

            # Intelligent LLM / Rule extraction
            extraction = extract_info_with_llm(raw_text, employee_name)
            doc_issues = extraction.get("issues") or []
            issues.extend(doc_issues)

            res = {
                "document": doc_name,
                "document_type": extraction.get("document_type", "KYC Document"),
                "readable": True,
                "extracted_name": extraction.get("extracted_name"),
                "name_match": extraction.get("name_match", True),
                "confidence": extraction.get("confidence", "high"),
                "llm_used": extraction.get("llm_used", False),
                "issues": doc_issues,
            }
            results.append(res)

            session.add(
                DocumentRecord(
                    employee_id=employee_id,
                    doc_name=doc_name,
                    doc_type=res["document_type"],
                    readable=True,
                    extracted_name=res["extracted_name"],
                    name_match=res["name_match"],
                    confidence=res["confidence"],
                    llm_used=res["llm_used"],
                    issues=json.dumps(doc_issues),
                )
            )

        passed = len(issues) == 0
        status_tag = "success" if passed else "warning"
        summary_msg = "All documents verified successfully." if passed else f"Document verification flagged {len(issues)} issue(s)."
        audit_log.append(f"[Document Verification] {summary_msg}")
        log_activity(employee_id, summary_msg, "Document Verification", status_tag)

        # Generate corporate email & employee profile
        first_last = employee_name.lower().replace(" ", ".")
        emp_email = f"{first_last}@enterpriseflow.ai"

        # Update employee record in DB if exists
        emp = session.get(Employee, employee_id)
        if emp:
            emp.email = emp_email
            if not passed:
                emp.onboarding_status = "action_required"

        # If issues exist, register an HR approval request
        if not passed:
            approval_id = f"APP-DOC-{str(uuid.uuid4().int)[:4]}"
            pending.append(approval_id)
            session.add(
                ApprovalRequest(
                    approval_id=approval_id,
                    employee_id=employee_id,
                    agent="Document Verification Agent",
                    approval_type="Document Review",
                    title=f"Document Review Needed for {employee_name}",
                    description=f"Automated verification flagged {len(issues)} item(s): {', '.join(issues)}",
                    checklist=json.dumps(issues),
                    status="Pending",
                )
            )
            audit_log.append(f"Created approval request {approval_id} for HR review")

        session.commit()
    except Exception as e:
        session.rollback()
        audit_log.append(f"[Document Verification Error] {e}")
        passed = False
    finally:
        session.close()

    return {
        **state,
        "employee_id": employee_id,
        "employee_email": emp_email,
        "documents_verified": True,  # Mark stage executed so pipeline advances
        "doc_issues": issues,
        "doc_results": results,
        "needs_human_review": not passed,
        "audit_log": audit_log,
        "pending_approvals": pending,
    }
