"""AWS S3 storage helper for NetCHB duty Excel artifacts."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Add app utils to path for imports
_app_dir = Path(__file__).parent.parent.parent.resolve()
_utils_dir = _app_dir / "utils"
if str(_utils_dir) not in sys.path:
    sys.path.insert(0, str(_utils_dir))

from s3_storage import S3StorageClient


class NetChbDutyStorageManager:
    """Handles AWS S3 storage interactions for duty report uploads."""

    def __init__(self) -> None:
        self.prefix = os.getenv("NETCHB_DUTY_STORAGE_PREFIX", "netchb-duty")
        self.expiry_seconds = int(os.getenv("NETCHB_DUTY_URL_TTL_SECONDS", "3600"))
        self.s3_client = S3StorageClient()

    def upload_excel(self, file_path: Path, mawb: str, airport_code: Optional[str] = None, customer: Optional[str] = None, template_name: Optional[str] = None) -> Tuple[str, str]:
        """
        Upload an Excel file to S3 storage and return (path, signed_url).
        
        File is renamed using format: "{mawb} {airport_code} {customer}.xlsx" or "{mawb} {airport_code} {customer}_V2.xlsx" for Shoaib template
        
        Args:
            file_path: Path to Excel file
            mawb: MAWB number (11 digits)
            airport_code: Optional airport code
            customer: Optional customer name
            template_name: Optional template name (for V2 suffix detection for Shoaib template)
            
        Returns:
            Tuple of (storage_path, signed_url)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        # Build filename: "{mawb_formatted} {airport_code} {customer}.xlsx"
        # Format MAWB as xxx-xxxxxxxx (e.g., 131-35768106)
        mawb_clean = mawb.replace("/", "-").replace("\\", "-").replace(" ", "").replace("-", "")
        if len(mawb_clean) == 11:
            formatted_mawb = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
        else:
            formatted_mawb = mawb_clean
        
        parts = [formatted_mawb]
        
        if airport_code:
            # Keep spaces but remove unsafe path characters
            safe_airport = airport_code.strip().replace("/", "-").replace("\\", "-")
            if safe_airport:
                parts.append(safe_airport)
        
        if customer:
            # Keep spaces but remove unsafe path characters
            safe_customer = customer.strip().replace("/", "-").replace("\\", "-")
            if safe_customer:
                parts.append(safe_customer)
        
        # Add V2 suffix for Shoaib template
        if template_name and "shoaib" in template_name.lower():
            filename = " ".join(parts) + "_V2.xlsx"
        else:
            filename = " ".join(parts) + ".xlsx"
        
        # Store in customizable-reports/ subfolder
        key = f"{self.prefix}/customizable-reports/{filename}"

        try:
            self.s3_client.upload_file(
                str(file_path),
                key,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to upload duty report to S3: {exc}") from exc

        signed_url = ""
        try:
            signed_url = self.s3_client.generate_presigned_url(key, expires_in=self.expiry_seconds)
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Excel Upload: Failed to create signed URL: {exc}")
            signed_url = ""

        return key, signed_url
    
    def create_signed_url(self, storage_path: str, expires_in: Optional[int] = None) -> Optional[str]:
        """
        Create a presigned URL for an existing file in storage.
        
        Args:
            storage_path: Path to file in storage (S3 key)
            expires_in: Expiration time in seconds (defaults to configured TTL)
            
        Returns:
            Presigned URL or None if failed
        """
        if expires_in is None:
            expires_in = self.expiry_seconds
        
        try:
            return self.s3_client.generate_presigned_url(storage_path, expires_in=expires_in)
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create presigned URL for {storage_path}: {exc}")
            return None

    def upload_pdf(self, file_path: Path, mawb: str, airport_code: Optional[str] = None, customer: Optional[str] = None, batch_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Upload a PDF file to S3 storage and return (path, signed_url).
        
        File is stored at: netchb-duty/7501-batch-pdfs/{mawb} {airport_code} {customer}.pdf
        
        Args:
            file_path: Path to PDF file
            mawb: MAWB number (11 digits)
            airport_code: Optional airport code
            customer: Optional customer name
            batch_id: Optional batch ID (deprecated, kept for backward compatibility but not used)
            
        Returns:
            Tuple of (storage_path, signed_url)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Build filename: "{mawb_formatted} {airport_code} {customer}.pdf"
        # Format MAWB as xxx-xxxxxxxx (e.g., 131-35768106)
        mawb_clean = mawb.replace("/", "-").replace("\\", "-").replace(" ", "").replace("-", "")
        if len(mawb_clean) == 11:
            formatted_mawb = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
        else:
            formatted_mawb = mawb_clean
        
        parts = [formatted_mawb]
        
        if airport_code:
            # Keep spaces but remove unsafe path characters
            safe_airport = airport_code.strip().replace("/", "-").replace("\\", "-")
            if safe_airport:
                parts.append(safe_airport)
        
        if customer:
            # Keep spaces but remove unsafe path characters
            safe_customer = customer.strip().replace("/", "-").replace("\\", "-")
            if safe_customer:
                parts.append(safe_customer)
        
        filename = " ".join(parts) + ".pdf"
        
        # Store in 7501-batch-pdfs/ subfolder (no batch_id subfolder)
        key = f"{self.prefix}/7501-batch-pdfs/{filename}"

        try:
            self.s3_client.upload_file(
                str(file_path),
                key,
                content_type="application/pdf",
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to upload PDF to S3: {exc}") from exc

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"PDF Upload: Successfully uploaded PDF to storage path: {key}")
        
        signed_url = ""
        try:
            signed_url = self.s3_client.generate_presigned_url(key, expires_in=self.expiry_seconds)
            logger.info(f"PDF Upload: ✓ Successfully created presigned URL for PDF")
        except Exception as exc:
            logger.error(f"PDF Upload: Failed to create presigned URL for key '{key}': {exc}", exc_info=True)
            signed_url = ""

        if not signed_url:
            logger.error(f"PDF Upload: ⚠️ No presigned URL created for PDF. Storage path: {key}")

        return key, signed_url

    def download_file(self, storage_path: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            storage_path: Path to file in storage (S3 key)
            
        Returns:
            File contents as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If download fails
        """
        try:
            return self.s3_client.download_file(storage_path)
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Failed to download file from S3: {exc}") from exc
