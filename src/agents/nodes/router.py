import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from src.router.schema import AnalysisPlan
from src.router.prompts import router_prompt

def get_router_chain():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )
    
    parser = JsonOutputParser(pydantic_object=AnalysisPlan)
    
    chain = router_prompt.partial(format_instructions=parser.get_format_instructions()) | llm | parser
    return chain

def router_node(state: dict):
    
    # 1. Khởi tạo chain 
    router_chain = get_router_chain()
    
    # 2. Lấy dữ liệu từ state
    user_input = state.get("input_data", "")
    query = state.get("query", "")
    # 3. Chạy Chain để lấy kết quả từ AI
    # Kết quả trả về sẽ tuân theo schema AnalysisPlan (input_type, user_intent...)
    try:
        prediction = router_chain.invoke({"input_data": user_input, "user_query": query})
        print(f"prediction: {prediction}")
        # 4. Trả về bản cập nhật cho State
        return {
            "input_type": prediction.get("agent_type"),
            "user_intent": prediction.get("output_format"),
            "quantity": prediction.get("quantity")
        }
    except Exception as e:
        print(f"❌ Lỗi router: {e}")
        # Fallback logic nếu AI lỗi
        return {"input_type": "question", "user_intent": "qa"}