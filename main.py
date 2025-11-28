#main.py
from selenium import webdriver
from web_crawler import WebCrawler
import data_processor
from config import *
import utils
from datetime import datetime
import os
from googleapiclient.errors import HttpError
import time 
from selenium.common.exceptions import TimeoutException
import google_service as gcp 

def main():
    # 1. Firestore에서 크롤링 메타정보 가져오기
    firestore_data = gcp.get_firestore_data('kepco_power')
    for doc in firestore_data:
        doc_data = doc._data
        login_url = doc_data.get("login_url")
        folder_id = doc_data.get("folder_id")
        table_id = doc_data.get("table_id")
        secret_name = doc_data.get("secret_name")

    # 2. Secret Manager에서 로그인 정보 가져오기
    secret_data = gcp.get_secretmanager_data(secret_name)  # secret_data는 JSON 배열로 파싱됨
    log_infos = []
    for account in secret_data:
        log_info = {
            'business_unit': account["business_unit"],
            'site_unit': account["site_unit"],
            'factory': account["factory"],
            'login_id': account["ID"],
            'login_pw': account["PW"]
        }
        log_infos.append(log_info)
    print("[START] KEPCO 데이터 수집 작업 시작")
    utils.ensure_dir_exists(GOOGLE_DRIVE_FOLDER_ID) 

    print("[INFO] Google Sheet에서 설정 데이터 읽는 중...")
    records = google.read_google_sheet()
    print(f"[INFO] 총 {len(records)}개의 프로젝트 레코드 로드됨")

    dfs_15m = []
    dfs_30m = []

    print("[INFO] Chrome 드라이버 실행 중...")
    options = webdriver.ChromeOptions()
    options.add_argument("--guest")
    driver = webdriver.Chrome(options=options)
    crawler = WebCrawler(driver)

    for idx, row in enumerate(records, 1):
        try:
            print(f"\n[INFO][{idx}/{len(records)}] 프로젝트 시작: Site_Unit={row['Site_Unit']}, Factory={row.get('Factory', '')}")

            # 날짜 유효성 체크
            start_date = row.get('start_date')
            end_date = row.get('end_date')

            if not start_date or not end_date or start_date > end_date:
                print(f"[SKIP] 잘못된 날짜 범위: Site_Unit={row.get('Site_Unit')}, Factory={row.get('Factory', '')}")
                continue

            crawler.handle_popup()

            # 로그인 시도
            try:
                print("[INFO] 로그인 시도 중...")
                crawler.login(
                    user_id=row['ID'],
                    password=row['PW'],
                    login_url=LOGIN_URL,
                    id_selector=ID_SELECTOR,
                    pw_selector=PW_SELECTOR,
                    submit_selector=SUBMIT_SELECTOR
                )
            except Exception as e:
                print(f"[ERROR] 로그인 실패: Site_Unit={row['Site_Unit']}, Factory={row.get('Factory', '')}, 에러: {e}")
                continue

            print("[INFO] 데이터 페이지로 이동 중...")
            crawler.move_to_data_page(DATA_PAGE_URL)

            # 날짜 범위 순회
            for current_date in utils.generate_date_range(start_date, end_date):
                print(f"[INFO] 날짜 {current_date} 처리 중...")

                try:
                    crawler.set_date(current_date)
                    crawler.wait_for_background_disappear()

                    # 1. 15분 모드
                    print("    [STEP] 15분 모드 조회 시작")
                    crawler.set_mode_15m()
                    print("15분 선택 완료")
                    time.sleep(2)
                    crawler.click_lookup()
                    print("    [STEP] 15분 모드 조회 버튼 클릭")
                    crawler.wait_for_background_disappear()
                    df_15m = crawler.extract_table()
                    df_15m = data_processor.process_dataframe(
                        df_15m, '15m', row['Project'], row['Site_Unit'], row.get('Factory', ''), current_date
                    )
                    dfs_15m.append(df_15m)
                    print(df_15m)
                    print(f"15분 데이터 행 수: {len(df_15m)}")
                    print("    [DONE] 15분 데이터 처리 완료")

                    # # 2. 30분 모드
                    print("    [STEP] 30분 모드 조회 시작")
                    crawler.set_mode_30m()
                    time.sleep(2)
                    crawler.click_lookup()
                    crawler.wait_for_background_disappear()
                    df_30m = crawler.extract_table()
                    df_30m = data_processor.process_dataframe(
                        df_30m, '30m', row['Project'], row['Site_Unit'], row.get('Factory', ''), current_date
                    )
                    dfs_30m.append(df_30m)
                    print(f"30분 데이터 행 수: {len(df_30m)}")
                    print("    [DONE] 30분 데이터 처리 완료")

                except Exception as e:
                    print(f"[ERROR] 날짜 {current_date} 처리 실패: {e}")
                    continue

        except Exception as e:
            print(f"[ERROR] 전체 처리 중 예외 발생: Site_Unit={row.get('Site_Unit')}, 에러: {e}")

    driver.quit()
    print("\n[INFO] 크롬 드라이버 종료")

    # 결과 병합 및 저장
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 15분 데이터 처리
    if dfs_15m:
        try:
            print("[INFO] 15분 데이터 병합 중...")
            final_15m = data_processor.merge_dataframes(dfs_15m, '15m')
            file_name_15m = f'kepco_power_15m_{current_time}.xlsx'
            path_15m = os.path.join(r'D:\RPA\Download\KEPCO', file_name_15m)
            final_15m.to_excel(path_15m, index=False)
            google.upload_to_drive(path_15m, file_name_15m)
            print(f"[UPLOAD] 15분 데이터 업로드 완료: {file_name_15m}")
        except HttpError as e:
            print(f"[ERROR] 15분 Google Drive 업로드 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 15분 병합 또는 저장 중 오류 발생: {e}")

    # # 30분 데이터 처리
    if dfs_30m:
        try:
            print("[INFO] 30분 데이터 병합 중...")
            final_30m = data_processor.merge_dataframes(dfs_30m, '30m')
            file_name_30m = f'kepco_power_30m_{current_time}.xlsx'
            path_30m = os.path.join(r'D:\RPA\Download\KEPCO', file_name_30m)
            final_30m.to_excel(path_30m, index=False)
            google.upload_to_drive(path_30m, file_name_30m)
            print(f"[UPLOAD] 30분 데이터 업로드 완료: {file_name_30m}")
        except HttpError as e:
            print(f"[ERROR] 30분 Google Drive 업로드 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 30분 병합 또는 저장 중 오류 발생: {e}")

    print("\n[INFO] BigQuery 변환 시작")

    if dfs_15m:  # 리스트가 비어있지 않은 경우
        # 먼저 DataFrame들을 병합
        merged_15m = data_processor.merge_dataframes(dfs_15m, '15m')
        # 병합된 DataFrame을 BigQuery용으로 변환
        transformed_15m = upload_bigquery.transform_for_bigquery(merged_15m, '15m')
        print("[INFO] 15분 데이터 BigQuery 변환 완료")
    else:
        print("[INFO] 15분 데이터가 없어 BigQuery 변환을 건너뜁니다.")

    if dfs_30m:  # 리스트가 비어있지 않은 경우
        # 먼저 DataFrame들을 병합
        merged_30m = data_processor.merge_dataframes(dfs_30m, '30m')
        # 병합된 DataFrame을 BigQuery용으로 변환
        transformed_30m = upload_bigquery.transform_for_bigquery(merged_30m, '30m')
        print("[INFO] 30분 데이터 BigQuery 변환 완료")
    else:
        print("[INFO] 30분 데이터가 없어 BigQuery 변환을 건너뜁니다.")

    # BigQuery 업로드
    # try:
    #     if dfs_15m:
    #         upload_bigquery.upload_to_bigquery(
    #             transformed_15m,
    #             credentials_path=r'D:\path\to\service_account.json',
    #             write_disposition='WRITE_APPEND'
    #         )
    #     if dfs_30m:
    #         upload_bigquery.upload_to_bigquery(
    #             transformed_30m,
    #             credentials_path=r'D:\path\to\service_account.json',
    #             write_disposition='WRITE_APPEND'
    #         )
    # except Exception as e:
    #     print(f"[ERROR] BigQuery 업로드 실패: {e}")
    #     raise

    
    print("\n[SUCCESS] 전체 KEPCO 작업 완료")

if __name__ == "__main__":
    main()
