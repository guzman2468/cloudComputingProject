"""Request and response schemas for chat rooms and messages."""

from datetime import datetime

from pydantic import BaseModel, Field


class RoomMember(BaseModel):
    email: str
    first_name: str
    last_name: str


class AttachmentResponse(BaseModel):
    filename: str
    content_type: str
    size: int | None = None
    url: str
    download_url: str


class LastMessage(BaseModel):
    content: str
    created_at: datetime
    sender_email: str
    is_system: bool = False
    attachment: AttachmentResponse | None = None


class ChatRoom(BaseModel):
    id: int
    name: str | None = None
    created_by_email: str
    created_at: datetime
    members: list[RoomMember]
    last_message: LastMessage | None = None
    is_removed: bool = False


class CreateRoomRequest(BaseModel):
    member_emails: list[str] = Field(min_length=1, max_length=50)
    name: str | None = Field(default=None, max_length=120)


class UpdateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AddRoomMemberRequest(BaseModel):
    member_email: str = Field(min_length=3, max_length=120)


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_email: str
    sender_name: str
    content: str
    created_at: datetime
    is_system: bool = False
    attachment: AttachmentResponse | None = None


class AttachmentInput(BaseModel):
    object_key: str = Field(min_length=1, max_length=300)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size: int = Field(gt=0, le=25 * 1024 * 1024)


class CreateMessageRequest(BaseModel):
    content: str = Field(default="", max_length=5000)
    attachment: AttachmentInput | None = None
