import os
import requests

GROK_API_KEY = os.getenv("GROK_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def analyze_and_send():
    if not GROK_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Thiếu mã Secrets! Hãy kiểm tra lại GROK_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID trên GitHub.")

    grok_url = "https://api.x.ai/v1/chat/completions"
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

    # Thử danh sách các model chính thức từ xAI
    models_to_try = ["grok-2-latest", "grok-2", "grok-beta"]
    analysis_text = None

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Bạn là chuyên gia phân tích tài chính vĩ mô và giao dịch Vàng (XAU/USD), USD."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        res = requests.post(grok_url, headers=headers, json=payload)
        if res.status_code == 200:
            analysis_text = res.json()['choices'][0]['message']['content']
            print(f"Đã gọi thành công bằng model: {model_name}")
            break
        else:
            print(f"Model {model_name} trả về mã lỗi {res.status_code}, đang thử model tiếp theo...")

    if not analysis_text:
        raise RuntimeError(f"Tất cả model xAI đều không khả dụng. Phản hồi cuối: {res.text}")

    # Gửi tin nhắn Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analysis_text
    }
    
    tg_res = requests.post(telegram_url, json=telegram_payload)
    tg_res.raise_for_status()
    print("Đã gửi tin nhắn báo cáo về Telegram thành công!")

if __name__ == "__main__":
    analyze_and_send()
