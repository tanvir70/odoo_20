# Bangladesh VAT & Mushak Management (`bd_mushak_vat`)
### Odoo 20 Statutory Accounting Localization Extension for Bangladesh

`bd_mushak_vat` provides complete compliance with the **Value Added Tax and Supplementary Duty Act 2012**, **VAT & SD Rules 2016 (Rule 40)**, and the **VDS Guidelines (SRO 182-Ain/2025/310-Mushak)**.

---

## 📋 Features Overview

1. **Master Data & BIN Validation (Phase 1)**:
   - Dedicated 13-digit numeric `mushak_bin` on partners and companies with auto-sanitization (stripping dashes and whitespace).
   - Validation constraint enforcing strictly 13 numeric digits.
   - Two-way commercial partner synchronization (`_commercial_fields` / `_synced_commercial_fields`).
   - Partner VDS Withholding Entity classification (`government`, `semi_government`, `bank`, `insurance`, `ngo`, `limited_company`, etc.) and Supplier Type (`manufacturer`, `trader`, `service_provider`, `importer`).

2. **Fiscal Year Sequences & Invoicing Lifecycle (Phase 2)**:
   - Annual sequence reset on Bangladesh fiscal year (1 July – 30 June) via `ir.sequence._create_date_range_seq()`.
   - Gapless numbering for Mushak 6.3 Tax Invoice (`%(range_year)s-000001`), Mushak 6.7 Credit Note, and Mushak 6.8 Debit Note.
   - Statutory integrity: Resetting to draft retains the assigned number; numbered records cannot be deleted (`unlink` protected).
   - Origin references and adjustment reasons strictly mandated on 6.7 and 6.8 before posting.

3. **Supplementary Duty (SD) Tax Engine (Phase 3)**:
   - Cumulative tax stacking: SD (Sequence 10, `include_base_amount=True`) affects the VAT base (Sequence 20, `is_base_affected=True`).
   - Stored per-line breakdown on `account.move.line`: `mushak_sd_rate`, `mushak_sd_amount`, `mushak_vat_rate`, `mushak_vat_amount`, `mushak_value_excl_tax`.
   - Constraint preventing mixed tax inclusion (exclusive SD with inclusive VAT).

4. **Statutory QWeb Reports & Bangla Typography (Phase 4)**:
   - Statutory 11-column Mushak 6.3 Tax Invoice, Mushak 6.7 Credit Note, and Mushak 6.8 Debit Note.
   - Dual amount-in-words converter (`mushak.amount.words`):
     - South-Asian English (Lakh / Crore notation; e.g. *One Lakh Seventy-Two Thousand Five Hundred Taka Only*).
     - Bengali words (কোটি, লক্ষ, হাজার, শত; e.g. *এক লক্ষ বাহাত্তর হাজার পাঁচ শত টাকা মাত্র*).
   - Bangla numeral conversion (`০১২৩৪৫৬৭৮৯`).
   - Embedded Noto Sans Bengali font for crisp PDF shaping.

5. **Statutory Registers 6.1 & 6.2 + Excel Export (Phase 6)**:
   - High-performance PostgreSQL views for **Mushak 6.1 Purchase Book** and **Mushak 6.2 Sales Book**.
   - Continuous audit trail: Cancelled sales challans appear with 0.00 amounts to prevent numbering gaps.
   - Input VAT claimable flag checking valid supplier challan numbers.
   - Excel (`.xlsx`) export wizard with bilingual headers, frozen panes, and `=SUM()` formulas.

6. **VAT Deducted at Source (VDS) & Mushak 6.6 (Phase 5)**:
   - Dated SRO rate table (`mushak.vds.rule`) matching product service codes (e.g. `S004.00`) and supplier classifications.
   - Automated payment difference / write-off handling during payment registration targeting **VDS Payable** (liability) or **VDS Receivable** (asset).
   - Generates statutory **Mushak 6.6 VDS Certificate** with July–June sequence numbering and compliance deadlines.

7. **Public QR Code Verification Portal (Phase 7)**:
   - 43-character URL-safe cryptographic token per document.
   - Public route `/mushak/verify/<token>` showing sanitized authenticity summary without exposing confidential lines.
   - Masked buyer names for privacy (`Dha***`).
   - Abuse protection: `X-Robots-Tag: noindex, nofollow`, `Cache-Control: no-store`.

---

## 🏛️ Step Zero Technical Audit (`l10n_bd`)

- **Existing Chart of Accounts (`l10n_bd`)**:
  - `112400`: VAT Input (`asset_current`)
  - `112500`: VAT Receivable (`asset_receivable`)
  - `211020`: VAT Payable (`liability_payable`)
  - `211040`: VAT Output (`liability_current`)
- **Fiscal Year**: Confirmed June 30 fiscal year end (`fiscalyear_last_month: 6`, `fiscalyear_last_day: 30`).
- **BIN Field Decision**: Implemented as dedicated `mushak_bin` rather than generic `vat` field because Bangladesh income-tax e-TIN (12 digits) is frequently entered in standard vat fields by users.

---

## 🧪 Automated Test Suite

Unit and integration tests are located in `tests/`:
- `test_mushak_partner.py`: BIN validation, 13-digit constraints, non-digit stripping, commercial inheritance.
- `test_mushak_sequence.py`: 30 June vs 1 July fiscal boundary, gapless numbering, draft reset preservation, deletion prevention.
- `test_mushak_sd_vat.py`: 9-case tax calculation matrix, base stacking, mixed inclusion prevention, order invariance.
- `test_mushak_words.py`: English South-Asian words, Bengali words (1-99 irregular lookup), Bengali digits.
- `test_mushak_vds.py`: SRO rule matching, validity windows, 6.6 certificate workflow.
- `test_mushak_verify.py`: Public route token parsing, masking, 404 security handling.
