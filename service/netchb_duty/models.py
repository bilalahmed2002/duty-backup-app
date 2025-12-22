"""Pydantic models for NetCHB duty service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator, model_validator, validator


MAWBPattern = constr(pattern=r"^\d{11}$")


class BrokerBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    username: constr(strip_whitespace=True, min_length=1, max_length=255)
    password: constr(strip_whitespace=True, min_length=1, max_length=255)
    company: Optional[constr(strip_whitespace=True, max_length=255)] = None
    is_active: bool = True
    is_authentication_required: bool = False
    otp_uri: Optional[constr(strip_whitespace=True, max_length=500)] = None
    entries_format: Optional[constr(strip_whitespace=True, max_length=50)] = "allied"

    @field_validator("otp_uri")
    @classmethod
    def validate_otp_uri_format(cls, v):
        if v and not v.startswith("otpauth://totp/"):
            raise ValueError("OTP URI must start with 'otpauth://totp/'")
        return v

    @model_validator(mode="after")
    def validate_otp_uri_required(self):
        if self.is_authentication_required and not self.otp_uri:
            raise ValueError("OTP URI is required when authentication is enabled")
        return self


class BrokerCreate(BrokerBase):
    pass


class BrokerUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    username: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    password: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    company: Optional[constr(strip_whitespace=True, max_length=255)] = None
    is_active: Optional[bool] = None
    is_authentication_required: Optional[bool] = None
    otp_uri: Optional[constr(strip_whitespace=True, max_length=500)] = None
    entries_format: Optional[constr(strip_whitespace=True, max_length=50)] = None

    @field_validator("otp_uri")
    @classmethod
    def validate_otp_uri_format(cls, v):
        if v and not v.startswith("otpauth://totp/"):
            raise ValueError("OTP URI must start with 'otpauth://totp/'")
        return v

    @model_validator(mode="after")
    def validate_otp_uri_required(self):
        if self.is_authentication_required is True and not self.otp_uri:
            raise ValueError("OTP URI is required when authentication is enabled")
        return self


class BrokerResponse(BaseModel):
    id: UUID
    name: str
    username: str
    company: Optional[str]
    is_active: bool
    is_authentication_required: bool
    entries_format: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    otp_uri: Optional[str] = None  # Included for super admin editing


class FormatBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    template_identifier: constr(strip_whitespace=True, min_length=1, max_length=255)
    description: Optional[constr(strip_whitespace=True, max_length=500)] = None
    template_payload: Optional[Dict[str, Any]] = None  # Stores full payload config for HTTP requests (headerFields, manifestFields, defaultValues, etc.)
    is_active: bool = True


class FormatCreate(FormatBase):
    pass


class FormatUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    template_identifier: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    description: Optional[constr(strip_whitespace=True, max_length=500)] = None
    template_payload: Optional[Dict[str, Any]] = None  # Stores full payload config for HTTP requests (headerFields, manifestFields, defaultValues, etc.)
    is_active: Optional[bool] = None


class FormatResponse(BaseModel):
    id: UUID
    name: str
    template_identifier: str
    description: Optional[str]
    template_payload: Optional[Dict[str, Any]] = None  # Full payload config (headerFields, manifestFields, defaultValues, etc.)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DutySections(BaseModel):
    ams: bool = True
    entries: bool = True
    custom: bool = True
    download_7501_pdf: bool = False


class DutyRunRequest(BaseModel):
    broker_id: UUID
    format_id: UUID
    mawbs: List[str] = Field(..., min_items=1, max_items=100)
    sections: DutySections = DutySections()

    @validator("mawbs")
    def validate_mawbs(cls, items: List[str]) -> List[str]:
        normalized: List[str] = []
        for mawb in items:
            digits = "".join(ch for ch in mawb if ch.isdigit())
            if len(digits) != 11:
                raise ValueError(f"MAWB value '{mawb}' must contain exactly 11 digits")
            normalized.append(digits)
        return normalized


class DutyRunStatus(str):
    """Enumeration for job status."""


DutyRunStatusLiteral = Literal["pending", "running", "success", "failed"]
BatchItemStatusLiteral = Literal["pending", "running", "success", "failed", "cancelled"]


class DutyRunStatusResponse(BaseModel):
    job_id: str
    status: DutyRunStatusLiteral
    message: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Dict[str, object]]] = None
    started_at: datetime
    updated_at: datetime


class DutyResultResponse(BaseModel):
    id: UUID
    mawb: str
    broker_id: UUID
    format_id: UUID
    status: DutyRunStatusLiteral
    broker_name: Optional[str] = None
    airport_code: Optional[str] = None
    customer: Optional[str] = None
    batch_id: Optional[UUID] = None
    template_name: Optional[str] = None
    sections: Optional[Dict[str, bool]] = None
    summary: Optional[Dict[str, str]] = None
    artifact_path: Optional[str] = None
    artifact_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime]
    updated_at: datetime


# Batch Processing Models
BatchStatusLiteral = Literal["pending", "running", "completed", "cancelled", "failed"]


class BatchItemCreate(BaseModel):
    mawb: str = Field(..., description="MAWB number (11 digits)")
    airport_code: Optional[str] = None
    customer: Optional[str] = None
    checkbook_hawbs: Optional[str] = None
    broker_id: UUID = Field(..., description="Broker ID for this item")
    format_id: UUID = Field(..., description="Format ID for this item")

    @validator("mawb")
    def validate_mawb(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) != 11:
            raise ValueError(f"MAWB must contain exactly 11 digits, found {len(digits)}")
        return digits


class BatchCreate(BaseModel):
    sections: DutySections = DutySections()
    items: List[BatchItemCreate] = Field(..., min_items=1, description="List of MAWBs to process (each with broker_id/format_id)")


class BatchItemResponse(BaseModel):
    id: UUID
    batch_id: UUID
    mawb: str
    airport_code: Optional[str] = None
    customer: Optional[str] = None
    checkbook_hawbs: Optional[str] = None
    broker_id: Optional[UUID] = None
    format_id: Optional[UUID] = None
    result_id: Optional[UUID] = None
    status: BatchItemStatusLiteral
    position: Optional[int] = None
    logs: Optional[List[str]] = None
    processing_time_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class BatchResponse(BaseModel):
    id: UUID
    batch_name: str
    sections: Dict[str, bool]
    status: BatchStatusLiteral
    initiated_by: Optional[str] = None
    estimated_time_seconds: Optional[int] = None
    actual_time_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: Optional[List[BatchItemResponse]] = None  # Optional, loaded separately


class BatchStatusResponse(BaseModel):
    batch: BatchResponse
    item_count: int
    pending_count: int
    running_count: int
    success_count: int
    failed_count: int
    cancelled_count: int
    items: List[BatchItemResponse]


class BatchLogsResponse(BaseModel):
    batch_id: UUID
    logs: List[Dict[str, Any]]  # List of {item_id, mawb, logs: []}


class BatchResultsResponse(BaseModel):
    batch_id: UUID
    results: List[Dict[str, Any]]  # List of result objects with all fields


