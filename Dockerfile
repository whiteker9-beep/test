# 1단계: 기본 환경 및 종속성 설치
FROM python:3.11-slim-bullseye

# Chrome 실행에 필요한 시스템 라이브러리 및 스크립팅 도구 설치 (jq, curl/wget, unzip)
RUN apt-get update -qq -y && \
    apt-get install -y --no-install-recommends \
    libasound2 libatk-bridge2.0-0 libgtk-4-1 libnss3 xdg-utils \
    wget unzip jq curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    # apt-get update는 패키지 목록을 갱신하고, apt-get install은 실제 설치를 수행합니다. [14, 15]

# 2단계: CfT API를 사용하여 최신 ChromeDriver 및 Chrome 다운로드
ENV CHROMEDRIVER_DIR /usr/local/bin
ENV CHROME_DIR /opt/chrome

# 쉘 스크립트 RUN 명령: CfT API를 호출하여 동적으로 최신 안정 버전의 URL 획득 및 설치
RUN CHROME_LATEST_VERSION_URL=$( \
        curl -sL https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
        jq -r '.versions[] | select(.version | test("^[0-9]+(\.[0-9]+){3}$")) |.downloads.chrome | select(.platform == "linux64") |.url' | tail -1 \
    ) && \
    CHROMEDRIVER_LATEST_URL=$( \
        curl -sL https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
        jq -r '.versions[] | select(.version | test("^[0-9]+(\.[0-9]+){3}$")) |.downloads.chromedriver | select(.platform == "linux64") |.url' | tail -1 \
    ) && \
    
    # Chrome 설치
    wget -q -O chrome.zip "$CHROME_LATEST_VERSION_URL" && \
    unzip chrome.zip && \
    mv chrome-linux64 $CHROME_DIR && \
    ln -s $CHROME_DIR/chrome /usr/local/bin/chrome && \
    rm chrome.zip && \

    # ChromeDriver 설치
    wget -q -O chromedriver.zip "$CHROMEDRIVER_LATEST_URL" && \
    unzip -j chromedriver.zip chromedriver-linux64/chromedriver -d $CHROMEDRIVER_DIR && \
    chmod +x $CHROMEDRIVER_DIR/chromedriver && \
    rm chromedriver.zip

# 3단계: Python 환경 구성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#
COPY . . 
# 현재 폴더의 모든 소스코드 복사 (requirements.txt만 복사했던 위 단계 아래에 추가)

# 컨테이너 시작 시 실행할 명령어
CMD ["python", "main.py"]