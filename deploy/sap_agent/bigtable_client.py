"""BigTable client for SAP Quality Management data queries.

Provides query methods for quality notifications (CAPAs),
quality info records, and controlled documents stored in BigTable.
"""

import json
import logging
import os

from google.cloud import bigtable

logger = logging.getLogger(__name__)

COLUMN_FAMILY = "data"
PROJECT_ID = os.environ.get("BIGTABLE_PROJECT_ID", "box-sap-sapphire")
INSTANCE_ID = os.environ.get("BIGTABLE_INSTANCE_ID", "sap-demo")

# Fields stored as JSON that need parsing
JSON_FIELDS = {"_Item", "_Task", "_Activity", "to_QltyFirstArticleInsp"}


class BigTableClient:
    """Manages BigTable connection and provides query methods for SAP QM data."""

    _instance = None

    @classmethod
    def get_instance(cls) -> "BigTableClient":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        os.environ.setdefault("BIGTABLE_EMULATOR_HOST", "localhost:8086")
        self._client = bigtable.Client(project=PROJECT_ID, admin=False)
        self._bt_instance = self._client.instance(INSTANCE_ID)
        logger.info("BigTable client initialized (project=%s, instance=%s)", PROJECT_ID, INSTANCE_ID)

    def _table(self, name: str):
        return self._bt_instance.table(name)

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a BigTable row to a Python dictionary."""
        result = {}
        # Preserve row key for filtering
        row_key = row.row_key
        if isinstance(row_key, bytes):
            row_key = row_key.decode()
        result["_row_key"] = row_key

        for _family_id, columns in row.cells.items():
            for col_key, cells in columns.items():
                col_name = col_key.decode() if isinstance(col_key, bytes) else col_key
                value = cells[0].value.decode()
                # Parse JSON for known nested fields
                if col_name in JSON_FIELDS:
                    try:
                        result[col_name] = json.loads(value)
                        continue
                    except (json.JSONDecodeError, ValueError):
                        pass
                # Try boolean
                if value in ("true", "false"):
                    result[col_name] = value == "true"
                    continue
                result[col_name] = value
        return result

    def _read_rows(self, table_name: str, prefix: str | None = None,
                   row_key: str | None = None) -> list[dict]:
        """Read rows from a table by exact key, prefix scan, or full scan."""
        table = self._table(table_name)
        if row_key:
            row = table.read_row(row_key.encode())
            return [self._row_to_dict(row)] if row else []
        if prefix:
            # Prefix scan: start_key=prefix, end_key=prefix with last byte incremented
            prefix_bytes = prefix.encode()
            end_bytes = prefix_bytes[:-1] + bytes([prefix_bytes[-1] + 1])
            rows = table.read_rows(start_key=prefix_bytes, end_key=end_bytes)
            return [self._row_to_dict(r) for r in rows]
        # Full scan
        rows = table.read_rows()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _is_primary_row(row: dict) -> bool:
        """Check if a row is a primary row (not a secondary index row)."""
        rk = row.get("_row_key", "")
        return not rk.startswith(("MAT#", "SUP#", "CAPA#", "ISO#"))

    @staticmethod
    def _strip_row_key(row: dict) -> dict:
        """Return a copy of the row without the internal _row_key field."""
        return {k: v for k, v in row.items() if k != "_row_key"}

    def _clean_results(self, rows: list[dict], primary_only: bool = True) -> list[dict]:
        """Filter to primary rows only and strip internal _row_key field."""
        if primary_only:
            rows = [r for r in rows if self._is_primary_row(r)]
        # Deduplicate by unique ID
        seen = set()
        result = []
        for row in rows:
            uid = (row.get("QualityNotification") or
                   row.get("DocumentID") or
                   f"{row.get('Material', '')}#{row.get('QltyInProcmtIntID', '')}")
            if uid not in seen:
                seen.add(uid)
                result.append(self._strip_row_key(row))
        return result

    # ── Quality Notifications ──────────────────────────────────────────

    def get_quality_notifications(
        self,
        status: str | None = None,
        notification_type: str | None = None,
        material: str | None = None,
    ) -> list[dict]:
        """Query quality notifications with optional filters.

        Row key: {Type}#{Status}#{Number}
        Secondary: MAT#{Material}#{Number}, SUP#{Supplier}#{Number}
        """
        # Material-based lookup uses secondary index
        if material and not notification_type and not status:
            rows = self._read_rows("quality_notifications", prefix=f"MAT#{material}")
            return self._clean_results(rows, primary_only=False)

        # Build prefix from type/status
        prefix = None
        if notification_type and status:
            prefix = f"{notification_type}#{status}#"
        elif notification_type:
            prefix = f"{notification_type}#"

        if prefix:
            rows = self._read_rows("quality_notifications", prefix=prefix)
        else:
            rows = self._read_rows("quality_notifications")

        rows = self._clean_results(rows)

        # Apply in-memory filters
        if status and not notification_type:
            rows = [r for r in rows if r.get("NotificationStatus") == status]
        if material:
            rows = [r for r in rows if r.get("Material") == material]

        return rows

    def get_quality_notification_detail(self, notification_number: str) -> dict | None:
        """Get a single notification by its number (full CAPA hierarchy)."""
        for ntype in ("Q1", "Q2", "Q3"):
            for nstatus in ("COMPLETED", "IN_PROCESS"):
                key = f"{ntype}#{nstatus}#{notification_number}"
                rows = self._read_rows("quality_notifications", row_key=key)
                if rows:
                    return self._strip_row_key(rows[0])
        return None

    # ── Quality Info Records ───────────────────────────────────────────

    def get_quality_info_records(
        self,
        material: str | None = None,
        supplier: str | None = None,
        plant: str | None = None,
        blocked_only: bool = False,
    ) -> list[dict]:
        """Query quality info records with optional filters.

        Row key: {Plant}#{Material}#{IntID}
        Secondary: SUP#{Supplier}#{Material}#{IntID}
        """
        if supplier and not plant and not material:
            rows = self._read_rows("quality_info_records", prefix=f"SUP#{supplier}")
            rows = self._clean_results(rows, primary_only=False)
        elif plant and material:
            rows = self._read_rows("quality_info_records", prefix=f"{plant}#{material}")
            rows = self._clean_results(rows)
        elif plant:
            rows = self._read_rows("quality_info_records", prefix=f"{plant}#")
            rows = self._clean_results(rows)
        else:
            rows = self._read_rows("quality_info_records")
            rows = self._clean_results(rows)

        # In-memory filters
        if material and not (plant and material):
            rows = [r for r in rows if r.get("Material") == material]
        if supplier and (plant or material):
            rows = [r for r in rows if r.get("Supplier") == supplier]
        if blocked_only:
            rows = [r for r in rows if r.get("ProcurementBlock") == "99"]

        return rows

    # ── Controlled Documents ───────────────────────────────────────────

    def get_controlled_documents(
        self,
        doc_type: str | None = None,
        iso_reference: str | None = None,
        status: str | None = None,
        capa_reference: str | None = None,
    ) -> list[dict]:
        """Query controlled documents with optional filters.

        Row key: {DocType}#{Status}#{DocID}
        Secondary: CAPA#{Ref}#{DocID}, ISO#{ISORef}#{DocID}
        """
        # CAPA reference lookup
        if capa_reference:
            rows = self._read_rows("controlled_documents", prefix=f"CAPA#{capa_reference}")
            return self._clean_results(rows, primary_only=False)

        # ISO reference lookup
        if iso_reference and not doc_type and not status:
            rows = self._read_rows("controlled_documents", prefix=f"ISO#{iso_reference}")
            return self._clean_results(rows, primary_only=False)

        # Build prefix from type/status
        prefix = None
        if doc_type and status:
            prefix = f"{doc_type}#{status}#"
        elif doc_type:
            prefix = f"{doc_type}#"

        if prefix:
            rows = self._read_rows("controlled_documents", prefix=prefix)
        else:
            rows = self._read_rows("controlled_documents")

        rows = self._clean_results(rows)

        # In-memory filters
        if status and not doc_type:
            rows = [r for r in rows if r.get("Status") == status]
        if iso_reference:
            rows = [r for r in rows if r.get("ISOReference") == iso_reference]

        return rows

    # ── CAPA Action Search ─────────────────────────────────────────────

    def search_capa_actions(
        self,
        task_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """Search corrective/preventive actions across all notifications.

        Returns a flat list of tasks with their parent notification context.
        """
        # Get all notifications (primary rows only)
        all_notifications = self._read_rows("quality_notifications")
        all_notifications = self._clean_results(all_notifications)

        results = []
        for notif in all_notifications:
            tasks = notif.get("_Task", [])
            if isinstance(tasks, str):
                try:
                    tasks = json.loads(tasks)
                except (json.JSONDecodeError, ValueError):
                    continue

            for task in tasks:
                if task_type and task.get("TaskType") != task_type:
                    continue
                if status and task.get("TaskStatus") != status:
                    continue

                results.append({
                    "QualityNotification": notif.get("QualityNotification"),
                    "NotificationType": notif.get("NotificationType"),
                    "NotificationText": notif.get("NotificationText"),
                    "Material": notif.get("Material"),
                    "TaskCode": task.get("NotificationTask"),
                    "TaskText": task.get("TaskText"),
                    "TaskType": task.get("TaskType"),
                    "TaskStatus": task.get("TaskStatus"),
                    "TaskResponsiblePerson": task.get("TaskResponsiblePerson"),
                    "TaskPlannedEndDate": task.get("TaskPlannedEndDate"),
                    "TaskCompletionDate": task.get("TaskCompletionDate"),
                })

        return results
