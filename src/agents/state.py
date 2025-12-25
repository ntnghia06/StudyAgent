from typing import List, TypedDict, Optional

class AgentState(TypedDict):
    input_data: str      # URL, Path file, hoặc câu hỏi
    query: str
    input_type: str      # 'question', 'slide', 'youtube', 'speech'
    user_intent: str     # 'qa', 'summary', 'anki'
    quantity: int
    context: str   # Dữ liệu trích xuất được
    answer: str          # Kết quả cuối cùng