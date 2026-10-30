import random
import string
from datetime import datetime, timedelta

def uid(length=6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ── Hardware Specs per Department/Role ──────────────────
LAPTOP_SPECS = {
    "engineering": {
        "model": 'MacBook Pro 14" M3 Pro',
        "ram": "18 GB",
        "storage": "512 GB SSD",
        "os": "macOS Sonoma",
        "extras": ["Dell 27\" 4K Monitor", "Magic Keyboard", "Magic Mouse", "USB-C Hub"],
    },
    "design": {
        "model": 'MacBook Air 15" M2',
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "os": "macOS Sonoma",
        "extras": ["LG 27\" 5K Monitor", "Wacom Intuos Tablet", "USB-C Hub"],
    },
    "finance": {
        "model": "Dell XPS 15",
        "ram": "16 GB",
        "storage": "256 GB SSD",
        "os": "Windows 11 Pro",
        "extras": ["Dell 24\" FHD Monitor", "Standard Keyboard", "Mouse"],
    },
    "human resources": {
        "model": "HP EliteBook 840 G10",
        "ram": "16 GB",
        "storage": "256 GB SSD",
        "os": "Windows 11 Pro",
        "extras": ["HP 24\" Monitor", "Standard Keyboard", "Mouse"],
    },
    "sales": {
        "model": "Lenovo ThinkPad X1 Carbon",
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "os": "Windows 11 Pro",
        "extras": ["Noise-cancelling Headset", "USB-C Hub", "Portable Charger"],
    },
    "_default": {
        "model": "Lenovo IdeaPad Pro 5",
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "os": "Windows 11 Pro",
        "extras": ["Standard Keyboard", "Mouse", "Dell 24\" Monitor"],
    },
}

# ── Software Bundles per Department ─────────────────────
SOFTWARE_BUNDLES = {
    "engineering": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "GitHub", "icon": "🐙", "licenseType": "Enterprise", "category": "DevOps"},
        {"name": "Jira", "icon": "📋", "licenseType": "Standard", "category": "Project Mgmt"},
        {"name": "Confluence", "icon": "📚", "licenseType": "Standard", "category": "Documentation"},
        {"name": "VS Code", "icon": "🧩", "licenseType": "Free", "category": "IDE"},
        {"name": "Datadog", "icon": "🐶", "licenseType": "Pro", "category": "Monitoring"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
        {"name": "AWS Console", "icon": "☁️", "licenseType": "IAM Access", "category": "Cloud"},
    ],
    "design": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "Figma", "icon": "🎨", "licenseType": "Professional", "category": "Design"},
        {"name": "Notion", "icon": "📒", "licenseType": "Team", "category": "Documentation"},
        {"name": "Jira", "icon": "📋", "licenseType": "Standard", "category": "Project Mgmt"},
        {"name": "Loom", "icon": "📹", "licenseType": "Business", "category": "Video"},
        {"name": "Zeplin", "icon": "🛠️", "licenseType": "Team", "category": "Handoff"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
    ],
    "finance": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "SAP ERP", "icon": "🏭", "licenseType": "Enterprise", "category": "ERP"},
        {"name": "Zoho Books", "icon": "📊", "licenseType": "Professional", "category": "Accounting"},
        {"name": "Excel 365", "icon": "📈", "licenseType": "M365 Business", "category": "Productivity"},
        {"name": "Power BI", "icon": "📉", "licenseType": "Pro", "category": "Analytics"},
        {"name": "DocuSign", "icon": "✍️", "licenseType": "Business Pro", "category": "e-Signature"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
    ],
    "human resources": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "Darwinbox", "icon": "👥", "licenseType": "Enterprise", "category": "HRMS"},
        {"name": "BambooHR", "icon": "🎋", "licenseType": "Advantage", "category": "HR Tools"},
        {"name": "Excel 365", "icon": "📈", "licenseType": "M365 Business", "category": "Productivity"},
        {"name": "Zoom", "icon": "📹", "licenseType": "Business", "category": "Video Conf"},
        {"name": "DocuSign", "icon": "✍️", "licenseType": "Business Pro", "category": "e-Signature"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
    ],
    "sales": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "Salesforce", "icon": "☁️", "licenseType": "Sales Cloud", "category": "CRM"},
        {"name": "HubSpot", "icon": "🟠", "licenseType": "Sales Pro", "category": "Marketing"},
        {"name": "Zoom", "icon": "📹", "licenseType": "Business", "category": "Video Conf"},
        {"name": "Loom", "icon": "🎥", "licenseType": "Business", "category": "Video"},
        {"name": "LinkedIn Sales Nav", "icon": "🔷", "licenseType": "Enterprise", "category": "Prospecting"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
    ],
    "_default": [
        {"name": "Slack", "icon": "💬", "licenseType": "Pro", "category": "Communication"},
        {"name": "Google Workspace", "icon": "📁", "licenseType": "Business", "category": "Productivity"},
        {"name": "Zoom", "icon": "📹", "licenseType": "Business", "category": "Video Conf"},
        {"name": "Tailscale VPN", "icon": "🔐", "licenseType": "Teams", "category": "Security"},
    ],
}

# ── Slack Channels Map ──────────────────────────────────
SLACK_CHANNELS = {
    "Engineering": ["#general", "#engineering", "#platform-team", "#dev-ops", "#code-reviews"],
    "Design": ["#general", "#design", "#product", "#ux-research", "#design-feedback"],
    "Finance": ["#general", "#finance", "#accounting", "#budgets", "#compliance"],
    "Human Resources": ["#general", "#hr-team", "#people-ops", "#culture", "#hiring"],
    "Sales": ["#general", "#sales", "#enterprise-sales", "#customer-success", "#deals"],
    "_default": ["#general", "#announcements", "#watercooler"],
}

# ── Desk Assignments Map ────────────────────────────────
DESK_MAP = {
    "Engineering": {"floor": "3rd Floor", "zone": "East Wing", "prefix": "ENG"},
    "Design": {"floor": "2nd Floor", "zone": "Creative Hub", "prefix": "DSG"},
    "Finance": {"floor": "4th Floor", "zone": "North Wing", "prefix": "FIN"},
    "Human Resources": {"floor": "1st Floor", "zone": "HR Suite", "prefix": "HR"},
    "Sales": {"floor": "2nd Floor", "zone": "Sales Floor", "prefix": "SLS"},
    "_default": {"floor": "1st Floor", "zone": "Open Area", "prefix": "GEN"},
}

# ── Day 1 Task Templates per Department ─────────────────
DAY1_TASK_TEMPLATES = {
    "Engineering": [
        {"id": "t1", "title": "Attend Dev Team Standup (9:00 AM)", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "Set up local dev environment", "priority": "high", "type": "setup"},
        {"id": "t3", "title": "Clone primary repositories from GitHub", "priority": "high", "type": "setup"},
        {"id": "t4", "title": "Read Architecture Decision Records (ADRs)", "priority": "medium", "type": "learning"},
        {"id": "t5", "title": "Meet buddy for codebase walkthrough", "priority": "high", "type": "meeting"},
        {"id": "t6", "title": "Complete Security & Compliance training", "priority": "high", "type": "training"},
        {"id": "t7", "title": "Join #engineering and #platform Slack channels", "priority": "medium", "type": "setup"},
        {"id": "t8", "title": "1-on-1 with Engineering Manager (3:00 PM)", "priority": "high", "type": "meeting"},
    ],
    "Design": [
        {"id": "t1", "title": "Attend Design Sync (10:00 AM)", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "Access Figma and explore Design System", "priority": "high", "type": "setup"},
        {"id": "t3", "title": "Review Brand Guidelines document", "priority": "medium", "type": "learning"},
        {"id": "t4", "title": "Meet Design buddy for tool walkthrough", "priority": "high", "type": "meeting"},
        {"id": "t5", "title": "Complete Design Onboarding 101 course", "priority": "high", "type": "training"},
        {"id": "t6", "title": "Join #design and #product Slack channels", "priority": "medium", "type": "setup"},
        {"id": "t7", "title": "1-on-1 with Design Lead (4:00 PM)", "priority": "high", "type": "meeting"},
    ],
    "Finance": [
        {"id": "t1", "title": "Attend Finance Team Briefing (9:30 AM)", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "Set up ERP system access (SAP/Zoho)", "priority": "high", "type": "setup"},
        {"id": "t3", "title": "Review Q4 Financial Reports", "priority": "medium", "type": "learning"},
        {"id": "t4", "title": "Complete Compliance & Audit Basics course", "priority": "high", "type": "training"},
        {"id": "t5", "title": "Meet Finance buddy for process walkthrough", "priority": "high", "type": "meeting"},
        {"id": "t6", "title": "Join #finance and #accounting Slack channels", "priority": "medium", "type": "setup"},
        {"id": "t7", "title": "1-on-1 with Finance Manager (3:30 PM)", "priority": "high", "type": "meeting"},
    ],
    "Human Resources": [
        {"id": "t1", "title": "Attend HR All-Hands (9:00 AM)", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "Access HRMS and explore employee portal", "priority": "high", "type": "setup"},
        {"id": "t3", "title": "Review HR Policies & Employee Handbook", "priority": "high", "type": "learning"},
        {"id": "t4", "title": "Complete Labor Law Compliance course", "priority": "high", "type": "training"},
        {"id": "t5", "title": "Meet HR buddy for systems walkthrough", "priority": "high", "type": "meeting"},
        {"id": "t6", "title": "Join #hr-team and #people-ops Slack channels", "priority": "medium", "type": "setup"},
        {"id": "t7", "title": "1-on-1 with HR Lead (4:00 PM)", "priority": "high", "type": "meeting"},
    ],
    "Sales": [
        {"id": "t1", "title": "Attend Sales Kick-off Call (8:30 AM)", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "Set up CRM access (Salesforce/HubSpot)", "priority": "high", "type": "setup"},
        {"id": "t3", "title": "Study Product Catalog & Pricing Guide", "priority": "high", "type": "learning"},
        {"id": "t4", "title": "Complete Sales Playbook & CRM training", "priority": "high", "type": "training"},
        {"id": "t5", "title": "Shadow a senior Sales call", "priority": "high", "type": "meeting"},
        {"id": "t6", "title": "Join #sales and #enterprise-sales Slack", "priority": "medium", "type": "setup"},
        {"id": "t7", "title": "1-on-1 with Sales Manager (3:00 PM)", "priority": "high", "type": "meeting"},
    ],
    "_default": [
        {"id": "t1", "title": "Company Introduction & Values", "priority": "high", "type": "meeting"},
        {"id": "t2", "title": "HR Policies & Handbook", "priority": "high", "type": "training"},
        {"id": "t3", "title": "Cybersecurity Awareness Training", "priority": "high", "type": "training"},
        {"id": "t4", "title": "Department Orientation", "priority": "medium", "type": "learning"},
        {"id": "t5", "title": "Tools and Systems Training", "priority": "high", "type": "setup"},
    ],
}

# ── LMS Courses per Department ──────────────────────────
LMS_COURSES = {
    "Engineering": ["Engineering Onboarding 101", "System Design Fundamentals", "Security & Compliance", "Git & CI/CD Practices"],
    "Design": ["Design System Onboarding", "Figma Best Practices", "User Research Methods", "Company Culture & Values"],
    "Finance": ["Finance Tools & ERP", "Compliance & Audit Basics", "Financial Reporting Standards", "Company Culture & Values"],
    "Human Resources": ["HR Systems & Tools", "Labor Law Compliance", "Performance Management", "DEI & Culture Training"],
    "Sales": ["Sales Playbook & CRM", "Product Demo Training", "Customer Success Basics", "Company Culture & Values"],
    "_default": ["Company Orientation 101", "Security & Phishing Basics", "Workplace Communication", "Product Overview"],
}

# ── Synthetic Employee Dataset ──────────────────────────
SYNTHETIC_EMPLOYEES = [
    {
        "id": "EMP-2024-001",
        "name": "Arjun Mehta",
        "role": "Senior Software Engineer",
        "department": "Engineering",
        "email": "arjun.mehta@enterpriseflow.ai",
        "phone": "+91 98765 43210",
        "joiningDate": "2024-11-04",
        "salary": "₹24,00,000 CTC",
        "manager": "Priya Sharma",
        "location": "Bangalore",
        "avatar": "AM",
        "avatarColor": "#6366f1",
        "team": "Platform Engineering",
        "buddy": "Rohan Verma",
    },
    {
        "id": "EMP-2024-002",
        "name": "Sneha Patel",
        "role": "Product Designer",
        "department": "Design",
        "email": "sneha.patel@enterpriseflow.ai",
        "phone": "+91 87654 32109",
        "joiningDate": "2024-11-05",
        "salary": "₹18,00,000 CTC",
        "manager": "Kiran Rao",
        "location": "Mumbai",
        "avatar": "SP",
        "avatarColor": "#ec4899",
        "team": "Product Design",
        "buddy": "Ananya Singh",
    },
    {
        "id": "EMP-2024-003",
        "name": "Rahul Gupta",
        "role": "Finance Analyst",
        "department": "Finance",
        "email": "rahul.gupta@enterpriseflow.ai",
        "phone": "+91 76543 21098",
        "joiningDate": "2024-11-06",
        "salary": "₹14,00,000 CTC",
        "manager": "Deepa Krishnan",
        "location": "Hyderabad",
        "avatar": "RG",
        "avatarColor": "#10b981",
        "team": "Financial Planning & Analysis",
        "buddy": "Meera Nair",
    },
    {
        "id": "EMP-2024-004",
        "name": "Divya Nair",
        "role": "HR Business Partner",
        "department": "Human Resources",
        "email": "divya.nair@enterpriseflow.ai",
        "phone": "+91 65432 10987",
        "joiningDate": "2024-11-07",
        "salary": "₹16,00,000 CTC",
        "manager": "Suresh Iyer",
        "location": "Chennai",
        "avatar": "DN",
        "avatarColor": "#f59e0b",
        "team": "HR Operations",
        "buddy": "Preethi Reddy",
    },
    {
        "id": "EMP-2024-005",
        "name": "Vikram Singh",
        "role": "Sales Executive",
        "department": "Sales",
        "email": "vikram.singh@enterpriseflow.ai",
        "phone": "+91 54321 09876",
        "joiningDate": "2024-11-08",
        "salary": "₹12,00,000 CTC + Incentives",
        "manager": "Amit Khanna",
        "location": "Delhi",
        "avatar": "VS",
        "avatarColor": "#ef4444",
        "team": "Enterprise Sales",
        "buddy": "Kabir Malhotra",
    },
]


# ── Mock External Service Clients ───────────────────────
class MockEmailAPI:
    @staticmethod
    def generate_address(name: str, domain: str = "enterpriseflow.ai") -> str:
        parts = [p.lower() for p in name.strip().split() if p]
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[-1]}@{domain}"
        return f"{parts[0] if parts else 'employee'}@{domain}"

    @staticmethod
    def create_account(name: str, department: str, role: str) -> dict:
        email = MockEmailAPI.generate_address(name)
        return {
            "requestId": f"EMAIL-REQ-{uid(6)}",
            "email": email,
            "displayName": name,
            "department": department,
            "role": role,
            "quota": "30 GB",
            "mfaRequired": True,
            "status": "created_pending_activation",
            "createdAt": datetime.utcnow().isoformat(),
        }


class MockLaptopAPI:
    @staticmethod
    def select_spec(department: str) -> dict:
        key = (department or "").lower()
        return LAPTOP_SPECS.get(key, LAPTOP_SPECS["_default"])

    @staticmethod
    def raise_ticket(employee_id: str, name: str, department: str) -> dict:
        spec = MockLaptopAPI.select_spec(department)
        return {
            "ticketId": f"HW-{uid(6)}",
            "employeeId": employee_id,
            "employeeName": name,
            "spec": spec,
            "status": "ticket_raised",
            "eta": (datetime.utcnow() + timedelta(days=2)).strftime("%d %b %Y"),
            "vendor": "TechSupply Direct Corp",
            "trackingId": f"TRK-{uid(8)}",
            "raisedAt": datetime.utcnow().isoformat(),
        }


class MockSoftwareAPI:
    @staticmethod
    def get_software_list(department: str) -> list[dict]:
        key = (department or "").lower()
        bundles = SOFTWARE_BUNDLES.get(key, SOFTWARE_BUNDLES["_default"])
        results = []
        for sw in bundles:
            results.append({
                "requestId": f"SW-REQ-{uid(6)}",
                "name": sw["name"],
                "icon": sw["icon"],
                "licenseType": sw["licenseType"],
                "category": sw["category"],
                "status": "active",
            })
        return results


class MockHRMS:
    @staticmethod
    def get_desk(department: str) -> str:
        d = DESK_MAP.get(department, DESK_MAP["_default"])
        return f"{d['floor']}, {d['zone']} (Desk #{d['prefix']}-{uid(4)})"

    @staticmethod
    def get_slack_channels(department: str) -> list[str]:
        return SLACK_CHANNELS.get(department, SLACK_CHANNELS["_default"])

    @staticmethod
    def get_courses(department: str) -> list[str]:
        return LMS_COURSES.get(department, LMS_COURSES["_default"])

    @staticmethod
    def get_day1_tasks(department: str) -> list[dict]:
        return DAY1_TASK_TEMPLATES.get(department, DAY1_TASK_TEMPLATES["_default"])
