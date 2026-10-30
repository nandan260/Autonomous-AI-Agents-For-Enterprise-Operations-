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

    # 5. Register Human-in-the-Loop IT Approval Request
    approval_id = f"APP-IT-{uid(4)}"
    pending.append(approval_id)

    it_summary = {
        "email": email_res,
        "laptop": laptop_res,
        "software": software_res,
        "master_ticket": master_ticket,
    }

    session = SessionLocal()
    try:
        # Save IT Asset Record
        session.add(
            ITAssetRecord(
                employee_id=employee_id,
                email_account=email_res["email"],
                laptop_model=laptop_res["spec"]["model"],
                laptop_specs=json.dumps(laptop_res["spec"]),
                laptop_ticket_id=laptop_res["ticketId"],
                master_ticket_id=master_ticket,
                software_licenses=json.dumps(software_res),
                status="provisioned_awaiting_approval",
            )
        )

        # Register HITL Gate
        approval_req = ApprovalRequest(
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
        session.add(approval_req)
        session.commit()
    except Exception as e:
        session.rollback()
        audit_log.append(f"[IT Provisioning DB Error] {e}")
    finally:
        session.close()

    log_activity(
        employee_id,
        f"IT Access approval gate raised ({approval_id}) for IT Manager review",
        "IT Provisioning",
        "gate",
    )
    audit_log.append(f"⚠️ HUMAN GATE: IT Manager sign-off required [Request #{approval_id}]")

    return {
        **state,
        "it_provisioned": True,
        "it_assets": it_summary,
        "audit_log": audit_log,
        "pending_approvals": pending,
    }
