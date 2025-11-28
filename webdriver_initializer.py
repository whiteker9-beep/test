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
    chrome_options.add_argument("--headless=new")              # GUI 없이 실행
    chrome_options.add_argument("--no-sandbox")             # 컨테이너 권한 문제 회피 
    chrome_options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 충돌 방지 
    
    # 기타 권장 옵션
    chrome_options.add_argument("--disable-gpu")            # GPU 사용 비활성화
    chrome_options.add_argument("--window-size=1920,1080") 
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("[INFO] Chrome 드라이버 성공적으로 실행됨.")
        return driver
    except Exception as e:
        print(f" Chrome 드라이버 실행 실패: {e}")
        raise