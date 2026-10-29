# Odoo 20 Advanced Inventory Management & Custom Addons

Custom business workflow extensions for Odoo 20:
1. **`bd_stock_transfer_approval`**: Inter-Warehouse Stock Transfer Requisition & Approval Workflow.
2. **`bd_low_stock_alert`**: Automated Multi-Warehouse Low Stock Detection & Replenishment Monitor.

---

## 📦 Custom Modules Overview

### 1. `bd_stock_transfer_approval`
- **Requisition Lifecycle**: `Draft` ➔ `Submitted` ➔ `Approved` / `Rejected` ➔ `Done`.
- **Pre-Transfer Stock Snapshot**: Captures source warehouse available quantity at the time of submission.
- **Controlled Approvals**: Role-based access groups (`Requester`, `Approver`, `Manager`).
- **Audit Chatter**: Tracks who requested, approved, or rejected with mandatory rejection reasons.
- **Native Picking Bridge**: Automatically generates native Odoo internal transfers (`stock.picking`) with moves upon approval and marks the requisition `Done` when validated.

### 2. `bd_low_stock_alert`
- **Warehouse-Specific Thresholds**: Configurable `Low Stock Alert Threshold` and `Target Restock Level` on product templates.
- **Severity Classification**:
  - `Out of Stock`: On-hand quantity $\le 0$.
  - `Critical Low`: On-hand quantity $< 50\%$ of threshold.
  - `Low Stock`: On-hand quantity $<$ threshold.
- **Dual Trigger Engine**:
  - **Real-Time Hook**: Automatically evaluates stock whenever any delivery order, sale pick, or transfer completes (`stock.move`).
  - **Scheduled Action (Cron)**: Periodic background evaluation every hour.
- **1-Click Replenishment Bridge**: Generates pre-filled transfer requisitions directly from active shortage alerts.
- **Auto-Resolution**: Automatically marks alerts resolved with chatter logs when stock is replenished.
- **Product Form Stat Button**: Real-time counter of active alerts directly on the product form.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Odoo 20.0 Community or Enterprise

### Quick Start
```bash
# Clone repository
git clone git@github.com:tanvir70/<repo-name>.git
cd <repo-name>

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy config and update database credentials
cp odoo.conf.example odoo.conf

# Install custom modules into your database
python3 odoo/odoo-bin -c odoo.conf -d <your-db-name> -i bd_stock_transfer_approval,bd_low_stock_alert
```

---

## 🔒 Security Groups
- **Refyne Stock Requester**: Can create, view, and submit own transfer requisitions.
- **Refyne Stock Transfer Approver**: Can approve or reject submitted requisitions.
- **Refyne Inventory & Approval Manager**: Full administrative access across all requisitions, alerts, and settings.
