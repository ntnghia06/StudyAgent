import os
import json
from dotenv import load_dotenv

# Import từ các file của bạn
from src.agents.nodes.router import router_node

# Load API Key từ file .env (nếu có)
load_dotenv()

def run_test():
    # 1. Khởi tạo State ban đầu theo AgentState bạn đã định nghĩa
    # Giả sử người dùng dán một link YouTube và yêu cầu tóm tắt
    state = {
        "input_data": "https://www.youtube.com/watch?v=abcdefgh",
        "query": "Tóm tắt video",
        "input_type": "",      # Đang trống để Router điền vào
        "user_intent": "",     # Đang trống để Router điền vào
        "context": "",
        "summary": "",
        "answer": ""
    }

    print("=== STATE TRƯỚC KHI CHẠY NODE ===")
    print(json.dumps(state, indent=4, ensure_ascii=False))

    # 2. Thực thi Node (Hàm này sẽ gọi get_router_chain bên trong)
    # Lưu ý: Đảm bảo đã set export GEMINI_API_KEY='...' trong terminal
    try:
        # Gọi hàm router_node bạn đã viết
        update = router_node(state)

        # 3. Cập nhật State (Mô phỏng cơ chế của LangGraph)
        state.update(update)

        print("\n=== STATE SAU KHI CẬP NHẬT TỪ AI (PREDICTION) ===")
        print(json.dumps(state, indent=4, ensure_ascii=False))
        
        # Kiểm tra logic
        if state["input_type"] and state["user_intent"]:
            print("\n✅ Test thành công: AI đã phân loại được dữ liệu!")
        else:
            print("\n⚠️ Cảnh báo: AI trả về kết quả rỗng hoặc không đúng định dạng.")

    except Exception as e:
        print(f"\n❌ Lỗi khi chạy test: {e}")

if __name__ == "__main__":
    run_test()