"""Chat room and message API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.database import get_db
from backend.api.routes.users import require_session
from backend.schemas.chat import AddRoomMemberRequest, ChatRoom, CreateMessageRequest, CreateRoomRequest, MessageResponse, UpdateRoomRequest
from backend.services.chat import ChatNotFound, ChatValidationError, add_room_member, create_message, create_room, get_room_member_emails, hide_room_for_user, leave_room, list_messages, list_user_rooms, remove_room_member, rename_room, search_user_rooms
from backend.services.chat_socket import chat_connection_manager
from backend.core.security import SESSION_COOKIE, get_session_email

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.websocket("/socket")
async def chat_socket(websocket: WebSocket):
    email = get_session_email(websocket.cookies.get(SESSION_COOKIE))
    if not email:
        await websocket.close(code=1008)
        return

    await chat_connection_manager.connect(email, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        chat_connection_manager.disconnect(email, websocket)


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
async def add_room(
    room_request: CreateRoomRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        room = create_room(db, room_request, email)
        await chat_connection_manager.broadcast(
            [member["email"] for member in room["members"]],
            {"type": "room.created", "room_id": room["id"]},
        )
        return room
    except ChatValidationError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch("/rooms/{room_id}", response_model=ChatRoom)
async def update_room_name(
    room_id: int,
    room_request: UpdateRoomRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        room = rename_room(db, room_id, room_request.name, email)
        # Broadcast after the database commit so listeners can immediately load the new name.
        await chat_connection_manager.broadcast(
            [member["email"] for member in room["members"]],
            {"type": "room.renamed", "room_id": room_id},
        )
        return room
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/rooms/{room_id}/members", response_model=ChatRoom)
async def add_member_to_room(
    room_id: int,
    member_request: AddRoomMemberRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> ChatRoom:
    try:
        room = add_room_member(db, room_id, member_request.member_email, email)
        await chat_connection_manager.broadcast(
            [member["email"] for member in room["members"]],
            {
                "type": "room.member_changed",
                "change": "added",
                "room_id": room_id,
                "member_email": member_request.member_email.strip().lower(),
            },
        )
        return room
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room or user not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/rooms/{room_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_chat_room(
    room_id: int,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> Response:
    try:
        member_emails = leave_room(db, room_id, email)
        await chat_connection_manager.broadcast(
            member_emails,
            {
                "type": "room.member_changed",
                "change": "left",
                "room_id": room_id,
                "member_email": email,
            },
        )
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/rooms/{room_id}/members/{member_email}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_chat_room_member(
    room_id: int,
    member_email: str,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> Response:
    try:
        removal = remove_room_member(db, room_id, member_email, email)
        await chat_connection_manager.broadcast(
            removal["member_emails"],
            {
                "type": "room.member_changed",
                "change": "removed",
                "room_id": room_id,
                "member_email": removal["removed_email"],
                "member_name": removal["removed_name"],
            },
        )
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room or member not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/rooms/{room_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
def hide_chat_room(
    room_id: int,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> Response:
    try:
        hide_room_for_user(db, room_id, email)
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
async def add_message(
    room_id: int,
    message_request: CreateMessageRequest,
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        message = create_message(db, room_id, message_request.content, email)
        member_emails = get_room_member_emails(db, room_id)
        await chat_connection_manager.broadcast(
            member_emails,
            {"type": "message.created", "room_id": room_id},
        )
        return message
    except ChatNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found") from error
    except ChatValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
