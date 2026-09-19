import os
import requests
import json

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def parse_xai_response(res_data):
    """Trích xuất văn bản thuần túy chuẩn UTF-8 từ phản hồi xAI"""
    # Nếu kết quả trả về là chuỗi string JSON
    if isinstance(res_data, str):
        try:
            res_data = json.loads(res_data)
        except Exception:
            return res_data

    # Trường hợp 1: Trích xuất từ cấu trúc mảng output_text / content
    if isinstance(res_data, list):
        for item in res_data:
            text = parse_xai_response(item)
            if text:
                return text
    elif isinstance(res_data, dict):
        # Ưu tiên lấy trực tiếp văn bản ở dạng output_text
        if res_data.get("type") == "output_text" and "text" in res_data:
            return res_data["text"]
        
        # Tìm trong trường choices (định dạng OpenAI / xAI standard)
        if "choices" in res_data and len(res_data["choices"]) > 0:
            choice = res_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
                
        # Tìm trong các trường content hoặc output khác
        if "output" in res_data:
            return parse_xai_response(res_data["output"])
        if "content" in res_data:
            return parse_xai_response(res_data["content"])

    return None

def analyze_and_send():
    if not GROK_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Thiếu mã Secrets! Hãy kiểm tra lại GROK_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID trên GitHub Secrets.")

    grok_url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    prompt = (
        "Hãy quét các thông tin kinh tế vĩ mô thời gian thực quan trọng nhất trong 8 giờ qua trên X/Web, "
        "đặc biệt là phát ngôn/bài đăng mới nhất từ Donald Trump ảnh hưởng tới DXY và XAU/USD.\n\n"
        "Phân tích theo cấu trúc ngắn gọn, văn phong nói chuyện tự nhiên giữa hai đồng nghiệp:\n"
        "📌 BẢN TIN VĨ MÔ & VÀNG\n"
        "⚡ Tin nổi bật & Phát ngôn của Trump: [Liệt kê gạch đầu dòng]\n"
        "🧠 Đánh giá tác động: [Phân tích tâm lý ngắn hạn trong ngày/tuần vs Dài hạn vĩ mô]\n"
        "📊 Xung đột PTKT: [So sánh xu hướng tin tức với biểu đồ PTKT XAU/USD hiện tại]\n"
        "🎯 Góc nhìn hành động: [Tóm tắt kịch bản ngắn gọn 1-2 câu]"
    )

    payload = {
        "model": "grok-4.6",
        "input": prompt
    }

    # Gọi API xAI
    response = requests.post(grok_url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Ép kiểu nhận dữ liệu dạng UTF-8 chuẩn
    response.encoding = 'utf-8'
    res_data = response.json()
    
    # Bóc tách văn bản phân tích
    analysis_text = parse_xai_response(res_data)
    
    if not analysis_text:
        analysis_text = response.text

    # Gửi báo cáo sạch đẹp về Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analysis_text,
        "parse_mode": "Markdown"
    }
    
    tg_response = requests.post(telegram_url, json=telegram_payload)
    
    # Nếu gửi lỗi do định dạng Markdown, gửi lại ở dạng văn bản thường
    if tg_response.status_code != 200:
        del telegram_payload["parse_mode"]
        tg_response = requests.post(telegram_url, json=telegram_payload)
        
    tg_response.raise_for_status()
    print("Đã gửi báo cáo vĩ mô chuẩn UTF-8 về Telegram thành công!")

if __name__ == "__main__":
    analyze_and_send()
