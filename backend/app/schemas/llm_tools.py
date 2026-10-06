"""Standard OpenAI/Groq Tool Calling definitions for JobTrack."""

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_job_application",
            "description": "บันทึกข้อมูลการสมัครงานใหม่ลงในระบบ",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "ชื่อบริษัทที่สมัครงาน เช่น KBank, SCB, Google, LINE",
                    },
                    "position": {
                        "type": "string",
                        "description": "ชื่อตำแหน่งงาน เช่น Backend Developer, Data Engineer, UX/UI",
                    },
                    "salary": {
                        "type": ["string", "null"],
                        "description": "เงินเดือน เช่น 35,000 หรือ 40,000 - 50,000 บาท",
                    },
                    "date_applied": {
                        "type": ["string", "null"],
                        "description": "วันที่สมัครงานในรูปแบบ YYYY-MM-DD (ถ้าเป็น 'วันนี้' หรือ 'เมื่อวาน' ให้คำนวณเป็นวันที่จริง)",
                    },
                    "status": {
                        "type": ["string", "null"],
                        "description": "สถานะการสมัคร เช่น 'ยังไม่ได้สมัคร', 'สมัครแล้ว', 'กำลังคัดกรอง', 'นัดสัมภาษณ์', 'สัมภาษณ์แล้ว', 'ผ่านการคัดเลือก', 'ปฏิเสธแล้ว'",
                    },
                    "work_mode": {
                        "type": ["string", "null"],
                        "enum": ["onsite", "hybrid", "remote", "unknown", None],
                        "description": "รูปแบบการทำงาน",
                    },
                    "location": {
                        "type": ["string", "null"],
                        "description": "สถานที่ทำงาน เช่น สุขุมวิท, อารีย์, พระราม 9",
                    },
                    "source": {
                        "type": ["string", "null"],
                        "description": "แหล่งที่มาของงาน เช่น LinkedIn, JobsDB, JobThai",
                    },
                    "job_url": {
                        "type": ["string", "null"],
                        "description": "URL ลิงก์ประกาศรับสมัครงาน",
                    },
                    "note": {
                        "type": ["string", "null"],
                        "description": "บันทึกเพิ่มเติม เช่น เตรียม portfolio, สัมภาษณ์ภาษาอังกฤษ",
                    },
                },
                "required": ["company", "position"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_job_applications",
            "description": "ค้นหาและดูรายการการสมัครงาน แสดงรายละเอียดรายชื่อบริษัท ตำแหน่งงาน วันที่สมัคร และสถานะ",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["string", "null"],
                        "description": "กรองตามสถานะ เช่น สมัครแล้ว, นัดสัมภาษณ์, สัมภาษณ์แล้ว",
                    },
                    "company": {
                        "type": ["string", "null"],
                        "description": "กรองตามบริษัท",
                    },
                    "position": {
                        "type": ["string", "null"],
                        "description": "กรองตามตำแหน่ง",
                    },
                    "work_mode": {
                        "type": ["string", "null"],
                        "enum": ["onsite", "hybrid", "remote", "unknown", None],
                        "description": "กรองตามรูปแบบการทำงาน",
                    },
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "วันที่เริ่มต้น YYYY-MM-DD",
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "วันที่สิ้นสุด YYYY-MM-DD",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_application_summary",
            "description": "ดูสถิติภาพรวมและสรุปผลการสมัครงาน เช่น จำนวนงานทั้งหมดที่สมัคร แจกแจงจำนวนงานตามแต่ละสถานะ (กำลังคัดกรอง, นัดสัมภาษณ์, ผ่านการคัดเลือก, ฯลฯ) และอัตราก้าวหน้า",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "วันที่เริ่มต้น YYYY-MM-DD (ถ้าต้องการกรองสรุปตามช่วงเวลา)",
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "วันที่สิ้นสุด YYYY-MM-DD (ถ้าต้องการกรองสรุปตามช่วงเวลา)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_job_application",
            "description": "อัปเดตสถานะหรือข้อมูลการสมัครงาน เช่น เปลี่ยนสถานะเป็นสัมภาษณ์แล้ว หรือเพิ่มโน้ต",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "ชื่อบริษัทที่ต้องการอัปเดต",
                    },
                    "position": {
                        "type": ["string", "null"],
                        "description": "ชื่อตำแหน่ง (ถ้ามีหลายงานในบริษัทเดียวกัน)",
                    },
                    "status": {
                        "type": ["string", "null"],
                        "description": "สถานะใหม่ เช่น นัดสัมภาษณ์, สัมภาษณ์แล้ว, ผ่านการคัดเลือก, ปฏิเสธแล้ว",
                    },
                    "salary": {
                        "type": ["string", "null"],
                        "description": "เงินเดือนที่ต้องการแก้ไข",
                    },
                    "note": {
                        "type": ["string", "null"],
                        "description": "บันทึกเพิ่มเติมใหม่",
                    },
                    "work_mode": {
                        "type": ["string", "null"],
                        "enum": ["onsite", "hybrid", "remote", "unknown", None],
                        "description": "รูปแบบการทำงานใหม่",
                    },
                },
                "required": ["company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_job_application",
            "description": "ลบข้อมูลการสมัครงานออกจากระบบ",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "ชื่อบริษัทของงานที่ต้องการลบ",
                    },
                    "position": {
                        "type": ["string", "null"],
                        "description": "ชื่อตำแหน่งของงานที่ต้องการลบ (ถ้ามี)",
                    },
                },
                "required": ["company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_applications",
            "description": "ส่งออกข้อมูลการสมัครงานเป็นไฟล์ Excel (XLSX) เพื่อนำไปเปิดในโปรแกรม Spreadsheet",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["string", "null"],
                        "description": "กรองตามสถานะ (ถ้าต้องการ)",
                    },
                    "company": {
                        "type": ["string", "null"],
                        "description": "กรองตามบริษัท (ถ้าต้องการ)",
                    },
                    "position": {
                        "type": ["string", "null"],
                        "description": "กรองตามตำแหน่ง (ถ้าต้องการ)",
                    },
                },
            },
        },
    },
]
