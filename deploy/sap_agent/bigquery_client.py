"""BigQuery client for SAP Quality Management data queries.

Provides query methods for quality notifications (CAPAs),
quality info records, and controlled documents stored in BigQuery.
"""

import json
import logging
import os

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "reliable-alpha-490519-i1")
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "sap_qm")

# Fields stored as JSON strings that need parsing
JSON_FIELDS = {"_Item", "_Task", "_Activity", "to_QltyFirstArticleInsp"}


class BigQueryClient:
    """Manages BigQuery connection and provides query methods for SAP QM data."""

    _instance = None

    @classmethod
    def get_instance(cls) -> "BigQueryClient":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._client = bigquery.Client(project=PROJECT_ID)
        self._dataset = f"{PROJECT_ID}.{DATASET_ID}"
        logger.info("BigQuery client initialized (project=%s, dataset=%s)", PROJECT_ID, DATASET_ID)

    def _query(self, sql: str, params: list | None = None) -> list[dict]:
        """Run a parameterised query and return results as dicts."""
        job_config = bigquery.QueryJobConfig(query_parameters=params or [])
        rows = self._client.query(sql, job_config=job_config).result()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a BigQuery Row to a Python dictionary, parsing JSON fields."""
        result = dict(row)
        for field in JSON_FIELDS:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, ValueError):
                    pass
        return result

    # ── Quality Notifications ──────────────────────────────────────────

    def get_quality_notifications(
        self,
        status: str | None = None,
        notification_type: str | None = None,
        material: str | None = None,
    ) -> list[dict]:
        """Query quality notifications with optional filters."""
        conditions = []
        params = []

        if notification_type:
            conditions.append("NotificationType = @ntype")
            params.append(bigquery.ScalarQueryParameter("ntype", "STRING", notification_type))
        if status:
            conditions.append("NotificationStatus = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
        if material:
            conditions.append("Material = @material")
            params.append(bigquery.ScalarQueryParameter("material", "STRING", material))

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM `{self._dataset}.quality_notifications`{where}"
        return self._query(sql, params)

    def get_quality_notification_detail(self, notification_number: str) -> dict | None:
        """Get a single notification by its number (full CAPA hierarchy)."""
        sql = f"SELECT * FROM `{self._dataset}.quality_notifications` WHERE QualityNotification = @num LIMIT 1"
        params = [bigquery.ScalarQueryParameter("num", "STRING", notification_number)]
        results = self._query(sql, params)
        return results[0] if results else None

    # ── Quality Info Records ───────────────────────────────────────────

    def get_quality_info_records(
        self,
        material: str | None = None,
        supplier: str | None = None,
        plant: str | None = None,
        blocked_only: bool = False,
    ) -> list[dict]:
        """Query quality info records with optional filters."""
        conditions = []
        params = []

        if material:
            conditions.append("Material = @material")
            params.append(bigquery.ScalarQueryParameter("material", "STRING", material))
        if supplier:
            conditions.append("Supplier = @supplier")
            params.append(bigquery.ScalarQueryParameter("supplier", "STRING", supplier))
        if plant:
            conditions.append("Plant = @plant")
            params.append(bigquery.ScalarQueryParameter("plant", "STRING", plant))
        if blocked_only:
            conditions.append("ProcurementBlock = '99'")

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM `{self._dataset}.quality_info_records`{where}"
        return self._query(sql, params)

    # ── Controlled Documents ───────────────────────────────────────────

    def get_controlled_documents(
        self,
        doc_type: str | None = None,
        iso_reference: str | None = None,
        status: str | None = None,
        capa_reference: str | None = None,
    ) -> list[dict]:
        """Query controlled documents with optional filters."""
        conditions = []
        params = []

        if capa_reference:
            conditions.append("STRPOS(RelatedCAPAReference, @capa_ref) > 0")
            params.append(bigquery.ScalarQueryParameter("capa_ref", "STRING", capa_reference))
        if doc_type:
            conditions.append("DocumentType = @doc_type")
            params.append(bigquery.ScalarQueryParameter("doc_type", "STRING", doc_type))
        if iso_reference:
            conditions.append("ISOReference = @iso_ref")
            params.append(bigquery.ScalarQueryParameter("iso_ref", "STRING", iso_reference))
        if status:
            conditions.append("Status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM `{self._dataset}.controlled_documents`{where}"
        return self._query(sql, params)

    # ── CAPA Action Search ─────────────────────────────────────────────

    def search_capa_actions(
        self,
        task_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """Search corrective/preventive actions across all notifications.

        Returns a flat list of tasks with their parent notification context.
        """
        all_notifications = self._query(
            f"SELECT * FROM `{self._dataset}.quality_notifications`"
        )

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
