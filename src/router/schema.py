from pydantic import BaseModel, Field
from typing import Optional, List

class AnalysisPlan(BaseModel):
    agent_type: str = Field(
        description="Loại Agent cần xử lý: 'VIDEO', 'SLIDE', 'SPEECH', hoặc 'RAG'."
    )
    output_format: str = Field(
        description="Định dạng kết quả mong muốn: 'FLASHCARD', 'SUMMARY', hoặc 'QA'."
    )
    quantity: int = Field(
        description="Số lượng thẻ nếu chọn FLASHCARD."
    )
    reasoning: str = Field(
        description="Giải thích ngắn gọn tại sao lại chọn Agent và định dạng này."
    )