# 1. 베이스 이미지 (가벼운 slim 버전 사용 권장, 원하시면 python:3.11도 가능)
FROM python:3.11-slim

# 2. 필수 패키지 및 Chromium 드라이버 설치
# apt-get으로 설치하면 의존성 라이브러리(libglib 등)가 자동으로 설치됩니다.
RUN apt-get update && \
    apt-get install -y \
    chromium-driver \
    curl unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 소스 코드 및 의존성 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 전체 복사
COPY . .

# 5. 실행 명령어 (웹 서버가 아닌 Job이므로 gunicorn 대신 python main.py 사용)
CMD ["python", "main.py"]