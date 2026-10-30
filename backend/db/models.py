from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String(50), primary_key=True)
    employee_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True, default="Engineering")
    role = Column(String(100), nullable=True, default="Software Engineer")
    joining_date = Column(String(20), nullable=True)
    salary = Column(String(50), nullable=True)
    manager = Column(String(100), nullable=True)
    buddy = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    desk = Column(String(100), nullable=True)
    avatar = Column(String(10), nullable=True, default="EP")
    avatar_color = Column(String(20), nullable=True, default="#6366f1")
    onboarding_status = Column(String(30), nullable=False, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("OnboardingTask", back_populates="employee", cascade="all, delete-orphan")


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    task_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False)
    task_name = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    details = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="tasks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), nullable=False, index=True)
    agent = Column(String(50), nullable=False, default="Orchestrator")
    action = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="info")
    timestamp = Column(DateTime, default=datetime.utcnow)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    approval_id = Column(String(50), primary_key=True)
    employee_id = Column(String(50), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    approval_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    checklist = Column(Text, nullable=True)  # JSON-serialized list of items
    status = Column(String(30), nullable=False, default="Pending")  # Pending, Approved, Rejected
    approver = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), nullable=False, index=True)
    doc_name = Column(String(100), nullable=False)
    doc_type = Column(String(100), nullable=True)
    readable = Column(Boolean, default=False)
    extracted_name = Column(String(100), nullable=True)
    name_match = Column(Boolean, default=False)
    confidence = Column(String(20), default="low")
    llm_used = Column(Boolean, default=False)
    issues = Column(Text, nullable=True)  # JSON-serialized list
    metadata_fields = Column(Text, nullable=True)  # JSON-serialized dict with field-by-field verification
    created_at = Column(DateTime, default=datetime.utcnow)


class ITAssetRecord(Base):
    __tablename__ = "it_asset_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), nullable=False, index=True)
    email_account = Column(String(100), nullable=True)
    laptop_model = Column(String(100), nullable=True)
    laptop_specs = Column(Text, nullable=True)  # JSON-serialized
    laptop_ticket_id = Column(String(50), nullable=True)
    master_ticket_id = Column(String(50), nullable=True)
    software_licenses = Column(Text, nullable=True)  # JSON-serialized
    status = Column(String(30), default="provisioned")
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingTaskRecord(Base):
    __tablename__ = "training_task_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="Orientation")
    status = Column(String(30), default="Pending")  # Pending, In progress, Completed
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
