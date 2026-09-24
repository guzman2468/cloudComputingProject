"""Chat room and message API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from backend.api.routes.users import require_session
from backend.schemas.chat import AddRoomMemberRequest, ChatRoom, CreateMessageRequest, CreateRoomRequest, MessageResponse, UpdateRoomRequest
from backend.services.chat import ChatNotFound, ChatValidationError, add_room_member, create_message, create_room, leave_room, list_messages, list_user_rooms, rename_room, search_user_rooms

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/rooms", response_model=list[ChatRoom])
def get_rooms(email: str = Depends(require_session), db: Session = Depends(get_db)) -> list[ChatRoom]:
    return list_user_rooms(db, email)


@router.get("/rooms/search", response_model=list[ChatRoom])
def search_rooms(
    query: str = Query(min_length=1, max_length=80, alias="q"),
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> list[ChatRoom]:
    return search_user_rooms(db, query, email)


@router.post("/rooms", response_model=ChatRoom, status_code=status.HTTP_201_CREATED)
def add_room(
    room_request: CreateRoomRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        return create_room(db, room_request, email)
    except ChatValidationError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch("/rooms/{room_id}", response_model=ChatRoom)
def update_room_name(
    room_id: int,
    room_request: UpdateRoomRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        return rename_room(db, room_id, room_request.name, email)
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/rooms/{room_id}/members", response_model=ChatRoom)
def add_member_to_room(
    room_id: int,
    member_request: AddRoomMemberRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        return add_room_member(db, room_id, member_request.member_email, email)
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room or user not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/rooms/{room_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_chat_room(
    room_id: int,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> Response:
    try:
        leave_room(db, room_id, email)
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rooms/{room_id}/messages", response_model=list[MessageResponse])
def get_room_messages(
    room_id: int,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    try:
        return list_messages(db, room_id, email)
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error


@router.post("/rooms/{room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message(
    room_id: int,
    message_request: CreateMessageRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        return create_message(db, room_id, message_request.content, email)
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
