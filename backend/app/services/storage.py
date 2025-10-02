"""Cloudflare R2 storage service using boto3."""

import uuid
from datetime import datetime, timedelta
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


class R2Storage:
    """
    Cloudflare R2 storage service.

    R2 is S3-compatible, so we use boto3 with custom endpoint.
    """

    def __init__(self):
        """Initialize R2 client with Cloudflare credentials."""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.r2_bucket_name

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str | None = None,
        content_type: str | None = None,
        folder: str = "uploads",
    ) -> str:
        """
        Upload file to R2.

        Args:
            file: File-like object to upload
            filename: Original filename (generates UUID if not provided)
            content_type: MIME type
            folder: Folder/prefix in bucket

        Returns:
            Public URL of uploaded file
        """
        # Generate unique filename if not provided
        if not filename:
            filename = f"{uuid.uuid4()}"

        # Construct object key with folder
        key = f"{folder}/{filename}"

        # Upload to R2
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
        except ClientError as e:
            raise Exception(f"Failed to upload file to R2: {str(e)}")

        # Return public URL
        return f"{settings.r2_endpoint}/{self.bucket}/{key}"

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: str | None = None,
        folder: str = "uploads",
    ) -> str:
        """
        Upload bytes to R2.

        Args:
            data: Bytes to upload
            filename: Filename
            content_type: MIME type
            folder: Folder/prefix in bucket

        Returns:
            Public URL of uploaded file
        """
        key = f"{folder}/{filename}"

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.put_object(
                Bucket=self.bucket, Key=key, Body=data, **extra_args
            )
        except ClientError as e:
            raise Exception(f"Failed to upload bytes to R2: {str(e)}")

        return f"{settings.r2_endpoint}/{self.bucket}/{key}"

    async def delete_file(self, url: str) -> bool:
        """
        Delete file from R2 by URL.

        Args:
            url: Public URL of file

        Returns:
            True if successful
        """
        # Extract key from URL
        key = url.split(f"{self.bucket}/")[-1]

        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file from R2: {str(e)}")

    async def get_presigned_url(
        self, key: str, expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary access.

        Args:
            key: Object key in bucket
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    async def list_files(self, folder: str = "") -> list[str]:
        """
        List files in folder.

        Args:
            folder: Folder/prefix to list

        Returns:
            List of object keys
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=folder
            )
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            raise Exception(f"Failed to list files in R2: {str(e)}")

    async def file_exists(self, key: str) -> bool:
        """Check if file exists in R2."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


# Singleton instance
r2_storage = R2Storage()
