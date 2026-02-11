import os
import logging
import requests  # requests 모듈 추가
from flask import Flask, render_template, request, jsonify
from google import genai
from datetime import datetime, timedelta

# Flask 기본 로깅은 유지 (치명적 오류 대비)
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

# API 클라이언트 설정
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 슬랙 웹훅 URL (환경변수에서 가져옴)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def send_slack_message(message):
    """슬랙으로 메시지를 보내는 헬퍼 함수"""
    if not SLACK_WEBHOOK_URL:
        return # 웹훅 URL이 없으면 아무것도 안 함

    try:
        payload = {"text": message}
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except Exception:
        pass # 슬랙 전송 실패해도 앱은 멈추면 안 됨

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 시도할 모델 리스트
    candidate_models = [
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]
    
    data = request.json
    year = data.get('year', '')
    month = data.get('month', '')
    day = data.get('day', '')
    time_str = data.get('time', '시간 모름')
    
    birth_info = f"{year}년 {month}월 {day}일 ({time_str})"
    korea_now = datetime.now() + timedelta(hours=9)
    today_date = korea_now.strftime("%Y년 %m월 %d일")
    
    prompt = f"""
    당신은 트렌디한 '퍼스널 사주 패션 디렉터' Theo입니다. 
    
    [사용자 정보]
    - 생년월일: {birth_info} (양력/Solar Calendar 기준)
    - 요청사항: 위 양력 날짜를 바탕으로 정확한 사주를 분석하세요.
    
    [현재 시점]
    - 오늘 날짜: {today_date}

    [출력 가이드]
    1. **중요: 모든 강조(Bold) 처리는 마크다운(**)이 아닌 HTML `<b>` 태그를 사용하세요.**
    2. 인사말: 반드시 `<div class="greeting">` 태그로 감싸서 작성하세요. 
       문구: "안녕하세요, 기다려 주셔서 감사합니다. {today_date} 기준, ... (후략)"
    3. 소개 생략: 자기소개(Theo입니다 등)는 이미 UI에 있으므로 포함하지 마세요.
    4. 형식: 모든 섹션('오늘의 사주 분석', '오늘의 행운 컬러', '오늘의 추천 코디', '오늘의 마음가짐')은 <details><summary>... [보기]</summary></details> 태그로 감싸서 접어두세요.
    5. 이모티콘: '오늘의 마음가짐' 제목에는 🧠(브레인)을 사용하세요.
    6. 톤앤매너: 본명조 서체에 어울리는 우아하고 전문적인 어조를 사용하세요.
    """

    last_error = None
    success_response = None
    
    # --- 슬랙 알림: 분석 시작 ---
    send_slack_message(f"🔮 [Theo] 분석 요청 들어옴: {birth_info}")

    # 모델 자동 순환 시도
    for model_name in candidate_models:
        try:
            # (옵션) 너무 시끄러우면 아래 줄 주석 처리
            # send_slack_message(f"trying: {model_name}...") 
            
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            success_response = response.text
            
            # --- 슬랙 알림: 성공 ---
            send_slack_message(f"✅ [성공] 모델: {model_name}")
            break 
            
        except Exception as e:
            # --- 슬랙 알림: 실패 (어떤 에러인지 확인용) ---
            send_slack_message(f"⚠️ [실패] {model_name}: {str(e)}")
            last_error = e
            continue

    if success_response:
        return jsonify({'result': success_response})
    else:
        error_msg = str(last_error)
        # --- 슬랙 알림: 전체 실패 ---
        send_slack_message(f"🚨 [전체 실패] 모든 모델 에러: {error_msg}")
        
        return jsonify({'result': f"<div class='greeting'>죄송합니다. 서버가 혼잡하여 연결에 실패했습니다.<br><span style='font-size:0.8rem; color:#999'>({error_msg})</span></div>"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
