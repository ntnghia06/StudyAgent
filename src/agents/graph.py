from langgraph.graph import StateGraph, END
import os
import sys
# Import các hàm node bạn đã viết
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if project_root not in sys.path:
    sys.path.append(project_root)

from src.agents.state import AgentState
from src.agents.nodes.router import router_node
from src.agents.nodes.slide import slide_processor_node
from src.agents.nodes.rag import get_answer
from src.agents.nodes.tools import anki_generator_node
# 1. Khởi tạo Graph với cấu trúc State

workflow = StateGraph(AgentState)

# 2. Thêm các Node vào Graph
workflow.add_node("router", router_node)
workflow.add_node("process_slide", slide_processor_node)
workflow.add_node("rag", get_answer)
workflow.add_node("anki_generator", anki_generator_node)

# 3. Thiết lập các Cạnh (Edges) và Điều kiện rẽ nhánh

# Điểm bắt đầu luôn là Router
workflow.set_entry_point("router")

# --- LUỒNG 1: Rẽ nhánh từ Router dựa trên input_type ---
workflow.add_conditional_edges(
    "router",
    lambda x: x["input_type"],
    {
        "RAG": "rag",
        "SLIDE": "process_slide",
    }
)


workflow.add_conditional_edges(
    "process_slide",
    lambda x: x["user_intent"],
    {
        "FLASHCARD": "anki_generator",
    }
)

# --- TẤT CẢ CÁC ĐƯỜNG ĐỀU DẪN VỀ KẾT THÚC ---
workflow.add_edge("rag", END)
workflow.add_edge("anki_generator", END)

# 4. Biên dịch Graph
app = workflow.compile()

from src.agents.graph import app

def visualize_graph():
    try:
        # Lấy sơ đồ dưới dạng bytes (sử dụng Mermaid.ink API mặc định)
        graph_png = app.get_graph().draw_mermaid_png()
        
        # Lưu vào file
        with open("graph_schema.png", "wb") as f:
            f.write(graph_png)
        print("🎨 Đã xuất sơ đồ Graph tại: graph_schema.png")
    except Exception as e:
        print(f"❌ Không thể xuất ảnh: {e}")
        print("💡 Gợi ý: Kiểm tra kết nối internet hoặc cài đặt pygraphviz.")

if __name__ == "__main__":
    visualize_graph()