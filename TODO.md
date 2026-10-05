# 📌 JobTrack — แผนงานที่ต้องทำต่อไป (TODO)

## 1. 🚀 Deploy ระบบขึ้น Cloud (Production 24/7)
- [ ] เลือกใช้แพลตฟอร์ม Cloud (แนะนำ: **Railway.app** หรือ **Render.com**)
- [ ] สร้าง Managed PostgreSQL Database บน Cloud
- [ ] ตั้งค่า Environment Variables บน Cloud (`DATABASE_URL`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `GROQ_API_KEY`, `GROQ_MODEL`)
- [ ] สั่งรันด้วย `backend/Dockerfile` พร้อมรัน Migration อัตโนมัติ
- [ ] นำ HTTPS Domain ที่ได้จาก Cloud ไปอัปเดต Webhook URL ใน LINE Developers Console แทน ngrok

---

## 2. 🛡️ ระบบจำกัดการสนทนา (Rate Limit: 10 ข้อความ / วัน / ผู้ใช้)
- [ ] ออกแบบโมเดลตาราง `user_daily_usage` (คอลัมน์: `user_id`, `usage_date`, `message_count`)
- [ ] สร้าง Alembic Migration สำหรับตาราง `user_daily_usage`
- [ ] ทำ Service ตรวจสอบโควต้าใน `backend/app/services/rate_limiter.py`
- [ ] ดักเช็คใน Webhook ก่อนส่งข้อความเข้า LLM:
  - หากครบ 10 ข้อความแล้ว: ตอบแจ้งเตือนอย่างสุภาพและหยุด ไม่เรียก LLM (ช่วยประหยัดโควต้า 100%)
  - หากยังไม่ครบ: เพิ่มยอด `message_count += 1` และประมวลผลต่อตามปกติ
- [ ] เพิ่ม Unit Test ตรวจสอบเงื่อนไขโควต้าและการรีเซ็ตรายวัน

---

## 3. 📊 ปรับปรุง LLM Intent "สรุปสถิติ" ให้หลากหลายและไม่ซ้ำกับ "รายการสมัคร"
- [ ] **แยก Tool / Intent ให้ชัดเจน**:
  - `query_job_applications`: ใช้สำหรับดูรายการงานจริงแบบละเอียด (แสดงชื่อบริษัท, ตำแหน่ง, วันที่สมัคร, สถานะ, เงินเดือน)
  - `get_application_summary`: ใช้สำหรับดูสถิติภาพรวม Metrics & Funnel ไม่ใช่แค่แสดงรายชื่อบริษัท
- [ ] **ปรับปรุง System Prompt ใน `groq_service.py`**:
  - เมื่อผู้ใช้ถามแนว *"สรุปสถิติ"*, *"ภาพรวม"*, *"dashboard"*, *"สถิติการสมัคร"* ให้เรียก `get_application_summary`
  - เมื่อผู้ใช้ถามแนว *"ขอดูรายการงาน"*, *"สมัครอะไรไปบ้าง"*, *"งานทั้งหมด"* ให้เรียก `query_job_applications`
- [ ] **ออกแบบข้อความสรุปสถิติให้สวยงามและมีมิติ**:
  - สรุปตัวเลขรวมทั้งหมด (Total Applications)
  - สรุปแจกแจงตามแต่ละสถานะพร้อม Emoji:
    - 📝 สมัครแล้ว: X งาน
    - ⏳ กำลังคัดกรอง: X งาน
    - 📅 นัดสัมภาษณ์ / สัมภาษณ์แล้ว: X งาน
    - 🎉 ผ่านการคัดเลือก: X งาน
    - ❌ ปฏิเสธแล้ว / เงียบ: X งาน
  - คำนวณ Conversion Rate (เช่น สัดส่วนที่ได้เรียกสัมภาษณ์กี่ %)
- [ ] เพิ่ม Unit Tests ตรวจสอบการแยก Intent ทั้งสองแบบ
