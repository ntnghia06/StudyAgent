import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if project_root not in sys.path:
    sys.path.append(project_root)

import torch
import json
import gc
import time
from transformers import pipeline
import google.generativeai as genai
import static_ffmpeg
static_ffmpeg.add_paths()
# --- CẤU HÌNH ---
MODEL_ID = "openai/whisper-large-v3-turbo" # Bản v3-turbo rất nhanh và chính xác cho tiếng Việt
OUTPUT_DIR = "output_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Khởi tạo Pipeline (Dùng cơ chế Global để tránh load lại model nhiều lần)
_asr_pipeline = None

def get_asr_pipeline():
    global _asr_pipeline
    if _asr_pipeline is None:
        print(f"⏳ Đang khởi tạo model Whisper từ Hugging Face ({MODEL_ID})...")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        _asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            torch_dtype=torch_dtype,
            device=device,
            model_kwargs={"attn_implementation": "sdpa"} if torch.cuda.is_available() else {}
        )
    return _asr_pipeline

# --- CÁC HÀM XỬ LÝ ---

def _transcribe_with_transformers(file_path):
    """
    Sử dụng Transformers Pipeline với cơ chế chunking tự động.
    Giải quyết vấn đề tràn RAM và file âm thanh dài.
    """
    pipe = get_asr_pipeline()
    
    print(f"🎙️ Đang nhận diện giọng nói: {os.path.basename(file_path)}...")
    
    # generate_kwargs giúp định hướng ngôn ngữ và thuật ngữ
    # Lưu ý: Whisper của Transformers không nhận 'prompt' mạnh như Gemini 
    # nhưng 'return_timestamps' giúp track nội dung tốt hơn.
    result = pipe(
        file_path,
        chunk_length_s=30,      # Tự động cắt mỗi 30s để xử lý
        batch_size=8,           # Xử lý song song 8 đoạn (tăng tốc độ)
        return_timestamps=True,
        generate_kwargs={"language": "vietnamese", "task": "transcribe"}
    )
    
    return result["text"]

def process_audio_v2(file_path: str, plan: dict):
    """
    Pipeline: Audio -> Transformers (Text) -> Gemini (JSON)
    """
    # 1. Chuyển đổi âm thanh thành văn bản
    raw_text = _transcribe_with_transformers(file_path)
    
    # 2. Cấu hình Gemini
    from config import GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)
    
    output_format = plan.get('output_format', 'SUMMARY').upper()
    quantity = plan.get('quantity', 5)

    # System Prompt cho Gemini
    if output_format == "FLASHCARD":
        system_instruction = (
            f"Bạn là chuyên gia soạn thảo học liệu. Hãy trích xuất {quantity} kiến thức quan trọng nhất từ tài liệu này để tạo flashcards."
        )
        # Ép kiểu JSON cho Flashcard
        prompt = "Trả về danh sách JSON array: [{\"question\": \"...\", \"answer\": \"...\"}]"
    else:
        system_instruction = (
            "Bạn là trợ lý tóm tắt tài liệu. Hãy phân tích cấu trúc của slide và tạo bản tóm tắt theo từng chương hoặc mục lớn một cách logic."
        )
        # Ép kiểu JSON cho Summary
        prompt = """
        Trả về theo cấu trúc: 
        {
            "title": "Tiêu đề tài liệu",
            "outline": [{"heading": "Tên phần", "summary": "Nội dung tóm tắt"}],
            "conclusion": "Kết luận chính"
        }
        """

    # 3. Gọi Gemini xử lý text (Vì text đã có sẵn, không cần upload file lên File API trừ khi text quá dài)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Nếu text quá dài (> 30.000 từ), nên lưu ra file rồi upload. 
    # Nếu ngắn, gửi trực tiếp trong message:
    response = model.generate_content(
        [raw_text, system_instruction, prompt],
        generation_config={"response_mime_type": "application/json"}
    )

    return json.loads(response.text)

# --- LANGGRAPH NODE ---

def audio_processor_node(state: dict):
    print(f"\n--- [TRANSFORMERS AGENT] XỬ LÝ: {state.get('user_intent')} ---")
    
    file_path = state.get("input_data")
    if not file_path or not os.path.exists(file_path):
        return {"answer": "❌ Lỗi: Không tìm thấy file audio."}

    try:
        plan = {
            "output_format": state.get("user_intent", "SUMMARY"),
            "quantity": state.get("quantity", 5)
        }
        
        result_json = process_audio_v2(file_path, plan)
        
        # Lưu kết quả
        file_id = os.path.splitext(os.path.basename(file_path))[0]
        save_path = os.path.join(OUTPUT_DIR, f"{file_id}_{plan['output_format'].lower()}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result_json, f, ensure_ascii=False, indent=4)

        return {
            "answer": json.dumps(result_json, ensure_ascii=False, indent=2),
            "context": [f"Dùng model: {MODEL_ID}", f"Lưu tại: {save_path}"]
        }
    except Exception as e:
        return {"answer": f"Lỗi pipeline: {str(e)}"}
    
