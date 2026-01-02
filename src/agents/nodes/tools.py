import json
import requests
import os
import logging
from typing import Dict, Any

# Cấu hình AnkiConnect
ANKI_URL = "http://localhost:8765"
ANKI_VERSION = 6

def invoke(action: str, **params):
    """Gửi yêu cầu tới AnkiConnect và xử lý lỗi kết nối."""
    request_json = {'action': action, 'params': params, 'version': ANKI_VERSION}
    try:
        # Thêm timeout=3 để tránh treo ứng dụng nếu Anki không phản hồi
        response = requests.post(ANKI_URL, json=request_json, timeout=3).json()
        if 'error' in response and response['error']:
            # Bỏ qua thông báo lỗi nếu thẻ bị trùng (duplicate)
            if "duplicate" not in str(response['error']):
                logging.warning(f"Anki Warning: {response['error']}")
            return {"error_detail": response['error']} # Trả về chi tiết lỗi
        return response.get('result')
    except Exception as e:
        logging.error(f"Lỗi kết nối Anki: {e}")
        return "CONNECTION_FAILED" # Trả về tín hiệu lỗi kết nối

def get_valid_model_name():
    """Tìm tên loại thẻ hợp lệ trong Anki của người dùng."""
    model_names = invoke('modelNames')
    if not model_names or model_names == "CONNECTION_FAILED": return None
    # Ưu tiên các loại thẻ cơ bản phổ biến
    for name in ["Basic", "Cơ bản", "Standard", "Plain"]:
        if name in model_names: return name
    return model_names[0]

def anki_generator_node(state: Dict[str, Any]):
    """
    LANGGRAPH NODE: Đẩy dữ liệu flashcards từ state vào Anki.
    """
    print("--- 📥 ĐANG ĐẨY THẺ VÀO ANKI ---")
    
    # 1. Lấy dữ liệu từ Answer (Chuỗi JSON do Gemini tạo ra ở Node trước)
    raw_content = state.get("answer", "")
    
    try:
        if isinstance(raw_content, str):
            cards_data = json.loads(raw_content)
        else:
            cards_data = raw_content
    except Exception as e:
        return {"answer": f"❌ Lỗi định dạng: AI không trả về JSON hợp lệ. ({str(e)})"}

    if not cards_data or not isinstance(cards_data, list):
        return {"answer": "⚠️ Không tìm thấy danh sách flashcard nào để xử lý."}

    # 2. Kiểm tra kết nối tới ứng dụng Anki Desktop
    version_check = invoke('version')
    if version_check == "CONNECTION_FAILED" or version_check is None:
        return {"answer": "❌ Thất bại: Không thể kết nối tới Anki. Hãy MỞ APP ANKI và cài đặt AnkiConnect."}

    # 3. Xác định tên bộ bài (Deck)
    file_path = state.get("input_data", "StudyAgent_Deck")
    deck_name = os.path.basename(file_path).split('.')[0] if os.path.isfile(file_path) else "Study_Agent_Flashcards"
    
    if invoke('createDeck', deck=deck_name) == "CONNECTION_FAILED":
        return {"answer": "❌ Lỗi: Mất kết nối với Anki khi đang tạo bộ bài."}

    # 4. Tìm loại thẻ (Note Type) tương thích
    model_name = get_valid_model_name()
    if not model_name:
        return {"answer": "❌ Lỗi: Không tìm thấy loại thẻ (Note Type) phù hợp trong Anki."}

    # 5. Tự động ánh xạ các trường (Fields) của thẻ
    model_fields = invoke('modelFieldNames', modelName=model_name)
    if model_fields == "CONNECTION_FAILED" or not model_fields:
        model_fields = ["Front", "Back"]
    
    notes_payload = []
    for card in cards_data:
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
    
    if results == "CONNECTION_FAILED":
        return {"answer": "❌ Lỗi: Mất kết nối đột ngột khi đang đẩy thẻ lên Anki."}
    
    if isinstance(results, dict) and "error_detail" in results:
        return {"answer": f"❌ Anki báo lỗi: {results['error_detail']}"}

    added_count = 0
    if results:
        added_count = len([x for x in results if x is not None])

    final_msg = f"✨ Thành công: Đã thêm {added_count}/{len(cards_data)} thẻ vào bộ bài '{deck_name}'."
    return {"answer": final_msg}