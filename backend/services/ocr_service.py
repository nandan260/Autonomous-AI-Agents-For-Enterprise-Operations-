import os
from pathlib import Path
import pymupdf as fitz

try:
    from rapidocr_onnxruntime import RapidOCR
    _ocr_engine = RapidOCR()
except Exception:
    _ocr_engine = None


def extract_text(file_path: str) -> str:
    """Extract text from PDF, images, or text file using PyMuPDF and RapidOCR."""
    if not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        if _ocr_engine is not None:
            try:
                with open(file_path, "rb") as f:
                    img_bytes = f.read()
                res, _ = _ocr_engine(img_bytes)
                if res:
                    return "\n".join([line[1] for line in res])
            except Exception as e:
                print(f"[OCR Image Error]: {e}")
        return ""
    elif ext in [".txt", ".md", ".csv", ".json"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def _extract_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            p_text = page.get_text()
            # If page text is empty (scanned image PDF), use RapidOCR
            if not p_text.strip() and _ocr_engine is not None:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    res, _ = _ocr_engine(img_bytes)
                    if res:
                        p_text = "\n".join([line[1] for line in res])
                except Exception as ocr_err:
                    print(f"[OCR Scanned PDF Error]: {ocr_err}")
            text += p_text + "\n"
        doc.close()
    except Exception as e:
        print(f"[OCR Error] Failed to read {pdf_path}: {e}")
    return text


DOC_ALIASES = {
    "aadhar_card": ["aadhar", "aadhaar", "adhar", "uidai", "id_card", "identity", "passport", "id_proof"],
    "degree_certificate": ["degree", "certificate", "grad", "diploma", "education", "university", "btech", "marksheet"],
    "offer_letter_signed": ["offer", "appointment", "contract", "offer_letter", "agreement", "joining", "signed"],
    "bank_details": ["bank", "cheque", "passbook", "statement", "banking", "account", "void", "ifsc"],
}


def detect_doc_category(filename: str, file_text: str = "") -> str:
    """Classify an uploaded file into one of the 4 required document slots."""
    combined = (filename + " " + file_text[:300]).lower()
    for cat, aliases in DOC_ALIASES.items():
        if any(alias in combined for alias in aliases):
            return cat
    return "aadhar_card"  # default fallback


def find_document(folder: str, doc_name: str, employee_id: str | None = None) -> str | None:
    """Find document file in uploads folder with matching base name or alias, strictly isolated to employee subfolder."""
    if not os.path.isdir(folder):
        return None

    # When an employee_id is specified, strictly isolate search to that employee's folder
    if employee_id:
        emp_sub = os.path.join(folder, employee_id)
        if os.path.isdir(emp_sub):
            folders_to_check = [emp_sub]
        else:
            return None
    else:
        folders_to_check = [folder]

    aliases = DOC_ALIASES.get(doc_name, [doc_name])

    for target_dir in folders_to_check:
        # 1. Exact base matches
        for ext in [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".webp"]:
            path = os.path.join(target_dir, doc_name + ext)
            if os.path.exists(path):
                return path

        # 2. Case-insensitive & alias matches
        try:
            for fname in os.listdir(target_dir):
                fpath = os.path.join(target_dir, fname)
                if os.path.isdir(fpath):
                    continue
                base, ext = os.path.splitext(fname)
                base_lower = base.lower()
                if ext.lower() in [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".webp"]:
                    if any(alias in base_lower for alias in aliases):
                        return fpath
        except Exception:
            pass

    return None


def generate_sample_pdf_pack(employee_name: str, target_dir: str) -> dict[str, str]:
    """Generates authentic candidate-specific KYC PDFs using PyMuPDF."""
    os.makedirs(target_dir, exist_ok=True)
    generated = {}

    templates = {
        "aadhar_card": f"""GOVERNMENT OF INDIA / UIDAI
UNIQUE IDENTIFICATION AUTHORITY OF INDIA
AADHAAR IDENTIFICATION CARD

Candidate Name: {employee_name}
Date of Birth: 14/08/1997
Gender: Verified
Aadhaar Number: 4892 8402 1948
Address: Flat 402, Skyline Residency, Tech Hub, Bengaluru - 560100
Status: Government Verified Identity Record
Enrollment Number: 2024/98172/00192
""",
        "degree_certificate": f"""NATIONAL INSTITUTE OF TECHNOLOGY
OFFICE OF ACADEMIC AFFAIRS & REGISTRAR

DEGREE OF BACHELOR OF TECHNOLOGY
This is to certify that:

Candidate Name: {employee_name}

has successfully completed all requirements for the Bachelor of Technology degree
Major: Computer Science & Systems Engineering
Grade: First Class with Distinction (CGPA: 8.92 / 10.0)
Conferred at Bengaluru, India.
Certificate Number: DEG-2022-849201
""",
        "offer_letter_signed": f"""ENTERPRISEFLOW AI PRIVATE LIMITED
OFFICIAL LETTER OF EMPLOYMENT APPOINTMENT

Candidate Name: {employee_name}
Position: Software Specialist & Cloud Systems
Department: Engineering / Enterprise Operations
Date of Joining: 2026-11-01
Compensation: Agreed as per Enterprise Grade Pay Scale

ACCEPTED & DIGITALLY COUNTERSIGNED BY EMPLOYEE:
Signature: {employee_name}
Date: 2026-10-30
Verification Hash: 8f4b29c1e09a
""",
        "bank_details": f"""HDFC BANK LIMITED
OFFICIAL CANCELLED CHEQUE & ACCOUNT VERIFICATION

Account Holder: {employee_name}
Account Number: 50100482910394
IFSC Code: HDFC0001842
MICR Code: 560240019
Branch: Central Tech Boulevard, Bengaluru
Account Type: Resident Savings Account
Status: Active & KYC Verified
""",
    }

    for doc_key, content in templates.items():
        pdf_path = os.path.join(target_dir, f"{doc_key}.pdf")
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        # Add header banner
        page.draw_rect(fitz.Rect(30, 30, 565, 80), color=(0.1, 0.2, 0.6), fill=(0.95, 0.96, 1.0))
        page.insert_text((45, 60), doc_key.replace("_", " ").upper(), fontsize=16, color=(0.1, 0.2, 0.6))
        # Add body content
        page.insert_textbox(fitz.Rect(45, 100, 550, 720), content, fontsize=12, color=(0.1, 0.1, 0.1))
        # Add stamp / watermarked status
        page.draw_rect(fitz.Rect(45, 750, 260, 790), color=(0.1, 0.6, 0.2), fill=(0.92, 1.0, 0.92))
        page.insert_text((55, 775), "VERIFIED OFFICIAL RECORD", fontsize=11, color=(0.1, 0.6, 0.2))
        doc.save(pdf_path)
        doc.close()
        generated[doc_key] = pdf_path

    return generated
