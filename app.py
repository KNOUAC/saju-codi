import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# Render에서 설정한 환경변수에서 API 키를 가져옵니다.
# 로컬에서 테스트할 때는 os.environ.get("GEMINI_API_KEY") 부분에 직접 키를 넣어도 됩니다.
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Gemini 모델 설정 (최신 모델 사용)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    birth_date = f"{data['year']}년 {data['month']}월 {data['day']}일 {data['time']}"
    today_date = datetime.now().strftime("%Y년 %m월 %d일")

    # AI에게 내리는 지령 (프롬프트 엔지니어링)
    prompt = f"""
    역할: 당신은 세련된 감각을 가진 'AI 사주 패션 디렉터'입니다.
    
    [정보]
    - 사용자 생년월일시: {birth_date}
    - 오늘 날짜: {today_date}
    
    [미션]
    1. 사용자의 생년월일을 바탕으로 '일주(Day Pillar)'를 계산하세요. (예: 갑자일주, 을미일주 등)
    2. 사용자의 일주와 오늘 날짜의 일진(Daily Energy)을 분석하여 '오늘의 운세'를 파악하세요.
    3. 운세를 보완하거나 강화할 수 있는 '오늘의 행운 컬러'와 '패션 코디'를 추천하세요.
    4. 하루를 잘 보내기 위한 '마음가짐' 조언을 해주세요.

    [출력 형식]
    HTML 태그를 사용하여 예쁘게 출력해주세요. (<h2>, <ul>, <li>, <strong> 등 사용)
    - 💎 <strong>당신의 일주:</strong> [일주]
    - 🎨 <strong>오늘의 행운 컬러:</strong> [색상명]
    - 👕 <strong>추천 코디:</strong> [구체적인 스타일링 제안]
    - 🍀 <strong>오늘의 마음가짐:</strong> [따뜻하고 위트 있는 조언]
    
    말투는 친절하고 트렌디하게 해주세요.
    """

    try:
        response = model.generate_content(prompt)
        return jsonify({'result': response.text})
    except Exception as e:
        # 이 줄을 추가하면 Render Logs 탭에서 실제 에러 내용을 볼 수 있습니다.
        print(f"--- API ERROR: {e} ---") 
        # 화면에도 에러 내용을 잠시 표시해봅니다.
        return jsonify({'result': f"AI 연결 실패: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
