"""
Gmail Inbox Zero Agent Schemas

Pydantic schemas for Gmail Inbox Zero management agent
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class GmailMessage(BaseModel):
    """Model for Gmail message data"""

    message_id: str = Field(..., description="Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    subject: str = Field(..., description="Email subject")
    sender: EmailStr = Field(..., description="Sender email address")
    sender_name: str | None = Field(None, description="Sender display name")
    recipients: list[EmailStr] = Field(
        default=[], description="Recipient email addresses"
    )
    body_plain: str | None = Field(None, description="Plain text body")
    body_html: str | None = Field(None, description="HTML body")
    date: datetime = Field(..., description="Message date")
    labels: list[str] = Field(default=[], description="Current Gmail labels")
    is_read: bool = Field(default=False, description="Is message read")
    is_starred: bool = Field(default=False, description="Is message starred")
    has_attachments: bool = Field(default=False, description="Has attachments")
    snippet: str | None = Field(None, description="Message snippet")
    size: int | None = Field(None, description="Message size in bytes")


class GmailLabel(BaseModel):
    """Model for Gmail label"""

    id: str = Field(..., description="Label ID")
    name: str = Field(..., description="Label name")
    type: Literal["system", "user"] = Field(..., description="Label type")
    message_list_visibility: str | None = Field(
        None, description="Message list visibility"
    )
    label_list_visibility: str | None = Field(None, description="Label list visibility")
    messages_total: int | None = Field(
        None, description="Total messages with this label"
    )
    messages_unread: int | None = Field(
        None, description="Unread messages with this label"
    )
    threads_total: int | None = Field(None, description="Total threads with this label")
    threads_unread: int | None = Field(
        None, description="Unread threads with this label"
    )


class InboxZeroRequest(BaseModel):
    """Request model for Inbox Zero operations"""

    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    operation: Literal[
        "analyze", "label", "archive", "delete", "mark_read", "star", "learn",
        "analyze_all_unread", "auto_archive", "apply_smart_labels", "mark_important",
        "batch_process", "batch_archive", "batch_delete", "batch_modify"
    ] = Field(..., description="Operation to perform")
    message_id: str | None = Field(None, description="Gmail message ID")
    message_ids: list[str] | None = Field(None, description="List of Gmail message IDs for batch operations")
    thread_id: str | None = Field(None, description="Gmail thread ID")
    labels: list[str] | None = Field(None, description="Labels to apply")
    add_labels: list[str] | None = Field(None, description="Labels to add")
    remove_labels: list[str] | None = Field(None, description="Labels to remove")
    mark_as_read: bool | None = Field(None, description="Mark messages as read")
    mark_as_unread: bool | None = Field(None, description="Mark messages as unread")
    user_feedback: str | None = Field(None, description="User feedback/comment")
    learning_data: dict[str, Any] | None = Field(
        None, description="Learning data for training"
    )
    email_data: dict[str, Any] | None = Field(
        None, description="Email data for analysis (when Gmail API is not available)"
    )


class InboxZeroResponse(BaseModel):
    """Response model for Inbox Zero operations"""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Response data")
    error: str | None = Field(None, description="Error message")
    suggestions: list[str] | None = Field(None, description="Suggested actions")
    learning_progress: dict[str, Any] | None = Field(
        None, description="Learning progress data"
    )


class GmailAnalysisRequest(BaseModel):
    """Request model for Gmail analysis"""

    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    analysis_type: Literal["inbox", "labels", "patterns", "suggestions"] = Field(
        ..., description="Type of analysis to perform"
    )
    time_range: str | None = Field(None, description="Time range for analysis")
    max_messages: int | None = Field(100, description="Maximum messages to analyze")


class GmailAnalysisResponse(BaseModel):
    """Response model for Gmail analysis"""

    success: bool = Field(..., description="Analysis success status")
    analysis_type: str = Field(..., description="Type of analysis performed")
    data: dict[str, Any] = Field(..., description="Analysis results")
    insights: list[str] = Field(default=[], description="Key insights")
    recommendations: list[str] = Field(default=[], description="Recommendations")
    stats: dict[str, Any] = Field(default={}, description="Statistics")


class LearningData(BaseModel):
    """Model for learning data from user interactions"""

    user_id: str = Field(..., description="User ID")
    message_id: str = Field(..., description="Gmail message ID")
    user_action: str = Field(..., description="Action taken by user")
    applied_labels: list[str] = Field(default=[], description="Labels applied by user")
    user_comment: str | None = Field(None, description="User comment/feedback")
    message_features: dict[str, Any] = Field(
        default={}, description="Message features for ML"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Learning timestamp"
    )


class InboxZeroStats(BaseModel):
    """Model for Inbox Zero statistics"""

    total_messages: int = Field(..., description="Total messages in inbox")
    unread_messages: int = Field(..., description="Unread messages")
    labeled_messages: int = Field(..., description="Messages with user labels")
    archived_messages: int = Field(..., description="Archived messages")
    deleted_messages: int = Field(..., description="Deleted messages")
    inbox_zero_percentage: float = Field(..., description="Inbox Zero percentage")
    learning_accuracy: float | None = Field(None, description="ML model accuracy")
    last_analysis: datetime | None = Field(None, description="Last analysis timestamp")
