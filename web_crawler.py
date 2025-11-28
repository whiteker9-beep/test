# web_crawler.py
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
from bs4 import BeautifulSoup

class WebCrawler:
    def __init__(self, driver):
        self.driver = driver

    def login(self, user_id, password, login_url, id_selector, pw_selector, submit_selector):
        try:
            self.driver.get(login_url)
            self.driver.maximize_window()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, id_selector))
            )
            self.driver.find_element(By.CSS_SELECTOR, id_selector).send_keys(user_id)
            self.driver.find_element(By.CSS_SELECTOR, pw_selector).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, submit_selector).click()

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SELECT_DT"))
            )
            print("[INFO] 로그인 성공")
        except Exception as e:
            print(f"[ERROR] 로그인 실패: {e}")
            raise

    def handle_popup(self):
        try:
            # "확인" 버튼을 찾고 클릭
            ok_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='확인']"))
            )
            ok_button.click()
            print("[INFO] 비밀번호 변경 팝업 닫힘")
        except Exception:
            # 팝업이 없거나 실패해도 무시하고 진행
            pass

    def move_to_data_page(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "SELECT_DT"))
        )
    def set_date(self, date_string: str):
            try:
                self.driver.execute_script(
                    f"document.getElementById('SELECT_DT').value = '{date_string}';"
                    f"document.getElementById('SELECT_DT').removeAttribute('readonly');"
                )
                print(f"[INFO] 날짜 {date_string} 설정 완료.")
            except Exception as e:
                print(f"[ERROR] 날짜 필드 설정 실패: {e}")
                raise

    def wait_for_background_disappear(self):
        try:
            WebDriverWait(self.driver, 30).until(
                EC.invisibility_of_element_located((By.ID, "backgroundLayer"))
            )
        except TimeoutException:
            print(f"[WARN] backgroundLayer 비활성화 대기 시간 초과")




    def set_mode_15m(self):
        try:
            radio_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='T_MODE'][value='15']"))
            )
            if not radio_button.is_selected():
                radio_button.click()
                # 실제 상태 변경 검증
                if radio_button.is_selected():
                    print(f"[INFO] 15분 모드 선택 완료.")
                    return True
                else:
                    print(f"[ERROR] 15분 모드 클릭했지만 선택되지 않음")
                    return False
            else:
                print(f"[INFO] 15분 모드 이미 선택됨.")
                return True
        except TimeoutException:
            print(f"[ERROR] 15분 라디오 버튼 로딩 실패")
            return False
        except Exception as e: 
            print(f"[ERROR] 15분 모드 설정 중 예외: {e}")
            return False

    def set_mode_30m(self):
        try:
            radio_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='T_MODE'][value='30']"))
            )
            if not radio_button.is_selected():
                radio_button.click()
                if radio_button.is_selected():
                    print(f"[INFO] 30분 모드 선택 완료.")
                    return True
            else:
                print(f"[INFO] 30분 모드 이미 선택됨.")
                return True
        except TimeoutException:
            print(f"[ERROR] 30분 라디오 버튼 로딩 실패")
            return False
        except Exception as e: 
            print(f"[ERROR] 30분 모드 설정 중 예외: {e}")
            return False

    def debug_lookup_button(self):
        # 모든 가능한 조회 버튼 셀렉터 확인
        selectors = [
            "//img[@alt='조회']",
            "//img[contains(@src, 'btn_blue_lookup.png')]",
            "//input[@type='image' and @alt='조회']",
            "//input[@type='button' and @value='조회']",
            "//button[contains(text(), '조회')]",
            "//a[contains(text(), '조회')]",
            "//*[@onclick and contains(@onclick, 'lookup')]",
            "//*[@onclick and contains(@onclick, 'search')]"
        ]
        
        print("[DEBUG] 조회 버튼 찾기 시작...")
        for i, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"[DEBUG] 셀렉터 {i+1} 성공: {selector} - {len(elements)}개 발견")
                    for j, elem in enumerate(elements):
                        print(f"  요소 {j+1}: visible={elem.is_displayed()}, enabled={elem.is_enabled()}")
                else:
                    print(f"[DEBUG] 셀렉터 {i+1} 실패: {selector}")
            except Exception as e:
                print(f"[DEBUG] 셀렉터 {i+1} 오류: {selector} - {e}")

    def click_lookup(self):
        try:
            print("[DEBUG] 조회 버튼 찾기 시작...")
            
            # 보이는 조회 버튼만 찾기
            selectors = [
                "//img[@alt='조회' and not(contains(@style,'display:none') or contains(@style,'visibility:hidden'))]",
                "//img[contains(@src, 'btn_blue_lookup.png') and not(contains(@style,'display:none') or contains(@style,'visibility:hidden'))]"
            ]
            
            lookup_btn = None
            for selector in selectors:
                try:
                    # 모든 요소를 찾아서 보이는 것만 선택
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            lookup_btn = element
                            print(f"[INFO] 보이는 조회 버튼 발견: {selector}")
                            break
                    if lookup_btn:
                        break
                except Exception as e:
                    print(f"[DEBUG] 셀렉터 오류: {e}")
                    continue
            
            # 대안: 직접 visible한 요소만 필터링
            if not lookup_btn:
                try:
                    all_lookup_buttons = self.driver.find_elements(By.XPATH, "//img[@alt='조회']")
                    for btn in all_lookup_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            lookup_btn = btn
                            print("[INFO] 필터링으로 보이는 조회 버튼 발견")
                            break
                except Exception as e:
                    print(f"[ERROR] 필터링 중 오류: {e}")
            
            if not lookup_btn:
                raise Exception("보이는 조회 버튼을 찾을 수 없습니다")
            
            # 스크롤하여 버튼이 화면 중앙에 오도록
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", lookup_btn)
            time.sleep(1)
            
            # 클릭 시도
            try:
                lookup_btn.click()
                print("[INFO] 일반 클릭 성공")
            except Exception as e:
                print(f"[DEBUG] 일반 클릭 실패: {e}, JavaScript 클릭 시도")
                self.driver.execute_script("arguments[0].click();", lookup_btn)
                print("[INFO] JavaScript 클릭 성공")
            
            # 테이블 로딩 대기
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "tableListChart"))
            )
            
            time.sleep(2)
            print("[INFO] 조회 완료")
            
        except Exception as e:
            screenshot_path = f"lookup_error_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"[ERROR] 조회 실패 - 스크린샷: {screenshot_path}")
            print(f"[ERROR] 오류 내용: {e}")
            raise e



    def extract_table(self, table_id='tableListChart') -> pd.DataFrame:
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table', {'id': table_id})

            if table is None:
                raise ValueError(f"[ERROR] ID '{table_id}' 테이블이 페이지에 존재하지 않음")

            rows = []

            for tr in table.select("tbody tr"):
                cols = [td.get_text(strip=True).replace(',', '') for td in tr.find_all(['td', 'th'])]
                if len(cols) == 16:
                    left = cols[:8]
                    right = cols[8:]
                    rows.append(left)
                    rows.append(right)
                elif len(cols) == 8:
                    rows.append(cols)
                else:
                    print(f"[WARN] 비정상 행 무시됨 (컬럼 수: {len(cols)})")

            columns = [
                'Time', 'Usage_kWh', 'MaxDemand_kW', 'ReactivePower_Lead', 'ReactivePower_Lag',
                'CO2_t', 'PowerFactor_Lead', 'PowerFactor_Lag'
            ]

            # 컬럼 수 검사
            for row in rows:
                if len(row) != len(columns):
                    raise ValueError(f"[ERROR] 일부 행의 컬럼 수가 예상({len(columns)})과 다릅니다: {len(row)}")

            df = pd.DataFrame(rows, columns=columns)
            print(f"[INFO] 테이블 데이터 {len(df)}건 추출 완료")
            return df

        except Exception as e:
            print(f"[ERROR] 테이블 추출 실패: {e}")
            raise

