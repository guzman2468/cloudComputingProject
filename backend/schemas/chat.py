"""Request and response schemas for chat rooms and messages."""

from datetime import datetime

from pydantic import BaseModel, Field


class RoomMember(BaseModel):
    email: str
    first_name: str
    last_name: str


class LastMessage(BaseModel):
    content: str
    created_at: datetime
    sender_email: str


class ChatRoom(BaseModel):
    id: int
    name: str
    created_by_email: str
    created_at: datetime
    members: list[RoomMember]
    last_message: LastMessage | None = None


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


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
