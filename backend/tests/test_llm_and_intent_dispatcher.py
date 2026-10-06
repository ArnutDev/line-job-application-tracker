import json
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.job_application import ApplicationStatus, WorkMode
from app.models.user import User
from app.repositories import job_application as repo
from app.services import groq_service, intent_dispatcher


class TestIntentDispatcher(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Seed two users for isolation testing
        self.user_a_id = uuid.uuid4()
        self.user_b_id = uuid.uuid4()
        self.session.add(User(id=self.user_a_id, line_user_id="line_user_a"))
        self.session.add(User(id=self.user_b_id, line_user_id="line_user_b"))
        self.session.commit()

    async def asyncTearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_create_application(self, mock_parse):
        mock_parse.return_value = {
            "type": "function_call",
            "name": "create_job_application",
            "args": {
                "company": "KBank",
                "position": "Backend Developer",
                "salary": "45,000",
                "work_mode": "hybrid",
                "status": "สมัครแล้ว",
                "date_applied": "2026-10-01",
            },
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="สมัครงาน KBank ตำแหน่ง Backend Developer เงินเดือน 45000",
        )

        response_text = result["text"]
        self.assertIn("บันทึกการสมัครงานสำเร็จ", response_text)
        self.assertIn("KBank", response_text)
        self.assertIn("Backend Developer", response_text)
        self.assertIn("45,000", response_text)

        # Verify persisted in database for user_a
        apps = repo.get_applications(self.session, self.user_a_id)
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].company, "KBank")
        self.assertEqual(apps[0].salary, "45,000")
        self.assertEqual(apps[0].work_mode, WorkMode.HYBRID)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_query_applications(self, mock_parse):
        # Pre-populate applications
        repo.create_application(self.session, self.user_a_id, {
            "company": "SCB",
            "position": "Data Engineer",
            "status": ApplicationStatus.INTERVIEWED,
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "Agoda",
            "position": "Software Engineer",
            "status": ApplicationStatus.APPLIED,
        })

        mock_parse.return_value = {
            "type": "function_call",
            "name": "query_job_applications",
            "args": {},
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="สรุปงานทั้งหมดที่สมัครหน่อย",
        )

        response_text = result["text"]
        self.assertIn("พบทั้งหมด 2 รายการ", response_text)
        self.assertIn("SCB", response_text)
        self.assertIn("Agoda", response_text)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_application_summary(self, mock_parse):
        repo.create_application(self.session, self.user_a_id, {
            "company": "SCB",
            "position": "Data Engineer",
            "status": ApplicationStatus.INTERVIEWED,
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "Agoda",
            "position": "Software Engineer",
            "status": ApplicationStatus.APPLIED,
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "KBank",
            "position": "Backend Developer",
            "status": ApplicationStatus.ACCEPTED,
        })

        mock_parse.return_value = {
            "type": "function_call",
            "name": "get_application_summary",
            "args": {},
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="สรุปสถิติการสมัครงานหน่อย",
        )

        response_text = result["text"]
        self.assertIn("สถิติภาพรวมการสมัครงานของคุณ", response_text)
        self.assertIn("ยื่นใบสมัครทั้งหมด: 3 งาน", response_text)
        self.assertIn("📨 สมัครแล้ว: 1 งาน", response_text)
        self.assertIn("💬 สัมภาษณ์แล้ว: 1 งาน", response_text)
        self.assertIn("🎉 ผ่านการคัดเลือก: 1 งาน", response_text)
        self.assertIn("อัตราก้าวหน้า (สัมภาษณ์/ผ่าน): 66.7%", response_text)
        self.assertIn("พิมพ์ 'ดูรายการสมัคร' เพื่อดูรายละเอียดรายชื่อบริษัท", response_text)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_application_summary_empty(self, mock_parse):
        mock_parse.return_value = {
            "type": "function_call",
            "name": "get_application_summary",
            "args": {},
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="สรุปสถิติหน่อย",
        )

        response_text = result["text"]
        self.assertIn("ยังไม่มีข้อมูลการสมัครงานในระบบครับ", response_text)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_update_application(self, mock_parse):
        app = repo.create_application(self.session, self.user_a_id, {
            "company": "LINE Man",
            "position": "Android Developer",
            "status": ApplicationStatus.APPLIED,
        })

        mock_parse.return_value = {
            "type": "function_call",
            "name": "update_job_application",
            "args": {
                "company": "LINE Man",
                "status": "ผ่านการคัดเลือก",
            },
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="ผ่านคัดเลือก LINE Man แล้วครับ",
        )

        response_text = result["text"]
        self.assertIn("อัปเดตข้อมูลเรียบร้อย", response_text)
        self.assertIn("ผ่านการคัดเลือก", response_text)

        # Verify DB updated
        updated_app = repo.get_application(self.session, self.user_a_id, app.id)
        self.assertEqual(updated_app.status, ApplicationStatus.ACCEPTED)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_delete_application(self, mock_parse):
        repo.create_application(self.session, self.user_a_id, {
            "company": "OldCompany",
            "position": "Intern",
            "status": ApplicationStatus.NOT_APPLIED,
        })

        mock_parse.return_value = {
            "type": "function_call",
            "name": "delete_job_application",
            "args": {
                "company": "OldCompany",
            },
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="ลบงาน OldCompany ให้หน่อย",
        )

        response_text = result["text"]
        self.assertIn("ลบข้อมูลการสมัครงานบริษัท 'OldCompany'", response_text)

        # Verify deleted
        apps = repo.get_applications(self.session, self.user_a_id)
        self.assertEqual(len(apps), 0)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_dispatch_general_text_conversation(self, mock_parse):
        greeting = "สวัสดีครับ! ผมคือ JobTrack ผู้ช่วยบันทึกการสมัครงานของคุณ มีอะไรให้ผมช่วยไหมครับ"
        mock_parse.return_value = {
            "type": "text",
            "text": greeting,
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="สวัสดีครับ บอททำอะไรได้บ้าง",
        )

        self.assertEqual(result["text"], greeting)

    @patch("app.services.groq_service.parse_intent_with_groq")
    async def test_user_isolation_prevent_cross_user_update(self, mock_parse):
        # User B created an application
        repo.create_application(self.session, self.user_b_id, {
            "company": "PrivateCorp",
            "position": "CEO",
            "status": ApplicationStatus.APPLIED,
        })

        # User A attempts to update or delete PrivateCorp
        mock_parse.return_value = {
            "type": "function_call",
            "name": "delete_job_application",
            "args": {
                "company": "PrivateCorp",
            },
        }

        result = await intent_dispatcher.dispatch_user_message(
            db=self.session,
            user_id=self.user_a_id,
            user_message="ลบงาน PrivateCorp ให้หน่อย",
        )

        response_text = result["text"]
        self.assertIn("ไม่พบรายการสมัครงานที่บริษัท 'PrivateCorp'", response_text)


        # Verify User B's application was NOT deleted
        apps_b = repo.get_applications(self.session, self.user_b_id)
        self.assertEqual(len(apps_b), 1)


class TestGroqService(unittest.TestCase):
    def test_missing_api_key(self):
        res = groq_service._call_groq_api_sync("test message", api_key="", model="openai/gpt-oss-20b")
        self.assertEqual(res["type"], "text")
        self.assertIn("ยังไม่ได้ตั้งค่า GROQ_API_KEY", res["text"])

    @patch("urllib.request.urlopen")
    def test_tool_call_parsing(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "create_job_application",
                                    "arguments": json.dumps({"company": "Agoda", "position": "Senior Dev"}),
                                },
                            }
                        ],
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = groq_service._call_groq_api_sync("สมัคร Agoda ตำแหน่ง Senior Dev", api_key="test_key", model="openai/gpt-oss-20b")
        self.assertEqual(res["type"], "function_call")
        self.assertEqual(res["name"], "create_job_application")
        self.assertEqual(res["args"]["company"], "Agoda")
        self.assertEqual(res["args"]["position"], "Senior Dev")

    @patch("urllib.request.urlopen")
    def test_text_response_parsing(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "สวัสดีครับ มีอะไรให้ผมช่วยไหมครับ",
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = groq_service._call_groq_api_sync("สวัสดีครับ", api_key="test_key", model="openai/gpt-oss-20b")
        self.assertEqual(res["type"], "text")
        self.assertIn("สวัสดีครับ", res["text"])


if __name__ == "__main__":
    unittest.main()
