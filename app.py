import os
import logging
from flask import Flask, render_template, request, jsonify
from google import genai
from datetime import datetime, timedelta

# 로그 설정 (에러 발생 시 터미널에서 확인하기 위함)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# 1. API 클라이언트 설정
# 환경 변수에서 가져오거나, 테스트 시 여기에 직접 키를 입력해서 확인해보세요.
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        
        # 입력 데이터 검증 및 기본값 설정
        year = data.get('year', '')
        month = data.get('month', '')
        day = data.get('day', '')
        time_str = data.get('time', '시간 모름')
        
        # 생년월일 정보 조합
        birth_info = f"{year}년 {month}월 {day}일 ({time_str})"
        
        # 오늘 날짜 (KST)
        korea_now = datetime.now() + timedelta(hours=9)
        today_date = korea_now.strftime("%Y년 %m월 %d일")
        
        # 프롬프트 구성
        prompt = f"""
        당신은 트렌디한 '퍼스널 사주 패션 디렉터' Theo입니다. 
        
        [사용자 정보]
        - 생년월일: {birth_info} (양력/Solar Calendar 기준)
        - 요청사항: 위 양력 날짜를 바탕으로 정확한 사주(Four Pillars)를 도출하여 분석하세요.
        
        [현재 시점]
        - 오늘 날짜: {today_date}

        [출력 가이드]
        1. **중요: 모든 강조(Bold) 처리는 마크다운(**)이 아닌 HTML `<b>` 태그를 사용하세요.**
        2. 인사말: 반드시 `<div class="greeting">` 태그로 감싸서 작성하세요. 
           문구: "안녕하세요, 기다려 주셔서 감사합니다. ({today_date} 기준)... (후략)"
        3. 소개 생략: 자기소개는 UI에 있으므로 생략하세요.
        4. 형식: 섹션별로 <details><summary>... [보기]</summary></details> 태그 사용.
        5. 톤앤매너: 전문적이고 우아한 어조.
        """

        # 2. 모델 호출 (핵심 수정 부분)
        # 문서의 'gemini-3-flash-preview' 대신 현재 사용 가능한 모델 사용
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        return jsonify({'result': response.text})

    except Exception as e:
        # 서버 로그에 구체적인 에러 출력
        app.logger.error(f"Error occurred: {str(e)}")
        # 사용자에게 에러 메시지 반환 (디버깅용)
        error_msg = str(e)
        if "404" in error_msg:
            msg = "모델을 찾을 수 없습니다. (모델명 확인 필요)"
        elif "403" in error_msg:
            msg = "API 키 오류 또는 권한이 없습니다."
        else:
            msg = f"오류가 발생했습니다: {error_msg}"
            
        return jsonify({'result': f"<div class='greeting'>죄송합니다. {msg}</div>"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
