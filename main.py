import os
import requests
import json

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def extract_text(data):
    """Trích xuất văn bản thuần túy từ phản hồi của xAI và giải mã Tiếng Việt"""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Ưu tiên lấy nội dung ở phần output_text
                if item.get("type") == "output_text" and "text" in item:
                    return item["text"]
                # Hoặc kiểm tra các thẻ content
                if "content" in item:
                    res = extract_text(item["content"])
                    if res:
                        return res
    elif isinstance(data, dict):
        if "output_text" in data:
            return data["output_text"]
        if "content" in data:
            return extract_text(data["content"])
    return None

def analyze_and_send():
    if not GROK_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Thiếu thông tin Secrets! Hãy kiểm tra lại GROK_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID trên GitHub.")

    grok_url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
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
    
    res_data = response.json()
    
    # Bóc tách nội dung văn bản
    analysis_text = extract_text(res_data)
    
    # Nếu không trích xuất được dạng mảng, lấy thử các trường mặc định
    if not analysis_text:
        if "output" in res_data:
            analysis_text = str(res_data["output"])
        elif "choices" in res_data:
            analysis_text = res_data["choices"][0]["message"]["content"]
        else:
            analysis_text = response.text

    # Giải mã Unicode tiếng Việt nếu còn vướng mã u00xx
    try:
        analysis_text = analysis_text.encode('utf-8').decode('unicode_escape')
    except Exception:
        pass

    # Gửi báo cáo sạch đẹp về Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analysis_text
    }
    
    tg_response = requests.post(telegram_url, json=telegram_payload)
    tg_response.raise_for_status()
    print("Đã gửi báo cáo vĩ mô định dạng đẹp về Telegram thành công!")

if __name__ == "__main__":
    analyze_and_send()
