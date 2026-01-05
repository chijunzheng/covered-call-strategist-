"""Rate limiting for Telegram bot using Firestore."""

from datetime import datetime, timezone, timedelta
from google.cloud import firestore


class RateLimiter:
    """Token bucket rate limiter backed by Firestore."""

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
        db: firestore.Client = None,
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window.
            window_seconds: Time window in seconds.
            db: Optional Firestore client (creates new one if not provided).
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.db = db or firestore.Client()
        self.collection = "rate_limits"

    def is_allowed(self, user_id: str, platform: str = "telegram") -> tuple[bool, int]:
        """Check if a request is allowed under rate limit.

        Args:
            user_id: The user's platform-specific ID.
            platform: The platform (telegram, whatsapp).

        Returns:
            Tuple of (is_allowed, seconds_until_reset).
        """
        doc_id = f"{platform}_{user_id}"
        doc_ref = self.db.collection(self.collection).document(doc_id)

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        @firestore.transactional
        def update_in_transaction(transaction):
            doc = doc_ref.get(transaction=transaction)

            if doc.exists:
                data = doc.to_dict()
                requests = data.get("requests", [])

                # Filter out old requests outside the window
                requests = [
                    r for r in requests
                    if datetime.fromisoformat(r) > window_start
                ]

                if len(requests) >= self.max_requests:
                    # Rate limited - calculate reset time
                    oldest = datetime.fromisoformat(requests[0])
                    reset_time = oldest + timedelta(seconds=self.window_seconds)
                    seconds_until_reset = max(0, int((reset_time - now).total_seconds()))
                    return False, seconds_until_reset

                # Add new request
                requests.append(now.isoformat())
                transaction.update(doc_ref, {
                    "requests": requests,
                    "updated_at": now,
                })
                return True, 0
            else:
                # First request from this user
                transaction.set(doc_ref, {
                    "user_id": user_id,
                    "platform": platform,
                    "requests": [now.isoformat()],
                    "created_at": now,
                    "updated_at": now,
                })
                return True, 0

        transaction = self.db.transaction()
        return update_in_transaction(transaction)

    def get_remaining(self, user_id: str, platform: str = "telegram") -> int:
        """Get remaining requests for a user.

        Args:
            user_id: The user's platform-specific ID.
            platform: The platform (telegram, whatsapp).

        Returns:
            Number of remaining requests in current window.
        """
        doc_id = f"{platform}_{user_id}"
        doc_ref = self.db.collection(self.collection).document(doc_id)

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            requests = data.get("requests", [])
            # Count requests in current window
            valid_requests = [
                r for r in requests
                if datetime.fromisoformat(r) > window_start
            ]
            return max(0, self.max_requests - len(valid_requests))
        return self.max_requests
