import os
from flask import Flask, render_template, request, jsonify
from google import genai
from datetime import datetime

app = Flask(__name__)

# Render 환경변수에 등록한 API 키 사용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    birth_info = f"{data['year']}년 {data['month']}월 {data['day']}일 {data['time']}"
    
    prompt = f"""
    당신은 트렌디한 'AI 사주 패션 디렉터'입니다. 
    사용자 생년월일시: {birth_info}
    오늘 날짜: 2026년 2월 8일

    [출력 가이드]
    1. 반드시 HTML 태그를 사용하세요.
    2. '오늘의 사주 분석'과 '오늘의 행운 컬러'는 <details><summary>... [보기]</summary></details> 태그로 감싸서 기본적으로 접어두세요.
    3. '추천 코디'와 '마음가짐'은 <h3> 태그를 사용하여 바로 보이게 하세요.
    4. 전체적인 문체는 본명조 서체에 어울리게 우아하고 차분하게 작성하세요.

    [작성 예시]
    <details>
        <summary>🔍 오늘의 사주 분석 [보기]</summary>
        <p>내용...</p>
    </details>
    <details>
        <summary>🎨 오늘의 행운 컬러 [보기]</summary>
        <p>내용...</p>
    </details>
    <h3>👕 오늘의 추천 코디</h3>
    <p>내용...</p>
    <h3>🍀 오늘의 마음가짐</h3>
    <p>내용...</p>
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return jsonify({'result': response.text})
    except Exception as e:
        return jsonify({'result': f"<p>오류가 발생했습니다: {str(e)}</p>"})

if __name__ == '__main__':
    app.run(debug=True)
