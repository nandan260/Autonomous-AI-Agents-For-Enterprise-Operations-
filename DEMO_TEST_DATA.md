# 📋 EnterpriseFlow AI: Live Demo Test Data & File Cheatsheet

Use this cheatsheet to perform a live demonstration for hackathon judges and faculty.

---

## 📂 Where Are the Test Files Located on Your Computer?
All generated test files are ready in your project directory:  
👉 `C:\Users\nandan\Downloads\enterpriseflow-ai-main\enterpriseflow-ai-main\DEMO_TEST_FILES\`

```
DEMO_TEST_FILES/
├── Candidate_1_Rohan_Sharma/
│   ├── rohan_sharma_aadhaar_card.pdf           (UIDAI Government ID)
│   ├── rohan_sharma_degree_certificate.pdf      (B.Tech CS Degree)
│   ├── rohan_sharma_offer_letter_signed.pdf     (Countersigned Offer)
│   └── rohan_sharma_bank_cheque.pdf             (HDFC Payroll Cheque)
│
├── Candidate_2_Ananya_Deshmukh/
│   ├── ananya_deshmukh_aadhaar_card.pdf        (UIDAI Government ID)
│   ├── ananya_deshmukh_degree_certificate.pdf   (M.Des Design Degree)
│   ├── ananya_deshmukh_offer_letter.pdf         (Countersigned Offer)
│   └── ananya_deshmukh_bank_details.pdf         (SBI Payroll Details)
│
└── Fraud_Or_Mismatch_Test/
    └── wrong_id_vikram_verma_aadhaar.pdf        (Intentional Mismatch Test)
```

---

## 🎯 DEMO SCENARIO 1: The Perfect 100% Pass Demo (Candidate: Rohan Sharma)

### Step 1: Register Candidate
1. Open **`http://localhost:8000`** in your browser.
2. Click **`+ Register Candidate`** in the top-right.
3. Fill in the following exact data:
   * **Full Name:** `Rohan Sharma`
   * **Department:** `Engineering`
   * **Role / Title:** `Senior Software Engineer`
   * **Joining Date:** Today's Date
4. Click **`Register Candidate`**.
   * *Notice:* The system assigns a unique ID like `EMP-2024-XXXXXX`, corporate email `rohan.sharma@enterpriseflow.ai`, and reserves desk space.

---

### Step 2: Upload Documents (2 Demo Options)
Navigate to the **`Doc Verification`** tab (ensure *Rohan Sharma* is selected in the top dropdown).

* **Option A (Batch Drag-and-Drop):**
  1. Open Windows File Explorer to:  
     `C:\Users\nandan\Downloads\enterpriseflow-ai-main\enterpriseflow-ai-main\DEMO_TEST_FILES\Candidate_1_Rohan_Sharma\`
  2. Select all **4 PDF files** together (`Ctrl + A`).
  3. Drag and drop them into the **Batch Upload Dropzone** in the browser.
* **Option B (1-Click Instant Demo):**
  1. Simply click the **`⚡ Auto-Generate All 4 KYC Docs`** button!

**What Happens on Screen:**
* All 4 cards turn emerald green with `Verified [OCR]` badges.
* Candidate Name Match displays: `Validated ✓`
* Confidence Score displays: `HIGH`
* Issues: `None (Clean verification)`

---

### Step 3: Run Live Pipeline with Human Governance
1. Click the **`Live Pipeline`** tab and click **`Start Execution`**.
2. **Watch the Freeze at 25% (Gate 1):**
   * The pipeline executes Stage 1 & 2, then **physically halts at 25%**.
   * An amber **`Human Intervention Required`** banner appears with Checkpoint ID `APP-IT-...`.
   * Displays: Laptop spec (**MacBook Pro 14" M3 Pro**) and enterprise software licenses.
   * Click **`Authorize & Proceed to Next Agent`**.
3. **Watch the Freeze at 50% (Gate 2):**
   * The pipeline finishes IT setup and **halts again at 50%**.
   * An amber **`Manager Confirmation`** banner appears with Checkpoint ID `APP-TM-...`.
   * Displays: Reporting Manager, Peer Buddy, and Physical Desk.
   * Click **`Authorize & Proceed`**.
4. **Completion (100%):**
   * Pipeline reaches **100% Complete** with a celebration banner!

---

### Step 4: Show Training LMS & Audit Trail
1. Switch to the **`Training & LMS`** tab:
   * Show the 4 role-specific courses.
   * Check off a Day-1 task (e.g. *Attend Dev Team Standup*). Show it turn green in real-time.
2. Switch to the **`Audit Trails`** tab:
   * Show the faculty the 22 cryptographic timestamped events with approval IDs.

---

## 🚨 DEMO SCENARIO 2: Fraud & Mismatch Detection (Judges Love This!)

Demonstrate how your AI protects the enterprise from impersonation and fraudulent uploads:

1. In the **`Doc Verification`** tab for **Rohan Sharma**:
2. Click the **`Upload Aadhaar`** button on the Aadhaar card.
3. Select the file:  
   `DEMO_TEST_FILES\Fraud_Or_Mismatch_Test\wrong_id_vikram_verma_aadhaar.pdf`
4. **What Happens on Screen:**
   * The card instantly turns amber/red!
   * Extracted Name displays: **`Vikram Verma`**
   * Candidate Name Match displays: **`Mismatch X`**
   * Issues Box displays:  
     `Name mismatch: expected 'Rohan Sharma', found 'Vikram Verma'`
5. **Tell the Judges:**
   > *"Notice our AI didn't just read the file—it cross-referenced the candidate's HR record with the UIDAI text stream and flagged an immediate identity mismatch, preventing unvetted candidates from entering our corporate network."*
