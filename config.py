# config.py

LOGIN_URL = "https://pp.kepco.co.kr/intro.do"
DATA_PAGE_URL = "https://pp.kepco.co.kr/rs/rs0101N.do?menu_id=O010201"
ID_SELECTOR = "#RSA_USER_ID"
PW_SELECTOR = "#RSA_USER_PWD"
SUBMIT_SELECTOR = ".intro_btn"
SHEET_ID = '1Df6PHyY6k5hkqsGUA9fFJO9THS3zg5qxNPVvYy-u8-U'
SHEET_RANGE = 'Period!A1:J'
GOOGLE_DRIVE_FOLDER_ID = "1zoLPlU3rovSdiyUAboSoT29ZK-81fIth"
# CLIENT_SECRET_FILE = r'D:\RPA\Download\client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PICKLE = 'token.pickle'
BQ_PROJECT_ID = "kr-ops-vk-operations"
BQ_DATASET_ID = "99999_tests"
BQ_TABLE_ID = "data_raw_kepco"
