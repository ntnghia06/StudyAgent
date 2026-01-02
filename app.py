import streamlit as st
import os
import sys
import time
from streamlit.runtime import exists

# --- 1. TỰ KÍCH HOẠT STREAMLIT ---
if __name__ == "__main__":
    if not exists():
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())

# --- 2. CẤU TRÌNH HỆ THỐNG ---
# Lấy đường dẫn tuyệt đối của thư mục chứa app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from src.agents.graph import app 
    from src.agents.state import AgentState
except ImportError:
    st.error("❌ Không tìm thấy thư mục 'src'. Hãy đảm bảo app.py nằm cùng cấp với folder src.")
    st.stop()

# --- 3. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Study AI Agent", page_icon="🎓", layout="wide")

# --- 4. KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] 
if "input_data" not in st.session_state:
    st.session_state.input_data = ""

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("📁 NGUỒN TÀI LIỆU")
    url_input = st.text_input("Link tài liệu:", value=st.session_state.input_data)
    st.session_state.input_data = url_input
    
    if st.button("🗑️ Xóa lịch sử"):
        st.session_state.messages = []
        pdf_file = os.path.join(BASE_DIR, "SUMMARY.pdf")
        if os.path.exists(pdf_file): 
            os.remove(pdf_file)
        st.rerun()

# --- 6. GIAO DIỆN CHAT ---
st.title("🎓 STUDY AI AGENT")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. XỬ LÝ NHẬP LIỆU ---
query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if not st.session_state.input_data:
        st.warning("⚠️ Vui lòng nhập link tài liệu!")
    else:
        with st.chat_message("assistant"):
            answer_placeholder = st.empty()
            
            with st.status("🤖 Agent đang thực thi...", expanded=True) as status:
                inputs: AgentState = {
                    "input_data": st.session_state.input_data,
                    "query": query,
                    "input_type": "", "user_intent": "", "quantity": 0,
                    "context": "", "summary": "", "answer": ""
                }

                final_answer = ""
                current_intent = "" 

                try:
                    for output in app.stream(inputs):
                        for node_name, state_update in output.items():
                            st.write(f"✅ Đã xong bước: **{node_name.upper()}**")
                            
                            if "user_intent" in state_update:
                                current_intent = state_update["user_intent"]
                            if "answer" in state_update:
                                final_answer = state_update["answer"]
                    
                    # Chờ 0.5 giây để đảm bảo hệ điều hành đã đóng file hoàn toàn
                    time.sleep(0.5) 
                    status.update(label="✨ Hoàn tất!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Lỗi thực thi: {str(e)}")

            if final_answer:
                if "❌" in final_answer or "⚠️" in final_answer:
                    st.error(final_answer) # Hiện màu đỏ nếu là lỗi
                else:
                    st.success(final_answer)

            # --- KIỂM TRA USER INTENT VỚI ĐƯỜNG DẪN TUYỆT ĐỐI ---
            if current_intent == "SUMMARY":
                # Luôn tìm file trong cùng thư mục với file app.py này
                pdf_path = os.path.join(BASE_DIR, "SUMMARY.pdf")

                if os.path.exists(pdf_path):
                    st.success("✅ Đã tạo xong bản tóm tắt PDF.")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Tải bản tóm tắt (PDF)",
                            data=f.read(),
                            file_name="SUMMARY.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error(f"❌ Không tìm thấy file tại: {pdf_path}")
                    st.write("Vui lòng kiểm tra lại Node tạo PDF trong Graph.")

            elif current_intent == "FLASHCARD":
                # Kiểm tra xem trong câu trả lời có chứa dấu hiệu lỗi không
                if "ERROR_ANKI" in final_answer:
                    st.error("❌ Không thể đẩy Flashcard lên Anki!")
                    st.warning("Mẹo: Hãy đảm bảo bạn đã mở App Anki và cài đặt Add-on AnkiConnect.")
                    st.session_state.messages.append({"role": "assistant", "content": "Lỗi kết nối Anki."})
                elif final_answer == "SUCCESS" or not final_answer:
                    # Chỉ hiện thành công nếu không có lỗi
                    st.info("✅ Đã tạo bộ Flashcard thành công trong hệ thống!")
                    st.session_state.messages.append({"role": "assistant", "content": "Đã tạo Flashcard thành công."})

            else:
                if final_answer:
                    answer_placeholder.markdown(final_answer)
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})