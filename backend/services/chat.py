"""Database operations for chat rooms, room membership, and messages."""

import re

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from backend.schemas.chat import CreateRoomRequest

SYSTEM_MESSAGE_PREFIX = "__MAVCHAT_SYSTEM__ "


class ChatNotFound(Exception):
    """Raised when a user cannot access a requested room."""


class ChatValidationError(Exception):
    """Raised when a room or message request cannot be fulfilled."""


def _message_payload(content: str) -> tuple[str, bool]:
    if content.startswith(SYSTEM_MESSAGE_PREFIX):
        return content[len(SYSTEM_MESSAGE_PREFIX):], True
    return content, False


def _get_user(db: Session, email: str) -> dict[str, int | str] | None:
    row = db.execute(
        text("SELECT id, email, first_name, last_name FROM public.users WHERE email = :email"),
        {"email": email},
    ).mappings().one_or_none()
    return dict(row) if row else None


def _get_room_members(db: Session, room_id: int) -> list[dict[str, str]]:
    rows = db.execute(
        text(
            """
            SELECT u.email, u.first_name, u.last_name
            FROM public.room_members rm
            JOIN public.users u ON u.id = rm.user_id
            WHERE rm.room_id = :room_id
            ORDER BY u.first_name, u.last_name, u.email
            """
        ),
        {"room_id": room_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def get_room_member_emails(db: Session, room_id: int) -> list[str]:
    rows = db.execute(
        text(
            """
            SELECT u.email
            FROM public.room_members rm
            JOIN public.users u ON u.id = rm.user_id
            WHERE rm.room_id = :room_id
            """
        ),
        {"room_id": room_id},
    ).scalars().all()
    return list(rows)


def _assert_room_member(db: Session, room_id: int, user_id: int) -> None:
    member = db.execute(
        text(
            """
            SELECT 1
            FROM public.room_members
            WHERE room_id = :room_id AND user_id = :user_id
            """
        ),
        {"room_id": room_id, "user_id": user_id},
    ).first()
    if not member:
        raise ChatNotFound


def _removed_room_access(db: Session, room_id: int, user_id: int) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT removed_at
            FROM public.chat_room_member_history
            WHERE room_id = :room_id AND user_id = :user_id
            """
        ),
        {"room_id": room_id, "user_id": user_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


def _assert_room_access(db: Session, room_id: int, user_id: int) -> dict | None:
    try:
        _assert_room_member(db, room_id, user_id)
        return None
    except ChatNotFound:
        removed_access = _removed_room_access(db, room_id, user_id)
        if not removed_access:
            raise
        return removed_access


def list_user_rooms(db: Session, email: str) -> list[dict]:
    user = _get_user(db, email)
    if not user:
        return []

    rows = db.execute(
        text(
            """
            SELECT
                cr.id,
                cr.name,
                cr.created_at,
                creator.email AS created_by_email,
                current_member.user_id AS current_member_user_id,
                latest.content AS last_content,
                latest.created_at AS last_created_at,
                latest.sender_email AS last_sender_email
            FROM public.chat_rooms cr
            LEFT JOIN public.room_members current_member
              ON current_member.room_id = cr.id
             AND current_member.user_id = :user_id
            LEFT JOIN public.chat_room_member_history removed_member
              ON removed_member.room_id = cr.id
             AND removed_member.user_id = :user_id
            LEFT JOIN public.chat_room_hidden hidden_chat
              ON hidden_chat.room_id = cr.id
             AND hidden_chat.user_id = :user_id
            JOIN public.users creator ON creator.id = cr.created_by
            LEFT JOIN LATERAL (
                SELECT m.content, m.created_at, sender.email AS sender_email
                FROM public.messages m
                JOIN public.users sender ON sender.id = m.sender_id
                WHERE m.room_id = cr.id
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) latest ON TRUE
            WHERE hidden_chat.user_id IS NULL
              AND (current_member.user_id IS NOT NULL OR removed_member.user_id IS NOT NULL)
            ORDER BY COALESCE(latest.created_at, cr.created_at) DESC, cr.id DESC
            """
        ),
        {"user_id": user["id"]},
    ).mappings().all()

    rooms = []
    for row in rows:
        room = {
            "id": row["id"],
            "name": row["name"],
            "created_by_email": row["created_by_email"],
            "created_at": row["created_at"],
            "members": _get_room_members(db, row["id"]),
            "is_removed": row["current_member_user_id"] is None,
            "last_message": None,
        }
        if row["last_content"] is not None:
            last_content, is_system = _message_payload(row["last_content"])
            room["last_message"] = {
                "content": last_content,
                "created_at": row["last_created_at"],
                "sender_email": row["last_sender_email"],
                "is_system": is_system,
            }
        rooms.append(room)
    return rooms


def search_user_rooms(db: Session, query: str, email: str) -> list[dict]:
    """Find accessible rooms by room names or member names/usernames."""
    user = _get_user(db, email)
    if not user:
        return []
    normalized_query = query.strip()
    if not normalized_query:
        return list_user_rooms(db, email)

    # Match the beginning of a word so a search for "ma" does not match "Sam".
    search_pattern = rf"(^|[^[:alnum:]]){re.escape(normalized_query)}"
    matching_rows = db.execute(
        text(
            """
            SELECT DISTINCT cr.id
            FROM public.chat_rooms cr
            LEFT JOIN public.room_members current_member
              ON current_member.room_id = cr.id
             AND current_member.user_id = :user_id
            LEFT JOIN public.chat_room_member_history removed_member
              ON removed_member.room_id = cr.id
             AND removed_member.user_id = :user_id
            LEFT JOIN public.chat_room_hidden hidden_chat
              ON hidden_chat.room_id = cr.id
             AND hidden_chat.user_id = :user_id
            LEFT JOIN public.room_members searched_member ON searched_member.room_id = cr.id
            LEFT JOIN public.users member_user ON member_user.id = searched_member.user_id
            WHERE hidden_chat.user_id IS NULL
              AND (current_member.user_id IS NOT NULL OR removed_member.user_id IS NOT NULL)
              AND (cr.name ~* :search_pattern
               OR member_user.first_name ~* :search_pattern
               OR member_user.last_name ~* :search_pattern
               OR split_part(member_user.email, '@', 1) ~* :search_pattern)
            """
        ),
        {"user_id": user["id"], "search_pattern": search_pattern},
    ).mappings().all()
    matching_ids = {row["id"] for row in matching_rows}
    return [room for room in list_user_rooms(db, email) if room["id"] in matching_ids]


def create_room(db: Session, request: CreateRoomRequest, current_email: str) -> dict:
    current_user = _get_user(db, current_email)
    if not current_user:
        raise ChatValidationError("Current user does not exist")

    requested_emails = {email.strip().lower() for email in request.member_emails if email.strip()}
    requested_emails.add(current_email.lower())
    if len(requested_emails) < 2:
        raise ChatValidationError("A chat room needs at least two users")

    users_query = text(
        """
        SELECT id, email, first_name, last_name
        FROM public.users
        WHERE email IN :emails
        ORDER BY first_name, last_name, email
        """
    ).bindparams(bindparam("emails", expanding=True))
    users = [dict(row) for row in db.execute(users_query, {"emails": list(requested_emails)}).mappings().all()]
    found_emails = {user["email"].lower() for user in users}
    if found_emails != requested_emails:
        raise ChatValidationError("One or more selected users could not be found")

    room_name = request.name.strip() if request.name and request.name.strip() else ", ".join(
        f"{user['first_name']} {user['last_name']}" for user in users
    )
    room_row = db.execute(
        text(
            """
            INSERT INTO public.chat_rooms (name, created_by)
            VALUES (:name, :created_by)
            RETURNING id, name, created_at
            """
        ),
        {"name": room_name[:120], "created_by": current_user["id"]},
    ).mappings().one()

    for user in users:
        db.execute(
            text(
                """
                INSERT INTO public.room_members (room_id, user_id)
                VALUES (:room_id, :user_id)
                """
            ),
            {"room_id": room_row["id"], "user_id": user["id"]},
        )
    db.commit()

    return {
        "id": room_row["id"],
        "name": room_row["name"],
        "created_by_email": current_user["email"],
        "created_at": room_row["created_at"],
        "members": [
            {"email": user["email"], "first_name": user["first_name"], "last_name": user["last_name"]}
            for user in users
        ],
        "last_message": None,
    }


def rename_room(db: Session, room_id: int, name: str, email: str) -> dict:
    user = _get_user(db, email)
    if not user:
        raise ChatNotFound
    _assert_room_member(db, room_id, user["id"])
    normalized_name = name.strip()
    if not normalized_name:
        raise ChatValidationError("Chat room name cannot be empty")

    db.execute(
        text(
            """
            UPDATE public.chat_rooms
            SET name = :name
            WHERE id = :room_id
            """
        ),
        {"name": normalized_name, "room_id": room_id},
    )
    db.commit()
    room = next((room for room in list_user_rooms(db, email) if room["id"] == room_id), None)
    if not room:
        raise ChatNotFound
    return room


def add_room_member(db: Session, room_id: int, member_email: str, current_email: str) -> dict:
    current_user = _get_user(db, current_email)
    if not current_user:
        raise ChatNotFound
    _assert_room_member(db, room_id, current_user["id"])

    member = _get_user(db, member_email.strip().lower())
    if not member:
        raise ChatValidationError("User could not be found")
    if member["id"] != current_user["id"]:
        already_member = db.execute(
            text(
                """
                SELECT 1
                FROM public.room_members
                WHERE room_id = :room_id AND user_id = :user_id
                """
            ),
            {"room_id": room_id, "user_id": member["id"]},
        ).first()
        if not already_member:
            db.execute(
                text(
                    """
                    DELETE FROM public.chat_room_member_history
                    WHERE room_id = :room_id AND user_id = :user_id
                    """
                ),
                {"room_id": room_id, "user_id": member["id"]},
            )
            db.execute(
                text(
                    """
                    DELETE FROM public.chat_room_hidden
                    WHERE room_id = :room_id AND user_id = :user_id
                    """
                ),
                {"room_id": room_id, "user_id": member["id"]},
            )
            db.execute(
                text(
                    """
                    INSERT INTO public.room_members (room_id, user_id)
                    VALUES (:room_id, :user_id)
                    """
                ),
                {"room_id": room_id, "user_id": member["id"]},
            )
            db.execute(
                text(
                    """
                    INSERT INTO public.messages (room_id, sender_id, content)
                    VALUES (:room_id, :sender_id, :content)
                    """
                ),
                {
                    "room_id": room_id,
                    "sender_id": current_user["id"],
                    "content": f"{SYSTEM_MESSAGE_PREFIX}{member['first_name']} {member['last_name']} has been added to the chat",
                },
            )
            db.commit()

    room = next((room for room in list_user_rooms(db, current_email) if room["id"] == room_id), None)
    if not room:
        raise ChatNotFound
    return room


def remove_room_member(db: Session, room_id: int, member_email: str, current_email: str) -> dict:
    creator = _get_user(db, current_email)
    target = _get_user(db, member_email.strip().lower())
    if not creator or not target:
        raise ChatNotFound
    _assert_room_member(db, room_id, creator["id"])

    room_owner = db.execute(
        text("SELECT created_by FROM public.chat_rooms WHERE id = :room_id"),
        {"room_id": room_id},
    ).scalar_one_or_none()
    if room_owner != creator["id"] or target["id"] == creator["id"]:
        raise ChatValidationError("Only the room creator can remove other members")

    target_is_member = db.execute(
        text("SELECT 1 FROM public.room_members WHERE room_id = :room_id AND user_id = :user_id"),
        {"room_id": room_id, "user_id": target["id"]},
    ).first()
    if not target_is_member:
        raise ChatNotFound

    member_emails = get_room_member_emails(db, room_id)
    system_message = db.execute(
        text(
            """
            INSERT INTO public.messages (room_id, sender_id, content)
            VALUES (:room_id, :sender_id, :content)
            RETURNING created_at
            """
        ),
        {
            "room_id": room_id,
            "sender_id": creator["id"],
            "content": f"{SYSTEM_MESSAGE_PREFIX}{target['first_name']} {target['last_name']} has been removed from the chat",
        },
    ).mappings().one()
    db.execute(
        text(
            """
            INSERT INTO public.chat_room_member_history (room_id, user_id, removed_at)
            VALUES (:room_id, :user_id, :removed_at)
            ON CONFLICT (room_id, user_id) DO UPDATE SET removed_at = EXCLUDED.removed_at
            """
        ),
        {"room_id": room_id, "user_id": target["id"], "removed_at": system_message["created_at"]},
    )
    db.execute(
        text("DELETE FROM public.room_members WHERE room_id = :room_id AND user_id = :user_id"),
        {"room_id": room_id, "user_id": target["id"]},
    )
    db.commit()
    return {
        "member_emails": member_emails,
        "removed_email": target["email"],
        "removed_name": f"{target['first_name']} {target['last_name']}",
    }


def hide_room_for_user(db: Session, room_id: int, email: str) -> None:
    user = _get_user(db, email)
    if not user:
        raise ChatNotFound
    _assert_room_access(db, room_id, user["id"])
    db.execute(
        text(
            """
            INSERT INTO public.chat_room_hidden (room_id, user_id)
            VALUES (:room_id, :user_id)
            ON CONFLICT (room_id, user_id) DO NOTHING
            """
        ),
        {"room_id": room_id, "user_id": user["id"]},
    )
    db.commit()


def leave_room(db: Session, room_id: int, email: str) -> list[str]:
    user = _get_user(db, email)
    if not user:
        raise ChatNotFound
    _assert_room_member(db, room_id, user["id"])
    room_member_emails = get_room_member_emails(db, room_id)
    db.execute(
        text(
            """
            INSERT INTO public.messages (room_id, sender_id, content)
            VALUES (:room_id, :sender_id, :content)
            """
        ),
        {
            "room_id": room_id,
            "sender_id": user["id"],
            "content": f"{SYSTEM_MESSAGE_PREFIX}{user['first_name']} {user['last_name']} has left the chat",
        },
    )
    db.execute(
        text(
            """
            DELETE FROM public.room_members
            WHERE room_id = :room_id AND user_id = :user_id
            """
        ),
        {"room_id": room_id, "user_id": user["id"]},
    )
    db.commit()
    return room_member_emails


def list_messages(db: Session, room_id: int, email: str) -> list[dict]:
    user = _get_user(db, email)
    if not user:
        raise ChatNotFound
    _assert_room_access(db, room_id, user["id"])
    rows = db.execute(
        text(
            """
            SELECT
                m.id,
                m.room_id,
                sender.email AS sender_email,
                CONCAT(sender.first_name, ' ', sender.last_name) AS sender_name,
                m.content,
                m.created_at
            FROM public.messages m
            JOIN public.users sender ON sender.id = m.sender_id
            WHERE m.room_id = :room_id
            ORDER BY m.created_at ASC, m.id ASC
            """
        ),
        {"room_id": room_id},
    ).mappings().all()
    messages = []
    for row in rows:
        message = dict(row)
        message["content"], message["is_system"] = _message_payload(message["content"])
        messages.append(message)
    return messages


def create_message(db: Session, room_id: int, content: str, email: str) -> dict:
    user = _get_user(db, email)
    if not user:
        raise ChatNotFound
    _assert_room_member(db, room_id, user["id"])
    normalized_content = content.strip()
    if not normalized_content:
        raise ChatValidationError("Message content cannot be empty")

    row = db.execute(
        text(
            """
            INSERT INTO public.messages (room_id, sender_id, content)
            VALUES (:room_id, :sender_id, :content)
            RETURNING id, room_id, created_at
            """
        ),
        {"room_id": room_id, "sender_id": user["id"], "content": normalized_content},
    ).mappings().one()
    db.commit()
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "sender_email": user["email"],
        "sender_name": f"{user['first_name']} {user['last_name']}",
        "content": normalized_content,
        "created_at": row["created_at"],
    }
