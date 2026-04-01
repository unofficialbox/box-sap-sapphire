#!/usr/bin/env python3
"""Preview the CAPA Completeness Report JSON that would be sent to Box DocGen.

Reads quality_notifications.jsonl and produces the user_input payload.
Usage: python scripts/preview_capa_report.py
"""

import json
import sys
from datetime import date
from pathlib import Path

JSONL_PATH = Path(__file__).parent.parent / "data" / "quality_notifications.jsonl"


def main():
    today = date.today().isoformat()

    # Load notifications from JSONL
    notifications = []
    tasks = []
    with open(JSONL_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            notifications.append(record)
            for t in record.get("_Task", []):
                t["QualityNotification"] = record["QualityNotification"]
                tasks.append(t)

    print(f"Parsed {len(notifications)} notifications, {len(tasks)} tasks from JSONL\n")

    # Full-population demo figures
    total = 342
    open_count = 47
    closed_count = 295
    corrective = 198
    preventive = 144
    missing_verification = 14
    past_due = 3
    avg_closure_days = 62

    # Build CAPA records for the template (up to 5)
    capa_records = []
    for n in notifications[:5]:
        capa_records.append({
            "notification_number": str(n.get("QualityNotification", "")),
            "notification_type": str(n.get("NotificationType", "")),
            "description": str(n.get("NotificationText", "")),
            "priority": str(n.get("NotificationPriority", "")),
            "status": str(n.get("NotificationStatus", "")),
            "plant": str(n.get("Plant", "1000")),
            "creation_date": str(n.get("CreationDate", today)),
        })

    # Build CAPA tasks for the template (up to 5)
    capa_tasks = []
    for t in tasks[:5]:
        capa_tasks.append({
            "capa_number": str(t.get("QualityNotification", "")),
            "task_description": str(t.get("TaskText", "")),
            "responsible_person": str(t.get("TaskResponsiblePerson", "")),
            "task_type": str(t.get("TaskType", "CORRECTIVE")),
            "task_status": str(t.get("TaskStatus", "IN_PROCESS")),
            "completion_date": str(t.get("TaskCompletionDate", "")),
        })

    # Executive summary — narrative text summarising key metrics
    executive_summary = (
        f"This report assesses the completeness of all Corrective and Preventive Actions (CAPAs) "
        f"within the 24-month assessment period in preparation for FDA QMSR compliance. "
        f"Of {total} CAPAs assessed, {closed_count} have been closed and {open_count} remain open. "
        f"The CAPA population includes {corrective} corrective actions and {preventive} preventive actions. "
        f"{missing_verification} closed CAPAs are missing required effectiveness verification — "
        f"a critical finding given the QMSR's enhanced inspection requirements under ISO 13485:2016. "
        f"{past_due} CAPAs are past due, and the average closure time is {avg_closure_days} days."
    )

    user_input = {
        "report_id": "RPT-CAPA-2026-001",
        "company_name": "MedTech Precision Devices, Inc.",
        "prepared_by": "Quality Management System",
        "report_date": today,
        "assessment_period": "March 2024 - March 2026 (24 months)",
        "total_capas_assessed": str(total),
        "iso_reference": "ISO 13485:2016 §8.5.2, §8.5.3",
        "classification": "CONFIDENTIAL",
        "executive_summary": executive_summary,
        "total_capas": str(total),
        "open_capas": str(open_count),
        "closed_capas": str(closed_count),
        "capas_corrective": str(corrective),
        "capas_preventive": str(preventive),
        "capas_missing_verification": str(missing_verification),
        "capas_past_due": str(past_due),
        "avg_closure_days": str(avg_closure_days),
        "capa_records": capa_records,
        "capa_tasks": capa_tasks,
        "missing_verification_summary": f"The following {missing_verification} CAPAs have been closed but are missing required effectiveness verification per ISO 13485:2016 §8.5.2. This represents a compliance gap that must be addressed before FDA inspection under QMSR.",
        "compliance_assessment": f"The CAPA system is largely compliant with ISO 13485:2016 §8.5.2 and §8.5.3 requirements. The primary compliance gap is the {missing_verification} CAPAs lacking effectiveness verification. Under the QMSR, FDA inspectors will have full access to CAPA records and may cite incomplete effectiveness verification as a nonconformity.",
        "recommendations": f"1. Immediately initiate effectiveness verification for all {missing_verification} identified CAPAs. 2. Establish a 90-day maximum timeline for effectiveness verification after CAPA closure. 3. Update the CAPA procedure to include automated alerts for overdue effectiveness verifications. 4. Conduct a management review of CAPA metrics to identify systemic improvement opportunities.",
    }

    print(json.dumps(user_input, indent=2))


if __name__ == "__main__":
    main()
