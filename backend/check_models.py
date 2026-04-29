from google import genai
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()

# ======================================
# เช็ค API Key
# ======================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ไม่พบ GEMINI_API_KEY ใน .env")
    print("กรุณาสร้างไฟล์ .env และใส่:")
    print("GEMINI_API_KEY=your_key_here")
    exit(1)

print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")

# ======================================
# List Models
# ======================================

client = genai.Client(api_key=api_key)

print("\n📋 Models ทั้งหมดที่ใช้ได้:")
print("-" * 50)

all_models = list(client.models.list())

# ✅ แยกประเภท model
text_models    = []
other_models   = []

for model in all_models:
    name = model.name
    # กรองเฉพาะ gemini ที่ใช้ generate text ได้
    if "gemini" in name and any(
        x in name for x in ["flash", "pro"]
    ) and not any(
        x in name for x in ["tts", "audio", "image", "vision"]
    ):
        text_models.append(name)
    else:
        other_models.append(name)

# แสดง text models (ที่ใช้กับโปรเจ็คได้)
print("\n🟢 Text Models (ใช้กับ Grammar Checker ได้):")
print("-" * 50)
for name in text_models:
    print(f"  ✅ {name}")

# แสดง other models
print(f"\n⚪ Other Models (ใช้ไม่ได้กับโปรเจ็คนี้):")
print("-" * 50)
for name in other_models:
    print(f"  • {name}")

# ======================================
# ทดสอบ Model ที่แนะนำ
# ======================================

print("\n🔍 ทดสอบ Models:")
print("-" * 50)

test_models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

working = []

for model in test_models:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Say OK in one word."
        )
        if response.text:
            print(f"  ✅ {model} → ใช้ได้!")
            working.append(model)
    except Exception as e:
        err = str(e)
        if "429" in err:
            print(f"  ⚠️ {model} → Quota หมด")
        elif "404" in err:
            print(f"  ❌ {model} → ไม่พบ model")
        else:
            print(f"  ❌ {model} → Error: {err[:50]}")

# ======================================
# สรุป
# ======================================

print("\n📊 สรุป:")
print("-" * 50)
if working:
    print(f"✅ Model ที่ใช้ได้: {working}")
    print(f"\n💡 อัปเดตใน grammar_checker.py:")
    print(f'   GEMINI_MODELS = ["{working}"]')
else:
    print("❌ ไม่มี model ที่ใช้ได้ตอนนี้")
    print("กรุณาขอ API Key ใหม่ที่:")
    print("https://aistudio.google.com/app/apikey")