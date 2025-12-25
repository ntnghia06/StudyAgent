from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
import os

# Sử dụng mô hình SBERT đa ngôn ngữ tốt nhất cho tiếng Việt
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def get_embedding_model():
    """Khởi tạo SBERT chạy cục bộ."""
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)

def get_qdrant_client():
    """Kết nối tới Qdrant (lưu database vào thư mục data/qdrant_storage)."""
    db_path = "data/qdrant_storage"
    if not os.path.exists("data"):
        os.makedirs("data")
    return QdrantClient(path=db_path)