import re
import json
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from config import GEMINI_API_KEY

def get_youtube_video_id(url):
    """Sử dụng yt-dlp để lấy ID video một cách an toàn nhất"""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("id"), info.get("title")

def youtube_processor_node(state: dict):
    print(f"--- ĐANG XỬ LÝ YOUTUBE (FIX MISSING ARGUMENT) ---")
    video_url = state.get("input_data")
    user_intent = str(state.get("user_intent", "summary")).upper()
    quantity = state.get("quantity", 5)
    output_format = state.get("user_intent")

    try:
        # 1. Lấy Video ID và Tiêu đề
        video_id, video_title = get_youtube_video_id(video_url)
        if not video_id:
            raise Exception("Không thể trích xuất Video ID.")

        # 2. Lấy danh sách phụ đề (Truyền video_id vào đây)
        # SỬA LỖI TẠI ĐÂY: Sử dụng đúng phương thức list_transcripts
        transcript_list = YouTubeTranscriptApi().list(video_id)

        # iterate over all available transcripts
        for transcript in transcript_list:
            # fetch returns a FetchedTranscript object
            data = transcript.fetch()
            
            # Lấy nội dung văn bản từ các snippets
            full_text = " ".join([item.text for item in data.snippets])
        
            # Nếu bạn chỉ muốn lấy 1 bản duy nhất thì dùng break tại đây
            break

        # 3. Gửi cho Gemini xử lý
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        if output_format == "FLASHCARD":
            system_instruction = (
                f"Bạn là chuyên gia soạn thảo học liệu. Hãy trích xuất {quantity} kiến thức quan trọng nhất từ tài liệu này để tạo flashcards."
            )
            # Ép kiểu JSON cho Flashcard
            prompt = "Trả về danh sách JSON array: [{\"question\": \"...\", \"answer\": \"...\"}]"
            
        else:
            system_instruction = (
                "Bạn là trợ lý tóm tắt tài liệu. Hãy phân tích cấu trúc của đoạn record bài giảng sau và tạo bản tóm tắt theo từng chương hoặc mục lớn một cách logic."
            )
            # Ép kiểu JSON cho Summary
            prompt = """
            Trả về theo cấu trúc: 
            {
                "title": "Tiêu đề tài liệu",
                "outline": [{"heading": "Tên phần", "summary": "Nội dung tóm tắt"}],
                "conclusion": "Kết luận chính"
            }
            """
        response = model.generate_content(
            [f"NỘI DUNG VIDEO:\n{full_text}", prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # 4. Trả về Dictionary/List (KHÔNG dùng json.dumps)
        return {
            "answer": json.loads(response.text),
            "context": [f"Nguồn: {video_url}", f"Tiêu đề: {video_title}"]
        }

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        # Trả về cấu trúc mặc định để PDF Node không bị lỗi AttributeError
        return {
            "answer": {
                "title": "Lỗi xử lý",
                "outline": [{"heading": "Thông báo lỗi", "summary": str(e)}],
                "conclusion": "Vui lòng thử lại với video khác."
            }
        }