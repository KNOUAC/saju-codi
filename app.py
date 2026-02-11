import os
import logging
import requests
from flask import Flask, render_template, request, jsonify
from google import genai
from datetime import datetime, timedelta

# Flask 기본 로깅
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

# ---------------------------------------------------------
# [수정됨] 멀티 API 키 로드 로직
# GEMINI_API_KEY, GEMINI_API_KEY1 ~ 10을 모두 찾아 리스트로 만듭니다.
# ---------------------------------------------------------
api_keys = []

# 1. 기본 키 확인
default_key = os.environ.get("GEMINI_API_KEY")
if default_key:
    api_keys.append(default_key)

# 2. 번호 붙은 키 확인 (1번부터 10번까지)
for i in range(1, 11):
    key = os.environ.get(f"GEMINI_API_KEY{i}")
    if key:
        # 중복 방지
        if key not in api_keys:
            api_keys.append(key)

# 키가 하나도 없으면 경고
if not api_keys:
    print("⚠️ [경고] 등록된 API 키가 없습니다. 환경 변수를 확인해주세요.")

# 슬랙 웹훅 URL
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def send_slack_message(message):
    """슬랙으로 메시지를 보내는 헬퍼 함수"""
    if not SLACK_WEBHOOK_URL:
        return 

    try:
        payload = {"text": message}
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except Exception:
        pass 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 요청하신 기존 모델 리스트 유지
    candidate_models = [
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
        "gemini-flash-latest"
    ]
    
    data = request.json
    year = data.get('year', '')
    month = data.get('month', '')
    day = data.get('day', '')
    time_str = data.get('time', '시간 모름')
    
    birth_info = f"{year}년 {month}월 {day}일 ({time_str})"
    korea_now = datetime.now() + timedelta(hours=9)
    today_date = korea_now.strftime("%Y년 %m월 %d일")
    
    # 프롬프트: 기존 내용 유지
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
    
    send_slack_message(f"🔮 [Theo] 분석 요청 들어옴: {birth_info} (가용 키: {len(api_keys)}개)")

    # ---------------------------------------------------------
    # [수정됨] 이중 루프: (모든 키) x (모든 모델) 순환
    # 키1로 모델들 시도 -> 실패 시 -> 키2로 모델들 시도...
    # ---------------------------------------------------------
    for key_idx, current_key in enumerate(api_keys):
        
        # 로깅용 키 별칭 (KEY_1, KEY_2...)
        key_alias = f"KEY_{key_idx+1}"
        
        # 현재 키로 클라이언트 생성
        try:
            client = genai.Client(api_key=current_key)
        except Exception:
            continue # 키 오류 시 다음 키로

        # 해당 키로 모델 리스트 순회
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                success_response = response.text
                
                # 성공 시 슬랙 알림 및 즉시 리턴
                send_slack_message(f"✅ [성공] {key_alias} / {model_name}")
                return jsonify({'result': success_response})
                
            except Exception as e:
                # 실패 시 에러 기록하고 계속 진행 (다음 모델 or 다음 키)
                error_msg = str(e)
                # send_slack_message(f"⚠️ [실패] {key_alias} / {model_name}: {error_msg}")
                last_error = e
                continue

    # 모든 시도가 실패했을 경우
    error_msg = str(last_error)
    send_slack_message(f"🚨 [전체 실패] 모든 키({len(api_keys)}개) 소진. 최후 에러: {error_msg}")
    
    return jsonify({'result': f"<div class='greeting'>죄송합니다. 서버가 혼잡하여 연결에 실패했습니다.<br><span style='font-size:0.8rem; color:#999'>({error_msg})</span></div>"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
