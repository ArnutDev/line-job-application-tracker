import asyncio
from datetime import datetime
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings
from app.schemas.llm_tools import GEMINI_TOOLS

logger = logging.getLogger(__name__)


def _build_system_instruction() -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    return (
        f"คุณคือผู้ช่วยจัดการข้อมูลการสมัครงานอัจฉริยะ 'JobTrack' ประจำ LINE Bot\n"
        f"วันนี้คือวันที่: {today_str}\n\n"
        f"หน้าที่ของคุณคือเข้าใจความต้องการของผู้ใช้และเลือกเรียกใช้ Tool ที่ถูกต้อง:\n"
        f"1. เมื่อผู้ใช้บอกว่าสมัครงาน ยื่นใบสมัคร หรือเพิ่มงานใหม่ ให้เรียก Tool `create_job_application`\n"
        f"   - ต้องมีชื่อบริษัท (company) และตำแหน่ง (position) เสมอ\n"
        f"   - ถ้าขาดชื่อตำแหน่ง หรือชื่อบริษัท ให้ตอบเป็นข้อความถามผู้ใช้กลับไปอย่างสุภาพ อย่าเดาเอง\n"
        f"   - ถ้าผู้ใช้ระบุว่า 'วันนี้' หรือ 'เมื่อวาน' ให้คำนวณเป็นวันที่ YYYY-MM-DD\n"
        f"2. เมื่อผู้ใช้ต้องการค้นหา ดูงานทั้งหมด สรุปผล หรือถามว่าสมัครอะไรไปบ้าง ให้เรียก Tool `query_job_applications`\n"
        f"3. เมื่อผู้ใช้ต้องการอัปเดตสถานะ เช่น 'KBank นัดสัมภาษณ์แล้ว', 'ผ่านสัมภาษณ์ SCB แล้ว' ให้เรียก Tool `update_job_application`\n"
        f"4. เมื่อผู้ใช้ต้องการลบงาน เช่น 'ขอลบงาน Agoda' ให้เรียก Tool `delete_job_application`\n"
        f"5. ถ้าผู้ใช้พูดคุยทั่วไป ทักทาย หรือถามการใช้งาน ให้ตอบกลับด้วยภาษาไทยที่เป็นมิตร สุภาพ มี emoji เหมาะสม โดยไม่ต้องเรียก Tool\n"
        f"ห้ามกุข้อมูลขึ้นมาเองโดยเด็ดขาด"
    )


def _call_gemini_api_sync(user_message: str, api_key: str, model: str) -> dict:
    if not api_key:
        logger.warning("GEMINI_API_KEY is not configured.")
        return {
            "type": "text",
            "text": "ขออภัยครับ ขณะนี้ยังไม่ได้ตั้งค่า GEMINI_API_KEY ในระบบ",
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {
            "parts": [{"text": _build_system_instruction()}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
        "tools": GEMINI_TOOLS,
        "generationConfig": {
            "temperature": 0.1,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Gemini API HTTP Error {e.code}: {error_body}")
        return {
            "type": "text",
            "text": "ขออภัยครับ ระบบประมวลผลข้อความขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้ง",
        }
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {
            "type": "text",
            "text": "ขออภัยครับ เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่อีกครั้ง",
        }

    # Extract function call or text response
    candidates = result.get("candidates", [])
    if not candidates:
        return {
            "type": "text",
            "text": "ขออภัยครับ ไม่สามารถทำความเข้าใจข้อความได้ กรุณาลองระบุใหม่อีกครั้งครับ",
        }

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "functionCall" in part:
            call = part["functionCall"]
            return {
                "type": "function_call",
                "name": call.get("name"),
                "args": call.get("args", {}),
            }

        if "text" in part:
            return {
                "type": "text",
                "text": part["text"].strip(),
            }

    return {
        "type": "text",
        "text": "ขออภัยครับ ไม่สามารถประมวลผลคำตอบได้ กรุณาลองใหม่อีกครั้ง",
    }


async def parse_intent_with_gemini(user_message: str) -> dict:
    """Asynchronously calls Gemini to parse user natural language into structured intent."""
    return await asyncio.to_thread(
        _call_gemini_api_sync,
        user_message,
        settings.gemini_api_key,
        settings.gemini_model,
    )
