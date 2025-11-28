# utils.py
import os
from datetime import datetime, timedelta
import pandas as pd

def ensure_dir_exists(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"[ERROR] 디렉토리 생성 실패: {path}, 에러: {e}")

def generate_date_range(start_date_str, end_date_str, date_format='%Y-%m-%d'):
    try:
        start_date = datetime.strptime(start_date_str, date_format)
        end_date = datetime.strptime(end_date_str, date_format)
    except ValueError as ve:
        raise ValueError(f"[ERROR] 날짜 형식 오류: '{start_date_str}' 또는 '{end_date_str}'는 {date_format} 형식이어야 함. 에러: {ve}")

    if start_date > end_date:
        raise ValueError(f"[ERROR] 시작일({start_date_str})이 종료일({end_date_str})보다 늦습니다.")

    while start_date <= end_date:
        yield start_date.strftime(date_format)
        start_date += timedelta(days=1)

def fix_datetime(row):
    try:
        if row['Time'] == '24:00':
            date = pd.to_datetime(row['Date']) + pd.Timedelta(days=1)
            return date.strftime('%Y-%m-%d') + ' 00:00'
        else:
            return row['Date'] + ' ' + row['Time']
    except Exception as e:
        raise ValueError(f"[ERROR] DateTime 생성 실패 - Date: {row.get('Date')}, Time: {row.get('Time')}, 에러: {e}")


