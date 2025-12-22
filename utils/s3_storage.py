"""Shared AWS S3 storage utilities for file operations."""

from __future__ import annotations

import io
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3StorageClient:
    """Base S3 storage client for common operations."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: S3 bucket name (defaults to AWS_S3_BUCKET_NAME env var)
            region_name: AWS region (defaults to AWS_REGION env var or 'us-east-1')
            access_key_id: AWS access key ID (defaults to AWS_ACCESS_KEY_ID env var)
            secret_access_key: AWS secret access key (defaults to AWS_SECRET_ACCESS_KEY env var)
        """
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET_NAME")
        if not self.bucket_name:
            raise RuntimeError("AWS_S3_BUCKET_NAME must be configured (env var or parameter)")

        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        if not self.access_key_id or not self.secret_access_key:
            raise RuntimeError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be configured")

        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name,
            )
        except Exception as exc:
            logger.error(f"Failed to initialize S3 client: {exc}")
            raise RuntimeError(f"Failed to initialize S3 client: {exc}") from exc

        # Verify bucket exists and is accessible
        self._verify_bucket_access()

    def _verify_bucket_access(self) -> None:
        """Verify that the bucket exists and is accessible."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                raise RuntimeError(
                    f"S3 bucket '{self.bucket_name}' does not exist. "
                    f"Please create it in AWS Console or contact your administrator."
                ) from exc
            elif error_code == '403':
                raise RuntimeError(
                    f"Access denied to S3 bucket '{self.bucket_name}'. "
                    f"Please check your AWS credentials and IAM permissions."
                ) from exc
            else:
                raise RuntimeError(
                    f"Failed to access S3 bucket '{self.bucket_name}': {exc}"
                ) from exc
        except NoCredentialsError:
            raise RuntimeError(
                "AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
            ) from exc
        except Exception as exc:
            logger.warning(f"Could not verify bucket access: {exc} (continuing anyway)")

    def upload_file(
        self,
        file_path: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path to upload
            key: S3 object key (path within bucket)
            content_type: Content type/MIME type (e.g., 'application/pdf')
            metadata: Optional metadata dictionary
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            extra_args['Metadata'] = metadata

        try:
            self.client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs=extra_args if extra_args else None,
            )
            logger.info(f"Successfully uploaded file to s3://{self.bucket_name}/{key}")
        except ClientError as exc:
            error_msg = exc.response.get('Error', {}).get('Message', str(exc))
            logger.error(f"Failed to upload file to S3: {error_msg}")
            raise RuntimeError(f"Failed to upload file to S3: {error_msg}") from exc

    def upload_fileobj(
        self,
        file_obj: io.BytesIO | bytes,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Upload file-like object or bytes to S3.
        
        Args:
            file_obj: File-like object (BytesIO) or bytes
            key: S3 object key (path within bucket)
            content_type: Content type/MIME type (e.g., 'application/pdf')
            metadata: Optional metadata dictionary
            
        Raises:
            RuntimeError: If upload fails
        """
        if isinstance(file_obj, bytes):
            file_obj = io.BytesIO(file_obj)

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            extra_args['Metadata'] = metadata

        try:
            file_obj.seek(0)  # Reset to beginning
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args if extra_args else None,
            )
            logger.info(f"Successfully uploaded file object to s3://{self.bucket_name}/{key}")
        except ClientError as exc:
            error_msg = exc.response.get('Error', {}).get('Message', str(exc))
            logger.error(f"Failed to upload file object to S3: {error_msg}")
            raise RuntimeError(f"Failed to upload file object to S3: {error_msg}") from exc

    def download_file(self, key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            key: S3 object key (path within bucket)
            
        Returns:
            File contents as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If download fails
        """
        try:
            buffer = io.BytesIO()
            self.client.download_fileobj(self.bucket_name, key, buffer)
            buffer.seek(0)
            return buffer.read()
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: s3://{self.bucket_name}/{key}") from exc
            error_msg = exc.response.get('Error', {}).get('Message', str(exc))
            logger.error(f"Failed to download file from S3: {error_msg}")
            raise RuntimeError(f"Failed to download file from S3: {error_msg}") from exc

    def delete_file(self, key: str) -> None:
        """
        Delete a file from S3.
        
        Args:
            key: S3 object key (path within bucket)
            
        Raises:
            RuntimeError: If deletion fails (file may not exist, but this is not an error)
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted file from s3://{self.bucket_name}/{key}")
        except ClientError as exc:
            error_msg = exc.response.get('Error', {}).get('Message', str(exc))
            logger.error(f"Failed to delete file from S3: {error_msg}")
            # Don't raise exception for delete operations - idempotent
            logger.warning(f"Delete operation failed but continuing (file may not exist): {key}")

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        http_method: str = 'GET',
    ) -> str:
        """
        Generate a presigned URL for accessing an S3 object.
        
        Args:
            key: S3 object key (path within bucket)
            expires_in: URL expiration time in seconds (default: 3600 = 1 hour)
            http_method: HTTP method ('GET' for download, 'PUT' for upload)
            
        Returns:
            Presigned URL string
            
        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object' if http_method == 'GET' else 'put_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as exc:
            error_msg = exc.response.get('Error', {}).get('Message', str(exc))
            logger.error(f"Failed to generate presigned URL: {error_msg}")
            raise RuntimeError(f"Failed to generate presigned URL: {error_msg}") from exc

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            key: S3 object key (path within bucket)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False
            # For other errors, log and return False
            logger.warning(f"Error checking file existence: {exc}")
            return False
        except Exception:
            return False





