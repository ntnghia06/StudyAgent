import jinja2
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright # Chuyển sang dùng bản sync
from dotenv import load_dotenv

load_dotenv()

def generate_pdf_from_state(state: dict):
    """
    Node xử lý chuyển đổi kết quả JSON trong state thành file PDF.
    Sử dụng Playwright bản Sync để tương thích với app.stream()
    """
    # Lấy dữ liệu từ state
    data = state.get("answer", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            data = {"title": "Kết quả", "outline": [{"heading": "Nội dung", "summary": data}], "conclusion": ""}
    if not data:
        print("Cảnh báo: Không tìm thấy dữ liệu 'answer' trong state.")
        return state

    # --- BƯỚC 1: ĐỊNH NGHĨA TEMPLATE HTML ---
    template_str = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 50px; }
            .header { text-align: center; border-bottom: 2px solid #4A90E2; padding-bottom: 20px; margin-bottom: 30px; }
            h1 { color: #2C3E50; margin: 0; font-size: 28px; }
            .meta { font-size: 12px; color: #7f8c8d; margin-top: 10px; }
            .section { margin-bottom: 25px; page-break-inside: avoid; }
            .section-title { color: #2980b9; border-left: 5px solid #2980b9; padding-left: 10px; margin-bottom: 10px; font-size: 20px; }
            .section-content { text-align: justify; margin-left: 15px; }
            .conclusion { background-color: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px inset #ddd; margin-top: 40px; }
            .conclusion-title { font-weight: bold; color: #c0392b; margin-bottom: 10px; display: block; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="meta">Ngày xuất bản: {{ date }}</div>
        </div>
        {% for item in outline %}
        <div class="section">
            <div class="section-title">{{ loop.index }}. {{ item.heading }}</div>
            <div class="section-content">{{ item.summary }}</div>
        </div>
        {% endfor %}
        <div class="conclusion">
            <span class="conclusion-title">Kết luận chính:</span>
            {{ conclusion }}
        </div>
    </body>
    </html>
    """

    # --- BƯỚC 2: RENDER HTML ---
    template = jinja2.Template(template_str)
    html_out = template.render(
        title=data.get("title", "Tài liệu không tiêu đề"),
        outline=data.get("outline", []),
        conclusion=data.get("conclusion", ""),
        date=datetime.now().strftime("%H:%M - %d/%m/%Y")
    )

    # --- BƯỚC 3: SỬ DỤNG PLAYWRIGHT (SYNC) ĐỂ XUẤT PDF ---
    output_file = "SUMMARY.pdf"
    
    try:
        print("Đang khởi tạo trình duyệt (Sync mode)...")
        with sync_playwright() as p:
            # Khởi tạo trình duyệt đồng bộ
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Đổ HTML và chờ load
            page.set_content(html_out, wait_until="networkidle")
            
            print(f"Đang in PDF: {output_file}")
            page.pdf(
                path=output_file,
                format="A4",
                print_background=True,
                margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
            )
            browser.close()
            
        print(f"--- Xuất file thành công: {output_file} ---")
        
        # Trả về state cập nhật (LangGraph cần điều này)
        return {"answer": output_file}

    except Exception as e:
        print(f"Lỗi khi chuyển đổi PDF: {e}")
        return state