import os
import json
import re
import threading

# Check if google.genai is available
GEMINI_AVAILABLE = False
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai_old
        GEMINI_AVAILABLE = True
    except ImportError:
        pass


def get_llm_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not GEMINI_AVAILABLE or not api_key or api_key in ("your_gemini_api_key_here", "CHANGE_ME"):
        return None
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception:
        return None


def extract_info_with_llm(document_text: str, employee_name: str) -> dict:
    """Extract document verification details with Gemini or graceful rule fallback."""
    client = get_llm_client()
    if not client:
        return _extract_with_rules(document_text, employee_name)

    result_holder = [None]
    error_holder = [None]

    def call_gemini():
        try:
            result_holder[0] = _call_gemini_api(client, document_text, employee_name)
        except Exception as e:
            error_holder[0] = str(e)

    thread = threading.Thread(target=call_gemini)
    thread.start()
    thread.join(timeout=6)

    if thread.is_alive() or error_holder[0] or not result_holder[0]:
        return _extract_with_rules(document_text, employee_name)

    return result_holder[0]


def _call_gemini_api(client, document_text: str, employee_name: str) -> dict:
    prompt = f"""
You are a document verification assistant for enterprise employee onboarding.
Expected Employee Name: {employee_name}

Document Text:
{document_text[:1200]}

Return ONLY a valid JSON object without markdown or code fences:
{{
  "extracted_name": "full name found in document or null",
  "document_type": "Aadhaar Card / Degree Certificate / Offer Letter / Bank Details / Identification",
  "name_match": true or false,
  "confidence": "high or medium or low",
  "issues": []
}}
"""
    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            text = (response.text or "").strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            data = json.loads(text)
            data["llm_used"] = True
            return data
        except Exception:
            continue

    return _extract_with_rules(document_text, employee_name)


def _extract_with_rules(document_text: str, employee_name: str) -> dict:
    """Intelligent rule-based extraction fallback."""
    extracted_name = _find_name(document_text)
    name_match = _name_matches(extracted_name, employee_name)

    # Detect document type from keywords
    doc_type = "Identification Document"
    text_lower = document_text.lower()
    if "aadhaar" in text_lower or "uidai" in text_lower or "government of india" in text_lower:
        doc_type = "Aadhaar Card"
    elif "degree" in text_lower or "university" in text_lower or "bachelor" in text_lower or "master" in text_lower:
        doc_type = "Degree Certificate"
    elif "offer" in text_lower or "employment agreement" in text_lower or "salary" in text_lower:
        doc_type = "Offer Letter Signed"
    elif "bank" in text_lower or "ifsc" in text_lower or "account number" in text_lower:
        doc_type = "Bank Details"

    issues = []
    if not extracted_name and not name_match:
        # Check if the expected name itself appears in the text
        if employee_name.lower() in text_lower:
            extracted_name = employee_name
            name_match = True

    if not extracted_name:
        issues.append("Could not extract candidate name from document")
    elif not name_match:
        issues.append(f"Name mismatch: expected '{employee_name}', found '{extracted_name}'")

    confidence = "high" if name_match else ("medium" if extracted_name else "low")

    return {
        "extracted_name": extracted_name or "Not detected",
        "document_type": doc_type,
        "name_match": name_match,
        "confidence": confidence,
        "issues": issues,
        "llm_used": False,
    }


def _find_name(text: str) -> str | None:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    for line in lines:
        # Check if line looks like a title/name line: e.g. "Name: John Doe"
        if ":" in line:
            parts = line.split(":", 1)
            if any(k in parts[0].lower() for k in ["name", "candidate", "employee", "to"]):
                val = parts[1].strip()
                if 2 <= len(val.split()) <= 4:
                    return val.title()
        words = line.split()
        if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
            # Avoid generic header words
            if not any(w.lower() in ["republic", "government", "india", "university", "department", "certificate"] for w in words):
                return line.title()
    return None


def _name_matches(extracted: str | None, expected: str) -> bool:
    if not extracted or not expected:
        return False
    ext_parts = [p.lower() for p in extracted.split()]
    exp_parts = [p.lower() for p in expected.split()]
    # If any non-trivial name part matches or full name matches
    return any(part in extracted.lower() for part in exp_parts if len(part) > 2)
