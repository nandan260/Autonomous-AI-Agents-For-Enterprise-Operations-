import json
import uuid
from datetime import datetime

from .state import AgentState
from ..db.models import ApprovalRequest, ITAssetRecord
from ..db.session import SessionLocal
from ..services.audit import log_activity
from ..services.mock_external_apis import (
    MockEmailAPI,
    MockLaptopAPI,
    MockSoftwareAPI,
    uid,
)


def it_provisioning_agent(state: AgentState) -> AgentState:
    """Agent 2: Provisions corporate email, hardware procurement, software access, and HITL gate."""
    employee_id = state.get("employee_id", "EMP-TEMP")
    employee_name = state.get("employee_name", "Jane Doe")
    department = state.get("department", "Engineering")
    role = state.get("designation", "Software Engineer")

    audit_log = list(state.get("audit_log") or [])
    pending = list(state.get("pending_approvals") or [])

    audit_log.append(f"[IT Provisioning] Commencing IT systems setup for {employee_name} ({department})")
    log_activity(employee_id, f"IT Provisioning initiated for {employee_name}", "IT Provisioning", "info")

    # 1. Email Account Provisioning
    email_res = MockEmailAPI.create_account(employee_name, department, role)
    audit_log.append(f"  ↳ Email created: {email_res['email']} [Quota: {email_res['quota']}]")

    # 2. Laptop Hardware Procurement Ticket
    laptop_res = MockLaptopAPI.raise_ticket(employee_id, employee_name, department)
    audit_log.append(
        f"  ↳ Hardware Ticket #{laptop_res['ticketId']} raised: {laptop_res['spec']['model']} (ETA: {laptop_res['eta']})"
    )

    # 3. Software Access Requests
    software_res = MockSoftwareAPI.get_software_list(department)
    audit_log.append(f"  ↳ Provisioned {len(software_res)} departmental software access licenses")

    # 4. Master IT Ticket ID
    master_ticket = f"TKT-IT-{uid(6)}"
    audit_log.append(f"  ↳ Master IT Ticket generated: #{master_ticket}")

    it_summary = {
        "email": email_res,
        "laptop": laptop_res,
        "software": software_res,
        "master_ticket": master_ticket,
    }

    session = SessionLocal()
    is_approved = False
    approval_id = f"APP-IT-{uid(4)}"
    try:
        existing_approval = session.query(ApprovalRequest).filter(
            ApprovalRequest.employee_id == employee_id,
            ApprovalRequest.approval_type == "IT Access",
        ).first()

        if existing_approval and existing_approval.status == "Approved":
            is_approved = True
            approval_id = existing_approval.approval_id
        elif state.get("it_approved", False):
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
                        agent="IT Provisioning Agent",
                        approval_type="IT Access",
                        title=f"IT Access & Hardware Sign-Off for {employee_name}",
                        description=(
                            f"IT Manager sign-off required for {employee_name} ({role}, {department}). "
                            f"Hardware: {laptop_res['spec']['model']}. Software: {len(software_res)} licenses."
                        ),
                        checklist=json.dumps([
                            f"Confirm hardware delivery to employee location ({laptop_res['spec']['model']})",
                            "Verify role-appropriate privilege tiers",
                            "Enforce multi-factor authentication (MFA)",
                            "Security training acknowledgment received",
                        ]),
                        status="Pending",
                    )
                )

        existing_asset = session.query(ITAssetRecord).filter(ITAssetRecord.employee_id == employee_id).first()
        if not existing_asset:
            session.add(
                ITAssetRecord(
                    employee_id=employee_id,
                    email_account=email_res["email"],
                    laptop_model=laptop_res["spec"]["model"],
                    laptop_specs=json.dumps(laptop_res["spec"]),
                    laptop_ticket_id=laptop_res["ticketId"],
                    master_ticket_id=master_ticket,
                    software_licenses=json.dumps(software_res),
                    status="provisioned" if is_approved else "awaiting_approval",
                )
            )
        else:
            existing_asset.status = "provisioned" if is_approved else "awaiting_approval"

        session.commit()
    except Exception as e:
        session.rollback()
        audit_log.append(f"[IT Provisioning DB Error] {e}")
    finally:
        session.close()

    if not is_approved:
        if approval_id not in pending:
            pending.append(approval_id)
        audit_log.append(f"[HITL CHECKPOINT PAUSE] Pipeline paused: IT Manager sign-off required [Request #{approval_id}]")
        log_activity(
            employee_id,
            f"Pipeline paused at IT Gate ({approval_id}): Waiting for IT Manager authorization",
            "IT Provisioning",
            "warning",
        )
        return {
            **state,
            "it_provisioned": False,
            "is_paused": True,
            "paused_reason": f"IT Access & Hardware Sign-Off Required for {employee_name}",
            "active_checkpoint": {
                "approval_id": approval_id,
                "agent": "IT Provisioning Agent",
                "approval_type": "IT Access",
                "task": "it_provisioning",
                "title": f"IT Access & Hardware Sign-Off for {employee_name}",
                "description": f"IT Manager sign-off required for {employee_name} ({role}, {department}). Hardware: {laptop_res['spec']['model']}.",
                "hardware": laptop_res["spec"]["model"],
                "software_count": len(software_res),
                "checklist": [
                    f"Confirm hardware delivery to employee location ({laptop_res['spec']['model']})",
                    "Verify role-appropriate privilege tiers",
                    "Enforce multi-factor authentication (MFA)",
                    "Security training acknowledgment received",
                ],
            },
            "it_assets": it_summary,
            "audit_log": audit_log,
            "pending_approvals": pending,
        }

    # If approved, proceed cleanly!
    audit_log.append(f"  ✅ [AUTHORIZED] IT Manager signed off on hardware & licenses [Request #{approval_id}]")
    log_activity(employee_id, f"IT Access approved ({approval_id})", "IT Provisioning", "success")
    return {
        **state,
        "it_provisioned": True,
        "is_paused": False,
        "paused_reason": "",
        "active_checkpoint": {},
        "it_assets": it_summary,
        "audit_log": audit_log,
        "pending_approvals": [p for p in pending if p != approval_id],
    }
