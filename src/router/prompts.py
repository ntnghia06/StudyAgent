from langchain_core.prompts import ChatPromptTemplate

# System Instruction để định hướng Gemini
ROUTER_SYSTEM_TEMPLATE = """
Bạn là một AI Orchestrator chuyên về học tập. Nhiệm vụ của bạn là:
1. Xác định loại tệp đính kèm (Video, Slide/PDF, Audio).
2. Phân tích yêu cầu người dùng để chọn Agent và định dạng đầu ra phù hợp nhất.
3. Nếu người dùng hỏi câu hỏi kiến thức thông thường, hãy chọn Agent 'RAG'.

{format_instructions}
"""

router_prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTER_SYSTEM_TEMPLATE),
    ("user", "{user_query}")
])