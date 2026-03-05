#!/usr/bin/env python3
"""Generate sample controlled document PDFs from controlled_documents.jsonl."""

import json
import os
from datetime import datetime
from fpdf import FPDF

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "controlled_documents.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "documents")

COMPANY = "MedTech Precision Devices, Inc."
COMPANY_ADDR = "4500 Innovation Drive, San Jose, CA 95134"

PERSONNEL = {
    "JSMITH": "John Smith, Quality Engineer",
    "AKUMAR": "Anika Kumar, Supplier Quality Manager",
    "RJONES": "Robert Jones, Production Supervisor",
    "SLEE": "Sarah Lee, Director of Quality Assurance",
    "DKIM": "David Kim, Quality Technician",
    "MWEBER": "Michael Weber, Senior Quality Engineer",
    "TCHEN": "Tina Chen, Process Engineer",
    "LPARK": "Lisa Park, QC Lab Analyst",
    "VPQUALITY": "Dr. James Hartwell, VP Quality & Regulatory",
}

# Section content templates keyed by DocumentID
DOCUMENT_BODIES = {
    "DOC-QMS-001": {
        "sections": [
            ("1. Purpose and Scope", [
                "This Quality Manual defines the Quality Management System (QMS) of {company} in accordance with "
                "ISO 13485:2016 as incorporated by reference into the FDA Quality Management System Regulation (QMSR), "
                "21 CFR Part 820, effective February 2, 2026.",
                "The QMS applies to the design, development, production, storage, distribution, installation, and servicing "
                "of Class II and Class III medical devices manufactured at our facilities.",
                "This manual serves as the top-level document of the QMS documentation hierarchy and provides a framework "
                "for establishing quality objectives, conducting management reviews, and ensuring continuous improvement."
            ]),
            ("2. Quality Management System (ISO 13485 Clause 4)", [
                "2.1 General Requirements",
                "{company} has established, documented, implemented, and maintains a quality management system and "
                "continually maintains its effectiveness in accordance with ISO 13485:2016 and applicable regulatory requirements.",
                "The organization has identified the processes needed for the QMS, determined their sequence and interaction, "
                "and applies a risk-based approach to the control of appropriate processes.",
                "2.2 Documentation Requirements",
                "The QMS documentation includes: this quality manual, documented procedures required by ISO 13485:2016, "
                "documents needed to ensure effective planning and control of processes, records required by the standard, "
                "and documentation specified by applicable regulatory requirements including 21 CFR Part 820.",
                "2.3 Control of Documents (ref: SOP-DOC-001)",
                "All documents required by the QMS are controlled per SOP-DOC-001. Documents are reviewed and approved "
                "for adequacy prior to issue, reviewed and updated as necessary, and current revision status is maintained.",
                "2.4 Control of Records (ref: SOP-REC-001)",
                "Records are maintained to provide evidence of conformity to requirements. Records are retained for at least "
                "the lifetime of the medical device, or as specified by applicable regulatory requirements, but not less than "
                "two years from device release."
            ]),
            ("3. Management Responsibility (ISO 13485 Clause 5)", [
                "3.1 Management Commitment",
                "Top management demonstrates commitment to the QMS by communicating the importance of meeting customer "
                "and regulatory requirements, establishing quality policy and objectives, conducting management reviews, "
                "and ensuring availability of resources.",
                "3.2 Quality Policy",
                "{company} is committed to designing, manufacturing, and delivering medical devices that consistently meet "
                "customer requirements and applicable regulatory standards. We maintain an effective quality management "
                "system that promotes continuous improvement, risk-based decision making, and patient safety.",
                "3.3 Management Review (ref: SOP-MR-001)",
                "Management reviews are conducted at planned intervals (minimum semi-annually) per SOP-MR-001. "
                "Note: Under the QMSR, management review records are subject to FDA inspection. The exemption previously "
                "provided under 21 CFR 820.180(c) has been removed."
            ]),
            ("4. Resource Management (ISO 13485 Clause 6)", [
                "4.1 Provision of Resources",
                "{company} determines and provides resources needed to implement and maintain the QMS and meet "
                "applicable regulatory and customer requirements.",
                "4.2 Human Resources",
                "Personnel performing work affecting product quality are competent based on appropriate education, "
                "training, skills, and experience. Training records are maintained per SOP-REC-001.",
                "4.3 Infrastructure",
                "The organization maintains the infrastructure needed to achieve conformity to product requirements, "
                "including buildings, process equipment (hardware and software), and supporting services."
            ]),
            ("5. Product Realization (ISO 13485 Clause 7)", [
                "5.1 Planning of Product Realization",
                "Product realization processes are planned consistent with QMS requirements. Risk management processes "
                "are documented per SOP-RM-001 in accordance with ISO 14971.",
                "5.2 Design and Development (ref: SOP-DD-001)",
                "Design and development activities follow SOP-DD-001 covering planning, inputs, outputs, review, "
                "verification, validation, transfer, change control, and design files per ISO 13485:2016 Section 7.3.",
                "5.3 Purchasing (ref: SOP-SUP-001)",
                "Supplier evaluation, selection, and monitoring are conducted per SOP-SUP-001. Written quality agreements "
                "are maintained with critical suppliers. Supplier audit reports are subject to FDA inspection under the QMSR.",
                "5.4 Production and Service Provision",
                "Production processes are controlled through documented procedures, work instructions, suitable equipment, "
                "monitoring and measurement activities, and defined product release criteria."
            ]),
            ("6. Measurement, Analysis and Improvement (ISO 13485 Clause 8)", [
                "6.1 Feedback and Complaint Handling (ref: SOP-COMP-001)",
                "Customer feedback is gathered and monitored. Complaints are handled per SOP-COMP-001 in accordance "
                "with ISO 13485:2016 Section 8.2.2 and applicable regulatory requirements.",
                "6.2 Internal Audit (ref: SOP-AUD-001)",
                "Internal audits are conducted per SOP-AUD-001 at planned intervals using a risk-based audit program. "
                "Note: Under the QMSR, audit reports are subject to FDA inspection.",
                "6.3 Control of Nonconforming Product (ref: SOP-NC-001)",
                "Nonconforming product is identified, controlled, and dispositioned per SOP-NC-001.",
                "6.4 Corrective and Preventive Action (ref: SOP-CAPA-001)",
                "The CAPA process is defined in SOP-CAPA-001. Corrective actions address existing nonconformities. "
                "Preventive actions address potential nonconformities. Actions are proportionate to the effects of the "
                "nonconformities encountered, as required by ISO 13485:2016 Sections 8.5.2 and 8.5.3.",
                "6.5 Regulatory Reporting (ref: SOP-REG-001)",
                "Adverse events and advisory notices are reported per SOP-REG-001 in accordance with 21 CFR 803 and "
                "ISO 13485:2016 Section 8.2.3."
            ]),
        ]
    },
    "DOC-QMS-002": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the controls for creating, reviewing, approving, distributing, and maintaining "
                "documents within the Quality Management System of {company}, in compliance with ISO 13485:2016 "
                "Section 4.2.4 and the FDA QMSR (21 CFR Part 820)."
            ]),
            ("2. Scope", [
                "This procedure applies to all controlled documents within the QMS, including the quality manual, "
                "standard operating procedures (SOPs), work instructions (WIs), forms, templates, specifications, "
                "medical device files, validation protocols, and external documents of regulatory origin.",
                "Records are controlled per SOP-REC-001 (Control of Records)."
            ]),
            ("3. Responsibilities", [
                "Document Author: Drafts and revises documents; ensures technical accuracy.",
                "Document Reviewer: Reviews documents for completeness, clarity, and compliance.",
                "Document Approver: Approves documents for release; ensures alignment with QMS objectives.",
                "Quality Assurance: Maintains the document control system, master document list, and distribution records.",
                "All Personnel: Use only current, approved versions of documents at their point of use."
            ]),
            ("4. Procedure", [
                "4.1 Document Creation and Identification",
                "All controlled documents shall be assigned a unique document ID using the format: "
                "DOC-QMS-NNN for QMS-level documents, SOP-XXX-NNN for procedures, WI-XXX-NNN for work instructions.",
                "Each document shall include: document ID, title, revision number, effective date, author, reviewer, "
                "approver, and page numbering.",
                "4.2 Review and Approval",
                "Documents shall be reviewed for adequacy and approved prior to issue. Reviews shall be conducted by "
                "personnel with access to pertinent background information. The review cycle shall not exceed 5 business days "
                "unless extended by the Document Approver.",
                "4.3 Revision Control",
                "Changes to documents require the same level of review and approval as the original document. "
                "Each revision shall increment the revision number. A revision history table shall document the nature "
                "of each change, the date, and the person responsible.",
                "4.4 Distribution and Availability",
                "Current versions of applicable documents shall be available at all points of use. The electronic document "
                "management system (Box) serves as the single source of truth for all controlled documents. "
                "Printed copies are considered uncontrolled unless stamped 'CONTROLLED COPY' with the print date.",
                "4.5 External Documents",
                "External documents necessary for QMS operation (e.g., ISO standards, regulatory guidance, supplier "
                "specifications) shall be identified, cataloged, and their distribution controlled.",
                "4.6 Obsolete Documents",
                "Obsolete documents shall be promptly removed from points of use. At least one copy shall be retained "
                "and marked 'OBSOLETE' for the retention period defined in SOP-REC-001. For medical device documents, "
                "retention shall be at least the lifetime of the device.",
                "4.7 QMSR-Specific Requirements",
                "Under the QMSR effective February 2, 2026, the exemption previously granted under 21 CFR 820.180(c) "
                "has been removed. Management review records, internal audit reports, and supplier audit reports are now "
                "subject to FDA inspection and must be maintained and readily available."
            ]),
            ("5. Records", [
                "The following records shall be maintained per SOP-REC-001:",
                "- Master Document List (current revision status of all controlled documents)",
                "- Document Change Requests (DCRs)",
                "- Document approval signatures (electronic or wet-ink)",
                "- Distribution records",
                "- Obsolete document archive log"
            ]),
        ]
    },
    "DOC-QMS-003": {
        "sections": [
            ("1. Purpose", [
                "This procedure establishes requirements for the identification, storage, security, integrity, retrieval, "
                "retention, and disposition of quality records within the QMS of {company}, per ISO 13485:2016 Section 4.2.5."
            ]),
            ("2. Scope", [
                "Applies to all records that provide evidence of conformity to requirements and effective operation of the QMS."
            ]),
            ("3. Procedure", [
                "3.1 Record Identification and Storage",
                "Records shall be clearly identified, indexed, and stored in a manner that ensures they remain legible, "
                "readily identifiable, and retrievable. Electronic records are stored in Box with appropriate access controls.",
                "3.2 Security and Integrity",
                "Access to quality records shall be restricted to authorized personnel. Electronic records shall be protected "
                "by access controls, audit trails, and regular backups. Changes to records shall remain identifiable.",
                "3.3 Confidential Health Information",
                "Methods for protecting confidential health information shall comply with applicable regulatory requirements "
                "including HIPAA where applicable.",
                "3.4 Retention Periods",
                "Records shall be retained for at least the lifetime of the medical device as defined by {company}, or as "
                "specified by applicable regulatory requirements, but not less than two years from medical device release.",
                "Current retention schedule: Design records - device lifetime + 5 years; Production records - device lifetime; "
                "CAPA records - 10 years minimum; Complaint records - device lifetime; Training records - employment + 3 years.",
                "3.5 Disposition",
                "Records past their retention period may be disposed of following documented disposition procedures. "
                "Disposition shall be recorded and shall ensure confidential information is properly destroyed."
            ]),
        ]
    },
    "DOC-QMS-004": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the process for identifying, documenting, investigating, and resolving corrective "
                "and preventive actions (CAPAs) at {company}, in compliance with ISO 13485:2016 Sections 8.5.2 and 8.5.3 "
                "and the FDA QMSR."
            ]),
            ("2. Scope", [
                "Applies to all CAPAs initiated from: customer complaints, internal audits, supplier audits, nonconforming "
                "product, process deviations, management review findings, regulatory inspections, post-market surveillance, "
                "and risk management activities."
            ]),
            ("3. Definitions", [
                "Correction: Action to eliminate a detected nonconformity (immediate containment).",
                "Corrective Action: Action to eliminate the cause of a detected nonconformity to prevent recurrence "
                "(ISO 13485:2016 Section 8.5.2).",
                "Preventive Action: Action to eliminate the cause of a potential nonconformity to prevent occurrence "
                "(ISO 13485:2016 Section 8.5.3).",
                "CAPA: The overall system encompassing corrective and preventive action processes."
            ]),
            ("4. Procedure", [
                "4.1 CAPA Initiation",
                "Any employee may identify a potential CAPA. The Quality Assurance department evaluates the need for a "
                "formal CAPA based on risk assessment, severity, frequency, and detectability.",
                "CAPAs are documented in the SAP Quality Notification system with TaskType = CORRECTIVE or PREVENTIVE.",
                "4.2 Investigation and Root Cause Analysis",
                "Root cause analysis shall be performed using appropriate methodology (5-Why, Fishbone, Fault Tree Analysis). "
                "The investigation shall determine the causes of the nonconformity or potential nonconformity.",
                "Investigation results are recorded in the Quality Notification Item Cause records.",
                "4.3 Action Planning",
                "Corrective and preventive actions shall be planned, documented, and assigned to responsible personnel "
                "with target completion dates. Actions shall be proportionate to the effects of the nonconformities "
                "encountered, as required by ISO 13485:2016.",
                "4.4 Implementation",
                "Actions are implemented per the plan. Any affected documents (SOPs, WIs, specifications) shall be "
                "revised through the document change control process (SOP-DOC-001).",
                "4.5 Verification of Effectiveness",
                "Each CAPA shall be verified to confirm that: (a) the action was implemented as planned, (b) the action "
                "effectively addressed the root cause, (c) the action does not adversely affect the ability to meet "
                "regulatory requirements or the safety and performance of the medical device.",
                "4.6 CAPA Closure",
                "CAPAs are closed by Quality Assurance upon successful verification of effectiveness. Closed CAPAs are "
                "reported in Management Review per SOP-MR-001."
            ]),
            ("5. Records", [
                "All CAPA records are maintained in the SAP QM module (Quality Notifications) and supporting documents "
                "are stored in Box. Records include: CAPA initiation form, investigation and root cause analysis, "
                "action plan, implementation evidence, effectiveness verification, and closure approval."
            ]),
        ]
    },
    "DOC-QMS-005": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the process for receiving, recording, evaluating, investigating, and resolving "
                "complaints related to medical devices manufactured by {company}, per ISO 13485:2016 Section 8.2.2."
            ]),
            ("2. Scope", [
                "Applies to all complaints: written, electronic, or oral communications alleging deficiencies related to "
                "identity, quality, durability, reliability, usability, safety, or performance of released medical devices."
            ]),
            ("3. Procedure", [
                "3.1 Complaint Receipt and Recording",
                "All complaints are logged in the SAP QM system as Quality Notification type Q1 (customer complaint) or "
                "Q2 (vendor complaint) within 24 hours of receipt. Each complaint record includes: date received, source, "
                "product identification, lot/batch number, nature of complaint, and initial risk assessment.",
                "3.2 Evaluation and Triage",
                "Quality Assurance evaluates each complaint to determine if it constitutes a reportable event under "
                "21 CFR 803 (MDR) and whether investigation is required. Priority is assigned: 1 (High - safety/critical), "
                "2 (Medium), 3 (Low).",
                "3.3 Investigation",
                "Complaints requiring investigation are investigated within timelines based on priority. The investigation "
                "determines root cause, extent of the issue, and whether corrective/preventive action is needed.",
                "If investigation determines external parties contributed to the complaint, relevant information is "
                "exchanged per ISO 13485:2016 Section 8.2.2.",
                "3.4 CAPA Linkage",
                "When investigation determines corrective or preventive action is needed, a CAPA is initiated per "
                "SOP-CAPA-001. The complaint notification is linked to the CAPA record.",
                "3.5 Regulatory Reporting",
                "Complaints meeting MDR reporting criteria are reported per SOP-REG-001 within required timeframes.",
                "3.6 Complaint Closure",
                "Complaints are closed when investigation is complete and any required actions have been initiated."
            ]),
        ]
    },
    "DOC-QMS-006": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines controls for identifying, documenting, segregating, evaluating, and dispositioning "
                "nonconforming product, per ISO 13485:2016 Section 8.3."
            ]),
            ("2. Procedure", [
                "2.1 Identification and Segregation",
                "Nonconforming product is identified and segregated to prevent unintended use or delivery. Nonconformance "
                "is documented as a Quality Notification type Q3 (internal) in SAP QM.",
                "2.2 Evaluation and Disposition",
                "Disposition options include: (a) rework per approved rework procedures, (b) accept by concession with "
                "documented justification and regulatory compliance verification, (c) reject/scrap, (d) return to supplier.",
                "2.3 Nonconforming Product Detected After Delivery",
                "When nonconforming product is detected after delivery, actions appropriate to the effects are taken. "
                "Advisory notices are issued per applicable regulatory requirements (ISO 13485:2016 Section 8.3.3).",
                "2.4 Rework",
                "Rework is performed per documented procedures that undergo the same review and approval as the original "
                "procedure. Reworked product is re-verified against acceptance criteria.",
                "2.5 Notification of External Parties",
                "The evaluation includes determination of the need for investigation and notification of any external "
                "party responsible for the nonconformity."
            ]),
        ]
    },
    "DOC-QMS-007": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the process for conducting management reviews of the Quality Management System "
                "at {company}, per ISO 13485:2016 Section 5.6."
            ]),
            ("2. QMSR Impact Notice", [
                "IMPORTANT: Under the QMSR (effective February 2, 2026), management review records are subject to FDA "
                "inspection. The exemption previously provided under 21 CFR 820.180(c) has been removed. All management "
                "review records must be maintained and readily available for regulatory inspection."
            ]),
            ("3. Procedure", [
                "3.1 Review Schedule",
                "Management reviews are conducted at least semi-annually. Ad hoc reviews may be called when significant "
                "quality events occur.",
                "3.2 Review Inputs (per ISO 13485:2016 Section 5.6.2)",
                "Review inputs include: (a) feedback, (b) complaint handling data, (c) reporting to regulatory authorities, "
                "(d) internal and external audit results, (e) monitoring and measurement of processes and product, "
                "(f) corrective action status, (g) preventive action status, (h) follow-up from previous reviews, "
                "(i) changes affecting the QMS, (j) recommendations for improvement, (k) applicable new or revised "
                "regulatory requirements including the QMSR transition.",
                "3.3 Review Outputs",
                "Documented decisions and actions related to: QMS improvement, product improvement, changes for "
                "regulatory compliance, and resource needs."
            ]),
        ]
    },
    "DOC-QMS-008": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the planning, conduct, and reporting of internal quality audits at {company}, "
                "per ISO 13485:2016 Section 8.2.4."
            ]),
            ("2. QMSR Impact Notice", [
                "IMPORTANT: Under the QMSR (effective February 2, 2026), internal audit reports are subject to FDA "
                "inspection. The exemption previously provided under 21 CFR 820.180(c) has been removed."
            ]),
            ("3. Procedure", [
                "3.1 Audit Program Planning",
                "The annual audit program is risk-based, considering process importance, previous audit results, "
                "and regulatory requirements. All QMS processes are audited within each 12-month cycle.",
                "3.2 Auditor Qualification",
                "Auditors shall be trained in ISO 13485:2016 requirements and audit techniques. Auditors shall not "
                "audit their own work to ensure objectivity.",
                "3.3 Audit Execution",
                "Audits are conducted per the approved audit plan. Findings are classified as: Major Nonconformity, "
                "Minor Nonconformity, Observation, or Opportunity for Improvement.",
                "3.4 Corrective Action",
                "Nonconformities identified during audits are addressed through the CAPA process (SOP-CAPA-001) "
                "without undue delay. Verification of corrective actions is included in follow-up activities."
            ]),
        ]
    },
    "DOC-QMS-009": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the process for evaluating, selecting, monitoring, and auditing suppliers "
                "of products and services that affect medical device quality, per ISO 13485:2016 Section 7.4."
            ]),
            ("2. QMSR Impact Notice", [
                "IMPORTANT: Under the QMSR (effective February 2, 2026), supplier audit reports are subject to FDA "
                "inspection. The exemption previously provided under 21 CFR 820.180(c) has been removed."
            ]),
            ("3. Procedure", [
                "3.1 Supplier Evaluation and Selection",
                "Suppliers are evaluated based on their ability to supply product meeting specified requirements. "
                "Criteria include: quality system certification, past performance, product quality data, and risk assessment.",
                "3.2 Quality Agreements",
                "Written quality agreements shall be established with all suppliers of critical materials and services, "
                "per ISO 13485:2016 Section 4.1.5. Agreements define quality requirements, right to audit, notification "
                "of changes, and complaint handling responsibilities.",
                "3.3 Supplier Monitoring",
                "Supplier performance is monitored through: incoming inspection results, CAPA data, delivery performance, "
                "and periodic quality reviews.",
                "3.4 Supplier Audits",
                "Risk-based supplier audit program. Critical suppliers are audited on-site at least every 2 years. "
                "Audit results are documented and included in Management Review inputs."
            ]),
        ]
    },
    "DOC-QMS-010": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines the risk management process for medical devices throughout the product lifecycle "
                "at {company}, per ISO 13485:2016 Section 7.1 and ISO 14971."
            ]),
            ("2. Procedure", [
                "2.1 Risk Management Planning",
                "A risk management plan is established for each medical device or device family, defining scope, "
                "risk acceptability criteria, verification activities, and responsibilities.",
                "2.2 Risk Analysis",
                "Hazards are identified through systematic analysis. Risk is estimated by combining probability of "
                "occurrence with severity of harm.",
                "2.3 Risk Evaluation and Control",
                "Risks are evaluated against acceptance criteria. Risk control measures are implemented following the "
                "priority: inherent safety by design, protective measures, information for safety.",
                "2.4 Post-Production Risk Management",
                "Post-market surveillance data, complaints, and CAPA data are reviewed for risk management implications. "
                "The risk management file is updated throughout the device lifecycle."
            ]),
        ]
    },
    "DOC-QMS-011": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines design and development controls at {company} per ISO 13485:2016 Section 7.3."
            ]),
            ("2. Procedure", [
                "2.1 Design Planning (7.3.2): Design plans define stages, review/verification/validation activities, "
                "responsibilities, and interfaces between groups.",
                "2.2 Design Inputs (7.3.3): Functional, performance, safety, regulatory, and risk management requirements.",
                "2.3 Design Outputs (7.3.4): Meet input requirements, provide purchasing/production information, "
                "specify acceptance criteria, identify characteristics essential for safety.",
                "2.4 Design Review (7.3.5): Systematic reviews at planned stages per the design plan.",
                "2.5 Design Verification (7.3.6): Confirmation that outputs meet input requirements.",
                "2.6 Design Validation (7.3.7): Performed under defined operating conditions on representative product.",
                "2.7 Design Transfer (7.3.8): Procedures ensure design outputs are verified as suitable for "
                "manufacturing before becoming final production specifications.",
                "2.8 Design Changes (7.3.9): Changes are identified, documented, reviewed, verified, validated, "
                "and approved before implementation.",
                "2.9 Design and Development Files (7.3.10): Design files are maintained for each device type."
            ]),
        ]
    },
    "DOC-QMS-012": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines incoming inspection requirements for raw materials received at {company} Plant 1000, "
                "per ISO 13485:2016 Sections 7.4.3 and 8.2.6."
            ]),
            ("2. Inspection Requirements by Material", [
                "2.1 RM-00034782 (Resin Compound)",
                "- Visual inspection of packaging integrity",
                "- Certificate of Analysis (CoA) review - verify supplier lot, test dates, specifications",
                "- Viscosity measurement (Brookfield viscometer) - added per CAPA 000300000002",
                "- Sample retention per lot",
                "",
                "2.2 RM-00078234 (Chemical Solvent)",
                "- Visual inspection of packaging and seal integrity",
                "- CoA review with trace metal data verification",
                "- ICP-OES trace metal screening (Fe, Cr, Ni) - max 50ppm Fe - added per CAPA 000300000005",
                "- Moisture content (Karl Fischer) - max 0.1%",
                "- Sample retention per lot",
                "",
                "2.3 RM-00091445 (Specialty Compound)",
                "- Visual inspection of packaging",
                "- CoA review",
                "- Material revision level verification against purchase order - added per CAPA 000300000010",
                "- Identification testing per specification",
                "",
                "2.4 RM-00045678 (Powder Material)",
                "- Packaging integrity check (moisture barrier verification)",
                "- CoA review",
                "- Moisture content test - max 2.0%",
                "- Particle size distribution check",
                "",
                "2.5 All Other Raw Materials",
                "- Visual inspection and CoA review as minimum",
                "- Additional tests per material specification"
            ]),
            ("3. Acceptance and Rejection", [
                "Materials meeting all acceptance criteria are released to inventory. Non-conforming materials are "
                "quarantined and processed per SOP-NC-001. Supplier quality notifications (type Q2) are created in SAP QM."
            ]),
        ]
    },
    "DOC-QMS-013": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines labeling requirements for production packaging at {company} Plant 2000, "
                "per ISO 13485:2016 Sections 7.5.1 and 7.5.8."
            ]),
            ("2. Procedure", [
                "2.1 Label Template Setup",
                "Label templates are configured in the labeling system by authorized personnel only. Template changes "
                "require dual-operator sign-off (operator + supervisor) - added per CAPA 000300000004.",
                "2.2 Product Changeover",
                "During product changeover, the labeling system template must be updated and verified against the "
                "production order. Verification includes: product name, lot/batch number, expiration date, UDI barcode.",
                "2.3 Barcode Verification",
                "All labels shall pass automated barcode verification scan before application to product. The scanner "
                "validates: barcode readability, data content matches production order, date code format correctness. "
                "This step was added per CAPA 000300000004 following a mislabeling incident.",
                "2.4 In-Process Checks",
                "First article inspection of labels at start of each production run and after any changeover. "
                "Periodic sampling per the inspection plan."
            ]),
        ]
    },
    "DOC-QMS-014": {
        "sections": [
            ("1. Purpose", [
                "This work instruction defines CNC machining parameters and quality requirements for semi-finished "
                "part HALB-00023456 at {company} Plant 1000."
            ]),
            ("2. Machine Setup", [
                "Machine: CNC Lathes #L-201 through #L-205",
                "Material: HALB-00023456 semi-finished component",
                "Tooling: Per tool setup sheet TS-HALB-023456-Rev03"
            ]),
            ("3. Critical Parameters", [
                "3.1 Outer Diameter: Nominal +/- 0.02mm (critical dimension)",
                "3.2 Bore Surface Roughness: Ra <= 1.6 um",
                "3.3 Tool Life Parameters (updated per CAPA 000300000003):",
                "- Maximum cuts per tool: 800 (reduced from 1000 - 20% reduction)",
                "- Tool wear monitoring: MANDATORY - hard interlock enabled on CNC controller",
                "- Tool wear alert override: PROHIBITED - interlock prevents continued operation",
                "- Tool change procedure: Per tool change checklist TC-HALB-023456"
            ]),
            ("4. In-Process Inspection", [
                "First article: 100% dimensional inspection of first 3 parts",
                "In-process: Every 50th part - outer diameter and bore surface roughness",
                "Tool change: First part after every tool change - full dimensional check"
            ]),
            ("5. Safety Note", [
                "Operators must NOT override tool wear alerts under any circumstances. Production deadline pressure "
                "does not justify bypassing safety interlocks. Report any concerns to the Production Supervisor immediately."
            ]),
        ]
    },
    "DOC-QMS-015": {
        "sections": [
            ("1. Purpose", [
                "This work instruction defines mixing and color control requirements for finished product FG-00098712 "
                "at {company} Plant 1000."
            ]),
            ("2. Mixing Process", [
                "2.1 Recipe Parameters (updated per CAPA 000300000009):",
                "- Mixing time: MINIMUM 45 minutes (enforced by PLC - operator override REMOVED)",
                "- Mixing speed: 120 +/- 5 RPM",
                "- Temperature: 65 +/- 2 degrees C",
                "- PLC recipe code: RCP-098712-Rev03",
                "",
                "2.2 Pigment Addition",
                "- Add pigment per batch ticket quantity",
                "- Incoming pigment QC: Spectrophotometer check per lot (added per CAPA 000300000009)",
                "- Pigment lots failing incoming check shall be rejected per SOP-INC-001"
            ]),
            ("3. Color Verification", [
                "3.1 In-Process Color Check",
                "- First article: Spectrophotometer measurement against master standard",
                "- Acceptance criteria: Delta-E <= 2.0",
                "- Inter-batch check: Compare each batch to previous batch and master (added per CAPA 000300000009)",
                "",
                "3.2 Corrective Action for Color Deviation",
                "- If Delta-E > 2.0: STOP production, notify Quality, investigate per SOP-NC-001",
                "- If Delta-E 1.5-2.0: Increase sampling frequency to every 15 minutes"
            ]),
        ]
    },
    "DOC-QMS-016": {
        "sections": [
            ("1. Purpose", [
                "This work instruction defines soldering and assembly requirements for finished product FG-00045123 "
                "at {company} Plant 1000."
            ]),
            ("2. DRAFT NOTICE", [
                "*** THIS DOCUMENT IS IN REVIEW - NOT YET EFFECTIVE ***",
                "Changes are being implemented per CAPA 000300000007 (field failure investigation - intermittent "
                "electrical failure and connector corrosion)."
            ]),
            ("3. Solder Process Updates (PENDING)", [
                "3.1 Solder Paste Requirements",
                "- Incoming inspection: Rheology testing of solder paste per lot (NEW)",
                "- Solder paste supplier qualification: Requires approved supplier status per SOP-SUP-001",
                "",
                "3.2 Power Connector Assembly",
                "- X-ray solder joint inspection: 100% of power connector joints (NEW per CAPA 000300000007)",
                "- Acceptance criteria: No voids > 25% of pad area, no cold joints, no bridging",
                "- X-ray system: Model XRI-500 (validation protocol pending)"
            ]),
            ("4. Conformal Coating Updates (PENDING)", [
                "- Minimum coating thickness: 50um (increased from 25um per CAPA 000300000007)",
                "- Coverage: 100% of connector area including pin bases",
                "- UV inspection: All coated assemblies inspected under UV light (NEW per CAPA 000300000007)",
                "- Acceptance: Complete, uniform fluorescence with no bare spots or thin areas"
            ]),
        ]
    },
    "DOC-QMS-017": {
        "sections": [
            ("1. Purpose", [
                "This procedure defines requirements for reporting adverse events and issuing advisory notices to "
                "regulatory authorities, per ISO 13485:2016 Section 8.2.3 and 21 CFR 803."
            ]),
            ("2. Procedure", [
                "2.1 MDR Reporting",
                "Medical Device Reports are filed with the FDA when a device may have caused or contributed to a death "
                "or serious injury, or has malfunctioned in a way that could cause death or serious injury if recurrence.",
                "Reporting timelines: 30-day reports (standard), 5-day reports (remedial action required).",
                "2.2 Advisory Notices",
                "Advisory notices are issued per ISO 13485:2016 Section 8.3.3 when supplementary information or actions "
                "are needed regarding use, modification, return, or destruction of a released device.",
                "2.3 FDA Inspection Readiness",
                "Under the QMSR effective February 2, 2026, regulatory reporting records shall be maintained per "
                "Compliance Program 7382.850 and available for FDA inspection.",
                "2.4 International Reporting",
                "Adverse events in jurisdictions outside the US are reported per local regulatory requirements. "
                "The regulatory affairs department maintains a current list of reporting obligations by market."
            ]),
        ]
    },
    "DOC-QMS-018": {
        "sections": [
            ("1. Purpose", [
                "This Medical Device File contains or references all documents demonstrating conformity with "
                "ISO 13485:2016 and applicable regulatory requirements for the FG-00012345 Housing Unit product family, "
                "per ISO 13485:2016 Section 4.2.3."
            ]),
            ("2. Device Description", [
                "Product: FG-00012345 Housing Unit",
                "Classification: Class II Medical Device",
                "Intended Use: Protective housing component for patient monitoring system",
                "Manufacturing Plants: 1000 (primary), 1100 (secondary), 2000 (distribution)"
            ]),
            ("3. File Contents", [
                "3.1 Device Description and Intended Use (this document)",
                "3.2 Product Specifications: SPEC-FG-00012345-Rev05",
                "3.3 Manufacturing Procedures: WI-MFG-012345-Rev04 (includes surface finish specification update "
                "per CAPA 000300000001)",
                "3.4 Packaging and Labeling Specifications: SPEC-PKG-012345-Rev02",
                "3.5 Inspection and Test Procedures: SOP-IQC-012345-Rev03",
                "3.6 Design History File: DHF-FG-00012345",
                "3.7 Risk Management File: RMF-FG-00012345-Rev04",
                "3.8 Post-Market Surveillance Data: PMS-FG-00012345 (updated quarterly)",
                "3.9 CAPA Records: Quality Notification 000300000001 (surface scratch complaint - resolved)"
            ]),
        ]
    },
    "DOC-QMS-019": {
        "sections": [
            ("1. Purpose", [
                "This validation protocol documents the revalidation of Filling Machine FM-004 at {company} Plant 2000, "
                "following dosage valve overhaul per CAPA 000300000006."
            ]),
            ("2. Background", [
                "Quality Notification 000300000006 identified weight variation exceeding +/-2% specification on trading "
                "goods HAWA-00056891 due to intermittent dosage valve sticking. The valve was overhauled and the machine "
                "requires revalidation per ISO 13485:2016 Section 7.5.6."
            ]),
            ("3. Validation Approach", [
                "3.1 IQ (Installation Qualification): Verify valve replacement per manufacturer specifications.",
                "3.2 OQ (Operational Qualification): Test filling accuracy across operating range.",
                "3.3 PQ (Performance Qualification): Three consecutive production runs meeting acceptance criteria.",
                "",
                "Acceptance Criteria:",
                "- Fill weight: Target +/- 1.5% (tightened from +/- 2.0%)",
                "- Cpk >= 1.33 for fill weight across all three PQ runs",
                "- No dosage valve sticking events during validation"
            ]),
            ("4. Results Summary", [
                "IQ: PASS - Valve installed per specification, torque values verified.",
                "OQ: PASS - Filling accuracy within +/- 1.0% across full operating range.",
                "PQ Run 1: PASS - Cpk = 1.52, n=500, no valve events.",
                "PQ Run 2: PASS - Cpk = 1.48, n=500, no valve events.",
                "PQ Run 3: PASS - Cpk = 1.45, n=500, no valve events.",
                "",
                "CONCLUSION: Filling Machine FM-004 validated for production use."
            ]),
        ]
    },
    "DOC-QMS-020": {
        "sections": [
            ("1. Purpose", [
                "This report documents {company}'s gap assessment comparing the existing Quality Management System "
                "(under 21 CFR 820 QS Regulation) against the requirements of the new Quality Management System "
                "Regulation (QMSR), effective February 2, 2026, which incorporates ISO 13485:2016 by reference."
            ]),
            ("2. Methodology", [
                "This assessment follows the FDA's recommendation (QMSR FAQ, Question 7) that manufacturers complete "
                "a comparative analysis to demonstrate documents and records created prior to the QMSR effective date "
                "meet QMSR requirements.",
                "References used:",
                "- ISO 13485:2016 Medical devices - Quality management systems",
                "- ISO 9000:2015 Clause 3 (terms and definitions)",
                "- 21 CFR Part 820 (as amended - QMSR)",
                "- FDA QMSR FAQ (updated February 2, 2026)",
                "- AAMI TIR102:2019 (21 CFR mapping to ISO 13485:2016)"
            ]),
            ("3. Key Findings", [
                "3.1 HIGH IMPACT - Records Previously Exempt Under 820.180(c)",
                "Management review records, internal audit reports, and supplier audit reports are now subject to "
                "FDA inspection. Action: SOPs MR-001, AUD-001, and SUP-001 revised to reflect this requirement. "
                "Historical records reviewed for completeness.",
                "",
                "3.2 MEDIUM IMPACT - Terminology Alignment",
                "ISO 13485:2016 uses different terminology than old 820. Action: Quality Manual and key SOPs revised "
                "to use ISO 13485 terminology while maintaining QMSR-specific terms where applicable.",
                "",
                "3.3 MEDIUM IMPACT - Risk-Based Approach",
                "ISO 13485:2016 emphasizes risk-based approach throughout (Section 4.1.2). Action: Risk management "
                "procedure updated; risk-based thinking integrated into CAPA, audit, and supplier management processes.",
                "",
                "3.4 LOW IMPACT - Medical Device File",
                "ISO 13485:2016 Section 4.2.3 requires medical device files. Action: Existing Design History Files "
                "supplemented with additional content to meet medical device file requirements.",
                "",
                "3.5 LOW IMPACT - Computer Software Validation",
                "ISO 13485:2016 Section 4.1.6 requires documented procedures for validation of QMS computer software. "
                "Action: Existing CSV procedures confirmed adequate."
            ]),
            ("4. Document Revision Schedule", [
                "All QMS-level documents revised and effective by February 1, 2026 (day before QMSR effective date).",
                "Product-level documents: Rolling updates as part of CAPA-driven changes.",
                "Gap assessment reviewed and approved by VP Quality & Regulatory."
            ]),
        ]
    },
}


class ControlledDocPDF(FPDF):
    def __init__(self, doc_meta):
        super().__init__()
        self.meta = doc_meta

    def header(self):
        m = self.meta
        if self.page_no() == 1:
            # Full header on first page
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 5, COMPANY, new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 7)
            self.cell(0, 4, COMPANY_ADDR, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

            # Document header box
            self.set_fill_color(41, 65, 122)
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 12)
            self.cell(0, 8, f"  {m['DocumentTitle']}", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.ln(1)

            # Metadata table
            self.set_font("Helvetica", "", 7)
            col_w = 47.5
            row_h = 4.5

            fields = [
                ("Document ID:", m["DocumentID"]),
                ("Document Type:", m["DocumentType"]),
                ("Revision:", f"Rev {m['RevisionNumber']}"),
                ("Status:", m["Status"]),
                ("Effective Date:", m["EffectiveDate"]),
                ("Review Due:", m["ExpirationReviewDate"]),
                ("ISO 13485 Ref:", m["ISOReference"]),
                ("Regulatory Ref:", m["RegulatoryReference"]),
            ]
            for i in range(0, len(fields), 4):
                for j in range(4):
                    if i + j < len(fields):
                        label, val = fields[i + j]
                        self.set_font("Helvetica", "B", 7)
                        self.cell(20, row_h, label)
                        self.set_font("Helvetica", "", 7)
                        self.cell(col_w - 20, row_h, val)
                self.ln(row_h)

            # Separator
            self.set_draw_color(41, 65, 122)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        else:
            # Compact header on continuation pages
            self.set_font("Helvetica", "B", 8)
            self.set_fill_color(41, 65, 122)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, f"  {m['DocumentID']}  |  {m['DocumentTitle']}  |  Rev {m['RevisionNumber']}", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.ln(3)

    def footer(self):
        m = self.meta
        self.set_y(-15)
        self.set_draw_color(41, 65, 122)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 6)
        self.cell(0, 3, f"{m['DocumentID']} | Rev {m['RevisionNumber']} | CONTROLLED DOCUMENT | Page {self.page_no()}/{{nb}}")

    def add_approval_block(self):
        m = self.meta
        self.ln(4)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, "DOCUMENT APPROVAL", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        col_w = 63.3
        row_h = 5
        # Header row
        self.set_fill_color(220, 220, 220)
        self.set_font("Helvetica", "B", 8)
        for h in ["Role", "Name", "Date"]:
            self.cell(col_w, row_h, f"  {h}", border=1, fill=True)
        self.ln(row_h)
        self.set_font("Helvetica", "", 8)
        rows = [
            ("Author", PERSONNEL.get(m["Author"], m["Author"]), m["RevisionDate"]),
            ("Reviewer", PERSONNEL.get(m["Reviewer"], m["Reviewer"]), m["RevisionDate"]),
            ("Approver", PERSONNEL.get(m["Approver"], m["Approver"]), m["RevisionDate"]),
        ]
        for role, name, date in rows:
            self.cell(col_w, row_h, f"  {role}", border=1)
            self.cell(col_w, row_h, f"  {name}", border=1)
            self.cell(col_w, row_h, f"  {date}", border=1)
            self.ln(row_h)

    def add_revision_history(self):
        m = self.meta
        self.ln(4)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, "REVISION HISTORY", new_x="LMARGIN", new_y="NEXT")
        self.set_fill_color(220, 220, 220)
        self.set_font("Helvetica", "B", 7)
        widths = [15, 25, 30, 120]
        headers = ["Rev", "Date", "Author", "Description of Change"]
        for w, h in zip(widths, headers):
            self.cell(w, 4.5, f" {h}", border=1, fill=True)
        self.ln(4.5)
        self.set_font("Helvetica", "", 7)
        # Current revision
        self.cell(widths[0], 4.5, f" {m['RevisionNumber']}", border=1)
        self.cell(widths[1], 4.5, f" {m['RevisionDate']}", border=1)
        self.cell(widths[2], 4.5, f" {PERSONNEL.get(m['Author'], m['Author']).split(',')[0]}", border=1)
        # Truncate change reason to fit
        reason = m["ChangeReason"][:155] + "..." if len(m["ChangeReason"]) > 155 else m["ChangeReason"]
        self.cell(widths[3], 4.5, f" {reason}", border=1)
        self.ln(4.5)
        # Previous revision placeholder
        prev_rev = str(int(m["RevisionNumber"]) - 1).zfill(2) if m["PreviousRevisionDate"] else None
        if prev_rev and m["PreviousRevisionDate"]:
            self.cell(widths[0], 4.5, f" {prev_rev}", border=1)
            self.cell(widths[1], 4.5, f" {m['PreviousRevisionDate']}", border=1)
            self.cell(widths[2], 4.5, f" {PERSONNEL.get(m['Author'], m['Author']).split(',')[0]}", border=1)
            self.cell(widths[3], 4.5, " Previous revision", border=1)
            self.ln(4.5)


def generate_pdf(doc_meta):
    doc_id = doc_meta["DocumentID"]
    body = DOCUMENT_BODIES.get(doc_id, None)
    if not body:
        return

    pdf = ControlledDocPDF(doc_meta)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()

    # Approval block
    pdf.add_approval_block()

    # Revision history
    pdf.add_revision_history()

    # Related CAPA
    if doc_meta.get("RelatedCAPAReference"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "RELATED CAPA REFERENCES", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for ref in doc_meta["RelatedCAPAReference"].split(", "):
            pdf.cell(0, 5, f"  - Quality Notification: {ref.strip()}", new_x="LMARGIN", new_y="NEXT")

    # Body sections
    page_w = pdf.w - pdf.l_margin - pdf.r_margin  # effective width
    for section_title, paragraphs in body["sections"]:
        # Ensure enough space for a section header + some content
        if pdf.get_y() > 245:
            pdf.add_page()
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, section_title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for para in paragraphs:
            text = para.replace("{company}", COMPANY)
            if pdf.get_y() > 245:
                pdf.add_page()
                pdf.set_font("Helvetica", "", 8)
            if text.startswith("- "):
                # Render bullet with hanging indent
                bullet_indent = 6
                pdf.set_x(pdf.l_margin + bullet_indent)
                pdf.multi_cell(page_w - bullet_indent, 4.5, text)
            elif text == "":
                pdf.ln(2)
            else:
                pdf.multi_cell(page_w, 4.5, text)
                pdf.ln(1)

    # Filename from FileReference
    filename = doc_meta["FileReference"].split("/")[-1]
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"  Generated: {filename}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(DATA_FILE) as f:
        docs = [json.loads(line) for line in f if line.strip()]

    print(f"Generating {len(docs)} PDFs...")
    for doc in docs:
        generate_pdf(doc)
    print(f"\nDone. Files in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
