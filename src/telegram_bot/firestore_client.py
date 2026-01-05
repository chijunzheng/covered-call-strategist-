"""Firestore client for user authentication and conversation history."""

import os
from datetime import datetime, timezone
from typing import Optional
from google.cloud import firestore


class FirestoreClient:
    """Client for Firestore database operations."""

    def __init__(self):
        """Initialize Firestore client."""
        self.db = firestore.Client()
        self.users_collection = "allowed_users"
        self.conversations_collection = "conversations"

    def is_user_allowed(self, phone_number: str) -> bool:
        """Check if a phone number is in the allowlist.

        Args:
            phone_number: The user's phone number (with country code).

        Returns:
            True if the user is allowed, False otherwise.
        """
        doc_ref = self.db.collection(self.users_collection).document(phone_number)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("active", False)
        return False

    def is_telegram_user_allowed(self, telegram_id: int) -> bool:
        """Check if a Telegram user ID is in the allowlist.

        Args:
            telegram_id: The user's Telegram ID.

        Returns:
            True if the user is allowed, False otherwise.
        """
        query = (
            self.db.collection(self.users_collection)
            .where("telegram_id", "==", telegram_id)
            .where("active", "==", True)
            .limit(1)
        )
        results = list(query.stream())
        return len(results) > 0

    def add_allowed_user(
        self,
        phone_number: str,
        telegram_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> bool:
        """Add a user to the allowlist.

        Args:
            phone_number: The user's phone number (with country code).
            telegram_id: Optional Telegram user ID.
            name: Optional user name for reference.

        Returns:
            True if added successfully.
        """
        doc_ref = self.db.collection(self.users_collection).document(phone_number)
        doc_ref.set({
            "phone_number": phone_number,
            "telegram_id": telegram_id,
            "name": name,
            "active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
        return True

    def link_telegram_id(self, phone_number: str, telegram_id: int) -> bool:
        """Link a Telegram ID to an existing phone number.

        Args:
            phone_number: The user's phone number.
            telegram_id: The Telegram user ID to link.

        Returns:
            True if linked successfully, False if phone not found.
        """
        doc_ref = self.db.collection(self.users_collection).document(phone_number)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({
                "telegram_id": telegram_id,
                "updated_at": datetime.now(timezone.utc),
            })
            return True
        return False

    def get_conversation_history(
        self,
        user_id: str,
        platform: str = "telegram",
        limit: int = 20,
    ) -> list:
        """Get conversation history for a user.

        Args:
            user_id: The user's platform-specific ID.
            platform: The platform (telegram, whatsapp).
            limit: Maximum number of messages to return.

        Returns:
            List of conversation messages, oldest first.
        """
        doc_id = f"{platform}_{user_id}"
        doc_ref = self.db.collection(self.conversations_collection).document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            messages = data.get("messages", [])
            # Return last N messages
            return messages[-limit:]
        return []

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        platform: str = "telegram",
        max_history: int = 50,
    ) -> bool:
        """Add a message to conversation history.

        Args:
            user_id: The user's platform-specific ID.
            role: Message role (user or assistant).
            content: Message content.
            platform: The platform (telegram, whatsapp).
            max_history: Maximum messages to retain.

        Returns:
            True if added successfully.
        """
        doc_id = f"{platform}_{user_id}"
        doc_ref = self.db.collection(self.conversations_collection).document(doc_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            messages = data.get("messages", [])
            messages.append(message)
            # Trim to max_history
            if len(messages) > max_history:
                messages = messages[-max_history:]
            doc_ref.update({
                "messages": messages,
                "updated_at": datetime.now(timezone.utc),
            })
        else:
            doc_ref.set({
                "user_id": user_id,
                "platform": platform,
                "messages": [message],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
        return True

    def clear_conversation(self, user_id: str, platform: str = "telegram") -> bool:
        """Clear conversation history for a user.

        Args:
            user_id: The user's platform-specific ID.
            platform: The platform (telegram, whatsapp).

        Returns:
            True if cleared successfully.
        """
        doc_id = f"{platform}_{user_id}"
        doc_ref = self.db.collection(self.conversations_collection).document(doc_id)
        doc_ref.delete()
        return True
