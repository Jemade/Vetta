import os
from pathlib import Path
from typing import Optional, BinaryIO
import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.is_s3 = settings.is_s3_configured
        self.local_dir = Path(settings.local_storage_dir)

        if self.is_s3:
            s3_config = Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            )
            client_kwargs = {
                "service_name": "s3",
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key,
                "region_name": settings.aws_region,
                "config": s3_config,
            }
            if settings.aws_s3_endpoint_url:
                client_kwargs["endpoint_url"] = settings.aws_s3_endpoint_url

            self.s3_client = boto3.client(**client_kwargs)
            self.bucket = settings.aws_s3_bucket
            logger.info("StorageService initialized in AWS S3 mode with bucket '%s'", self.bucket)
        else:
            self.s3_client = None
            self.bucket = None
            self.local_dir.mkdir(parents=True, exist_ok=True)
            logger.info("StorageService initialized in local disk mode at '%s'", self.local_dir)

    def upload_bytes(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        if self.is_s3:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                )
                return f"s3://{self.bucket}/{key}"
            except ClientError as e:
                logger.error("Failed to upload %s to S3: %s", key, e)
                raise
        else:
            dest_path = self.local_dir / key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(data)
            return str(dest_path.resolve())

    def download_bytes(self, key: str) -> bytes:
        if self.is_s3:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                return response["Body"].read()
            except ClientError as e:
                logger.error("Failed to download %s from S3: %s", key, e)
                raise
        else:
            dest_path = self.local_dir / key
            if not dest_path.exists():
                raise FileNotFoundError(f"File not found: {dest_path}")
            return dest_path.read_bytes()

    def generate_presigned_upload_url(self, key: str, expires_in: int = 3600) -> str:
        if self.is_s3:
            try:
                url = self.s3_client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                logger.error("Failed generating presigned upload URL for %s: %s", key, e)
                raise
        else:
            return f"/storage/local-upload/{key}"

    def generate_presigned_download_url(self, key: str, expires_in: int = 3600) -> str:
        if self.is_s3:
            try:
                url = self.s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                logger.error("Failed generating presigned download URL for %s: %s", key, e)
                raise
        else:
            return f"/interviews/media/{key}"

    def delete(self, key: str) -> bool:
        if self.is_s3:
            try:
                self.s3_client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError as e:
                logger.error("Failed deleting %s from S3: %s", key, e)
                return False
        else:
            dest_path = self.local_dir / key
            if dest_path.exists():
                dest_path.unlink()
                return True
            return False

    def exists(self, key: str) -> bool:
        if self.is_s3:
            try:
                self.s3_client.head_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False
        else:
            return (self.local_dir / key).exists()


storage_service = StorageService()
