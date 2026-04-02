import json
import logging
from typing import Any, Mapping, Sequence

import boto3

from flight_deals_engine.domain.models import CalendarPriceSnapshot

logger = logging.getLogger(__name__)


class S3StorageWriter:
    """
    Storage writer used for production.
    It writes the outputs to S3 bucket.
    """
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")

    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured")
            return

        file_key = "calendar_prices.json"
        data = [item.model_dump(mode="json") for item in items]

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json",
            )
            logger.info("Saved %d calendar snapshots to s3://%s/%s", len(items), self.bucket_name, file_key)
        except Exception as e:
            logger.error("Failed to write calendar snapshots to S3: %s", e)

    def write_category(self, category_id: str, payload: Mapping[str, Any]) -> None:
        file_key = f"deals/{category_id}.json"
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=json.dumps(dict(payload), indent=2),
                ContentType="application/json",
            )
            logger.info("Saved category %s to s3://%s/%s", category_id, self.bucket_name, file_key)
        except Exception as e:
            logger.error("Failed to write category %s to S3: %s", category_id, e)

    def write_manifest(self, payload: Mapping[str, Any]) -> None:
        file_key = "deals/manifest.json"
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=json.dumps(dict(payload), indent=2),
                ContentType="application/json",
            )
            logger.info("Saved manifest to s3://%s/%s", self.bucket_name, file_key)
        except Exception as e:
            logger.error("Failed to write manifest to S3: %s", e)