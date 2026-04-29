# Emily Grammar Checker AI

ระบบตรวจสอบและแก้ไขไวยากรณ์ภาษาอังกฤษ  
ด้วย **Gramformer** + **Gemini AI**

---

## 🖥️ ตัวอย่างการใช้งาน

```
Input:  "She go to school yesterday"
Output: "She went to school yesterday."

🔧 พบ 1 จุดที่ต้องแก้ไข
กฎไวยากรณ์: Past Tense
ทำไมถึงผิด: 'go' เป็นรูปปัจจุบัน...
ทำไมถึงถูก: 'went' เป็นรูป Past Tense...
```

---

## 📋 Requirements

| Tool   | Version            |
|--------|--------------------|
| Python | **3.11.x** (แนะนำ) |
| pip    | 23.x ขึ้นไป          |
| Git    | any                |

> ⚠️ **Python 3.14 ใช้ไม่ได้** เพราะ torch ยังไม่รองรับ

---

## 📁 โครงสร้างโปรเจ็ค

```
Emily_Project/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── grammar_checker.py   # Gramformer + Gemini logic
│   ├── check_models.py      # เช็ค Gemini models
│   └── .env                 # API Keys
├── frontend/
│   └── app.py               # Streamlit UI
├── venv/                    # Virtual environment
└── README.md
```

---

## ⚙️ การติดตั้ง (Setup)

### Step 1: Clone หรือดาวน์โหลดโปรเจ็ค

```bash
cd 
# วางโฟลเดอร์ Emily_Project ไว้ที่นี่
```

---

### Step 2: ติดตั้ง Python 3.11

```
🔗 https://www.python.org/downloads/release/python-3119/
```

- เลือก → **Windows installer (64-bit)**
- ติ๊ก ✅ **Add python.exe to PATH**

เช็คว่าติดตั้งสำเร็จ:
```bash
py -3.11 --version
# Python 3.11.9
```

---

### Step 3: สร้าง Virtual Environment

```bash
cd \Emily_Project

# สร้าง venv ด้วย Python 3.11
py -3.11 -m venv venv

# Activate (Windows)
venv\Scripts\activate

# ต้องเห็น (venv) หน้า PS
(venv) PS \Emily_Project>
```

---

### Step 4: ติดตั้ง Dependencies

```bash
# อัปเกรด pip
python -m pip install --upgrade pip

# ติดตั้ง PyTorch (CPU)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# ติดตั้ง packages หลัก
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install transformers==4.35.0
pip install streamlit==1.28.0
pip install requests==2.31.0
pip install pydantic==2.4.2
pip install python-dotenv==1.0.0
pip install google-genai
pip install spacy==3.7.2
pip install happytransformer

# ติดตั้ง spaCy model
python -m spacy download en_core_web_sm

# ติดตั้ง Gramformer
pip install git+https://github.com/PrithivirajDamodaran/Gramformer.git
```

---

### Step 5: แก้ไข Gramformer (สำคัญ!)

เปิดไฟล์:
```
\Emily_Project\venv\Lib\site-packages\gramformer\gramformer.py
```

หาบรรทัดนี้แล้วลบ `use_auth_token=False` ออก:

```python
# ❌ เดิม
self.correction_tokenizer = AutoTokenizer.from_pretrained(
    correction_model_tag, use_auth_token=False
)
self.correction_model = AutoModelForSeq2SeqLM.from_pretrained(
    correction_model_tag, use_auth_token=False
)

# ✅ แก้เป็น
self.correction_tokenizer = AutoTokenizer.from_pretrained(
    correction_model_tag
)
self.correction_model = AutoModelForSeq2SeqLM.from_pretrained(
    correction_model_tag
)
```

---

### Step 6: ตั้งค่า Gemini API Key

สร้างไฟล์ `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

ขอ API Key ฟรีได้ที่:
```
🔗 https://aistudio.google.com/app/apikey
→ Create API key in new project
```

---

### Step 7: เช็ค Gemini Models

```bash
cd \Emily_Project\backend
venv\Scripts\activate
python check_models.py
```

ดูว่า model ไหนใช้ได้ แล้วอัปเดตใน `grammar_checker.py`:
```python
GEMINI_MODELS = [
    "gemini-2.5-flash",  # ใส่ model ที่ใช้ได้
]
```

---

## 🚀 วิธีรัน

### Terminal 1 → Backend

```bash
cd \Emily_Project\backend
\Emily_Project\venv\Scripts\activate
python main.py
```

รอจนเห็น:
```
✅ Gramformer Loaded!
✅ Working model found: gemini-2.5-flash
✅ Engine Ready!
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### Terminal 2 → Frontend

```bash
cd \Emily_Project\frontend
\Emily_Project\venv\Scripts\activate
streamlit run app.py
```

รอจนเห็น:
```
Local URL: http://localhost:8501
```

---

## 🌐 เปิดใช้งาน

| URL | หน้าที่ |
|-----|--------|
| http://localhost:8501 | 🌐 หน้าเว็บ UI |
| http://localhost:8000 | 📡 Backend API |
| http://localhost:8000/docs | 📖 API Documentation |

---

## 🛠️ Tech Stack

| เทคโนโลยี | เวอร์ชัน | หน้าที่ |
|-----------|---------|--------|
| Python | 3.11.9 | Programming Language |
| FastAPI | 0.104.1 | Backend API |
| Uvicorn | 0.24.0 | ASGI Server |
| Streamlit | 1.28.0 | Frontend UI |
| Gramformer | latest | Grammar Correction |
| Transformers | 4.35.0 | NLP Model |
| PyTorch | 2.x (CPU) | Deep Learning |
| spaCy | 3.7.2 | NLP Pipeline |
| Google Gemini | 2.5 Flash | AI Explanation |
| python-dotenv | 1.0.0 | Environment Variables |

---

## ❗ ปัญหาที่พบบ่อย

### `No module named 'torch'`
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### `Can't find model 'en_core_web_sm'`
```bash
python -m spacy download en_core_web_sm
```

### `use_auth_token error`
```
แก้ไฟล์ gramformer.py ตาม Step 5
```

### `429 RESOURCE_EXHAUSTED`
```
Gemini quota หมด → รอพรุ่งนี้ หรือขอ API Key ใหม่
ระบบจะใช้ Offline Rules แทนอัตโนมัติ
```

### `Cannot connect to API`
```
ต้องรัน Backend ก่อน (Terminal 1)
แล้วค่อยรัน Frontend (Terminal 2)
```

### Python 3.14 ใช้ไม่ได้
```
ติดตั้ง Python 3.11 แล้วสร้าง venv ใหม่
py -3.11 -m venv venv
```

---

## 📝 หมายเหตุ

- **Gemini Free Tier** มี quota จำกัด (~20 req/day สำหรับ gemini-2.5-flash)
- ถ้า Gemini quota หมด ระบบจะใช้ **Offline Rules** อธิบายแทน
- ครั้งแรกที่รัน จะโหลด model ~892MB (ใช้เวลานาน)
- ครั้งต่อไปจะเร็วขึ้นเพราะ cache ไว้แล้ว