import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.core.config import settings
from app.services.storage import StorageService


def test_local_storage_lifecycle(tmp_path: Path):
    with patch.object(settings, "aws_access_key_id", None), \
         patch.object(settings, "aws_secret_access_key", None), \
         patch.object(settings, "aws_s3_bucket", None), \
         patch.object(settings, "local_storage_dir", str(tmp_path)):
        service = StorageService()

        key = "test_transcripts/sample.txt"
        test_data = b"Interviewer: Tell me about yourself.\nCandidate: I am a software engineer."

        # Upload
        uri = service.upload_bytes(test_data, key, "text/plain")
        assert Path(uri).exists()
        assert service.exists(key)

        # Download
        downloaded = service.download_bytes(key)
        assert downloaded == test_data

        # Presigned URLs
        upload_url = service.generate_presigned_upload_url(key)
        assert "sample.txt" in upload_url
        download_url = service.generate_presigned_download_url(key)
        assert "sample.txt" in download_url

        # Delete
        assert service.delete(key) is True
        assert service.exists(key) is False


def test_s3_storage_mock():
    mock_s3 = MagicMock()
    with patch.object(settings, "aws_access_key_id", "mock-key"), \
         patch.object(settings, "aws_secret_access_key", "mock-secret"), \
         patch.object(settings, "aws_s3_bucket", "test-bucket"), \
         patch("app.services.storage.boto3.client", return_value=mock_s3):
        service = StorageService()
        assert service.is_s3 is True
        assert service.bucket == "test-bucket"

        # Test upload
        uri = service.upload_bytes(b"content", "doc.txt")
        assert uri == "s3://test-bucket/doc.txt"
        mock_s3.put_object.assert_called_once()

        # Test download
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"content")}
        data = service.download_bytes("doc.txt")
        assert data == b"content"

        # Test delete
        service.delete("doc.txt")
        mock_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key="doc.txt")
