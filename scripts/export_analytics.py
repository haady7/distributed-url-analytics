"""Export click analytics to CSV and optionally upload the file to S3.

Usage: python scripts/export_analytics.py --from 2026-01-01 --to 2026-02-01 [--s3]
"""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import boto3
from sqlalchemy import select

from app.core.config import settings
from app.db import SessionLocal
from app.models import ClickEvent, ShortURL


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True, help="Inclusive UTC date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", required=True, help="Exclusive UTC date (YYYY-MM-DD)")
    parser.add_argument("--s3", action="store_true", help="Upload the resulting CSV to configured S3_BUCKET")
    args = parser.parse_args()
    start = datetime.fromisoformat(args.date_from).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.date_to).replace(tzinfo=timezone.utc)
    output = Path(f"click-analytics-{args.date_from}-to-{args.date_to}.csv")

    db = SessionLocal()
    try:
        rows = db.execute(
            select(ShortURL.code, ShortURL.original_url, ClickEvent.clicked_at, ClickEvent.country,
                   ClickEvent.city, ClickEvent.referrer, ClickEvent.user_agent)
            .join(ClickEvent, ClickEvent.url_id == ShortURL.id)
            .where(ClickEvent.clicked_at >= start, ClickEvent.clicked_at < end)
            .order_by(ClickEvent.clicked_at)
        ).all()
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["code", "original_url", "clicked_at_utc", "country", "city", "referrer", "user_agent"])
            writer.writerows(rows)
    finally:
        db.close()

    print(f"Exported {len(rows)} click events to {output}")
    if args.s3:
        if not settings.S3_BUCKET:
            raise SystemExit("Set S3_BUCKET before using --s3")
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        s3.upload_file(str(output), settings.S3_BUCKET, f"analytics/{output.name}")
        print(f"Uploaded to s3://{settings.S3_BUCKET}/analytics/{output.name}")


if __name__ == "__main__":
    main()
