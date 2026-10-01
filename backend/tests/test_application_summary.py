import unittest
import uuid
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.job_application import ApplicationStatus, WorkMode
from app.models.user import User
from app.repositories import job_application as repo


class TestApplicationSummary(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Seed users
        self.user_a_id = uuid.uuid4()
        self.user_b_id = uuid.uuid4()

        self.session.add(User(id=self.user_a_id, line_user_id="line_user_a"))
        self.session.add(User(id=self.user_b_id, line_user_id="line_user_b"))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_normalize_work_mode(self):
        self.assertEqual(repo.normalize_work_mode("onsite"), WorkMode.ON_SITE)
        self.assertEqual(repo.normalize_work_mode("on-site"), WorkMode.ON_SITE)
        self.assertEqual(repo.normalize_work_mode("hybrid"), WorkMode.HYBRID)
        self.assertEqual(repo.normalize_work_mode("remote"), WorkMode.REMOTE)
        self.assertEqual(repo.normalize_work_mode("unknown"), WorkMode.UNKNOWN)
        self.assertIsNone(repo.normalize_work_mode(None))
        self.assertIsNone(repo.normalize_work_mode("invalid_mode"))

    def test_normalize_status(self):
        self.assertEqual(repo.normalize_status("สมัครแล้ว"), ApplicationStatus.APPLIED)
        self.assertEqual(repo.normalize_status("applied"), ApplicationStatus.APPLIED)
        self.assertEqual(repo.normalize_status("สัมภาษณ์แล้ว"), ApplicationStatus.INTERVIEWED)
        self.assertEqual(repo.normalize_status("interviewed"), ApplicationStatus.INTERVIEWED)
        self.assertIsNone(repo.normalize_status(None))
        self.assertIsNone(repo.normalize_status("non_existent_status"))

    def test_summary_empty_database(self):
        summary = repo.get_application_summary(self.session, self.user_a_id)
        self.assertEqual(summary["total"], 0)
        self.assertEqual(len(summary["applications"]), 0)
        self.assertEqual(len(summary["by_status"]), 8)
        for count in summary["by_status"].values():
            self.assertEqual(count, 0)

    def test_summary_counts_and_user_isolation(self):
        # User A applications
        repo.create_application(self.session, self.user_a_id, {
            "company": "KBank",
            "position": "Backend Developer",
            "status": ApplicationStatus.APPLIED,
            "work_mode": WorkMode.HYBRID,
            "date_applied": date(2026, 10, 1),
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "SCB",
            "position": "Frontend Developer",
            "status": ApplicationStatus.INTERVIEWED,
            "work_mode": WorkMode.REMOTE,
            "date_applied": date(2026, 9, 20),
        })

        # User B application
        repo.create_application(self.session, self.user_b_id, {
            "company": "Agoda",
            "position": "Full Stack Engineer",
            "status": ApplicationStatus.ACCEPTED,
            "work_mode": WorkMode.ON_SITE,
            "date_applied": date(2026, 9, 10),
        })

        # Test User A
        summary_a = repo.get_application_summary(self.session, self.user_a_id)
        self.assertEqual(summary_a["total"], 2)
        self.assertEqual(summary_a["by_status"]["สมัครแล้ว"], 1)
        self.assertEqual(summary_a["by_status"]["สัมภาษณ์แล้ว"], 1)
        self.assertEqual(summary_a["by_status"]["ผ่านการคัดเลือก"], 0)
        self.assertEqual(len(summary_a["applications"]), 2)

        # Test User B
        summary_b = repo.get_application_summary(self.session, self.user_b_id)
        self.assertEqual(summary_b["total"], 1)
        self.assertEqual(summary_b["by_status"]["ผ่านการคัดเลือก"], 1)
        self.assertEqual(summary_b["by_status"]["สมัครแล้ว"], 0)
        self.assertEqual(len(summary_b["applications"]), 1)

    def test_summary_filters(self):
        repo.create_application(self.session, self.user_a_id, {
            "company": "Kasikorn Bank (KBank)",
            "position": "Senior Backend Developer",
            "status": ApplicationStatus.APPLIED,
            "work_mode": WorkMode.HYBRID,
            "date_applied": date(2026, 10, 1),
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "SCB TechX",
            "position": "Backend Developer",
            "status": ApplicationStatus.INTERVIEWED,
            "work_mode": WorkMode.REMOTE,
            "date_applied": date(2026, 9, 15),
        })
        repo.create_application(self.session, self.user_a_id, {
            "company": "LINE Man Wongnai",
            "position": "Mobile Developer",
            "status": ApplicationStatus.APPLIED,
            "work_mode": WorkMode.ON_SITE,
            "date_applied": date(2026, 8, 1),
        })

        # 1. Filter by company (partial & case-insensitive)
        summary_kbank = repo.get_application_summary(self.session, self.user_a_id, company="kbank")
        self.assertEqual(summary_kbank["total"], 1)
        self.assertEqual(summary_kbank["applications"][0].company, "Kasikorn Bank (KBank)")

        # 2. Filter by position
        summary_backend = repo.get_application_summary(self.session, self.user_a_id, position="backend")
        self.assertEqual(summary_backend["total"], 2)

        # 3. Filter by work_mode
        summary_remote = repo.get_application_summary(self.session, self.user_a_id, work_mode="remote")
        self.assertEqual(summary_remote["total"], 1)
        self.assertEqual(summary_remote["applications"][0].company, "SCB TechX")

        # 4. Filter by status
        summary_status = repo.get_application_summary(self.session, self.user_a_id, status="สมัครแล้ว")
        self.assertEqual(summary_status["total"], 2)

        # 5. Filter by date range
        summary_date = repo.get_application_summary(
            self.session,
            self.user_a_id,
            date_from=date(2026, 9, 1),
            date_to=date(2026, 9, 30),
        )
        self.assertEqual(summary_date["total"], 1)
        self.assertEqual(summary_date["applications"][0].company, "SCB TechX")


if __name__ == "__main__":
    unittest.main()
