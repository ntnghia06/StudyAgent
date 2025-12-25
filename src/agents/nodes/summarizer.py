import convertapi
import json
import os

# ⚠️ QUAN TRỌNG: Dán Token của bạn vào giữa dấu nháy bên dưới
# Nếu để None hoặc chuỗi rỗng sẽ bị lỗi "can only concatenate str"
convertapi.api_secret = 'AZLn9FsjFwboanyN5VIgWJEAmijucl56'

# --- BƯỚC 1: CHUẨN BỊ DỮ LIỆU JSON ---
# Giả lập dữ liệu nhận được từ API hoặc Database
du_lieu_json = {
    "tieu_de": "HỒ SƠ SINH VIÊN",
    "ho_ten": "Nguyễn Trọng Nghĩa",
    "mssv": "24521148",
    "nganh_hoc": "Y Đa Khoa",
    "khoa": "Y Tế Công Cộng",
    "diem_gpa": 3.8,
    "ngay_cap_nhat": "25/12/2025"
}

# --- BƯỚC 2: TẠO FILE HTML TỪ JSON (MAPPING) ---
# Chúng ta sẽ chèn các biến từ JSON vào chuỗi HTML (f-string)
# Bạn có thể viết CSS (style) ở đây để file PDF đẹp hơn
noi_dung_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Báo Cáo</title>
    <style>
        body {{ font-family: DejaVu Sans, Arial, sans-serif; padding: 40px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .info-box {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #000; margin-left: 10px; }}
        .footer {{ margin-top: 50px; font-size: 12px; color: #777; text-align: center; }}
    </style>
</head>
<body>
    <h1>{du_lieu_json['tieu_de']}</h1>
    
    <div class="info-box">
        <p><span class="label">Họ và tên:</span> <span class="value">{du_lieu_json['ho_ten']}</span></p>
        <p><span class="label">MSSV:</span> <span class="value">{du_lieu_json['mssv']}</span></p>
        <p><span class="label">Ngành học:</span> <span class="value">{du_lieu_json['nganh_hoc']}</span></p>
        <p><span class="label">Khoa:</span> <span class="value">{du_lieu_json['khoa']}</span></p>
        <p><span class="label">GPA Tích lũy:</span> <span class="value">{du_lieu_json['diem_gpa']}</span></p>
    </div>

    <div class="footer">
        Báo cáo được tạo tự động vào ngày {du_lieu_json['ngay_cap_nhat']}
    </div>
</body>
</html>
"""

# Lưu file HTML tạm thời xuống ổ cứng
ten_file_html = 'temp_report.html'
with open(ten_file_html, 'w', encoding='utf-8') as f:
    f.write(noi_dung_html)

print("✅ Đã tạo xong file HTML từ JSON.")

# --- BƯỚC 3: GỬI HTML LÊN CONVERTAPI ĐỂ LẤY PDF ---
print("⏳ Đang chuyển đổi sang PDF...")

try:
    # Convert từ file HTML local sang PDF
    result = convertapi.convert('pdf', {
        'File': 'temp_report.html'
    }, from_format = 'html')
    
    # Lưu file PDF kết quả
    ten_file_pdf = 'ho_so_sinh_vien.pdf'
    result.save_files(os.getcwd())
    
    print(f"🎉 Thành công! File PDF đã được lưu: {ten_file_pdf}")

except convertapi.ApiError as e:
    print(f"❌ Lỗi API: {e}")
except Exception as e:
    print(f"❌ Lỗi: {e}")