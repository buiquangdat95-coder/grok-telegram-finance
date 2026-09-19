import os
import requests
import json
import re

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

def remove_links(text):
    """Xóa bỏ tất cả đường link URL trong văn bản trước khi gửi sang Telegram"""
    # Xóa URL bắt đầu bằng http:// hoặc https://
    clean_text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Xóa định dạng link Markdown [Text](URL)
    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)
    return clean_text.strip()

def analyze_and_send():
    if not GROK_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Thiếu mã Secrets! Hãy kiểm tra lại trên GitHub Secrets.")

    grok_url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Prompt tinh chỉnh với quy tắc nghiêm ngặt: Tiếng Việt, Nguồn uy tín, Không chèn link
    prompt = (
        "Thực hiện tìm kiếm trực tuyến (live search) trên X và Internet ngay bây giờ. "
        "Hãy quét các tin tức vĩ mô, dữ liệu kinh tế Mỹ/toàn cầu mới nhất, "
        "và bài đăng/phát ngôn mới nhất từ Donald Trump hoặc các quan chức liên quan đến DXY và Vàng (XAU/USD).\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. BẮT BUỘC TRẢ LỜI 100% BẰNG TIẾNG VIỆT.\n"
        "2. CHỈ CHẮT LỌC VÀ THAM KHẢO NGUỒN UY TÍN CAO (Bloomberg, Reuters, CNBC, Financial Times, MarketWatch, trang Fed, tài khoản chính thức Donald Trump).\n"
        "3. KHÔNG ĐƯỢC ĐÈN DẤU LINK, URL HAY ĐƯỜNG DẪN LIÊN KẾT NÀO TRONG BẢO CÁO.\n"
        "4. Nếu thị trường đi ngang/không có tin mới đột biến, hãy tóm tắt bối cảnh vĩ mô hiện tại và mốc giá XAU/USD, DXY mới nhất.\n\n"
        "CẤU TRÚC BÁO CÁO:\n"
        "📌 BẢN TIN VĨ MÔ & VÀNG (CẬP NHẬT REAL-TIME)\n"
        "⚡ Tin nổi bật & Phát ngôn của Trump: [Tóm tắt tin cào được từ nguồn uy tín]\n"
        "🧠 Đánh giá tác động: [Phân tích ngắn hạn & dài hạn tới USD/Vàng]\n"
        "📊 PTKT & Vùng giá hiện tại: [Trạng thái giá DXY & XAU/USD thực tế]\n"
        "🎯 Góc nhìn hành động: [Kịch bản tham khảo 1-2 câu]"
    )

    payload = {
        "model": "grok-4.6",
        "input": prompt,
        "tools": [{"type": "web_search"}]
    }

    # Gọi API xAI
    response = requests.post(grok_url, headers=headers, json=payload)
    
    # Fallback nếu cần
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

    # Xóa sạch các link rác trước khi gửi
    final_report = remove_links(analysis_text)

    # Gửi báo cáo về Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": final_report
    }
    
    tg_response = requests.post(telegram_url, json=telegram_payload)
    tg_response.raise_for_status()
    print("Đã cào tin mới nhất từ nguồn uy tín và gửi báo cáo về Telegram thành công!")

if __name__ == "__main__":
    analyze_and_send()
