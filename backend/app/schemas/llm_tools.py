GEMINI_TOOLS = [
    {
        "function_declarations": [
            {
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
                            "type": "string",
                            "description": "เงินเดือน เช่น 35,000 หรือ 40,000 - 50,000 บาท",
                        },
                        "date_applied": {
                            "type": "string",
                            "description": "วันที่สมัครงานในรูปแบบ YYYY-MM-DD (ถ้าเป็น 'วันนี้' หรือ 'เมื่อวาน' ให้คำนวณเป็นวันที่จริง)",
                        },
                        "status": {
                            "type": "string",
                            "description": "สถานะการสมัคร เช่น 'ยังไม่ได้สมัคร', 'สมัครแล้ว', 'กำลังคัดกรอง', 'นัดสัมภาษณ์', 'สัมภาษณ์แล้ว', 'ผ่านการคัดเลือก', 'ปฏิเสธแล้ว'",
                        },
                        "work_mode": {
                            "type": "string",
                            "enum": ["onsite", "hybrid", "remote", "unknown"],
                            "description": "รูปแบบการทำงาน",
                        },
                        "location": {
                            "type": "string",
                            "description": "สถานที่ทำงาน เช่น สุขุมวิท, อารีย์, พระราม 9",
                        },
                        "source": {
                            "type": "string",
                            "description": "แหล่งที่มาของงาน เช่น LinkedIn, JobsDB, JobThai",
                        },
                        "job_url": {
                            "type": "string",
                            "description": "URL ลิงก์ประกาศรับสมัครงาน",
                        },
                        "note": {
                            "type": "string",
                            "description": "บันทึกเพิ่มเติม เช่น เตรียม portfolio, สัมภาษณ์ภาษาอังกฤษ",
                        },
                    },
                    "required": ["company", "position"],
                },
            },
            {
                "name": "query_job_applications",
                "description": "ค้นหาและสรุปข้อมูลการสมัครงาน ดูรายการงานทั้งหมด หรือดูสรุปสถิติตามเงื่อนไข",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "กรองตามสถานะ เช่น สมัครแล้ว, นัดสัมภาษณ์, สัมภาษณ์แล้ว",
                        },
                        "company": {
                            "type": "string",
                            "description": "กรองตามบริษัท",
                        },
                        "position": {
                            "type": "string",
                            "description": "กรองตามตำแหน่ง",
                        },
                        "work_mode": {
                            "type": "string",
                            "enum": ["onsite", "hybrid", "remote", "unknown"],
                            "description": "กรองตามรูปแบบการทำงาน",
                        },
                        "date_from": {
                            "type": "string",
                            "description": "วันที่เริ่มต้น YYYY-MM-DD",
                        },
                        "date_to": {
                            "type": "string",
                            "description": "วันที่สิ้นสุด YYYY-MM-DD",
                        },
                    },
                },
            },
            {
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
                            "type": "string",
                            "description": "ชื่อตำแหน่ง (ถ้ามีหลายงานในบริษัทเดียวกัน)",
                        },
                        "status": {
                            "type": "string",
                            "description": "สถานะใหม่ เช่น นัดสัมภาษณ์, สัมภาษณ์แล้ว, ผ่านการคัดเลือก, ปฏิเสธแล้ว",
                        },
                        "salary": {
                            "type": "string",
                            "description": "เงินเดือนที่ต้องการแก้ไข",
                        },
                        "note": {
                            "type": "string",
                            "description": "บันทึกเพิ่มเติมใหม่",
                        },
                        "work_mode": {
                            "type": "string",
                            "enum": ["onsite", "hybrid", "remote", "unknown"],
                            "description": "รูปแบบการทำงานใหม่",
                        },
                    },
                    "required": ["company"],
                },
            },
            {
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
                            "type": "string",
                            "description": "ชื่อตำแหน่งของงานที่ต้องการลบ (ถ้ามี)",
                        },
                    },
                    "required": ["company"],
                },
            },
        ]
    }
]
