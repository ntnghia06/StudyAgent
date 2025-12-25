import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if project_root not in sys.path:
    sys.path.append(project_root)

import google.generativeai as genai
import os
import time
import json
from config import GEMINI_API_KEY

def process_slide(file_path: str, plan: dict):

    genai.configure(api_key=GEMINI_API_KEY)
    
    print(f"📤 Đang upload file: {os.path.basename(file_path)}...")
    doc_file = genai.upload_file(path=file_path)
    
    while doc_file.state.name == "PROCESSING":
        print("⏳ Gemini đang phân tích tài liệu...")
        time.sleep(2)
        doc_file = genai.get_file(doc_file.name)
    
    print("✅ Phân tích xong. Đang tạo nội dung...")
    
    # 1. Tải tài liệu lên Gemini File API
    doc_file = genai.upload_file(path=file_path)
    
    # Đợi tài liệu được xử lý xong trên server
    while doc_file.state.name == "PROCESSING":
        time.sleep(1)
        doc_file = genai.get_file(doc_file.name)

    # 2. Xây dựng Prompt và Schema dựa trên yêu cầu từ Router
    output_format = plan.get('output_format', 'SUMMARY')
    quantity = plan.get('quantity', 5)

    if output_format == "FLASHCARD":
        system_instruction = (
            f"Bạn là chuyên gia soạn thảo học liệu. Hãy trích xuất {quantity} kiến thức quan trọng nhất từ tài liệu này để tạo flashcards."
        )
        # Ép kiểu JSON cho Flashcard
        prompt = "Trả về danh sách JSON array: [{\"question\": \"...\", \"answer\": \"...\"}]"
        
    elif output_format == "SUMMARY":
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

    # 3. Gọi Gemini API với cấu hình JSON Mode
    model = genai.GenerativeModel("gemini-2.5-flash") # Gemini-2.5-Flash tối ưu cho tài liệu dài
    
    response = model.generate_content(
        [doc_file, system_instruction, prompt],
        generation_config={"response_mime_type": "application/json"}
    )
    
    # 4. Dọn dẹp tệp trên Cloud để bảo mật
    genai.delete_file(doc_file.name)
    
    return json.loads(response.text)


def slide_processor_node(state: dict):
    """
    Node này kết nối Agent State với hàm process_slide của bạn.
    """
    print(f"--- ĐANG XỬ LÝ SLIDE THEO Ý ĐỊNH: {state.get('user_intent')} ---")
    
    # 1. Lấy dữ liệu từ State
    file_path = state.get("input_data")  # Đường dẫn file đã được Router xác định
    output_format = state.get("user_intent", "summary")
    quantity = state.get("quantity", 5)
     
    plan = {
        "output_format": output_format,
        "quantity": quantity  # Số lượng flashcard mong muốn
    }

    # 3. Gọi hàm xử lý chính (giữ nguyên logic bạn đã viết)
    try:
        result_json = process_slide(file_path, plan)
        
        # 4. Cập nhật kết quả vào State
        # Lưu kết quả JSON vào 'answer' dưới dạng string đẹp để hiển thị
        return {
            "answer": json.dumps(result_json, ensure_ascii=False, indent=2),
            "context": [f"Tài liệu gốc: {file_path}"]
        }
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý Slide: {e}")
        return {"answer": f"Có lỗi xảy ra khi đọc tài liệu: {str(e)}"}

