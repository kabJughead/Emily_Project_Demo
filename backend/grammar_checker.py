# ======================================
# grammar_checker.py
# Gramformer + HappyTransformer + Gemini
# Version: 3.1.0 (with Gemini Role)
# ======================================

import re
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from happytransformer import HappyTextToText, TTSettings

load_dotenv()

# ======================================
# Gemini Models (เรียงลำดับความสำคัญ)
# ======================================

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]

# ======================================
# Gemini System Instruction (Role)
# ======================================

SYSTEM_INSTRUCTION = (
    "คุณคือผู้หญิงใจดีที่เป็นผู้เชี่ยวชาญด้านภาษาอังกฤษ"
    "ที่อธิบายการแก้ไขไวยากรณ์ให้นักเรียนอย่างเข้าใจง่าย "
    "อธิบายเป็นภาษาไทย ให้เข้าใจง่าย "
    "เหมาะสำหรับผู้เริ่มต้นเรียนภาษาอังกฤษ"
)

# ======================================
# Grammar Rules (Offline Fallback)
# ======================================

GRAMMAR_RULES = {
    ("i", "I"): (
        "Capitalization",
        "'i' → 'I'",
        "สรรพนามบุรุษที่ 1 'I' ต้องเป็นตัวพิมพ์ใหญ่เสมอ",
        "❌ i am happy → ✅ I am happy"
    ),
    ("dont", "don't"): (
        "Contraction",
        "'dont' → 'don't'",
        "คำย่อต้องมี apostrophe",
        "❌ I dont know → ✅ I don't know"
    ),
    ("doesnt", "doesn't"): (
        "Contraction",
        "'doesnt' → 'doesn't'",
        "คำย่อต้องมี apostrophe",
        "❌ He doesnt like → ✅ He doesn't like"
    ),
    ("cant", "can't"): (
        "Contraction",
        "'cant' → 'can't'",
        "คำย่อต้องมี apostrophe",
        "❌ I cant do → ✅ I can't do"
    ),
    ("wont", "won't"): (
        "Contraction",
        "'wont' → 'won't'",
        "คำย่อต้องมี apostrophe",
        "❌ I wont go → ✅ I won't go"
    ),
    ("im", "I'm"): (
        "Contraction + Capitalization",
        "'im' → 'I'm'",
        "คำย่อของ 'I am' ต้องเขียน \"I'm\"",
        "❌ im fine → ✅ I'm fine"
    ),
    ("hes", "he's"): (
        "Contraction",
        "'hes' → 'he's'",
        "คำย่อของ 'he is' / 'he has'",
        "❌ hes going → ✅ he's going"
    ),
    ("shes", "she's"): (
        "Contraction",
        "'shes' → 'she's'",
        "คำย่อของ 'she is' / 'she has'",
        "❌ shes smart → ✅ she's smart"
    ),
    ("theyre", "they're"): (
        "Contraction",
        "'theyre' → 'they're'",
        "คำย่อของ 'they are'",
        "❌ theyre here → ✅ they're here"
    ),
    ("youre", "you're"): (
        "Contraction",
        "'youre' → 'you're'",
        "คำย่อของ 'you are'",
        "❌ youre right → ✅ you're right"
    ),
    ("its", "it's"): (
        "Contraction vs Possessive",
        "'its' → 'it's'",
        "'it's' = 'it is' / 'it has', 'its' = possessive",
        "❌ its raining → ✅ it's raining"
    ),
    ("alot", "a lot"): (
        "Spelling",
        "'alot' → 'a lot'",
        "'a lot' ต้องเขียนแยก 2 คำ",
        "❌ I have alot → ✅ I have a lot"
    ),
    ("goed", "went"): (
        "Irregular Verb",
        "'goed' → 'went'",
        "'go' เป็น irregular verb → past tense = 'went'",
        "❌ I goed home → ✅ I went home"
    ),
    ("runned", "ran"): (
        "Irregular Verb",
        "'runned' → 'ran'",
        "'run' เป็น irregular verb → past tense = 'ran'",
        "❌ He runned fast → ✅ He ran fast"
    ),
    ("eated", "ate"): (
        "Irregular Verb",
        "'eated' → 'ate'",
        "'eat' เป็น irregular verb → past tense = 'ate'",
        "❌ I eated lunch → ✅ I ate lunch"
    ),
    ("thinked", "thought"): (
        "Irregular Verb",
        "'thinked' → 'thought'",
        "'think' เป็น irregular verb → past tense = 'thought'",
        "❌ I thinked about it → ✅ I thought about it"
    ),
    ("writed", "wrote"): (
        "Irregular Verb",
        "'writed' → 'wrote'",
        "'write' เป็น irregular verb → past tense = 'wrote'",
        "❌ She writed a letter → ✅ She wrote a letter"
    ),
    ("is", "are"): (
        "Subject-Verb Agreement",
        "'is' → 'are'",
        "ประธานพหูพจน์ต้องใช้ 'are'",
        "❌ They is happy → ✅ They are happy"
    ),
    ("are", "is"): (
        "Subject-Verb Agreement",
        "'are' → 'is'",
        "ประธานเอกพจน์ต้องใช้ 'is'",
        "❌ He are tall → ✅ He is tall"
    ),
    ("has", "have"): (
        "Subject-Verb Agreement",
        "'has' → 'have'",
        "ประธานพหูพจน์ / I / You ใช้ 'have'",
        "❌ They has a car → ✅ They have a car"
    ),
    ("have", "has"): (
        "Subject-Verb Agreement",
        "'have' → 'has'",
        "ประธานเอกพจน์บุรุษที่ 3 ใช้ 'has'",
        "❌ She have a dog → ✅ She has a dog"
    ),
    ("go", "goes"): (
        "Subject-Verb Agreement",
        "'go' → 'goes'",
        "ประธานเอกพจน์บุรุษที่ 3 ต้องเติม -es",
        "❌ He go to school → ✅ He goes to school"
    ),
    ("a", "an"): (
        "Article",
        "'a' → 'an'",
        "ใช้ 'an' หน้าคำที่ขึ้นต้นด้วยเสียงสระ",
        "❌ a apple → ✅ an apple"
    ),
    ("an", "a"): (
        "Article",
        "'an' → 'a'",
        "ใช้ 'a' หน้าคำที่ขึ้นต้นด้วยเสียงพยัญชนะ",
        "❌ an book → ✅ a book"
    ),
    ("your", "you're"): (
        "Your vs You're",
        "'your' → 'you're'",
        "'you're' = 'you are', 'your' = possessive",
        "❌ Your welcome → ✅ You're welcome"
    ),
    ("there", "their"): (
        "There vs Their",
        "'there' → 'their'",
        "'their' = possessive, 'there' = สถานที่",
        "❌ there house → ✅ their house"
    ),
    ("their", "there"): (
        "Their vs There",
        "'their' → 'there'",
        "'there' = สถานที่, 'their' = possessive",
        "❌ Go over their → ✅ Go over there"
    ),
    ("then", "than"): (
        "Then vs Than",
        "'then' → 'than'",
        "'than' ใช้เปรียบเทียบ, 'then' ใช้บอกลำดับเวลา",
        "❌ bigger then → ✅ bigger than"
    ),
    ("than", "then"): (
        "Than vs Then",
        "'than' → 'then'",
        "'then' ใช้บอกลำดับเวลา, 'than' ใช้เปรียบเทียบ",
        "❌ first do this, than that → ✅ first do this, then that"
    ),
    ("to", "too"): (
        "To vs Too",
        "'to' → 'too'",
        "'too' = มากเกินไป / ด้วย, 'to' = preposition",
        "❌ me to → ✅ me too"
    ),
    ("too", "to"): (
        "Too vs To",
        "'too' → 'to'",
        "'to' = preposition / infinitive, 'too' = มากเกินไป",
        "❌ I want too go → ✅ I want to go"
    ),
    ("was", "were"): (
        "Subject-Verb Agreement (Past)",
        "'was' → 'were'",
        "ประธานพหูพจน์ / you ใช้ 'were'",
        "❌ They was tired → ✅ They were tired"
    ),
    ("were", "was"): (
        "Subject-Verb Agreement (Past)",
        "'were' → 'was'",
        "ประธานเอกพจน์ใช้ 'was'",
        "❌ He were tired → ✅ He was tired"
    ),
    ("did", "does"): (
        "Tense Agreement",
        "'did' → 'does'",
        "Present tense ใช้ 'does' กับเอกพจน์บุรุษที่ 3",
        "❌ Did he likes it? → ✅ Does he like it?"
    ),
    ("good", "well"): (
        "Adjective vs Adverb",
        "'good' → 'well'",
        "'well' เป็น adverb ขยายกริยา, 'good' เป็น adjective",
        "❌ She sings good → ✅ She sings well"
    ),
    ("me", "I"): (
        "Subject Pronoun",
        "'me' → 'I'",
        "ใช้ 'I' เป็นประธาน, 'me' เป็นกรรม",
        "❌ Me and him went → ✅ He and I went"
    ),
    ("who", "whom"): (
        "Who vs Whom",
        "'who' → 'whom'",
        "'whom' ใช้เป็นกรรม (object)",
        "❌ Who did you see? → ✅ Whom did you see?"
    ),
    ("much", "many"): (
        "Much vs Many",
        "'much' → 'many'",
        "'many' ใช้กับนามนับได้พหูพจน์",
        "❌ much books → ✅ many books"
    ),
    ("many", "much"): (
        "Many vs Much",
        "'many' → 'much'",
        "'much' ใช้กับนามนับไม่ได้",
        "❌ many water → ✅ much water"
    ),
    ("less", "fewer"): (
        "Less vs Fewer",
        "'less' → 'fewer'",
        "'fewer' ใช้กับนามนับได้พหูพจน์",
        "❌ less people → ✅ fewer people"
    ),
}


# ======================================
# Main Class
# ======================================

class GrammarCheckerEngine:

    def __init__(self):
        self.gramformer = None
        self.happy_tt = None
        self.happy_settings = None
        self.gemini_client = None
        self._load_gramformer()
        self._load_happy_transformer()
        self.working_model = self._find_working_model()

    # ══════════════════════════════════════
    # Model Loading
    # ══════════════════════════════════════

    def _load_gramformer(self):
        """โหลด Gramformer model"""
        print("🔄 Loading Gramformer...")
        try:
            from gramformer import Gramformer
            self.gramformer = Gramformer(models=1, use_gpu=False)
            print("✅ Gramformer Loaded!")
        except Exception as e:
            print(f"❌ Gramformer Error: {e}")
            raise e

    def _load_happy_transformer(self):
        """โหลด HappyTransformer model"""
        print("🔄 Loading HappyTransformer...")
        try:
            self.happy_tt = HappyTextToText(
                "T5", "vennify/t5-base-grammar-correction"
            )
            self.happy_settings = TTSettings(
                num_beams=5,
                min_length=1,
                max_length=512
            )
            print("✅ HappyTransformer Loaded!")
        except Exception as e:
            print(f"❌ HappyTransformer Error: {e}")
            self.happy_tt = None

    # ══════════════════════════════════════
    # Find Working Gemini Model
    # ══════════════════════════════════════

    def _find_working_model(self) -> str | None:
        """หา Gemini model ที่ใช้ได้"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ No GEMINI_API_KEY → Offline mode")
            return None

        self.gemini_client = genai.Client(api_key=api_key)

        for model in GEMINI_MODELS:
            try:
                response = self.gemini_client.models.generate_content(
                    model=model,
                    contents="Say OK",
                    config=types.GenerateContentConfig(
                        max_output_tokens=10,
                    )
                )
                if response.text:
                    print(f"✅ Gemini Model: {model}")
                    return model
            except Exception as e:
                err = str(e)
                if "429" in err:
                    print(f"⚠️ {model} → Quota exhausted")
                elif "404" in err:
                    print(f"❌ {model} → Not found")
                else:
                    print(f"❌ {model} → {err[:80]}")
                continue

        print("⚠️ No Gemini model available → Offline mode")
        return None

    # ══════════════════════════════════════
    # Grammar Correction (Individual)
    # ══════════════════════════════════════

    def _correct_with_gramformer(self, text: str) -> str:
        """แก้ไวยากรณ์ด้วย Gramformer"""
        try:
            corrections = self.gramformer.correct(
                text, max_candidates=1
            )
            for corrected in corrections:
                return corrected
            return text
        except Exception as e:
            print(f"❌ Gramformer error: {e}")
            return text

    def _correct_with_happy(self, text: str) -> str:
        """แก้ไวยากรณ์ด้วย HappyTransformer"""
        if not self.happy_tt:
            return text
        try:
            input_text = "grammar: " + text
            result = self.happy_tt.generate_text(
                input_text, args=self.happy_settings
            )
            return result.text.strip() if result.text else text
        except Exception as e:
            print(f"❌ HappyTransformer error: {e}")
            return text

    # ══════════════════════════════════════
    # Ensemble Strategy
    # ══════════════════════════════════════

    def _ensemble_results(
        self,
        original: str,
        gramformer_result: str,
        happy_result: str
    ) -> dict:
        """
        Ensemble: เลือกผลลัพธ์ที่ดีที่สุดจากทั้ง 2 models

        Strategy:
        1. ทั้งสองเห็นตรงกัน → confidence สูง → ใช้เลย
        2. ทั้งสองแก้ แต่ต่างกัน → ใช้ Gramformer เป็นหลัก
        3. มีแค่ตัวเดียวแก้ → ใช้ตัวที่แก้
        4. ไม่มีใครแก้ → ประโยคถูกแล้ว
        """
        orig_clean = original.lower().strip()
        gram_clean = gramformer_result.lower().strip()
        happy_clean = happy_result.lower().strip()

        gram_changed = gram_clean != orig_clean
        happy_changed = happy_clean != orig_clean

        # Case 1: ทั้งสองเห็นตรงกัน (highest confidence)
        if (
            gram_changed
            and happy_changed
            and gram_clean == happy_clean
        ):
            return {
                "corrected": gramformer_result,
                "source": "both_agree",
                "confidence": "high",
                "gramformer_result": gramformer_result,
                "happy_result": happy_result,
            }

        # Case 2: ทั้งสองแก้ แต่ต่างกัน → ใช้ Gramformer
        if (
            gram_changed
            and happy_changed
            and gram_clean != happy_clean
        ):
            return {
                "corrected": gramformer_result,
                "source": "gramformer_primary",
                "confidence": "medium",
                "gramformer_result": gramformer_result,
                "happy_result": happy_result,
            }

        # Case 3: Gramformer แก้ แต่ Happy ไม่แก้
        if gram_changed and not happy_changed:
            return {
                "corrected": gramformer_result,
                "source": "gramformer_only",
                "confidence": "medium",
                "gramformer_result": gramformer_result,
                "happy_result": happy_result,
            }

        # Case 4: Happy แก้ แต่ Gramformer ไม่แก้
        if happy_changed and not gram_changed:
            return {
                "corrected": happy_result,
                "source": "happy_only",
                "confidence": "medium",
                "gramformer_result": gramformer_result,
                "happy_result": happy_result,
            }

        # Case 5: ไม่มีใครแก้ → ประโยคถูกแล้ว
        return {
            "corrected": original,
            "source": "no_change",
            "confidence": "high",
            "gramformer_result": gramformer_result,
            "happy_result": happy_result,
        }

    # ══════════════════════════════════════
    # Main Correction (Public Method)
    # ══════════════════════════════════════

    def correct_grammar(self, text: str) -> dict:
        """
        แก้ไวยากรณ์โดยใช้ทั้ง Gramformer + HappyTransformer
        Returns dict พร้อมข้อมูล ensemble
        """
        print(f"\n📝 Input: \"{text}\"")

        # Step 1: Gramformer
        gramformer_result = self._correct_with_gramformer(text)
        print(f"  🔹 Gramformer: \"{gramformer_result}\"")

        # Step 2: HappyTransformer
        happy_result = self._correct_with_happy(text)
        print(f"  🔹 HappyTransformer: \"{happy_result}\"")

        # Step 3: Ensemble
        ensemble = self._ensemble_results(
            text, gramformer_result, happy_result
        )
        print(
            f"  ✅ Final ({ensemble['source']}): "
            f"\"{ensemble['corrected']}\""
        )

        return ensemble

    # ══════════════════════════════════════
    # Find Differences
    # ══════════════════════════════════════

    def _normalize(self, word: str) -> str:
        """Normalize คำสำหรับเปรียบเทียบ"""
        return re.sub(r'[^\w\s]', '', word).lower().strip()

    def find_differences(
        self,
        original: str,
        corrected: str
    ) -> list[dict]:
        """หาความแตกต่างระหว่างต้นฉบับกับที่แก้แล้ว"""
        original_words = original.split()
        corrected_words = corrected.split()

        differences = []
        max_len = max(len(original_words), len(corrected_words))

        for i in range(max_len):
            orig_word = (
                original_words[i] if i < len(original_words) else ""
            )
            corr_word = (
                corrected_words[i] if i < len(corrected_words) else ""
            )

            if self._normalize(orig_word) != self._normalize(corr_word):
                differences.append({
                    "position": i,
                    "original": orig_word,
                    "corrected": corr_word,
                    "type": self._classify_error(orig_word, corr_word)
                })

        return differences

    def _classify_error(self, original: str, corrected: str) -> str:
        """จำแนกประเภทของ error"""
        orig = original.lower().strip()
        corr = corrected.lower().strip()

        # Missing word
        if not orig:
            return "missing_word"
        if not corr:
            return "extra_word"

        # Capitalization
        if orig == corr:
            return "capitalization"

        # Contraction
        if "'" in corr and "'" not in orig:
            return "contraction"

        # Article
        if orig in ("a", "an", "the") or corr in ("a", "an", "the"):
            return "article"

        # Spelling (edit distance สั้น)
        if self._edit_distance(orig, corr) <= 2:
            return "spelling"

        # Verb form
        verb_endings = ("ed", "ing", "s", "es")
        if any(
            orig.endswith(e) or corr.endswith(e)
            for e in verb_endings
        ):
            return "verb_form"

        return "grammar"

    def _edit_distance(self, s1: str, s2: str) -> int:
        """คำนวณ Levenshtein distance"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(
                    min(insertions, deletions, substitutions)
                )
            prev_row = curr_row

        return prev_row[-1]

    # ══════════════════════════════════════
    # Gemini Explanation (with Role)
    # ══════════════════════════════════════

    def explain_with_gemini(
        self,
        original: str,
        corrected: str,
        differences: list[dict],
        ensemble_info: dict = None
    ) -> list[dict]:
        """อธิบายการแก้ไขด้วย Gemini (หรือ Offline)"""
        if not differences:
            return []

        explanations = []

        for change in differences:
            if self.working_model and self.gemini_client:
                explanation = self._get_gemini_explanation(
                    original, corrected, change, ensemble_info
                )
            else:
                explanation = self._get_offline_explanation(change)

            explanations.append({
                "position": change["position"],
                "original": change["original"],
                "corrected": change["corrected"],
                "type": change["type"],
                "explanation": explanation
            })

        return explanations

    def _get_gemini_explanation(
        self,
        original: str,
        corrected: str,
        change: dict,
        ensemble_info: dict = None
    ) -> str:
        """อธิบายด้วย Gemini API พร้อม Role"""
        try:
            # สร้าง change description
            change_desc = (
                f"'{change['original']}' → '{change['corrected']}' "
                f"(ประเภท: {change['type']})"
            )

            # เพิ่ม ensemble info (ถ้ามี)
            ensemble_note = ""
            if ensemble_info:
                ensemble_note = (
                    f"\n\nข้อมูลเพิ่มเติมจาก AI Models:\n"
                    f"- Gramformer แก้เป็น: "
                    f"\"{ensemble_info.get('gramformer_result', 'N/A')}\"\n"
                    f"- HappyTransformer แก้เป็น: "
                    f"\"{ensemble_info.get('happy_result', 'N/A')}\"\n"
                    f"- ความเห็นตรงกัน: "
                    f"{ensemble_info.get('source', 'N/A')}\n"
                    f"- ความมั่นใจ: "
                    f"{ensemble_info.get('confidence', 'N/A')}"
                )

            # ✅ Prompt ตาม format ที่ต้องการ
            prompt = f"""ประโยคต้นฉบับ: "{original}"
ประโยคที่แก้แล้ว: "{corrected}"
การเปลี่ยนแปลง: {change_desc}
{ensemble_note}

กรุณาอธิบายการแก้ไขนี้ในรูปแบบนี้เท่านั้น:

**กฎไวยากรณ์:** [ชื่อกฎ เช่น Past Tense, Subject-Verb Agreement]

**ทำไมถึงผิด:** [อธิบายว่าทำไมคำเดิมถึงผิด 1-2 ประโยค]

**ทำไมถึงถูก:** [อธิบายว่าทำไมคำที่แก้แล้วถึงถูกต้อง 1-2 ประโยค]

**ตัวอย่าง:** [ยกตัวอย่างประโยคที่ใช้กฎเดียวกัน]""".strip()

            # ✅ เรียก Gemini พร้อม system_instruction (Role)
            response = self.gemini_client.models.generate_content(
                model=self.working_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )

            return (
                response.text if response.text
                else self._get_offline_explanation(change)
            )

        except Exception as e:
            print(f"⚠️ Gemini error: {e}")
            return self._get_offline_explanation(change)

    # ══════════════════════════════════════
    # Offline Explanation (Fallback)
    # ══════════════════════════════════════

    def _get_offline_explanation(self, change: dict) -> str:
        """อธิบายแบบ Offline ไม่ต้องใช้ Gemini"""
        orig = change["original"].lower().strip()
        corr = change["corrected"].lower().strip()

        # ค้นหาใน GRAMMAR_RULES
        key = (orig, corr)
        if key in GRAMMAR_RULES:
            rule, change_str, why, example = GRAMMAR_RULES[key]
            return (
                f"**กฎไวยากรณ์:** {rule}\n\n"
                f"**ทำไมถึงผิด:** "
                f"คำว่า '{change['original']}' {why}\n\n"
                f"**ทำไมถึงถูก:** "
                f"คำว่า '{change['corrected']}' "
                f"เป็นรูปแบบที่ถูกต้องตามกฎ {rule}\n\n"
                f"**ตัวอย่าง:** {example}"
            )

        # Fallback: สร้างคำอธิบายจาก error type
        error_type = change.get("type", "grammar")
        type_explanations = {
            "capitalization": (
                "ตัวพิมพ์ใหญ่-เล็กไม่ถูกต้อง",
                "ต้องใช้ตัวพิมพ์ใหญ่ตามกฎภาษาอังกฤษ"
            ),
            "contraction": (
                "การเขียนคำย่อ (contraction) ไม่ถูกต้อง",
                "คำย่อต้องมี apostrophe (') ในตำแหน่งที่ถูกต้อง"
            ),
            "article": (
                "การใช้ article (a/an/the) ไม่ถูกต้อง",
                "ต้องเลือก article ที่เหมาะกับคำนามที่ตามมา"
            ),
            "spelling": (
                "สะกดคำผิด",
                "ต้องใช้การสะกดที่ถูกต้อง"
            ),
            "verb_form": (
                "รูปกริยาไม่ถูกต้อง",
                "ต้องใช้รูปกริยาที่ถูกต้องตาม tense และประธาน"
            ),
            "missing_word": (
                "ขาดคำที่จำเป็น",
                "ต้องเพิ่มคำเพื่อให้ประโยคสมบูรณ์"
            ),
            "extra_word": (
                "มีคำเกินที่ไม่จำเป็น",
                "ต้องตัดคำที่ไม่จำเป็นออก"
            ),
            "grammar": (
                "ไวยากรณ์ไม่ถูกต้อง",
                "ต้องแก้ไขให้ตรงตามกฎไวยากรณ์"
            ),
        }

        why_wrong, why_right = type_explanations.get(
            error_type,
            ("ไวยากรณ์ไม่ถูกต้อง", "ต้องแก้ไขให้ตรงตามกฎไวยากรณ์")
        )

        return (
            f"**กฎไวยากรณ์:** "
            f"{error_type.replace('_', ' ').title()}\n\n"
            f"**ทำไมถึงผิด:** "
            f"'{change['original']}' — {why_wrong}\n\n"
            f"**ทำไมถึงถูก:** "
            f"'{change['corrected']}' — {why_right}\n\n"
            f"**ตัวอย่าง:**\n"
            f"❌ ...{change['original']}...\n"
            f"✅ ...{change['corrected']}..."
        )

    # ══════════════════════════════════════
    # Full Check (All-in-One)
    # ══════════════════════════════════════

    def full_check(self, text: str) -> dict:
        """
        ตรวจไวยากรณ์แบบครบ pipeline:
        Input → Gramformer + HappyTransformer → Ensemble →
        Differences → Gemini Explain → Output
        """
        original = text.strip()

        # Step 1: Ensemble Correction
        ensemble = self.correct_grammar(original)
        corrected = ensemble["corrected"]

        # Step 2: Find Differences
        differences = self.find_differences(original, corrected)

        # Step 3: Explain
        explanations = self.explain_with_gemini(
            original, corrected, differences, ensemble
        )

        is_correct = (
            original.lower().strip() == corrected.lower().strip()
        )

        return {
            "original": original,
            "corrected": corrected,
            "is_correct": is_correct,
            "differences": differences,
            "explanations": explanations,
            "ensemble": {
                "source": ensemble["source"],
                "confidence": ensemble["confidence"],
                "gramformer_result": ensemble["gramformer_result"],
                "happy_result": ensemble["happy_result"],
            }
        }


# ======================================
# Quick Test
# ======================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Grammar Checker Engine v3.1")
    print("  Gramformer + HappyTransformer + Gemini (with Role)")
    print("=" * 60)

    engine = GrammarCheckerEngine()

    # แสดงสถานะ
    print(f"\n📊 Engine Status:")
    print(f"  🔹 Gramformer: {'✅' if engine.gramformer else '❌'}")
    print(f"  🔹 HappyTransformer: {'✅' if engine.happy_tt else '❌'}")
    print(f"  🔹 Gemini: {engine.working_model or '❌ Offline mode'}")
    print(f"  🔹 Role: {'✅ Set' if SYSTEM_INSTRUCTION else '❌ Not set'}")

    test_sentences = [
        "I has a apple.",
        "She dont like swimming.",
        "They was going to the store yesterday.",
        "He goed to school.",
        "Me and him went to the park.",
        "I think your right about that.",
        "The children plays in the garden.",
        "She can sings very good.",
        "I have went to the store.",
        "He dont knows the answer.",
    ]

    print("\n" + "=" * 60)
    print("  Test Results")
    print("=" * 60)

    for sentence in test_sentences:
        result = engine.full_check(sentence)

        print(f"\n{'─' * 50}")
        print(f"📝 Input:     {result['original']}")
        print(f"✅ Corrected: {result['corrected']}")
        print(
            f"📊 Source:    {result['ensemble']['source']} "
            f"({result['ensemble']['confidence']})"
        )
        print(
            f"🔹 Gramformer:       "
            f"{result['ensemble']['gramformer_result']}"
        )
        print(
            f"🔹 HappyTransformer: "
            f"{result['ensemble']['happy_result']}"
        )

        if result['differences']:
            print(f"📌 Changes ({len(result['differences'])}):")
            for diff in result['differences']:
                print(
                    f"   • '{diff['original']}' → "
                    f"'{diff['corrected']}' [{diff['type']}]"
                )

        if result['explanations']:
            print(f"💬 Explanations:")
            for exp in result['explanations']:
                # แสดงแค่ 2 บรรทัดแรก
                lines = exp['explanation'].split('\n')
                preview = lines if lines else ""
                print(f"   📖 {preview[:80]}...")

    print(f"\n{'=' * 60}")
    print("  Done!")
    print(f"{'=' * 60}")