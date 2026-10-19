# Novacore Applied Technologies — Employee & Operations Policy Manual (2026)

**Document Version:** 4.2  
**Effective Date:** January 1, 2026  
**Classification:** Internal  
**Scope:** All Global Full-Time, Part-Time, Hybrid, and Remote Employees  

---

## 1. Employment & Governance
This policy manual establishes the operational standards and governance framework for all Novacore personnel. Company policies take precedence over local department guidelines unless explicitly exempted in writing by People Operations. Policy ownership resides with the Executive Committee, with annual compliance reviews conducted by Human Resources and Information Security.

---

## 2. Work Schedule & Core Hours
- **Standard Schedule:** Standard business hours are 9:00 AM to 6:00 PM local time.
- **Core Hours:** All full-time employees must observe mandatory core collaboration hours between 10:00 AM and 4:00 PM.
- **Flexibility:** Flexible arrival (8:00 AM – 10:00 AM) and departure (4:00 PM – 7:00 PM) schedules outside core hours are permitted with prior manager agreement.
- **Overtime:** Non-exempt personnel must obtain written supervisor pre-approval prior to working overtime hours.

---

## 3. Remote & Hybrid Work Policy
- **Hybrid Arrangement:** Eligible roles may work remotely up to 3 days per week (minimum 2 mandatory days in-office per week for hybrid staff).
- **International Remote Work:** Temporary overseas/international remote work is strictly capped at a maximum of 10 business days per calendar year and requires formal pre-approval from the Department Head and People Operations at least 14 days in advance.

---

## 4. Leave & Time-Off Benefits
- **Annual Leave:** Full-time staff accrue 24 paid annual leave days per calendar year.
- **Sick Leave:** Employees receive 12 days of paid sick leave annually. Medical certification is required for consecutive sick leaves exceeding 3 business days.
- **Parental Leave:** 16 weeks of fully paid parental leave for primary caregivers; 6 weeks of fully paid leave for secondary caregivers.
- **Bereavement Leave:** Up to 5 consecutive days of paid bereavement leave for immediate family members.
- **Carryover Limit:** A maximum of 5 unused annual leave days may be carried over into the next calendar year, expiring on March 31.

---

## 5. Travel & Business Expenses
- **Airfare:** All flights must be booked via the corporate travel portal. Business-class airfare is strictly restricted to continuous international flights exceeding 6 hours in duration or with written VP approval.
- **Accommodations:** Daily hotel rates are capped at $250/night for standard domestic travel and $350/night for tier-1 metropolitan cities.
- **Per Diem:** Daily meal allowance is $75/day.
- **Receipts:** Itemized receipts are mandatory for all individual reimbursement claims exceeding $25.

---

## 6. Information Security & Device Management
- **Encryption:** All corporate laptops must have full-disk encryption enabled (BitLocker for Windows, FileVault for macOS).
- **Authentication:** Multi-Factor Authentication (MFA) is strictly enforced across all Single Sign-On (SSO) and corporate cloud applications.
- **Credentials:** Password sharing across employees or services is strictly prohibited.
- **Lost/Stolen Devices:** Any lost, stolen, or compromised company hardware must be reported to `security@novacore.internal` within 1 hour of discovery.

---

## 7. Data Classification & Privacy Standard
Novacore classifies all corporate and client information into four security tiers:
1. **Public:** Freely shareable marketing collateral, press releases, and public web documentation.
2. **Internal:** Standard internal communications, policy manuals, organizational charts, and internal wiki pages.
3. **Confidential:** Non-public strategic roadmaps, vendor contracts, proprietary architectures, and pricing models.
4. **Restricted:** Customer Personally Identifiable Information (PII), payment credentials, health records, cryptographic keys, and production source code. Restricted data must never be transferred across unencrypted channels or stored on personal devices.

---

## 8. Generative AI Governance & Usage
- **Approved Tools:** Employees may only use enterprise-approved AI tools on corporate devices under managed workspace licenses.
- **Data Protection:** Pasting, uploading, or training public generative AI tools with Restricted or Confidential customer data is strictly prohibited.
- **Engineering Review:** All AI-assisted software code must undergo mandatory human peer review and automated security scanning prior to merging into production branches.
- **Decision Oversight:** Generative AI tools must never be used autonomously to make binding employment, hiring, promotion, performance evaluation, or disciplinary decisions.

---

## 9. Software Engineering & Code Integrity
- **Version Control:** All code must reside in approved corporate GitHub enterprise repositories.
- **Secrets Management:** Hardcoded secrets, API tokens, passwords, and private keys in source code repositories are prohibited. Dedicated secrets managers (Vault / AWS Secrets Manager) must be used.
- **Code Review:** Every pull request requires at least one peer code review and passing automated CI/CD security lints before merging into the main branch.

---

## 10. Code of Conduct & Ethics
- **Professional Behavior:** Novacore enforces zero tolerance for harassment, discrimination, or abusive workplace conduct.
- **Conflicts of Interest:** External consulting, second employment, or board memberships that create a conflict of interest with Novacore business must be disclosed to the Ethics Committee.
- **Gifts:** Gifts from vendors, suppliers, or partners valued above $50 must be reported and declined or surrendered to People Operations.

---

## 11. Performance Evaluation & Compensation
- **Review Cycles:** Formal performance evaluations occur twice yearly (Q2 mid-year review and Q4 annual performance cycle).
- **Promotion & Merit:** Promotions and salary adjustments are determined by demonstrated competencies and peer feedback.
- **Appeals:** Employees may file a written evaluation appeal to HR within 14 days of review publication.
- **Disbursement:** Payroll is disbursed semi-monthly on the 15th and the final business day of each month.

---

## 12. Onboarding & Access Lifecycle
- **New Hires:** Mandatory security and compliance training must be completed within the first 5 business days of joining.
- **Access Principles:** System access follows the Principle of Least Privilege (PoLP).
- **Offboarding:** Upon employee departure, all SSO accounts, VPN tokens, and system credentials are automatically revoked at the end of the final working day. Corporate hardware must be returned within 48 hours.

---

## 13. Security Incident Management & Escalation
Incidents are categorized by severity with strict Response SLAs:
- **SEV-1 (Critical):** Total system outage, confirmed data breach, or active cyber intrusion. SLA < 15 minutes.
- **SEV-2 (Major):** High business impact, core customer service degradation. SLA < 30 minutes.
- **SEV-3 (Minor):** Partial functionality loss or non-critical application defect. SLA < 2 hours.
- **SEV-4 (Low):** Cosmetic bug or minor administrative issue. SLA < 24 hours.

---

## 14. Appendix: Historical Security Audit Log
- **NC-2026-017:** Staging API key accidentally exposed in a public snippet repo; revoked and rotated in 12 minutes, zero customer data compromised.
- **NC-2026-041:** Quarterly employee phishing simulation; recorded a 4.2% click rate; targeted training assigned to affected staff.
- **NC-2026-052:** Unauthorized third-party cloud storage service utilized by contractor; account revoked, data integrity verified.
