from datetime import date
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.models.job_application import ApplicationStatus
from app.repositories import job_application as repo
from app.services import export_service, groq_service

logger = logging.getLogger(__name__)



def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        return None


def _handle_create(db: Session, user_id: UUID, args: dict) -> str:
    company = args.get("company", "").strip()
    position = args.get("position", "").strip()

    if not company or not position:
        return "⚠️ กรุณาระบุชื่อบริษัทและตำแหน่งงานให้ชัดเจนเพื่อบันทึกข้อมูลครับ"

    status = repo.normalize_status(args.get("status")) or ApplicationStatus.APPLIED
    work_mode = repo.normalize_work_mode(args.get("work_mode"))
    date_applied = _parse_date(args.get("date_applied"))

    data = {
        "company": company,
        "position": position,
        "status": status,
        "work_mode": work_mode,
        "salary": args.get("salary"),
        "location": args.get("location"),
        "source": args.get("source"),
        "job_url": args.get("job_url"),
        "note": args.get("note"),
        "date_applied": date_applied,
    }

    application = repo.create_application(db=db, user_id=user_id, data=data)

    salary_text = f"\n💵 เงินเดือน: {application.salary}" if application.salary else ""
    work_mode_text = (
        f"\n🏢 รูปแบบ: {application.work_mode.value}" if application.work_mode else ""
    )
    note_text = f"\n📝 โน้ต: {application.note}" if application.note else ""

    return (
        f"✅ บันทึกการสมัครงานสำเร็จ!\n"
        f"🏢 บริษัท: {application.company}\n"
        f"💼 ตำแหน่ง: {application.position}\n"
        f"📌 สถานะ: {application.status.value}\n"
        f"📅 วันที่สมัคร: {application.date_applied}"
        f"{salary_text}"
        f"{work_mode_text}"
        f"{note_text}"
    )


def _handle_query(db: Session, user_id: UUID, args: dict) -> str:
    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))

    summary = repo.get_application_summary(
        db=db,
        user_id=user_id,
        status=args.get("status"),
        company=args.get("company"),
        position=args.get("position"),
        work_mode=args.get("work_mode"),
        date_from=date_from,
        date_to=date_to,
    )

    total = summary["total"]
    if total == 0:
        return "📋 ไม่พบข้อมูลการสมัครงานตามเงื่อนไขที่ระบุครับ"

    applications = summary["applications"]
    lines = [f"📊 สรุปข้อมูลการสมัครงาน (พบทั้งหมด {total} รายการ):"]

    for idx, app in enumerate(applications[:10], 1):
        status_val = app.status.value if hasattr(app.status, "value") else str(app.status)
        date_val = str(app.date_applied) if app.date_applied else "-"
        lines.append(f"{idx}. {app.company} — {app.position}")
        lines.append(f"   สถานะ: {status_val} | วันที่: {date_val}")

    if total > 10:
        lines.append(f"...และอีก {total - 10} รายการ")

    return "\n".join(lines)


def _handle_update(db: Session, user_id: UUID, args: dict) -> str:
    company = args.get("company", "").strip()
    if not company:
        return "⚠️ กรุณาระบุชื่อบริษัทที่ต้องการอัปเดตครับ"

    position = args.get("position")
    matching_apps = repo.get_applications(
        db=db,
        user_id=user_id,
        company=company,
        position=position,
    )

    if not matching_apps:
        return f"❌ ไม่พบรายการสมัครงานที่บริษัท '{company}' ในระบบครับ"

    # Pick the most recent matching application
    target_app = matching_apps[0]
    update_data = {}

    if args.get("status"):
        new_status = repo.normalize_status(args.get("status"))
        if new_status:
            update_data["status"] = new_status

    if args.get("salary"):
        update_data["salary"] = args.get("salary")

    if args.get("note"):
        update_data["note"] = args.get("note")

    if args.get("work_mode"):
        new_mode = repo.normalize_work_mode(args.get("work_mode"))
        if new_mode:
            update_data["work_mode"] = new_mode

    if not update_data:
        return f"⚠️ ไม่พบข้อมูลที่ต้องการแก้ไขสำหรับบริษัท '{target_app.company}' ครับ"

    updated = repo.update_application(db=db, application=target_app, data=update_data)
    status_val = updated.status.value if hasattr(updated.status, "value") else str(updated.status)

    return (
        f"✨ อัปเดตข้อมูลเรียบร้อยครับ!\n"
        f"🏢 บริษัท: {updated.company}\n"
        f"💼 ตำแหน่ง: {updated.position}\n"
        f"📌 สถานะ: {status_val}"
    )


def _handle_delete(db: Session, user_id: UUID, args: dict) -> str:
    company = args.get("company", "").strip()
    if not company:
        return "⚠️ กรุณาระบุชื่อบริษัทที่ต้องการลบครับ"

    position = args.get("position")
    matching_apps = repo.get_applications(
        db=db,
        user_id=user_id,
        company=company,
        position=position,
    )

    if not matching_apps:
        return f"❌ ไม่พบรายการสมัครงานที่บริษัท '{company}' ที่ต้องการลบครับ"

    target_app = matching_apps[0]
    comp_name = target_app.company
    pos_name = target_app.position

    repo.delete_application(db=db, application=target_app)
    return f"🗑️ ลบข้อมูลการสมัครงานบริษัท '{comp_name}' ({pos_name}) เรียบร้อยแล้วครับ"


def _handle_export(db: Session, user_id: UUID, args: dict, base_url: str | None = None) -> dict:
    applications = repo.get_applications(
        db=db,
        user_id=user_id,
        status=args.get("status"),
        company=args.get("company"),
        position=args.get("position"),
    )

    count = len(applications)
    if count == 0:
        return {
            "type": "text",
            "text": "📋 ไม่พบข้อมูลการสมัครงานตามเงื่อนไขที่ระบุสำหรับส่งออกเป็นไฟล์ Excel ครับ",
        }

    # Generate Excel in-memory to get exact byte length
    file_stream = export_service.export_applications_to_xlsx(applications)
    file_size = len(file_stream.getvalue())

    secret = settings.line_channel_secret or "jobtrack-secret"
    token = security.create_export_token(user_id, secret)

    base = base_url.rstrip("/") if base_url else "http://localhost:8000"
    download_url = f"{base}/applications/export?token={token}"

    return {
        "type": "file",
        "title": "job_applications.xlsx",
        "file_size": file_size,
        "download_url": download_url,
        "text": f"📊 รวบรวมข้อมูลการสมัครงานทั้งหมด {count} รายการ เรียบร้อยแล้วครับ กดดาวน์โหลดไฟล์ Excel ได้ที่ปุ่มด้านล่างครับ 👇",
    }


async def dispatch_user_message(
    db: Session,
    user_id: UUID,
    user_message: str,
    base_url: str | None = None,
) -> dict:
    """Takes user natural language message, parses intent with Groq (gpt-oss-20b),
    executes authorized application operations, and returns a structured response dict.
    """
    intent_result = await groq_service.parse_intent_with_groq(user_message)

    if intent_result.get("type") == "text":
        return {
            "type": "text",
            "text": intent_result.get("text", ""),
        }

    if intent_result.get("type") == "function_call":
        func_name = intent_result.get("name")
        args = intent_result.get("args", {})
        logger.info(f"Executing intent function '{func_name}' for user {user_id}")

        if func_name == "create_job_application":
            return {"type": "text", "text": _handle_create(db, user_id, args)}
        elif func_name == "query_job_applications":
            return {"type": "text", "text": _handle_query(db, user_id, args)}
        elif func_name == "update_job_application":
            return {"type": "text", "text": _handle_update(db, user_id, args)}
        elif func_name == "delete_job_application":
            return {"type": "text", "text": _handle_delete(db, user_id, args)}
        elif func_name == "export_applications":
            return _handle_export(db, user_id, args, base_url=base_url)
        else:
            logger.warning(f"Unsupported function call '{func_name}'")
            return {"type": "text", "text": "ขออภัยครับ ระบบยังไม่รองรับคำสั่งนี้ในขณะนี้"}

    return {"type": "text", "text": "ขออภัยครับ ไม่สามารถประมวลผลข้อความได้ในขณะนี้"}


