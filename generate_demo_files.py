import os
import pymupdf as fitz

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DEMO_TEST_FILES")

def create_pdf(filepath, title, content):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4
    
    # Border
    rect = fitz.Rect(30, 30, 565, 812)
    page.draw_rect(rect, color=(0.1, 0.2, 0.4), width=1.5)
    
    # Header Banner
    banner = fitz.Rect(32, 32, 563, 85)
    page.draw_rect(banner, color=(0.12, 0.22, 0.42), fill=(0.12, 0.22, 0.42))
    page.insert_textbox(
        fitz.Rect(45, 45, 550, 80),
        title.upper(),
        fontsize=16,
        fontname="helv",
        color=(1, 1, 1),
        align=fitz.TEXT_ALIGN_CENTER
    )
    
    # Body Content
    page.insert_textbox(
        fitz.Rect(50, 110, 545, 780),
        content,
        fontsize=12,
        fontname="helv",
        color=(0.15, 0.15, 0.15),
        align=fitz.TEXT_ALIGN_LEFT
    )
    
    doc.save(filepath)
    doc.close()
    print(f"Created: {filepath}")

def generate_all_demo_files():
    # ──────────────────────────────────────────────────────────
    # CANDIDATE 1: Rohan Sharma (Software Engineer, Engineering)
    # ──────────────────────────────────────────────────────────
    c1_dir = os.path.join(BASE_DIR, "Candidate_1_Rohan_Sharma")
    os.makedirs(c1_dir, exist_ok=True)
    
    # 1. Aadhaar Card
    create_pdf(
        os.path.join(c1_dir, "rohan_sharma_aadhaar_card.pdf"),
        "Unique Identification Authority of India (UIDAI)",
        """GOVERNMENT OF INDIA / UIDAI
AADHAAR IDENTIFICATION CARD
======================================================

Candidate Name: Rohan Sharma
Father's Name: Rajesh Sharma
Date of Birth: 12/05/1998
Gender: Male

Aadhaar Number: 7492 8840 1928
Enrollment No: 4050/60077/00892

Permanent Address:
Flat #304, Green Meadows Apartments,
Sarjapur Road, Bellandur,
Bengaluru, Karnataka - 560103

Identity Verification Status: Government Verified Record
UIDAI Digital Signature Verified ✓
"""
    )

    # 2. Degree Certificate
    create_pdf(
        os.path.join(c1_dir, "rohan_sharma_degree_certificate.pdf"),
        "Indian Institute of Information Technology",
        """OFFICE OF THE ACADEMIC COUNCIL & REGISTRAR
DEGREE OF BACHELOR OF TECHNOLOGY
======================================================

This is to certify that:

Candidate Name: Rohan Sharma

having satisfied all academic requirements, is admitted to the
Degree of Bachelor of Technology in Computer Science & Engineering.

Graduation Year: 2022
Cumulative Grade Point Average (CGPA): 8.84 / 10.0
Division: First Class with Distinction
Conferred at Bengaluru, Republic of India.

Official Degree Seal & Registrar Signature Verified ✓
"""
    )

    # 3. Countersigned Offer Letter
    create_pdf(
        os.path.join(c1_dir, "rohan_sharma_offer_letter_signed.pdf"),
        "EnterpriseFlow AI - Employment Appointment",
        """OFFICIAL LETTER OF EMPLOYMENT APPOINTMENT
======================================================

Date: 2026-10-31

Dear Rohan Sharma,

EnterpriseFlow AI is pleased to confirm your appointment for
the position of Senior Software Engineer in the Engineering Department.

Key Details:
- Candidate Name: Rohan Sharma
- Role / Designation: Senior Software Engineer
- Department: Engineering / Cloud Systems
- Joining Date: 2026-11-01
- Base Location: Bengaluru HQ (Floor 4, Tech Wing)

ACCEPTED & DIGITALLY COUNTERSIGNED BY EMPLOYEE:
Signature: Rohan Sharma
Date: 2026-10-31
Verification Hash: ef84c0192a77b
"""
    )

    # 4. Bank Cheque / Details
    create_pdf(
        os.path.join(c1_dir, "rohan_sharma_bank_cheque.pdf"),
        "HDFC Bank - Account Verification & Cancelled Cheque",
        """HDFC BANK LIMITED
RETAIL BANKING & CORPORATE PAYROLL SERVICES
======================================================

Official Account Verification Record:

Candidate Name: Rohan Sharma
Account Holder: Rohan Sharma
Account Number: 50100482910394
Account Type: Resident Savings Account
IFSC Code: HDFC0000240
MICR Code: 560240012
Branch: Koramangala 4th Block, Bengaluru

Status: Active KYC Compliant Payroll Account
Bank Branch Manager Digital Sign-Off Verified ✓
"""
    )

    # ──────────────────────────────────────────────────────────
    # CANDIDATE 2: Ananya Deshmukh (Staff Product Designer, Design)
    # ──────────────────────────────────────────────────────────
    c2_dir = os.path.join(BASE_DIR, "Candidate_2_Ananya_Deshmukh")
    os.makedirs(c2_dir, exist_ok=True)

    create_pdf(
        os.path.join(c2_dir, "ananya_deshmukh_aadhaar_card.pdf"),
        "Unique Identification Authority of India (UIDAI)",
        """GOVERNMENT OF INDIA / UIDAI
AADHAAR IDENTIFICATION CARD
======================================================

Candidate Name: Ananya Deshmukh
Date of Birth: 24/09/1997
Gender: Female

Aadhaar Number: 8492 1093 4819
Enrollment No: 2024/91823/00142

Permanent Address:
Plot 12, Design Colony, Indiranagar,
Bengaluru, Karnataka - 560038

Identity Verification Status: Government Verified Record
UIDAI Digital Signature Verified ✓
"""
    )

    create_pdf(
        os.path.join(c2_dir, "ananya_deshmukh_degree_certificate.pdf"),
        "National Institute of Design (NID)",
        """OFFICE OF ACADEMIC AFFAIRS
MASTER OF DESIGN (M.DES) IN HUMAN-COMPUTER INTERACTION
======================================================

This is to certify that:

Candidate Name: Ananya Deshmukh

has successfully completed the prescribed curriculum and evaluation for
the Master of Design in Interaction & Experience Design.

Graduation Year: 2023
Performance: Grade A with Honors
Certificate Serial: NID-2023-M8401
Registrar Seal & Signature Verified ✓
"""
    )

    create_pdf(
        os.path.join(c2_dir, "ananya_deshmukh_offer_letter.pdf"),
        "EnterpriseFlow AI - Employment Appointment",
        """OFFICIAL LETTER OF EMPLOYMENT APPOINTMENT
======================================================

Dear Ananya Deshmukh,

We are delighted to offer you employment as Staff Product Designer
in the Product Design Department at EnterpriseFlow AI.

Key Details:
- Candidate Name: Ananya Deshmukh
- Role / Designation: Staff Product Designer
- Department: Design / UX Systems
- Joining Date: 2026-11-01

ACCEPTED & DIGITALLY COUNTERSIGNED BY EMPLOYEE:
Signature: Ananya Deshmukh
Date: 2026-10-31
"""
    )

    create_pdf(
        os.path.join(c2_dir, "ananya_deshmukh_bank_details.pdf"),
        "State Bank of India - Account Verification",
        """STATE BANK OF INDIA
OFFICIAL CANCELLED CHEQUE & SALARY ACCOUNT VERIFICATION
======================================================

Candidate Name: Ananya Deshmukh
Account Holder: Ananya Deshmukh
Account Number: 20491829401
Account Type: Savings Account
IFSC Code: SBIN0001840
Branch: Indiranagar Branch, Bengaluru

Status: Validated for Enterprise Direct Deposit ✓
"""
    )

    # ──────────────────────────────────────────────────────────
    # MISMATCH TEST: Vikram Verma ID (To demo fraud detection)
    # ──────────────────────────────────────────────────────────
    mismatch_dir = os.path.join(BASE_DIR, "Fraud_Or_Mismatch_Test")
    os.makedirs(mismatch_dir, exist_ok=True)

    create_pdf(
        os.path.join(mismatch_dir, "wrong_id_vikram_verma_aadhaar.pdf"),
        "Government of India - Identity Record",
        """GOVERNMENT OF INDIA / UIDAI
AADHAAR IDENTIFICATION CARD
======================================================

Candidate Name: Vikram Verma
Date of Birth: 15/03/1994
Aadhaar Number: 1948 2940 9182

Address: Mumbai, Maharashtra - 400001
Status: Active

NOTE: If uploaded for Rohan Sharma or Ananya Deshmukh, the OCR
engine will detect 'Vikram Verma' and trigger an immediate
NAME MISMATCH alert on screen!
"""
    )

    print("\n[SUCCESS] All Demo Test PDF Files generated in DEMO_TEST_FILES/")

if __name__ == "__main__":
    generate_all_demo_files()
