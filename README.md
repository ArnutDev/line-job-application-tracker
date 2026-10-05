# 💼 JobTrack — LINE Job Application Tracker

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--20b-f55036.svg)](https://groq.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)

**JobTrack** คือระบบผู้ช่วยบันทึกและติดตามสถานะการสมัครงานผ่าน **LINE Chatbot** อัจฉริยะ ช่วยให้ผู้ใช้จัดการประวัติการสมัครงาน อัปเดตสถานะ ดูสถิติสรุป และส่งออกข้อมูลเป็นไฟล์ Excel (.xlsx) ได้ทันทีผ่านห้องแชต LINE โดยไม่ต้องเปิดสเปรดชีตจดเอง

---

## 🌟 ฟีเจอร์เด่น (Core Features)

- 🤖 **Natural Language Understanding (AI)**: คุยด้วยภาษาธรรมชาติ เช่น *"สมัครงาน KBank ตำแหน่ง Backend Developer เงินเดือน 50,000 บาท เมื่อวาน"* ขับเคลื่อนโดย **Groq (`openai/gpt-oss-20b`)** ตอบสนองรวดเร็วระดับเสี้ยววินาที
- 📋 **CRUD & Filtering**: บันทึก, ดูรายละเอียด, แก้ไขสถานะ/เงินเดือน/โน้ต, ลบงาน และกรองตามสถานะ บริษัท ตำแหน่ง หรือรูปแบบงาน (Remote / Hybrid / On-site)
- 📊 **Application Summary**: สรุปผลภาพรวมการสมัครงานทั้งหมด แจกแจงจำนวนงานแยกตามสถานะด้วย SQL Aggregation
- 📥 **Interactive Excel Export**: ส่งออกประวัติการสมัครงานเป็นไฟล์ Excel (.xlsx) พร้อมจัดสไตล์หัวตาราง ส่งกลับมาในแชตเป็นการ์ด **LINE Flex Message** ให้กดแตะปุ่มดาวน์โหลดลงเครื่องได้ทันที
- 📱 **LINE Native UI**: รองรับ **Rich Menu 4 ช่อง** ด้านล่างหน้าจอแชต และปุ่ม **Quick Reply** อำนวยความสะดวก
- 🔒 **Security & User Isolation**: แยกข้อมูลผู้ใช้เด็ดขาด (User Isolation) ทุกคำสั่งใน DB ล็อกตาม `user_id` พร้อมตรวจสอบลายเซ็น LINE Webhook Signature และใช้ HMAC-SHA256 Signed Token สำหรับลิงก์ดาวน์โหลด

---

## 🏗️ สถาปัตยกรรมระบบ (Architecture)

```mermaid
flowchart TD
    User["👤 ผู้ใช้งาน LINE"] -->|ส่งข้อความ / กดปุ่ม| LINE["📱 LINE Messaging API"]
    LINE -->|Webhook HTTP POST| FastAPI["⚡ FastAPI Backend"]
    FastAPI --> Security["🔐 Signature & User Resolver"]
    Security --> LLM["⚡ Groq API (openai/gpt-oss-20b)"]
    LLM -->|Structured Tool Call / Intent| Dispatcher["⚙️ Intent Dispatcher"]
    Dispatcher --> Service["💼 Business Logic & Export Service"]
    Service --> Repo["🗄️ Repository Layer"]
    Repo --> DB[("🐘 PostgreSQL")]
    Service -->|Flex Message / Text Reply| LINE
```

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
- **AI / LLM**: [Groq Cloud](https://groq.com/) — โมเดล `openai/gpt-oss-20b` (Tool Calling / Function Calling)
- **Database**: PostgreSQL 17
- **Messaging**: LINE Messaging API (Webhook, Flex Message, Quick Reply, Rich Menu)
- **Export**: openpyxl
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest / unittest

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
line-job-application-tracker/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI Routers & Webhook endpoint
│   │   ├── core/           # Config, Database engine, Security (HMAC tokens)
│   │   ├── models/         # SQLAlchemy ORM Models (User, JobApplication)
│   │   ├── repositories/   # Data Access Layer (CRUD, Queries, Isolation)
│   │   ├── schemas/        # Pydantic Schemas & Groq Tool definitions
│   │   ├── services/       # Business Logic, Groq NLP, Export, LINE messaging
│   │   └── main.py         # FastAPI App Entrypoint
│   ├── alembic/            # Database Migrations
│   ├── tests/              # Automated Test Suite (31 tests)
│   ├── requirements.txt    # Python Dependencies
│   ├── Dockerfile          # Backend Containerfile
│   └── .env.example        # ตัวอย่าง Environment Variables
├── scripts/
│   ├── setup_rich_menu.py  # สคริปต์สร้างและติดตั้ง LINE Rich Menu
│   └── rich_menu.png       # ภาพเมนูความละเอียด 2500x1686
├── docker-compose.yml      # Multi-container orchestration (Backend + Postgres)
├── .gitignore
└── README.md
```

---

## 🚀 การติดตั้งและเริ่มต้นใช้งาน (Getting Started)

### 1. คัดลอก Repository และเตรียม Environment Variables

```bash
git clone https://github.com/ArnutDev/line-job-application-tracker.git
cd line-job-application-tracker
```

คัดลอกไฟล์ `.env.example` ไปเป็น `.env` ในโฟลเดอร์ `backend/`:

```bash
cp backend/.env.example backend/.env
```

แก้ไขค่าใน `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/jobtrack
LINE_CHANNEL_SECRET=your_line_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

> 💡 **รับ API Keys:**
> - **Groq API Key**: สมัครฟรีได้ทันทีที่ [console.groq.com/keys](https://console.groq.com/keys)
> - **LINE Credentials**: รับได้ที่ [LINE Developers Console](https://developers.line.biz/console/)

---

### 2. รันระบบ

#### ทางเลือกที่ 1: รันผ่าน Docker Compose (แนะนำ สะดวกที่สุด) 🐳

```bash
docker compose up --build
```
ระบบจะเริ่มต้นทั้ง **PostgreSQL** และ **FastAPI Backend** พร้อมรัน Database Migration ให้อัตโนมัติที่พอร์ต `8000`

---

#### ทางเลือกที่ 2: รันแบบ Local Development 💻

1. **สตาร์ท PostgreSQL ผ่าน Docker:**
   ```bash
   docker compose up -d postgres
   ```

2. **ติดตั้ง Python Dependencies:**
   ```bash
   cd backend
   python -m venv .venv
   # บน Windows:
   .\.venv\Scripts\activate
   # บน Mac/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **รัน Database Migrations:**
   ```bash
   alembic upgrade head
   ```

4. **สตาร์ท FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

### 3. เชื่อมต่อ LINE Webhook ด้วย ngrok 🌐

เนื่องจาก LINE Messaging API ต้องยิง Webhook มาที่ URL ที่เป็น HTTPS ให้เปิด Tunnel ด้วย ngrok:

```bash
ngrok http 8000
```

นำ Forwarding URL ที่ได้ (เช่น `https://xxxx.ngrok-free.app`) ไปตั้งค่าใน **LINE Developers Console**:
- **Webhook URL**: `https://xxxx.ngrok-free.app/webhook`
- เปิดใช้งาน **Use Webhook: ON**
- ปิด **Auto-reply messages: OFF** ใน LINE Official Account Manager

---

### 4. ติดตั้ง LINE Rich Menu (เมนูลัด 4 ช่อง) 📱

รันสคริปต์เพื่อสร้างและผูก Rich Menu เป็น Default ให้กับผู้ใช้ทุกคน:

```bash
python scripts/setup_rich_menu.py --action create
```

---

## 💬 ตัวอย่างคำสั่งที่คุยกับบอทใน LINE

| การกระทำ | ตัวอย่างประโยคที่พิมพ์คุยกับบอท |
|---|---|
| **➕ บันทึกงานใหม่** | *"สมัครงาน KBank ตำแหน่ง Backend Developer เงินเดือน 55,000 บาท เมื่อวาน"* |
| **📋 ดูรายการงานทั้งหมด** | *"ดูรายการสมัครงานทั้งหมด"* หรือ *"ตอนนี้สมัครงานอะไรไปบ้าง"* |
| **🔍 ค้นหา/กรองงาน** | *"ขอดูงานที่สถานะสัมภาษณ์แล้วหน่อย"* หรือ *"หางานบริษัท Agoda"* |
| **✏️ อัปเดตสถานะ** | *"KBank นัดสัมภาษณ์แล้วครับ"* หรือ *"ผ่านคัดเลือก LINE Man แล้ว"* |
| **🗑️ ลบประวัติงาน** | *"ขอลบงานบริษัท SCB"* |
| **📊 สรุปสถิติ** | *"สรุปสถิติการสมัครงานทั้งหมด"* |
| **📥 ส่งออก Excel** | *"ขอ export ข้อมูลการสมัครงานเป็น excel"* |
| **👋 สนทนาทั่วไป** | *"สวัสดีครับ บอททำอะไรได้บ้าง"* |

---

## 🧪 การรันชุดทดสอบ (Automated Testing)

โปรเจกต์มีชุดทดสอบครอบคลุมทุก Layer (Repository, Intent Dispatcher, Webhook, Security, Export, Groq LLM):

```bash
cd backend
python -m unittest discover tests
```

ผลการทดสอบ:
```text
Ran 31 tests in 1.100s
OK
```

---

## 📄 ใบอนุญาต (License)

โปรเจกต์นี้เปิดให้ใช้งานและพัฒนาต่อได้ภายใต้ [MIT License](LICENSE)