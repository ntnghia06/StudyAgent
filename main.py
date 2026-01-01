import os
from src.agents.graph import app # Import graph đã compiled
from src.agents.state import AgentState
def main():
    print("=== 🎓 HỆ THỐNG STUDY AI AGENT ĐANG SẴN SÀNG ===")
    print("Hướng dẫn: Nhập câu hỏi hoặc đường dẫn file (PDF/DOCX). Nhập 'exit' để thoát.")
    
    while True:
        # 1. Nhận đầu vào từ người dùng
        user_input = r"https://www.youtube.com/watch?v=0S0LvVmn_xU"
        query = input("\n👤 Bạn: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'thoát']:
            print("👋 Tạm biệt!")
            break
            
        if not user_input:
            continue

        # 2. Khởi tạo State ban đầu
        # LangGraph sẽ tự động đẩy state này vào Node đầu tiên (Router)
        inputs: AgentState = {
            "input_data": user_input,   
            "query": query,
            "input_type": "" ,  
            "user_intent": "" ,  
            "quantity": 0,
            "context": "" ,   
            "summary": "" ,        
            "answer": ""         
        }

        print("\n🤖 Agent đang xử lý...")
        print("-" * 30)

        # 3. Chạy Graph và theo dõi luồng dữ liệu (Streaming)
            # stream giúp ta nhìn thấy kết quả ngay khi mỗi Node chạy xong
        for output in app.stream(inputs):
            for node_name, state_update in output.items():
                print(f"📍 Đã xong bước: [{node_name.upper()}]")
                final_state = state_update
                # Log nhẹ các thông tin quan trọng để debug
                if "input_type" in state_update:
                    print(f"   📂 Loại đầu vào: {state_update['input_type']}")
                if "user_intent" in state_update:
                    print(f"   🎯 Ý định: {state_update['user_intent']}")
            
        # 4. Lấy kết quả cuối cùng sau khi Graph kết thúc
        # Ta gọi invoke một lần nữa hoặc lấy state cuối từ stream
        #final_state = app.invoke(inputs)
            
        print("\n--- 🏁 KẾT QUẢ CUỐI CÙNG ---")
        print(final_state["answer"])
        print("-" * 30)
        break


if __name__ == "__main__":
    main()