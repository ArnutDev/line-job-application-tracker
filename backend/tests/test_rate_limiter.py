from datetime import date, timedelta
import json
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.api.webhook import line_webhook
from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.repositories import usage as usage_repo
from app.services import rate_limiter


def make_mock_request(payload: dict, headers: dict | None = None) -> Request:
    body_bytes = json.dumps(payload).encode("utf-8")
    header_list = [(b"content-type", b"application/json")]
    if headers:
        for k, v in headers.items():
            header_list.append((k.lower().encode("utf-8"), v.encode("utf-8")))

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/webhook",
        "headers": header_list,
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope, receive)


class TestUsageRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.user_a_id = uuid.uuid4()
        self.user_b_id = uuid.uuid4()
        self.session.add(User(id=self.user_a_id, line_user_id="U_user_a"))
        self.session.add(User(id=self.user_b_id, line_user_id="U_user_b"))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_get_or_create_daily_usage(self):
        today = date(2026, 10, 6)
        usage = usage_repo.get_or_create_daily_usage(self.session, self.user_a_id, today)
        self.assertIsNotNone(usage.id)
        self.assertEqual(usage.user_id, self.user_a_id)
        self.assertEqual(usage.usage_date, today)
        self.assertEqual(usage.message_count, 0)

        # Calling again should retrieve the same record
        usage2 = usage_repo.get_or_create_daily_usage(self.session, self.user_a_id, today)
        self.assertEqual(usage.id, usage2.id)

    def test_increment_daily_usage(self):
        today = date(2026, 10, 6)
        count1 = usage_repo.increment_daily_usage(self.session, self.user_a_id, today)
        self.assertEqual(count1, 1)

        count2 = usage_repo.increment_daily_usage(self.session, self.user_a_id, today)
        self.assertEqual(count2, 2)

        # Check User B isolation
        usage_b = usage_repo.get_daily_usage(self.session, self.user_b_id, today)
        self.assertIsNone(usage_b)

    def test_reset_daily_usage(self):
        today = date(2026, 10, 6)
        usage_repo.increment_daily_usage(self.session, self.user_a_id, today)
        usage_repo.increment_daily_usage(self.session, self.user_a_id, today)

        usage_repo.reset_daily_usage(self.session, self.user_a_id, today)
        usage = usage_repo.get_daily_usage(self.session, self.user_a_id, today)
        self.assertEqual(usage.message_count, 0)


class TestRateLimiterService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.user_id = uuid.uuid4()
        self.session.add(User(id=self.user_id, line_user_id="U_regular_user"))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_is_unlimited_user_config(self):
        with patch.object(settings, "admin_line_user_ids", "U_my_line_account, U_second_admin"):
            self.assertTrue(settings.is_unlimited_user("U_my_line_account"))
            self.assertTrue(settings.is_unlimited_user("U_second_admin"))
            self.assertFalse(settings.is_unlimited_user("U_other_user"))
            self.assertFalse(settings.is_unlimited_user(""))

    def test_is_quota_inquiry(self):
        self.assertTrue(rate_limiter.is_quota_inquiry("เช็คโควต้า"))
        self.assertTrue(rate_limiter.is_quota_inquiry("ดูโควต้า"))
        self.assertTrue(rate_limiter.is_quota_inquiry("quota"))
        self.assertTrue(rate_limiter.is_quota_inquiry("Quota"))
        self.assertFalse(rate_limiter.is_quota_inquiry("สมัครงาน KBank"))

    def test_regular_user_consume_quota_up_to_limit(self):
        with patch.object(settings, "daily_message_limit", 3), \
             patch.object(settings, "admin_line_user_ids", ""):
            # 1st message
            allowed, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
            self.assertTrue(allowed)
            self.assertIsNone(msg)

            # 2nd message
            allowed, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
            self.assertTrue(allowed)
            self.assertIsNone(msg)

            # 3rd message
            allowed, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
            self.assertTrue(allowed)
            self.assertIsNone(msg)

            # 4th message -> Exceeded
            allowed, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
            self.assertFalse(allowed)
            self.assertIsNotNone(msg)
            self.assertIn("ครบโควต้า 3 ข้อความสำหรับวันนี้แล้ว", msg)

    def test_unlimited_user_consume_quota_bypasses_limit(self):
        with patch.object(settings, "daily_message_limit", 2), \
             patch.object(settings, "admin_line_user_ids", "U_admin_boss"):
            for _ in range(15):
                allowed, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_admin_boss")
                self.assertTrue(allowed)
                self.assertIsNone(msg)

    def test_quota_resets_on_new_date(self):
        today = date(2026, 10, 6)
        tomorrow = today + timedelta(days=1)

        with patch.object(settings, "daily_message_limit", 1), \
             patch.object(settings, "admin_line_user_ids", ""):
            # Day 1: consume limit
            with patch("app.services.rate_limiter.get_current_usage_date", return_value=today):
                allowed, _ = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
                self.assertTrue(allowed)
                allowed_again, msg = rate_limiter.consume_quota(self.session, self.user_id, "U_regular_user")
                self.assertFalse(allowed_again)

            # Day 2: fresh quota available
            with patch("app.services.rate_limiter.get_current_usage_date", return_value=tomorrow):
                allowed_tomorrow, msg_tomorrow = rate_limiter.consume_quota(
                    self.session, self.user_id, "U_regular_user"
                )
                self.assertTrue(allowed_tomorrow)
                self.assertIsNone(msg_tomorrow)

    def test_format_quota_status(self):
        # Regular user status
        reg_info = {
            "is_unlimited": False,
            "used": 4,
            "limit": 10,
            "remaining": 6,
        }
        reg_text = rate_limiter.format_quota_status(reg_info)
        self.assertIn("4/10 ข้อความ", reg_text)
        self.assertIn("คงเหลือ: 6 ข้อความ", reg_text)

        # Unlimited user status
        unlim_info = {
            "is_unlimited": True,
            "used": 15,
        }
        unlim_text = rate_limiter.format_quota_status(unlim_info)
        self.assertIn("👑 สิทธิ์การใช้งานของคุณ: ไม่จำกัด (Unlimited)", unlim_text)
        self.assertIn("15 ข้อความ", unlim_text)


class TestWebhookRateLimitIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._orig_channel_secret = settings.line_channel_secret
        settings.line_channel_secret = ""

    async def asyncTearDown(self):
        settings.line_channel_secret = self._orig_channel_secret
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    @patch("app.services.line_messaging.reply_text_message", new_callable=AsyncMock)
    @patch("app.services.intent_dispatcher.dispatch_user_message", new_callable=AsyncMock)
    async def test_webhook_blocks_after_daily_limit_and_saves_llm_call(
        self, mock_dispatch, mock_reply
    ):
        mock_dispatch.return_value = {"type": "text", "text": "บันทึกเรียบร้อย"}

        line_id = "U_limited_user"
        limit = 2

        with patch.object(settings, "daily_message_limit", limit), \
             patch.object(settings, "admin_line_user_ids", ""):
            # Send message 1 -> Allowed
            req1 = make_mock_request({
                "events": [{
                    "type": "message",
                    "replyToken": "token_1",
                    "source": {"userId": line_id},
                    "message": {"type": "text", "text": "สมัครงาน KBank"},
                }]
            })
            await line_webhook(request=req1, x_line_signature=None, db=self.session)
            self.assertEqual(mock_dispatch.call_count, 1)

            # Send message 2 -> Allowed
            req2 = make_mock_request({
                "events": [{
                    "type": "message",
                    "replyToken": "token_2",
                    "source": {"userId": line_id},
                    "message": {"type": "text", "text": "สมัครงาน SCB"},
                }]
            })
            await line_webhook(request=req2, x_line_signature=None, db=self.session)
            self.assertEqual(mock_dispatch.call_count, 2)

            # Send message 3 -> Exceeded! Should reply with quota message and NOT call dispatch
            req3 = make_mock_request({
                "events": [{
                    "type": "message",
                    "replyToken": "token_3",
                    "source": {"userId": line_id},
                    "message": {"type": "text", "text": "สมัครงาน Agoda"},
                }]
            })
            await line_webhook(request=req3, x_line_signature=None, db=self.session)

            # LLM dispatch count should remain 2 (not called for 3rd message)
            self.assertEqual(mock_dispatch.call_count, 2)

            # LINE reply was called for the quota error message
            last_reply_call = mock_reply.call_args_list[-1]
            self.assertIn("ครบโควต้า 2 ข้อความสำหรับวันนี้แล้ว", last_reply_call.kwargs["text"])

    @patch("app.services.line_messaging.reply_text_message", new_callable=AsyncMock)
    @patch("app.services.intent_dispatcher.dispatch_user_message", new_callable=AsyncMock)
    async def test_webhook_allows_unlimited_admin_user(
        self, mock_dispatch, mock_reply
    ):
        mock_dispatch.return_value = {"type": "text", "text": "บันทึกเรียบร้อย"}

        admin_line_id = "U_my_admin_account"
        limit = 2

        with patch.object(settings, "daily_message_limit", limit), \
             patch.object(settings, "admin_line_user_ids", admin_line_id):
            for i in range(5):
                req = make_mock_request({
                    "events": [{
                        "type": "message",
                        "replyToken": f"token_{i}",
                        "source": {"userId": admin_line_id},
                        "message": {"type": "text", "text": f"งานที่ {i}"},
                    }]
                })
                await line_webhook(request=req, x_line_signature=None, db=self.session)

            # All 5 messages were dispatched to LLM
            self.assertEqual(mock_dispatch.call_count, 5)

    @patch("app.services.line_messaging.reply_text_message", new_callable=AsyncMock)
    @patch("app.services.intent_dispatcher.dispatch_user_message", new_callable=AsyncMock)
    async def test_webhook_quota_inquiry_does_not_consume_quota(
        self, mock_dispatch, mock_reply
    ):
        line_id = "U_user_checking_quota"

        with patch.object(settings, "daily_message_limit", 10), \
             patch.object(settings, "admin_line_user_ids", ""):
            req = make_mock_request({
                "events": [{
                    "type": "message",
                    "replyToken": "token_check",
                    "source": {"userId": line_id},
                    "message": {"type": "text", "text": "เช็คโควต้า"},
                }]
            })
            await line_webhook(request=req, x_line_signature=None, db=self.session)

            # LLM was not called
            self.assertEqual(mock_dispatch.call_count, 0)

            # Reply was sent
            self.assertEqual(mock_reply.call_count, 1)
            reply_text = mock_reply.call_args.kwargs["text"]
            self.assertIn("0/10 ข้อความ", reply_text)
            self.assertIn("คงเหลือ: 10 ข้อความ", reply_text)


if __name__ == "__main__":
    unittest.main()
