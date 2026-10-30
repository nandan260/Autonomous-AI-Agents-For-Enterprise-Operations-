from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class OnboardingStartRequest(BaseModel):
    employee_id: Optional[str] = None
    employee_name: str
    department: Optional[str] = "Engineering"
    designation: Optional[str] = "Software Engineer"
    joining_date: Optional[str] = None
    upload_folder: Optional[str] = None


class MonitoringReport(BaseModel):
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    completed_tasks: list[str] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    pending_approvals: list[Any] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    progress: str = "0/4"
    percent: int = 0


class OnboardingStatusResponse(BaseModel):
    employee_id: str
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    onboarding_status: str
    documents_verified: bool
    it_provisioned: bool
    training_assigned: bool
    team_allocated: bool
    pending_approvals: list[Any] = Field(default_factory=list)
    monitoring: Optional[MonitoringReport] = None


class AuditLogItem(BaseModel):
    log_id: int
    employee_id: str
    agent: str
    action: str
    status: str
    timestamp: datetime


class AuditLogsResponse(BaseModel):
    employee_id: str
    logs: list[AuditLogItem]


class EmployeeCreateRequest(BaseModel):
    employee_name: str
    department: str = "Engineering"
    role: str = "Software Engineer"
    joining_date: Optional[str] = None
    salary: Optional[str] = None
    email: Optional[str] = None


class EmployeeResponse(BaseModel):
    employee_id: str
    employee_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    joining_date: Optional[str] = None
    salary: Optional[str] = None
    manager: Optional[str] = None
    buddy: Optional[str] = None
    team: Optional[str] = None
    desk: Optional[str] = None
    avatar: Optional[str] = None
    avatar_color: Optional[str] = None
    onboarding_status: str
    progress: int = 0


class ApprovalItemResponse(BaseModel):
    approval_id: str
    employee_id: str
    employee_name: Optional[str] = None
    agent: str
    approval_type: str
    title: str
    description: str
    checklist: list[str] = Field(default_factory=list)
    status: str
    approver: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class ApprovalActionRequest(BaseModel):
    action: str  # "Approved" or "Rejected"
    approver: Optional[str] = "Admin Supervisor"
    notes: Optional[str] = ""
    # Optional customized IT Provisioning parameters
    laptop_model: Optional[str] = None
    asset_tag: Optional[str] = None
    privilege_tier: Optional[str] = None
    software_licenses: Optional[list[str]] = None
    # Optional customized Team Allocation parameters
    reporting_manager: Optional[str] = None
    peer_buddy: Optional[str] = None
    assigned_team: Optional[str] = None
    desk_location: Optional[str] = None
    work_mode: Optional[str] = None


class TrainingTaskUpdate(BaseModel):
    status: str  # "Pending", "In progress", "Completed"
