"""S3-compatible storage helpers for chat attachments."""

import os
import uuid
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024
ALLOWED_ATTACHMENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _settings() -> tuple[str, str, str | None, str, str]:
    bucket = os.getenv("S3_BUCKET_NAME")
    region = os.getenv("S3_REGION")
    access_key = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
    if not bucket or not region or not access_key or not secret_key:
        raise RuntimeError("S3 storage is not configured")
    return bucket, region, os.getenv("S3_ENDPOINT_URL"), access_key, secret_key


def _client():
    bucket, region, endpoint, access_key, secret_key = _settings()
    client_options: dict[str, str] = {
        "region_name": region,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if endpoint:
        client_options["endpoint_url"] = endpoint
    return boto3.client("s3", **client_options)


def validate_attachment(filename: str, content_type: str, size: int) -> tuple[str, str]:
    extension = PurePosixPath(filename.strip()).suffix.lower()
    expected_type = ALLOWED_ATTACHMENT_TYPES.get(extension)
    normalized_type = content_type.lower().split(";", 1)[0].strip()
    jpeg_types = {"image/jpeg", "image/jpg"}
    valid_type = normalized_type in jpeg_types if extension in {".jpg", ".jpeg"} else normalized_type == expected_type
    if not expected_type or not valid_type:
        raise ValueError("Supported attachments are JPG, JPEG, and PNG files")
    if size < 1 or size > MAX_ATTACHMENT_SIZE:
        raise ValueError("Attachments must be smaller than 25 MB")
    return extension, expected_type


def create_upload_url(filename: str, content_type: str, size: int) -> dict[str, str | int]:
    extension, normalized_type = validate_attachment(filename, content_type, size)
    bucket, _, _, _, _ = _settings()
    object_key = f"chat-attachments/{uuid.uuid4().hex}{extension}"
    try:
        upload_url = _client().generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": object_key, "ContentType": normalized_type},
            ExpiresIn=900,
        )
    except (BotoCoreError, ClientError) as error:
        raise RuntimeError("Unable to prepare S3 upload") from error
    return {"upload_url": upload_url, "object_key": object_key, "content_type": normalized_type, "size": size}


def create_download_url(object_key: str, filename: str, download: bool = False) -> str:
    bucket, _, _, _, _ = _settings()
    try:
        params = {"Bucket": bucket, "Key": object_key}
        if download:
            safe_filename = filename.replace('"', "")
            params["ResponseContentDisposition"] = f'attachment; filename="{safe_filename}"'
        return _client().generate_presigned_url("get_object", Params=params, ExpiresIn=3600)
    except (BotoCoreError, ClientError) as error:
        raise RuntimeError("Unable to prepare attachment URL") from error
