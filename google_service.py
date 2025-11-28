# google_service.py
import io
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth
from google.cloud import bigquery
from google.auth.transport.requests import Request 
from google.cloud import secretmanager
from google.cloud import firestore
from itertools import zip_longest
import json
# 기존 config에서 필요한 값들만 임포트
from config import SCOPES, SHEET_ID, SHEET_RANGE

from datetime import datetime, timezone

def get_credentials():
    """
    Cloud Run 환경에서 서비스 계정 자격 증명을 로드합니다 (ADC 사용).
    Google Sheets, Drive 등에 접근하기 위해 필요한 SCOPES를 지정합니다.
    """
    try:
        # ADC(Application Default Credentials)를 사용하여 Cloud Run 서비스 계정의
        # 자격 증명을 자동으로 로드합니다.
        creds, project = google.auth.default(scopes=SCOPES)
        
        # 만료되었을 경우 갱신을 시도합니다. (대부분 자동으로 처리되지만, 안전을 위해 유지)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        return creds
        
    except Exception as e:
        # 클라우드런 배포 후, 이 오류가 발생하면 서비스 계정 권한(IAM) 설정을 확인해야 합니다.
        print(f"[ERROR] 인증 정보 로드 실패. Cloud Run 서비스 계정 권한(IAM)을 확인하세요: {e}")
        raise e
    


# Get data from firestore  
def get_firestore_data(collection_name):

    firestore_client = firestore.Client()
    collection_ref = firestore_client.collection(collection_name)
    firestore_data = collection_ref.get()
    firestore_client.close()
    return firestore_data


# Get data from secretmanager  
def get_secretmanager_data(secret_name):
    
    secret_client = secretmanager.SecretManagerServiceClient()
    
    response = secret_client.access_secret_version(request={"name": secret_name})
    payload = response.payload.data.decode("UTF-8")

    return json.loads(payload)



def read_google_sheet() -> list[dict]:
    """
    Google Sheet에서 데이터를 읽어와 리스트로 반환
    """
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets() # type: ignore

    result = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range=SHEET_RANGE
    ).execute()

    values = result.get('values', [])

    if not values or len(values) < 2:
        # 데이터가 없어도 에러 대신 빈 리스트 반환이 나을 수 있음 (선택 사항)
        print("[WARN] 시트에 데이터가 없습니다.")
        return []

    header = values[0]
    
    # [수정] zip 대신 zip_longest 사용
    # fillvalue='' 옵션으로 비어있는 셀은 빈 문자열로 채움
    data = [
        dict(zip_longest(header, row, fillvalue='')) 
        for row in values[1:]
    ]

    return data


def upload_to_drive(file_path, file_name, folder_id): 
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id]  # [변경점] 전달받은 folder_id 사용
    }

    media = MediaFileUpload(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        resumable=True
    )

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
    ).execute()

    return uploaded.get('id')


def upload_to_bigquery(df: pd.DataFrame, full_table_id: str, write_disposition: str = 'WRITE_APPEND') -> None:
    """
    Args:
        full_table_id (str): "프로젝트ID.데이터셋ID.테이블ID" 형태의 전체 경로
    """
    try:
        project_id = full_table_id.split('.')[0]
        credentials, _ = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=project_id)

        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            source_format=bigquery.SourceFormat.PARQUET,
            autodetect=True 
        )

        # 4. DataFrame을 메모리에서 Parquet로 변환
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, allow_truncated_timestamps=True, coerce_timestamps='us')
        buffer.seek(0)

        # 5. 업로드 (full_table_id 그대로 사용)
        print(f"[INFO] BigQuery 업로드 시작: {full_table_id}, 모드: {write_disposition}")
        job = client.load_table_from_file(buffer, full_table_id, job_config=job_config)
        job.result()  # 완료 대기

        # 6. 결과 확인
        table = client.get_table(full_table_id)
        print(f"[SUCCESS] {full_table_id}에 {job.output_rows}행 업로드 완료. (총 {table.num_rows}행)")
        
    except Exception as e:
        print(f"[ERROR] BigQuery 업로드 실패: {e}")
        raise


