import streamlit as st
import os
import sys

# Mẹo: Thêm dòng này để đảm bảo Streamlit tìm thấy folder 'src' 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

try:
    from src.agents.graph import app  # Import graph đã compiled
    from src.agents.state import AgentState
except ImportError as e:
    st.error(f"❌ Không tìm thấy thư mục code. Hãy đảm bảo bạn đặt file app.py ở thư mục gốc chứa folder 'src'. Lỗi: {e}")
    st.stop()

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Study AI Agent", page_icon="🎓", layout="wide")

# CSS để giao diện gọn gàng hơn
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 HỆ THỐNG STUDY AI AGENT")
st.caption("Trợ lý ảo hỗ trợ học tập từ PDF, Docx và YouTube")
st.markdown("---")

# --- KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "input_data" not in st.session_state:
    st.session_state.input_data = ""

# --- SIDEBAR: CẤU HÌNH ĐẦU VÀO ---
with st.sidebar:
    st.header("📁 Cấu hình nguồn")
    input_source = st.text_input(
        "Nhập đường dẫn File hoặc Link YouTube:",
        placeholder="https://www.youtube.com/watch?v=...",
        value=st.session_state.input_data
    )
    
    if input_source != st.session_state.input_data:
        st.session_state.input_data = input_source
        st.toast("Đã cập nhật nguồn dữ liệu!", icon="✅")
    
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- HIỂN THỊ LỊCH SỬ CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- XỬ LÝ NHẬP LIỆU ---
query = st.chat_input("Hỏi tôi bất cứ điều gì về tài liệu này...")

if query:
    # 1. Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Kiểm tra nguồn dữ liệu
    if not st.session_state.input_data:
        with st.chat_message("assistant"):
            st.warning("⚠️ Bạn chưa nhập link tài liệu hoặc video ở thanh bên (Sidebar)!")
    else:
        # 3. Gọi Agent xử lý
        with st.chat_message("assistant"):
            answer_placeholder = st.empty()
            
            with st.status("🤖 AI đang suy nghĩ...", expanded=True) as status:
                # Khởi tạo State ban đầu
                inputs = {
                    "input_data": st.session_state.input_data,
                    "query": query,
                    "input_type": "",
                    "user_intent": "",
                    "quantity": 0,
                    "context": "",
                    "summary": "",
                    "answer": ""
                }

                final_answer = ""
                
                try:
                    # Chạy Graph (Streaming)
                    for output in app.stream(inputs):
                        for node_name, state_update in output.items():
                            st.write(f"⚙️ **Bước:** `{node_name.upper()}`")
                            
                            # Cập nhật kết quả cuối cùng nếu có
                            if isinstance(state_update, dict) and "answer" in state_update:
                                if state_update["answer"]:
                                    final_answer = state_update["answer"]
                    
                    status.update(label="✅ Đã xử lý xong!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Lỗi xử lý!", state="error")
                    st.error(f"Đã xảy ra lỗi trong quá trình chạy Agent: {e}")

            # 4. Hiển thị kết quả cuối cùng
            if final_answer:
                answer_placeholder.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            elif not final_answer:
                st.info("Agent đã chạy nhưng không trả về câu trả lời nội dung.")