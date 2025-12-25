import os
import sys

# Xử lý đường dẫn để Python nhận diện thư mục 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from src.database.qdrant_manager import get_qdrant_client, get_embedding_model

COLLECTION_NAME = "study_materials"

def add_to_vector_db(chunks: list, metadatas: list = None):
    """Lưu các đoạn văn bản vào Qdrant."""
    client = get_qdrant_client()
    embeddings = get_embedding_model()
    
    if not client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"📡 Đang tạo collection mới: {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384, # Kích thước vector của SBERT paraphrase-multilingual là 384
                distance=Distance.COSINE
            ),
        )

    # Khởi tạo Vector Store theo chuẩn hiện đại
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )
    
    vector_store.add_texts(texts=chunks, metadatas=metadatas)
    print(f"✅ Đã lưu {len(chunks)} đoạn kiến thức vào Qdrant.")

def query_vector_db(query: str, k: int = 3):
    """Tìm kiếm nội dung liên quan nhất."""
    client = get_qdrant_client()
    embeddings = get_embedding_model()
    
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )
    
    return vector_store.similarity_search(query, k=k)

if __name__ == "__main__":
    # Test thật với dữ liệu nhỏ
    texts = ["AI Agent là tương lai của học tập.", "Hệ thống này dùng Qdrant."]
    print("🚀 Đang chạy Integration Test...")
    add_to_vector_db(texts)
    
    res = query_vector_db("Tương lai học tập", k=1)
    if res:
        print(f"🔍 Kết quả tìm được: {res[0].page_content}")