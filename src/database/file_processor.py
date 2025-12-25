import os
import sys
import fitz  # PyMuPDF
import docx  # python-docx
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Xử lý đường dẫn
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.database.vector_store import add_to_vector_db

def extract_text_from_word(docx_path):
    """Trích xuất toàn bộ văn bản từ file Word."""
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)

def ingest_document_to_qdrant(file_path: str):
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file tại: {file_path}")
        return

    file_extension = os.path.splitext(file_path)[1].lower()
    print(f"📄 Đang xử lý file {file_extension.upper()}: {os.path.basename(file_path)}...")
    
    all_chunks = []
    all_metadatas = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    try:
        # --- LUỒNG XỬ LÝ PDF ---
        if file_extension == ".pdf":
            with fitz.open(file_path) as doc:
                for i, page in enumerate(doc):
                    page_text = page.get_text().strip()
                    if not page_text: continue
                    
                    chunks = text_splitter.split_text(page_text)
                    for chunk in chunks:
                        all_chunks.append(chunk)
                        all_metadatas.append({
                            "source": os.path.basename(file_path),
                            "page": i + 1,
                            "type": "pdf"
                        })

        # --- LUỒNG XỬ LÝ WORD ---
        elif file_extension == ".docx":
            full_text = extract_text_from_word(file_path)
            if full_text:
                # Vì Word không có khái niệm trang vật lý như PDF, 
                # ta chia toàn bộ văn bản và để metadata page = 1 (hoặc theo section)
                chunks = text_splitter.split_text(full_text)
                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "source": os.path.basename(file_path),
                        "page": 1, 
                        "type": "docx"
                    })
        
        else:
            print(f"⚠️ Định dạng {file_extension} chưa được hỗ trợ.")
            return

    except Exception as e:
        print(f"❌ Lỗi khi đọc tài liệu: {e}")
        return

    # 3. Đẩy vào Database
    if all_chunks:
        print(f"🧬 Đã tạo {len(all_chunks)} chunks.")
        print(f"📡 Đang nạp vào Qdrant...")
        add_to_vector_db(chunks=all_chunks, metadatas=all_metadatas)
        print("✅ Quá trình nạp dữ liệu hoàn tất!")
    else:
        print("⚠️ Không trích xuất được văn bản nào.")

if __name__ == "__main__":
    # Test thử với file Word của bạn
    SAMPLE_WORD = r"D:\Study-Agent\data\thuvienhoclieu.com-GA-Lich-su-9-CTST-ca-nam-hay.docx"
    ingest_document_to_qdrant(SAMPLE_WORD)