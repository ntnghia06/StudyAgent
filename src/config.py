import os
from dotenv import load_dotenv
from dataclasses import dataclass
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@dataclass
class PipelineConfig:
    # Thay vì audio_filename, ta dùng input_audio_path chứa đường dẫn đầy đủ
    input_audio_path: str 
    # ---------------------

    # Các cấu hình mặc định khác giữ nguyên
    project_root: str = os.getcwd()
    api_key: str = os.getenv("GOOGLE_API_KEY")
    whisper_model: str = "large-v3-turbo"
    gemini_model: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    chunk_minutes: int = 10

    # THÊM DÒNG NÀY: Chế độ tóm tắt mặc định ('SHORT', 'MEDIUM', 'LONG')
    summary_mode: str = "MEDIUM"
    
    cs_prompt: str = (
        "Bài giảng chuyên ngành Khoa Học Máy Tính (CS). "
        "Giữ nguyên thuật ngữ: Gradient Descent, Regression, Policy, Reward, Agent, Bias, Variance. "
        "Code Python: def, import, class, object, numpy, tensor."
    )

    @property
    def output_folder(self):
        # Output sẽ nằm cùng chỗ với project
        path = os.path.join(self.project_root, "Pipeline_Output")
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def temp_folder(self):
        path = os.path.join(self.project_root, "temp_data")
        os.makedirs(path, exist_ok=True)
        return path