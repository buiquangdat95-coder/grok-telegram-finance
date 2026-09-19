import os
import requests
import json

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def parse_xai_response(res_data):
    """Trích xuất văn bản thuần túy chuẩn UTF-8 từ phản hồi xAI"""
    if isinstance(res_data, str):
        try:
            res_data = json.loads(res_data)
        except Exception:
            return res_data

    if isinstance(res_data, list):
        for item in res_data:
            text = parse_xai_response(item)
            if text:
                return text
    elif isinstance(res_data, dict):
        if res_data.get("type") == "output_text" and "text" in res_data:
            return res_data["text"]
        
        if "choices" in res_data and len(res_data["choices"]) > 0:
            choice = res_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
                
        if "output" in res_data:
            return parse_xai_response(res_data["output"])
        if "content" in res_data:
            return parse_xai_response(res_data["content"])

    return None

def analyze_and_send():
    if not GROK_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Thiếu mã Secrets! Hãy kiểm tra lại trên GitHub Secrets.")

    grok_url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Câu lệnh ép Grok chủ động tra cứu dữ liệu mới nhất trên mạng
    prompt = (
        "Thực hiện tìm kiếm trực tuyến (live search) trên X và Internet ngay bây giờ. "
        "Hãy quét các tin tức vĩ mô, dữ liệu kinh tế Mỹ/toàn cầu mới nhất, "
        "và các bài đăng/phát ngôn mới nhất từ Donald Trump hoặc các quan chức liên quan đến DXY và Vàng (XAU/USD).\n\n"
        "Nếu thị trường đang trong giờ nghỉ/không có tin mới đột biến, hãy lấy giá hiện tại của XAU/USD, DXY "
        "và tóm tắt xu hướng tâm lý chính trên thị trường.\n\n"
        "Trình bày báo cáo ngắn gọn, súc tích theo cấu trúc:\n"
        "📌 BẢN TIN VĨ MÔ & VÀNG (CẬP NHẬT REAL-TIME)\n"
        "⚡ Tin mới nhất & Phát ngôn từ Trump: [Tóm tắt tin cào được mới nhất]\n"
        "🧠 Đánh giá tác động: [Tác động ngắn hạn & dài hạn tới USD/Vàng]\n"
        "📊 PTKT & Vùng giá hiện tại: [Trạng thái giá DXY & XAU/USD mới nhất]\n"
        "🎯 Góc nhìn hành động: [Kịch bản tham khảo 1-2 câu]"
    )

    payload = {
        "model": "grok-4.6",
        "input": prompt,
        "tools": [{"type": "web_search"}]  # Bật công cụ tìm kiếm Web/X thời gian thực
    }

    # Gọi API xAI
    response = requests.post(grok_url, headers=headers, json=payload)
    
    # Nếu API không nhận định dạng tools kiểu mới, fallback về cấu hình search chuẩn
    if response.status_code != 200:
        payload["search"] = True
        del payload["tools"]
        response = requests.post(grok_url, headers=headers, json=payload)
        
    response.raise_for_status()
    
    response.encoding = 'utf-8'
    res_data = response.json()
    
    analysis_text = parse_xai_response(res_data)
    if not analysis_text:
        analysis_text = response.text

    # Gửi báo cáo về Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analysis_text
    }
    
    tg_response = requests.post(telegram_url, json=telegram_payload)
    tg_response.raise_for_status()
    print("Đã cào tin mới nhất và gửi báo cáo về Telegram thành công!")

if __name__ == "__main__":
    analyze_and_send()
