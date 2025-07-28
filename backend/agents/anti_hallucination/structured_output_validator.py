"""
Structured output validator with JSON Schema validation.

Provides mechanisms to validate structured outputs from LLM responses
using JSON Schema to prevent hallucinations and ensure data consistency.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import re
from typing import Any

from jsonschema import (
    ValidationError as JSONSchemaValidationError,
    validate,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of structured output validation"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    confidence: float
    validated_data: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class StructuredOutputValidator:
    """
    Validates structured outputs using JSON Schema to prevent hallucinations.

    Implements strict validation with fallback mechanisms and
    confidence scoring based on validation results.
    """

    def __init__(self, **kwargs):
        self.strict_mode = kwargs.get("strict_mode", True)
        self.allow_partial = kwargs.get("allow_partial", False)
        self.max_validation_errors = kwargs.get("max_validation_errors", 5)

        # Define receipt analysis schema
        self.receipt_schema = {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Name of the store",
                },
                "store_address": {"type": "string", "description": "Store address"},
                "date": {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$",
                    "description": "Receipt date in YYYY-MM-DD format",
                },
                "time": {
                    "type": "string",
                    "pattern": r"^\d{2}:\d{2}$",
                    "description": "Receipt time in HH:MM format",
                },
                "receipt_number": {"type": "string", "description": "Receipt number"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Product name",
                            },
                            "original_name": {
                                "type": "string",
                                "description": "Original product name from receipt",
                            },
                            "product_code": {
                                "type": "string",
                                "description": "Product code/barcode",
                            },
                            "quantity": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Product quantity",
                            },
                            "unit": {
                                "type": "string",
                                "description": "Unit of measurement",
                            },
                            "unit_price": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Price per unit",
                            },
                            "total_price": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Total price for this item",
                            },
                            "vat_rate": {
                                "type": "string",
                                "enum": ["A", "B", "C"],
                                "description": "VAT rate category",
                            },
                            "discount": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Discount amount",
                            },
                            "category": {
                                "type": "string",
                                "description": "Product category",
                            },
                        },
                        "required": ["name", "quantity", "unit_price", "total_price"],
                    },
                    "minItems": 0,
                    "description": "List of purchased items",
                },
                "discounts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "amount": {"type": "number", "minimum": 0},
                        },
                        "required": ["description", "amount"],
                    },
                    "description": "List of discounts applied",
                },
                "coupons": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "amount": {"type": "number", "minimum": 0},
                        },
                        "required": ["code", "amount"],
                    },
                    "description": "List of coupons used",
                },
                "vat_summary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tax_category": {"type": "string"},
                            "net": {"type": "number", "minimum": 0},
                            "tax_amount": {"type": "number", "minimum": 0},
                            "gross": {"type": "number", "minimum": 0},
                        },
                        "required": ["tax_category", "net", "tax_amount", "gross"],
                    },
                    "description": "VAT summary by category",
                },
                "subtotals": {
                    "type": "object",
                    "properties": {
                        "vat_a_amount": {"type": "number", "minimum": 0},
                        "vat_b_amount": {"type": "number", "minimum": 0},
                        "vat_c_amount": {"type": "number", "minimum": 0},
                        "total_discount": {"type": "number", "minimum": 0},
                    },
                    "description": "Subtotals by VAT category",
                },
                "total_amount": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Total amount to pay",
                },
                "payment_method": {
                    "type": "string",
                    "description": "Payment method used",
                },
            },
            "required": ["store_name", "items", "total_amount"],
            "additionalProperties": False,
        }

    def validate_receipt_data(self, data: str | dict[str, Any]) -> ValidationResult:
        """
        Validate receipt data against JSON Schema.

        Args:
            data: Receipt data as string (JSON) or dictionary

        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        confidence = 1.0

        try:
            # Parse JSON if string
            if isinstance(data, str):
                parsed_data = self._extract_json_from_text(data)
                if parsed_data is None:
                    return ValidationResult(
                        is_valid=False,
                        errors=["Failed to extract valid JSON from text"],
                        warnings=warnings,
                        confidence=0.0,
                    )
            else:
                parsed_data = data

            # Validate against schema with detailed error reporting
            try:
                validate(instance=parsed_data, schema=self.receipt_schema)
            except JSONSchemaValidationError as e:
                # Extract detailed validation errors
                error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
                errors.append(f"Schema validation error at {error_path}: {e.message}")
                confidence *= 0.5
            except Exception as e:
                errors.append(f"Unexpected validation error: {e!s}")
                confidence *= 0.3

            # Additional business logic validation
            business_errors, business_warnings = self._validate_business_logic(
                parsed_data
            )
            errors.extend(business_errors)
            warnings.extend(business_warnings)

            # Calculate confidence
            confidence = self._calculate_validation_confidence(
                parsed_data, errors, warnings
            )

            # Determine if valid based on errors and strict mode
            is_valid = len(errors) == 0 or (not self.strict_mode and confidence > 0.5)

            # Add validation metadata
            {
                "total_errors": len(errors),
                "total_warnings": len(warnings),
                "strict_mode": self.strict_mode,
                "schema_validated": len(errors) == 0,
            }

            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                confidence=confidence,
                validated_data=parsed_data if is_valid else None,
            )

        except Exception as e:
            logger.error(f"Critical error in receipt validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Critical validation error: {e!s}"],
                warnings=warnings,
                confidence=0.0,
            )

    def _extract_json_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract JSON from text that may contain additional content.

        Args:
            text: Text that may contain JSON

        Returns:
            Parsed JSON dictionary or None if extraction fails
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for JSON extraction")
            return None

        # Clean the text first
        text = text.strip()

        # Try to find JSON object in text with multiple strategies
        json_patterns = [
            r"```json\s*(\{[\s\S]*?\})\s*```",  # JSON in markdown code block
            r"```\s*(\{[\s\S]*?\})\s*```",  # JSON in code block
            r"\{[\s\S]*\}",  # Basic JSON object
            r"\[[\s\S]*\]",  # JSON array
        ]

        for pattern in json_patterns:
            try:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    try:
                        # Handle both direct matches and group matches
                        json_str = (
                            match
                            if isinstance(match, str)
                            else match[0] if match else ""
                        )
                        if json_str:
                            # Clean the JSON string
                            json_str = json_str.strip()
                            # Try to fix common JSON issues
                            json_str = self._fix_common_json_issues(json_str)

                            parsed_data = json.loads(json_str)
                            if isinstance(parsed_data, dict):
                                logger.info(
                                    "Successfully extracted and parsed JSON from text"
                                )
                                return parsed_data
                    except json.JSONDecodeError as e:
                        logger.debug(
                            f"Failed to parse JSON with pattern {pattern}: {e}"
                        )
                        continue
            except Exception as e:
                logger.debug(f"Error with pattern {pattern}: {e}")
                continue

        # Try parsing the entire text as JSON (last resort)
        try:
            cleaned_text = self._fix_common_json_issues(text)
            parsed_data = json.loads(cleaned_text)
            if isinstance(parsed_data, dict):
                logger.info("Successfully parsed entire text as JSON")
                return parsed_data
        except json.JSONDecodeError:
            pass

        logger.warning("Failed to extract valid JSON from text")
        return None

    def _fix_common_json_issues(self, json_str: str) -> str:
        """
        Fix common JSON formatting issues.

        Args:
            json_str: Raw JSON string

        Returns:
            Cleaned JSON string
        """
        if not json_str:
            return json_str

        # Remove leading/trailing whitespace and newlines
        json_str = json_str.strip()

        # Fix common issues
        fixes = [
            # Fix trailing commas
            (r",(\s*[}\]])", r"\1"),
            # Fix missing quotes around keys (but be more careful)
            (r"(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)", r'\1"\2"\3'),
            # Fix single quotes to double quotes
            (r"'([^']*)'", r'"\1"'),
            # Fix unescaped quotes in values (simplified)
            (r'([^\\])"([^"]*)"([^"]*)"', r'\1"\2\\"\3"'),
            # Remove comments (simple)
            (r"//.*$", "", re.MULTILINE),
            (r"/\*.*?\*/", "", re.DOTALL),
        ]

        for pattern, replacement, *flags in fixes:
            try:
                if flags:
                    json_str = re.sub(pattern, replacement, json_str, flags=flags[0])
                else:
                    json_str = re.sub(pattern, replacement, json_str)
            except Exception as e:
                logger.debug(f"Error applying JSON fix {pattern}: {e}")
                continue

        return json_str

    def _validate_business_logic(
        self, data: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """
        Validate business logic consistency.

        Args:
            data: Parsed receipt data

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        # Validate total amount consistency
        items = data.get("items", [])
        if items:
            calculated_total = sum(
                item.get("total_price", 0) for item in items if isinstance(item, dict)
            )
            claimed_total = data.get("total_amount", 0)

            if abs(calculated_total - claimed_total) > 0.01:
                errors.append(
                    f"Total amount mismatch: calculated {calculated_total:.2f}, "
                    f"claimed {claimed_total:.2f}"
                )

        # Validate item consistency
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            total_price = item.get("total_price", 0)

            if quantity > 0 and unit_price > 0:
                expected_total = quantity * unit_price
                if abs(expected_total - total_price) > 0.01:
                    errors.append(
                        f"Item {i} price mismatch: {quantity} * {unit_price} = "
                        f"{expected_total}, but total_price is {total_price}"
                    )

        # Validate date format
        date_str = data.get("date", "")
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append(f"Invalid date format: {date_str}")

        # Validate store name
        store_name = data.get("store_name", "")
        if not store_name or store_name.lower() in ["unknown", "nieznany", ""]:
            warnings.append("Store name is generic or missing")

        return errors, warnings

    def _calculate_validation_confidence(
        self, data: dict[str, Any], errors: list[str], warnings: list[str]
    ) -> float:
        """
        Calculate confidence score based on validation results.

        Args:
            data: Validated data
            errors: Validation errors
            warnings: Validation warnings

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0

        # Reduce confidence for errors
        confidence -= len(errors) * 0.2

        # Reduce confidence for warnings
        confidence -= len(warnings) * 0.05

        # Boost confidence for complete data
        required_fields = ["store_name", "items", "total_amount"]
        present_fields = sum(1 for field in required_fields if data.get(field))
        completeness_ratio = present_fields / len(required_fields)
        confidence *= 0.5 + 0.5 * completeness_ratio

        # Boost confidence for realistic data
        if self._is_realistic_data(data):
            confidence *= 1.1

        return max(0.0, min(1.0, confidence))

    def _is_realistic_data(self, data: dict[str, Any]) -> bool:
        """
        Check if data appears realistic.

        Args:
            data: Receipt data

        Returns:
            True if data appears realistic
        """
        # Check total amount
        total = data.get("total_amount", 0)
        if total <= 0 or total > 10000:
            return False

        # Check item prices
        items = data.get("items", [])
        for item in items:
            if not isinstance(item, dict):
                continue
            price = item.get("unit_price", 0)
            if price <= 0 or price > 1000:
                return False

        return True

    def get_structured_output_prompt(self) -> str:
        """
        Get prompt for structured output generation.

        Returns:
            Formatted prompt for LLM
        """
        return (
            f"Analyze the receipt and return structured data in JSON format.\n\n"
            f"The response must be a valid JSON object with the following structure:\n"
            f"{json.dumps(self.receipt_schema, indent=2)}\n\n"
            f"Important:\n"
            f"- All required fields must be present\n"
            f"- Numbers must be positive\n"
            f"- Dates must be in YYYY-MM-DD format\n"
            f"- Times must be in HH:MM format\n"
            f"- VAT rates must be A, B, or C\n"
            f"- Return ONLY the JSON object, no additional text\n\n"
            f"Example response:\n"
            f"{{\n"
            f'  "store_name": "Lidl",\n'
            f'  "date": "2024-12-20",\n'
            f'  "time": "14:30",\n'
            f'  "items": [\n'
            f"    {{\n"
            f'      "name": "Mleko 3.2%",\n'
            f'      "quantity": 1,\n'
            f'      "unit_price": 4.99,\n'
            f'      "total_price": 4.99,\n'
            f'      "vat_rate": "A"\n'
            f"    }}\n"
            f"  ],\n"
            f'  "total_amount": 4.99\n'
            f"}}"
        )
