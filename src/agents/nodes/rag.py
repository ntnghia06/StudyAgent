import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if project_root not in sys.path:
    sys.path.append(project_root)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.database.vector_store import query_vector_db
from dotenv import load_dotenv
load_dotenv()

# 1. Cấu hình Model Gemini
# Đảm bảo bạn đã đặt GOOGLE_API_KEY trong biến môi trường
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3, # Thấp để trả lời chính xác, tránh "ảo giác"
)

# 2. Xây dựng Prompt mẫu (Instruction)
SYSTEM_PROMPT = """
Bạn là một Trợ lý Học tập thông minh (Study Agent). 
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng dựa trên các tài liệu đã được cung cấp dưới đây.

YÊU CẦU:
- Chỉ sử dụng thông tin trong phần "NGỮ CẢNH" để trả lời.
- Nếu không có thông tin trong ngữ cảnh, hãy nói "Xin lỗi, kiến thức này chưa có trong dữ liệu học tập của bạn".
- Trả lời ngắn gọn, súc tích và dễ hiểu theo phong cách học thuật.

NGỮ CẢNH:
{context}
"""

def get_answer(state: dict): 
    """Quy trình RAG: Trích xuất query từ state -> Tìm kiếm -> Trả lời."""
    
    # BƯỚC 0: Lấy chuỗi văn bản thực sự từ trong state ra
    # Trong AgentState của bạn, câu hỏi nằm ở trường "query"
    user_query = state.get("query", "") 
    
    # Kiểm tra nếu query trống (để tránh lỗi embedding)
    if not user_query:
        # Nếu chưa có query, có thể lấy từ input_data
        user_query = state.get("input_data", "")

    print(f"--- 🔍 ĐANG TÌM KIẾM CHO CÂU HỎI: {user_query} ---")

    # BƯỚC 1: Tìm kiếm tài liệu (Lúc này user_query chắc chắn là String)
    relevant_docs = query_vector_db(user_query, k=3)
    
    context = "\n".join([doc.page_content for doc in relevant_docs])
    
    if not context:
        return {"answer": "Tài liệu học tập của bạn hiện đang trống hoặc không có thông tin liên quan."}

    # BƯỚC 2: Tạo Prompt (Giữ nguyên logic của bạn)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}")
    ])
    
    # BƯỚC 3: Gọi AI tạo câu trả lời
    chain = prompt | llm
    response = chain.invoke({
        "context": context,
        "question": user_query # Truyền string vào đây
    })
    
    # BƯỚC 4: TRẢ VỀ bản cập nhật cho State (Dạng Dictionary)
    # LangGraph sẽ lấy giá trị này để cập nhật vào trường "answer" trong AgentState
    print(response.content)
    return {
        "answer": response.content,
        "context": context # Lưu luôn context vào state để tiện debug nếu cần
    }
