import json
import requests
import os
import logging
from typing import Dict, Any

# Cấu hình AnkiConnect
ANKI_URL = "http://localhost:8765"
ANKI_VERSION = 6

def invoke(action: str, **params):
    """Gửi yêu cầu tới AnkiConnect."""
    request_json = {'action': action, 'params': params, 'version': ANKI_VERSION}
    try:
        response = requests.post(ANKI_URL, json=request_json).json()
        if 'error' in response and response['error']:
            # Bỏ qua thông báo lỗi nếu thẻ bị trùng (duplicate)
            if "duplicate" not in str(response['error']):
                logging.warning(f"Anki Warning: {response['error']}")
            return None
        return response.get('result')
    except Exception as e:
        logging.error(f"Lỗi kết nối Anki: {e}")
        return None

def get_valid_model_name():
    """Tìm tên loại thẻ hợp lệ trong Anki của người dùng."""
    model_names = invoke('modelNames')
    if not model_names: return None
    # Ưu tiên các loại thẻ cơ bản phổ biến
    for name in ["Basic", "Cơ bản", "Standard", "Plain"]:
        if name in model_names: return name
    return model_names[0]

def anki_generator_node(state: Dict[str, Any]):
    """
    LANGGRAPH NODE: Đẩy dữ liệu flashcards từ state vào Anki.
    Node này nhận kết quả JSON từ bước xử lý Slide/Tài liệu.
    """
    print("--- 📥 ĐANG ĐẨY THẺ VÀO ANKI ---")
    
    # 1. Lấy dữ liệu từ Answer (Chuỗi JSON do Gemini tạo ra ở Node trước)
    raw_content = state.get("answer", "")
    
    try:
        # Nếu Node trước trả về chuỗi JSON, ta cần parse nó thành List
        if isinstance(raw_content, str):
            cards_data = json.loads(raw_content)
        else:
            cards_data = raw_content
    except Exception as e:
        return {"answer": f"❌ Lỗi định dạng: AI không trả về JSON hợp lệ để tạo Anki. ({str(e)})"}

    if not cards_data or not isinstance(cards_data, list):
        return {"answer": "⚠️ Không tìm thấy danh sách flashcard nào trong nội dung phản hồi."}

    # 2. Kiểm tra kết nối tới ứng dụng Anki Desktop
    if not invoke('version'):
        return {"answer": "❌ Thất bại: Agent không thể kết nối tới Anki. Vui lòng mở Anki Desktop và cài đặt AnkiConnect."}

    # 3. Xác định tên bộ bài (Deck)
    # Lấy tên file từ input_data để đặt tên Deck cho chuyên nghiệp
    file_path = state.get("input_data", "StudyAgent_Deck")
    deck_name = os.path.basename(file_path).split('.')[0] if os.path.isfile(file_path) else "Study_Agent_Flashcards"
    
    invoke('createDeck', deck=deck_name)

    # 4. Tìm loại thẻ (Note Type) tương thích
    model_name = get_valid_model_name()
    if not model_name:
        return {"answer": "❌ Lỗi: Không tìm thấy loại thẻ (Note Type) nào trong Anki của bạn."}

    # 5. Tự động ánh xạ các trường (Fields) của thẻ
    model_fields = invoke('modelFieldNames', modelName=model_name) or ["Front", "Back"]
    
    notes_payload = []
    for card in cards_data:
        # Khớp dữ liệu từ JSON của AI với các trường trong Anki
        question = card.get('question') or card.get('front') or "No Question"
        answer = card.get('answer') or card.get('back') or "No Answer"
        
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {
                model_fields[0]: question,
                model_fields[1]: answer
            },
            "options": {"allowDuplicate": False},
            "tags": ["study-agent", "ai-generated"]
        }
        notes_payload.append(note)

    # 6. Thực hiện đẩy thẻ hàng loạt (Batch Add)
    results = invoke('addNotes', notes=notes_payload)
    
    added_count = 0
    if results:
        added_count = len([x for x in results if x is not None])

    # Trả về thông báo cuối cùng để hiển thị trên UI
    final_msg = f"✨ Thành công: Đã thêm {added_count}/{len(cards_data)} thẻ vào bộ bài '{deck_name}'."
    print(f"DEBUG: {final_msg}")
    
    return {"answer": final_msg}