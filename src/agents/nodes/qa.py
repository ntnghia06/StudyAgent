import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if project_root not in sys.path:
    sys.path.append(project_root)


import numpy as np
import google.generativeai as genai
from typing import Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import model embedding từ manager của bạn
from database.qdrant_manager import get_embedding_model
from config import GEMINI_API_KEY

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)

def cosine_similarity(v1, v2):
    """Tính toán tương đồng Cosine giữa vector câu hỏi và mảng các vector chunks."""
    # Chuyển về numpy để tính toán ma trận cho nhanh
    v1 = np.array(v1)
    v2 = np.array(v2)
    
    dot_product = np.dot(v2, v1)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2, axis=1)
    
    return dot_product / (norm_v1 * norm_v2)

def qa_node(state: Dict[str, Any]):
    """
    NODE: Chunk text từ state -> Search cục bộ -> Gọi API trả lời.
    Input state: { "answer": "văn bản thô...", "query": "câu hỏi..." }
    """
    print("--- 🧠 ĐANG XỬ LÝ TRUY VẤN CỤC BỘ (NO-DB RAG) ---")
    
    # 1. Lấy dữ liệu đầu vào từ state
    raw_text = state.get("answer", "")
    query = state.get("query", "")
    if isinstance(raw_text, dict):
        # Nếu nó là JSON từ Gemini, thường văn bản nằm trong một key nào đó, 
        # hoặc ta convert toàn bộ sang string để chunk
        print("⚠️ Cảnh báo: raw_text đang là Dict, đang chuyển sang String...")
        # Cách 1: Lấy trường 'content' nếu có
        # raw_text = raw_text.get("content", str(raw_text)) 
        # Cách 2: Chuyển toàn bộ dict thành chuỗi JSON
        import json
        raw_text = json.dumps(raw_text, ensure_ascii=False)

    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"answer": "❌ Lỗi: Không có văn bản hợp lệ để xử lý."}
    if not raw_text or not query:
        return {"answer": "❌ Lỗi: Thiếu văn bản nguồn hoặc câu hỏi trong state."}

    # 2. Chunking: Chia nhỏ văn bản
    # Nghĩa nên để chunk_size vừa phải để Gemini nhận đủ ngữ cảnh
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(raw_text)
    
    if not chunks:
        return {"answer": "⚠️ Không thể chia nhỏ văn bản (văn bản quá ngắn hoặc rỗng)."}

    # 3. Local Semantic Search (Sử dụng model 384-dim của bạn)
    try:
        embeddings_model = get_embedding_model()
        
        # Chuyển query và toàn bộ chunks thành vectors
        query_vec = embeddings_model.embed_query(query)
        chunk_vecs = embeddings_model.embed_documents(chunks)
        
        # Tính điểm tương đồng và lấy top 3
        scores = cosine_similarity(query_vec, chunk_vecs)
        top_k_indices = np.argsort(scores)[-3:][::-1] # Lấy 3 cái cao nhất
        relevant_context = [chunks[i] for i in top_k_indices]
        
    except Exception as e:
        print(f"❌ Lỗi xử lý Vector: {e}")
        relevant_context = chunks[:3] # Fallback: lấy đại 3 đoạn đầu

    # 4. API Call: Gửi context và query lên Gemini
    context_combined = "\n\n---\n\n".join(relevant_context)
    
    system_instruction = (
        "Bạn là trợ lý học thuật chuyên sâu. Hãy trả lời câu hỏi dựa trên ngữ cảnh được cung cấp. "
        "Giữ nguyên thuật ngữ chuyên ngành tiếng Anh và dùng LaTeX cho công thức toán/tin."
    )
    
    prompt = f"""
    NGỮ CẢNH TRÍCH XUẤT:
    {context_combined}
    
    CÂU HỎI:
    {query}
    
    YÊU CẦU: Hãy phân tích dựa trên ngữ cảnh trên và trả lời chi tiết.
    """

    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3}
        )
        
        # Trả về state mới với câu trả lời cuối cùng
        return {
            "answer": response.text,
            "context": relevant_context # Lưu lại để debug hoặc hiển thị nguồn
        }
    except Exception as e:
        return {"answer": f"❌ Lỗi API: {str(e)}"}