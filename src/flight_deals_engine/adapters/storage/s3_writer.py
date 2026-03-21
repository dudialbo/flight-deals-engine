import json
import logging
from typing import Sequence

import boto3

from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate

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

    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None:
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured")
            return

        file_key = "hot_deals.json"
        data = [item.model_dump(mode="json") for item in items]

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json",
            )
            logger.info("Saved %d hot deals to s3://%s/%s", len(items), self.bucket_name, file_key)
        except Exception as e:
            logger.error("Failed to write hot deals to S3: %s", e)
