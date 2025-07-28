"""
File security validation module for receipt processing
"""

import hashlib
from io import BytesIO
import logging
from pathlib import Path
import re

import magic
from PIL import Image

from core.receipt_exceptions import FileSecurityError, FileValidationError

logger = logging.getLogger(__name__)

# Allowed file types and their magic number signatures
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF", b"WEBP"],
    "application/pdf": [b"%PDF-"],
}

# Maximum file sizes per type (in bytes)
MAX_FILE_SIZES = {
    "image/jpeg": 10 * 1024 * 1024,  # 10MB
    "image/png": 10 * 1024 * 1024,  # 10MB
    "image/webp": 10 * 1024 * 1024,  # 10MB
    "application/pdf": 15 * 1024 * 1024,  # 15MB
}

# Suspicious patterns in file content
SUSPICIOUS_PATTERNS = [
    b"<script",
    b"javascript:",
    b"vbscript:",
    b"onload=",
    b"onerror=",
    b"eval(",
    b"exec(",
    b"System.IO",
    b"Shell.Application",
]


class FileSecurityValidator:
    """Comprehensive file security validator for receipt uploads"""

    def __init__(self):
        self.magic_detector = magic.Magic(mime=True)

    def validate_file_comprehensive(
        self, file_bytes: bytes, declared_content_type: str, filename: str | None = None
    ) -> dict[str, any]:
        """
        Perform comprehensive file validation including security checks

        Args:
            file_bytes: The file content as bytes
            declared_content_type: MIME type declared by client
            filename: Original filename (optional)

        Returns:
            Dict with validation results

        Raises:
            FileSecurityError: If file fails security validation
            FileValidationError: If file fails basic validation
        """
        validation_result = {
            "is_valid": True,
            "detected_type": None,
            "file_size": len(file_bytes),
            "security_checks": {},
            "warnings": [],
        }

        # Basic file size check
        if len(file_bytes) == 0:
            raise FileValidationError("Empty file uploaded")

        if len(file_bytes) < 100:
            raise FileValidationError("File too small to be a valid document")

        # Detect actual file type using magic numbers
        try:
            detected_type = self.magic_detector.from_buffer(file_bytes)
            validation_result["detected_type"] = detected_type
        except Exception as e:
            logger.warning(f"Magic number detection failed: {e}")
            validation_result["warnings"].append("Could not detect file type")

        # Validate declared vs detected type
        if detected_type and detected_type != declared_content_type:
            # Allow some common variations
            type_aliases = {
                "image/jpg": "image/jpeg",
                "image/pjpeg": "image/jpeg",
            }

            normalized_declared = type_aliases.get(
                declared_content_type, declared_content_type
            )

            if detected_type != normalized_declared:
                raise FileSecurityError(
                    f"File type mismatch: declared '{declared_content_type}' but detected '{detected_type}'",
                    details={
                        "declared_type": declared_content_type,
                        "detected_type": detected_type,
                    },
                )

        # Check if file type is allowed
        if declared_content_type not in ALLOWED_MIME_TYPES:
            raise FileValidationError(
                f"File type '{declared_content_type}' is not allowed",
                details={"allowed_types": list(ALLOWED_MIME_TYPES.keys())},
            )

        # Check file size limits
        max_size = MAX_FILE_SIZES.get(declared_content_type, 5 * 1024 * 1024)
        if len(file_bytes) > max_size:
            raise FileValidationError(
                f"File too large: {len(file_bytes)} bytes (max: {max_size} bytes)",
                details={
                    "file_size": len(file_bytes),
                    "max_size": max_size,
                    "size_mb": round(len(file_bytes) / (1024 * 1024), 2),
                },
            )

        # Magic number validation
        self._validate_magic_numbers(file_bytes, declared_content_type)
        validation_result["security_checks"]["magic_numbers"] = "passed"

        # Content structure validation
        self._validate_file_structure(file_bytes, declared_content_type)
        validation_result["security_checks"]["structure"] = "passed"

        # Malware pattern detection
        suspicious_patterns = self._scan_for_suspicious_patterns(file_bytes)
        if suspicious_patterns:
            raise FileSecurityError(
                "Suspicious patterns detected in file",
                details={"patterns": suspicious_patterns},
            )
        validation_result["security_checks"]["malware_scan"] = "passed"

        # Filename validation (if provided)
        if filename:
            self._validate_filename(filename, declared_content_type)
            validation_result["security_checks"]["filename"] = "passed"

        return validation_result

    def _validate_magic_numbers(self, file_bytes: bytes, content_type: str) -> None:
        """Validate file magic numbers/signatures"""
        expected_signatures = ALLOWED_MIME_TYPES.get(content_type, [])

        if not expected_signatures:
            return

        # Check if file starts with any of the expected signatures
        file_header = file_bytes[:20]  # Check first 20 bytes

        for signature in expected_signatures:
            if file_header.startswith(signature):
                return

        # Special case for WEBP (RIFF container)
        if content_type == "image/webp":
            if file_header.startswith(b"RIFF") and b"WEBP" in file_bytes[:20]:
                return

        raise FileSecurityError(
            f"Invalid file signature for {content_type}",
            details={
                "expected_signatures": [sig.hex() for sig in expected_signatures],
                "actual_header": file_header[:10].hex(),
            },
        )

    def _validate_file_structure(self, file_bytes: bytes, content_type: str) -> None:
        """Validate internal file structure"""

        if content_type.startswith("image/"):
            self._validate_image_structure(file_bytes)
        elif content_type == "application/pdf":
            self._validate_pdf_structure(file_bytes)

    def _validate_image_structure(self, file_bytes: bytes) -> None:
        """Validate image file structure using PIL"""
        try:
            with Image.open(BytesIO(file_bytes)) as img:
                # Verify the image can be loaded
                img.verify()

                # Additional checks
                if img.size[0] * img.size[1] > 50000000:  # 50MP limit
                    raise FileSecurityError("Image resolution too high")

                if img.size[0] < 50 or img.size[1] < 50:
                    raise FileValidationError("Image resolution too low for OCR")

        except Image.UnidentifiedImageError:
            raise FileSecurityError("Invalid or corrupted image file")
        except Exception as e:
            raise FileSecurityError(f"Image validation failed: {e!s}")

    def _validate_pdf_structure(self, file_bytes: bytes) -> None:
        """Basic PDF structure validation"""
        if not file_bytes.startswith(b"%PDF-"):
            raise FileSecurityError("Invalid PDF header")

        if b"%%EOF" not in file_bytes[-1024:]:
            raise FileValidationError("PDF missing EOF marker")

        # Check for suspicious PDF content
        pdf_text = file_bytes.decode("latin1", errors="ignore").lower()

        suspicious_pdf_patterns = [
            "/javascript",
            "/js",
            "/launch",
            "/openaction",
            "eval(",
            "unescape(",
        ]

        for pattern in suspicious_pdf_patterns:
            if pattern in pdf_text:
                raise FileSecurityError(
                    f"Suspicious PDF content detected: {pattern}",
                    details={"pattern": pattern},
                )

    def _scan_for_suspicious_patterns(self, file_bytes: bytes) -> list[str]:
        """Scan for malware patterns in file content"""
        found_patterns = []

        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in file_bytes:
                found_patterns.append(pattern.decode("utf-8", errors="ignore"))

        return found_patterns

    def _validate_filename(self, filename: str, content_type: str) -> None:
        """Validate filename for security issues"""

        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise FileSecurityError("Path traversal attempt in filename")

        # Check filename length
        if len(filename) > 255:
            raise FileValidationError("Filename too long")

        # Check for suspicious characters
        if re.search(r'[<>:"|?*\x00-\x1f]', filename):
            raise FileSecurityError("Suspicious characters in filename")

        # Validate file extension matches content type
        extension_mapping = {
            "image/jpeg": [".jpg", ".jpeg"],
            "image/png": [".png"],
            "image/webp": [".webp"],
            "application/pdf": [".pdf"],
        }

        expected_extensions = extension_mapping.get(content_type, [])
        if expected_extensions:
            file_ext = Path(filename).suffix.lower()
            if file_ext not in expected_extensions:
                raise FileValidationError(
                    f"Filename extension '{file_ext}' doesn't match content type '{content_type}'",
                    details={
                        "filename": filename,
                        "expected_extensions": expected_extensions,
                    },
                )

    def calculate_file_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash of file for caching and deduplication"""
        return hashlib.sha256(file_bytes).hexdigest()

    def generate_safe_filename(
        self, original_filename: str | None, content_type: str
    ) -> str:
        """Generate a safe filename for storage"""
        from datetime import datetime
        import uuid

        # Get file extension
        extension_mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
        }

        extension = extension_mapping.get(content_type, ".bin")

        # Generate safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        return f"receipt_{timestamp}_{unique_id}{extension}"


# Global instance
file_security_validator = FileSecurityValidator()
