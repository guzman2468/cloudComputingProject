"""Unit tests for graceful degradation when S3 is unconfigured."""

from backend.schemas.chat import AttachmentResponse
from backend.services.chat import ATTACHMENT_MESSAGE_PREFIX, _attachment_payload, _attachment_response


def test_attachment_response_unconfigured_s3_does_not_crash(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_ACCESS_KEY_ID", raising=False)

    result = _attachment_response("attachments/sample.png", "sample.png", "image/png", 1024)
    assert result["filename"] == "sample.png"
    assert result["url"] is None
    assert result["download_url"] is None

    # Validate schema accepts null URLs
    schema = AttachmentResponse(**result)
    assert schema.filename == "sample.png"
    assert schema.url is None
    assert schema.download_url is None


def test_attachment_payload_unconfigured_s3_does_not_crash(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_ACCESS_KEY_ID", raising=False)

    raw_content = f'{ATTACHMENT_MESSAGE_PREFIX}{{"object_key":"attachments/foo.png","filename":"foo.png"}}'
    result = _attachment_payload(raw_content)
    assert result is not None
    assert result["filename"] == "foo.png"
    assert result["url"] is None
