import base64
import hashlib
import hmac
import json
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.api.webhook import line_webhook, verify_line_signature
from app.core.database import Base
from app.models.user import User
from app.repositories import user as user_repo
from app.services import user_resolver


class TestUserRepositoryAndResolver(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # --- Repository Tests ---

    def test_create_and_get_user(self):
        line_id = "U_test_12345"
        user = user_repo.create_user(self.session, line_id)

        self.assertIsNotNone(user.id)
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.line_user_id, line_id)

        found_by_line = user_repo.get_user_by_line_id(self.session, line_id)
        self.assertIsNotNone(found_by_line)
        self.assertEqual(found_by_line.id, user.id)

        found_by_id = user_repo.get_user_by_id(self.session, user.id)
        self.assertIsNotNone(found_by_id)
        self.assertEqual(found_by_id.line_user_id, line_id)

    def test_get_or_create_user(self):
        line_id = "U_test_duplicate_check"

        # First call: creates user
        user1 = user_repo.get_or_create_user(self.session, line_id)
        self.assertIsNotNone(user1.id)

        # Second call: returns existing user
        user2 = user_repo.get_or_create_user(self.session, line_id)
        self.assertEqual(user1.id, user2.id)

    # --- Service / User Resolver Tests ---

    def test_resolve_line_user_new(self):
        line_id = "U_new_incoming_line_user"
        user = user_resolver.resolve_line_user(self.session, line_id)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.line_user_id, line_id)

    def test_resolve_line_user_existing(self):
        line_id = "U_existing_line_user"
        user1 = user_resolver.resolve_line_user(self.session, line_id)
        user2 = user_resolver.resolve_line_user(self.session, line_id)

        self.assertEqual(user1.id, user2.id)

    def test_resolve_line_user_invalid_input(self):
        with self.assertRaises(ValueError):
            user_resolver.resolve_line_user(self.session, "")

        with self.assertRaises(ValueError):
            user_resolver.resolve_line_user(self.session, "   ")

        with self.assertRaises(ValueError):
            user_resolver.resolve_line_user(self.session, None)

    def test_resolve_line_user_id_helper(self):
        line_id = "U_helper_test"
        resolved_id = user_resolver.resolve_line_user_id(self.session, line_id)

        self.assertIsInstance(resolved_id, uuid.UUID)


class TestLineWebhook(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.secret = "test_channel_secret_abc123"

    async def asyncTearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()


    def _generate_signature(self, body: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def test_signature_verification_valid(self):
        body = b'{"events":[]}'
        signature = self._generate_signature(body, self.secret)
        self.assertTrue(verify_line_signature(body, signature, self.secret))

    def test_signature_verification_invalid(self):
        body = b'{"events":[]}'
        signature = self._generate_signature(body, self.secret)
        self.assertFalse(verify_line_signature(body, "invalid_sig", self.secret))
        self.assertFalse(verify_line_signature(body + b"tampered", signature, self.secret))
        self.assertFalse(verify_line_signature(body, None, self.secret))
        self.assertFalse(verify_line_signature(body, signature, ""))

    async def test_webhook_successful_event_resolves_user(self):
        line_user_id = "U_webhook_event_user_1"
        payload = {
            "destination": "U_bot_dest",
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "12345",
                        "text": "สมัครงาน KBank ตำแหน่ง Backend",
                    },
                    "timestamp": 1727764800,
                    "source": {
                        "type": "user",
                        "userId": line_user_id,
                    },
                    "replyToken": "dummy_reply_token_abc",
                }
            ],
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        signature = self._generate_signature(body_bytes, self.secret)

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=body_bytes)

        with patch("app.api.webhook.settings.line_channel_secret", self.secret), \
             patch("app.api.webhook.line_messaging.reply_text_message", new_callable=AsyncMock) as mock_reply:
            response = await line_webhook(
                request=mock_request,
                x_line_signature=signature,
                db=self.session,
            )

        self.assertEqual(response, {"status": "ok"})
        mock_reply.assert_called_once()


        # Verify user was automatically created and resolved in the database
        user = user_repo.get_user_by_line_id(self.session, line_user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.line_user_id, line_user_id)

    async def test_webhook_invalid_signature_raises_400(self):
        body_bytes = b'{"events":[]}'
        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=body_bytes)

        with patch("app.api.webhook.settings.line_channel_secret", self.secret):
            with self.assertRaises(HTTPException) as ctx:
                await line_webhook(
                    request=mock_request,
                    x_line_signature="wrong_signature",
                    db=self.session,
                )
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertEqual(ctx.exception.detail, "Invalid LINE signature")

    @patch("app.services.line_messaging.urllib.request.urlopen")
    async def test_reply_text_message_success(self, mock_urlopen):
        from app.services.line_messaging import reply_text_message

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch("app.services.line_messaging.settings.line_channel_access_token", "dummy_token"):
            result = await reply_text_message("test_reply_token", "Hello LINE!")
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

