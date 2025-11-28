import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def initialize_chrome_driver():
    """
    Cloud Run Job 환경에 최적화된 Headless Chrome WebDriver를 초기화합니다.
    """
    print("[INFO] Chrome 드라이버 초기화 및 옵션 설정 중...")
    
    chrome_options = Options()
    
    # 1. Cloud Run Job 실행에 필수적인 옵션
    chrome_options.add_argument("--headless")              # GUI 없이 실행
    chrome_options.add_argument("--no-sandbox")             # 컨테이너 권한 문제 회피 
    chrome_options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 충돌 방지 
    
    # 기타 권장 옵션
    chrome_options.add_argument("--disable-gpu")            # GPU 사용 비활성화
    chrome_options.add_argument("window-size=1920,1080")    # 안정적인 해상도 설정
    
    try:
        # Dockerfile에서 ChromeDriver가 PATH에 설치되었다고 가정하고 Service 객체를 사용합니다.
        # executable_path를 명시적으로 지정할 경우 (예: Service(executable_path="/usr/local/bin/chromedriver"))
        # 더 명확할 수 있으나, PATH에 있다면 생략 가능합니다.
        driver = webdriver.Chrome(options=chrome_options)
        print("[INFO] Chrome 드라이버 성공적으로 실행됨.")
        return driver
    except Exception as e:
        print(f" Chrome 드라이버 실행 실패: {e}")
        # 실패 시 시스템 종료 또는 로그 기록 후 재시도 로직 추가 가능
        raise