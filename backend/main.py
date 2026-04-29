# ======================================
# main.py
# Grammar Checker API
# Version: 3.0.0
# Gramformer + HappyTransformer + Gemini
# ======================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
from typing import Optional
import time

from grammar_checker import GrammarCheckerEngine

# ======================================
# Lifespan (โหลด Engine ตอน startup)
# ======================================

engine: Optional[GrammarCheckerEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """โหลด Engine ตอน startup"""
    global engine
    print("=" * 60)
    print("  🚀 Starting Grammar Checker Engine v3.0")
    print("  📦 Models: Gramformer + HappyTransformer + Gemini")
    print("=" * 60)
    engine = GrammarCheckerEngine()
    print("\n" + "=" * 60)
    print("  ✅ Engine Ready!")
    print("=" * 60)
    yield
    # ตอน shutdown
    print("👋 Shutting down Grammar Checker...")


# ======================================
# App Setup
# ======================================

app = FastAPI(
    title="Grammar Checker API",
    description=(
        "English Grammar Checker powered by "
        "Gramformer + HappyTransformer + Gemini AI"
    ),
    version="3.0.0",
    lifespan=lifespan
)

# ── CORS ──────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================
# Request / Response Models
# ======================================

class CheckRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text must not be empty")
        if len(v.strip()) < 2:
            raise ValueError("Text must be at least 2 characters")
        if len(v.strip()) > 1000:
            raise ValueError("Text must not exceed 1000 characters")
        return v.strip()


class DifferenceItem(BaseModel):
    position: int
    original: str
    corrected: str
    type: str


class ExplanationItem(BaseModel):
    position: int
    original: str
    corrected: str
    type: str
    explanation: str


class EnsembleInfo(BaseModel):
    source: str
    confidence: str
    gramformer_result: str
    happy_result: str


class CheckResponse(BaseModel):
    original: str
    corrected: str
    is_correct: bool
    differences: list[DifferenceItem]
    explanations: list[ExplanationItem]
    ensemble: EnsembleInfo
    processing_time: float
    models_used: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    engine: str
    gramformer: bool
    happy_transformer: bool
    gemini_model: Optional[str]
    models_used: list[str]


class ExampleItem(BaseModel):
    text: str
    category: str


class ExamplesResponse(BaseModel):
    examples: list[ExampleItem]


# ======================================
# Endpoints
# ======================================

# ── Health Check ──────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - แสดงสถานะ API"""
    return _build_health_response()


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return _build_health_response()


def _build_health_response() -> dict:
    """สร้าง health response"""
    if not engine:
        return {
            "status": "starting",
            "version": "3.0.0",
            "engine": "not ready",
            "gramformer": False,
            "happy_transformer": False,
            "gemini_model": None,
            "models_used": [],
        }

    models_used = []
    if engine.gramformer:
        models_used.append("Gramformer")
    if engine.happy_tt:
        models_used.append("HappyTransformer")
    if engine.working_model:
        models_used.append(f"Gemini ({engine.working_model})")

    return {
        "status": "ok",
        "version": "3.0.0",
        "engine": "ready",
        "gramformer": engine.gramformer is not None,
        "happy_transformer": engine.happy_tt is not None,
        "gemini_model": engine.working_model,
        "models_used": models_used,
    }


# ── Grammar Check ────────────────────────────────────────

@app.post("/check", response_model=CheckResponse)
async def check_grammar(request: CheckRequest):
    """
    ตรวจไวยากรณ์ภาษาอังกฤษ

    Pipeline:
    1. Gramformer + HappyTransformer แก้ไข (Ensemble)
    2. หา Differences
    3. Gemini อธิบาย (หรือ Offline fallback)
    """
    if not engine:
        raise HTTPException(
            status_code=503,
            detail="Engine is not ready yet. Please wait."
        )

    start_time = time.time()

    try:
        # ✅ ใช้ full_check (ครบ pipeline)
        result = engine.full_check(request.text)

        processing_time = round(time.time() - start_time, 3)

        # สร้าง models_used list
        models_used = []
        if engine.gramformer:
            models_used.append("Gramformer")
        if engine.happy_tt:
            models_used.append("HappyTransformer")
        if engine.working_model:
            models_used.append(f"Gemini ({engine.working_model})")

        return CheckResponse(
            original=result["original"],
            corrected=result["corrected"],
            is_correct=result["is_correct"],
            differences=[
                DifferenceItem(**diff)
                for diff in result["differences"]
            ],
            explanations=[
                ExplanationItem(**exp)
                for exp in result["explanations"]
            ],
            ensemble=EnsembleInfo(**result["ensemble"]),
            processing_time=processing_time,
            models_used=models_used,
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = round(time.time() - start_time, 3)
        print(f"❌ Error in /check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


# ── Compare Models (เปรียบเทียบ 2 models) ────────────────

@app.post("/compare")
async def compare_models(request: CheckRequest):
    """
    เปรียบเทียบผลลัพธ์จาก Gramformer vs HappyTransformer
    (สำหรับ debug / วิเคราะห์)
    """
    if not engine:
        raise HTTPException(
            status_code=503,
            detail="Engine is not ready yet."
        )

    start_time = time.time()

    try:
        text = request.text.strip()

        # เรียกแต่ละ model แยก
        gramformer_result = engine._correct_with_gramformer(text)
        happy_result = engine._correct_with_happy(text)

        # Ensemble
        ensemble = engine._ensemble_results(
            text, gramformer_result, happy_result
        )

        processing_time = round(time.time() - start_time, 3)

        return {
            "original": text,
            "gramformer": {
                "corrected": gramformer_result,
                "changed": gramformer_result.lower().strip() != text.lower().strip(),
            },
            "happy_transformer": {
                "corrected": happy_result,
                "changed": happy_result.lower().strip() != text.lower().strip(),
            },
            "ensemble": {
                "final": ensemble["corrected"],
                "source": ensemble["source"],
                "confidence": ensemble["confidence"],
            },
            "processing_time": processing_time,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


# ── Examples ──────────────────────────────────────────────

@app.get("/examples", response_model=ExamplesResponse)
async def get_examples():
    """ตัวอย่างประโยคที่ผิดไวยากรณ์สำหรับทดสอบ"""
    return ExamplesResponse(
        examples=[
            ExampleItem(
                text="She go to school yesterday",
                category="Past Tense"
            ),
            ExampleItem(
                text="He don't like pizza",
                category="Subject-Verb Agreement"
            ),
            ExampleItem(
                text="I am very boring in class",
                category="Word Choice"
            ),
            ExampleItem(
                text="They was playing football",
                category="Subject-Verb Agreement (Past)"
            ),
            ExampleItem(
                text="I have went to Paris last year",
                category="Perfect Tense"
            ),
            ExampleItem(
                text="She is more taller than me",
                category="Comparative"
            ),
            ExampleItem(
                text="He goed to the store",
                category="Irregular Verb"
            ),
            ExampleItem(
                text="Me and him went to school",
                category="Subject Pronoun"
            ),
            ExampleItem(
                text="I has a apple",
                category="Article + Verb Agreement"
            ),
            ExampleItem(
                text="She can sings very good",
                category="Modal Verb + Adverb"
            ),
        ]
    )


# ── Batch Check (ตรวจหลายประโยคพร้อมกัน) ─────────────────

class BatchRequest(BaseModel):
    texts: list[str]

    @field_validator("texts")
    @classmethod
    def texts_must_not_be_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Texts list must not be empty")
        if len(v) > 20:
            raise ValueError("Maximum 20 sentences per batch")
        return v


class BatchResultItem(BaseModel):
    original: str
    corrected: str
    is_correct: bool
    differences: list[DifferenceItem]
    ensemble_source: str
    ensemble_confidence: str


class BatchResponse(BaseModel):
    results: list[BatchResultItem]
    total: int
    correct_count: int
    incorrect_count: int
    processing_time: float


@app.post("/batch", response_model=BatchResponse)
async def batch_check(request: BatchRequest):
    """ตรวจไวยากรณ์หลายประโยคพร้อมกัน (ไม่มี Gemini explanation)"""
    if not engine:
        raise HTTPException(
            status_code=503,
            detail="Engine is not ready yet."
        )

    start_time = time.time()

    try:
        results = []
        correct_count = 0

        for text in request.texts:
            text = text.strip()
            if not text or len(text) < 2:
                continue

            # Correction (ไม่ต้อง explain เพื่อความเร็ว)
            ensemble = engine.correct_grammar(text)
            corrected = ensemble["corrected"]
            differences = engine.find_differences(text, corrected)

            is_correct = (
                text.lower().strip() == corrected.lower().strip()
            )
            if is_correct:
                correct_count += 1

            results.append(BatchResultItem(
                original=text,
                corrected=corrected,
                is_correct=is_correct,
                differences=[
                    DifferenceItem(**diff) for diff in differences
                ],
                ensemble_source=ensemble["source"],
                ensemble_confidence=ensemble["confidence"],
            ))

        processing_time = round(time.time() - start_time, 3)

        return BatchResponse(
            results=results,
            total=len(results),
            correct_count=correct_count,
            incorrect_count=len(results) - correct_count,
            processing_time=processing_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


# ── Stats ─────────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    """แสดงข้อมูลสถานะของ models"""
    if not engine:
        raise HTTPException(
            status_code=503,
            detail="Engine is not ready yet."
        )

    return {
        "engine_version": "3.0.0",
        "models": {
            "gramformer": {
                "loaded": engine.gramformer is not None,
                "model": "prithivida/grammar_error_correcter_v1",
                "role": "Primary grammar correction",
            },
            "happy_transformer": {
                "loaded": engine.happy_tt is not None,
                "model": "vennify/t5-base-grammar-correction",
                "role": "Secondary grammar correction (ensemble)",
            },
            "gemini": {
                "loaded": engine.working_model is not None,
                "model": engine.working_model,
                "role": "Thai explanation generation",
            },
        },
        "ensemble_strategy": {
            "description": "Combine results from Gramformer + HappyTransformer",
            "strategies": [
                "both_agree → Highest confidence",
                "gramformer_primary → Both changed, use Gramformer",
                "gramformer_only → Only Gramformer changed",
                "happy_only → Only HappyTransformer changed",
                "no_change → Sentence is correct",
            ]
        },
        "endpoints": [
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/check", "method": "POST", "description": "Check single sentence"},
            {"path": "/compare", "method": "POST", "description": "Compare model outputs"},
            {"path": "/batch", "method": "POST", "description": "Check multiple sentences"},
            {"path": "/examples", "method": "GET", "description": "Example sentences"},
            {"path": "/stats", "method": "GET", "description": "Model statistics"},
        ]
    }


# ======================================
# Run Server
# ======================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render inject PORT
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )