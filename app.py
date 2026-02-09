import os
from flask import Flask, render_template, request, jsonify
from google import genai
from datetime import datetime, timedelta

app = Flask(__name__)

# Render 환경변수 API 키 사용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    # 1. 사용자 생년월일 정보 처리
    time_str = data.get('time', '시간 모름')
    birth_info = f"{data['year']}년 {data['month']}월 {data['day']}일 ({time_str})"
    
    # 2. [추가] 클라이언트에서 선택한 언어 가져오기
    lang_code = data.get('language', 'ko')
    
    # 언어 코드 매핑
    lang_map = {
        'ko': '한국어 (Korean)',
        'en': 'English',
        'zh': '중국어 (Simplified Chinese)',
        'ja': '일본어 (Japanese)',
        'fr': '프랑스어 (French)'
    }
    target_lang = lang_map.get(lang_code, '한국어')

    # 3. 오늘 날짜 자동 생성 (한국 시간 기준: UTC+9)
    korea_now = datetime.now() + timedelta(hours=9)
    today_date = korea_now.strftime("%Y년 %m월 %d일")
    
    # 4. 프롬프트 수정 (다국어 지원 로직 추가)
    prompt = f"""
    당신은 트렌디한 '퍼스널 사주 패션 디렉터' Theo입니다. 
    
    [사용자 정보]
    - 생년월일: {birth_info} (양력/Solar Calendar 기준)
    - 요청사항: 위 양력 날짜를 바탕으로 정확한 사주(Four Pillars)를 도출하여 분석하세요.
    
    [현재 시점]
    - 오늘 날짜: {today_date}

    [출력 언어 및 설정]
    - **분석 결과는 반드시 '{target_lang}'로 작성하세요.** (인사말 포함 모든 내용)
    
    [출력 가이드]
    1. **중요: 모든 강조(Bold) 처리는 마크다운(**)이 아닌 HTML `<b>` 태그를 사용하세요.**
    2. 인사말: 반드시 `<div class="greeting">` 태그로 감싸서 작성하세요.
       - 내용: "안녕하세요(또는 해당 언어의 인사), 당신의 고유한 기운을 읽어 스타일을 제안하는 Theo입니다..." 와 같은 뉘앙스로 작성.
    3. 형식: 모든 섹션('오늘의 사주 분석', '오늘의 행운 컬러', '오늘의 추천 코디', '오늘의 마음가짐')은 <details><summary>... [보기]</summary></details> 태그로 감싸서 접어두세요.
       - 주의: 섹션 제목(summary)도 '{target_lang}'로 번역해서 출력하세요. (예: Today's Luck -> [View])
    4. 이모티콘: '오늘의 마음가짐' 제목에는 🧠(브레인)을 사용하세요.
    5. 톤앤매너: 본명조 서체에 어울리는 우아하고 전문적인 어조를 사용하세요.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return jsonify({'result': response.text})
    except Exception as e:
        # 에러 발생 시 간단한 메시지
        return jsonify({'result': f"<div class='greeting'>Sorry, connection is unstable. Please try again. ({str(e)})</div>"})

if __name__ == '__main__':
    app.run(debug=True)
