# data_processor.py
import pandas as pd
from datetime import datetime, timezone 
import utils

def add_metadata(df: pd.DataFrame, project: str, customer: str, factory: str, date: str) -> pd.DataFrame:
    df['Project'] = project
    df['Site_Unit'] = customer
    df['Factory'] = factory if factory else ''
    df['Date'] = date
    return df

# data_processor.py
def process_dataframe(df, mode, project, site_unit, factory, current_date):
    if df.empty:
        raise ValueError("[ERROR] 입력 데이터프레임이 비어 있습니다.")

    expected_columns = {
        'Usage_kWh', 'MaxDemand_kW', 'ReactivePower_Lead', 'ReactivePower_Lag',
        'CO2_t', 'PowerFactor_Lead', 'PowerFactor_Lag'
    }

    if not expected_columns.issubset(set(df.columns)):
        raise ValueError(f"[ERROR] 예상 컬럼이 누락됨. 현재 컬럼: {list(df.columns)}")

    df = add_metadata(df, project, site_unit, factory, current_date)

    if mode == '30m':
        df = df.rename(columns={
            'Usage_kWh': 'Electricity consumption_30m',
            'MaxDemand_kW': 'Peak power_30m',
            'ReactivePower_Lead': 'Leading reactive power_30m',
            'ReactivePower_Lag': 'Lagging reactive power_30m',
            'CO2_t': 'CO2_30m',
            'PowerFactor_Lead': 'Leading power factor_30m',
            'PowerFactor_Lag': 'Lagging power factor_30m'
        })
    elif mode == '15m':
        df = df.rename(columns={
            'Usage_kWh': 'Electricity consumption',
            'MaxDemand_kW': 'Peak power',
            'ReactivePower_Lead': 'Leading reactive power',
            'ReactivePower_Lag': 'Lagging reactive power',
            'CO2_t': 'CO2',
            'PowerFactor_Lead': 'Leading power factor',
            'PowerFactor_Lag': 'Lagging power factor'
        })
    else:
        raise ValueError(f"[ERROR] 지원되지 않는 모드: {mode}")

    return df



def merge_dataframes(dfs, mode):
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df['DateTime'] = merged_df.apply(utils.fix_datetime, axis=1)
    merged_df['DateTime'] = pd.to_datetime(merged_df['DateTime'])

    if mode == '30m':
        column_order = [
            'Date', 'Time', 'DateTime', 
            'Electricity consumption_30m', 'Peak power_30m',
            'Leading reactive power_30m', 'Lagging reactive power_30m',
            'CO2_30m', 'Leading power factor_30m', 'Lagging power factor_30m',
            'Project', 'Site_Unit', 'Factory'
        ]
    else:
        column_order = [
            'Date', 'Time', 'DateTime', 
            'Electricity consumption', 'Peak power', 
            'Leading reactive power', 'Lagging reactive power',
            'CO2', 'Leading power factor', 'Lagging power factor',
            'Project', 'Site_Unit', 'Factory'
        ]

    return merged_df[column_order]


def transform_for_bigquery(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """
    Wide format → Long format with units for BigQuery
    """
    if mode == '30m':
        value_columns = {
            'Electricity consumption_30m': ('Electricity consumption', 'kWh'),
            'Peak power_30m': ('Peak power', 'kW'),
            'Leading reactive power_30m': ('Leading reactive power', 'kVarh'),
            'Lagging reactive power_30m': ('Lagging reactive power', 'kVarh'),
            'CO2_30m': ('CO2', 'tCO2'),
            'Leading power factor_30m': ('Leading power factor', '%'),
            'Lagging power factor_30m': ('Lagging power factor', '%')
        }
    else:
        # 15m 모드 (원래 컬럼명 사용)
        value_columns = {
            'Electricity consumption': ('Electricity consumption', 'kWh'),
            'Peak power': ('Peak power', 'kW'),
            'Leading reactive power': ('Leading reactive power', 'kVarh'),
            'Lagging reactive power': ('Lagging reactive power', 'kVarh'),
            'CO2': ('CO2', 'tCO2'),
            'Leading power factor': ('Leading power factor', '%'),
            'Lagging power factor': ('Lagging power factor', '%')
        }

    id_vars = ['DateTime', 'Project', 'Site_Unit', 'Factory']
    
    # DataFrame의 복사본으로 작업하여 SettingWithCopyWarning 방지
    temp_df = df.copy() 
    
    melted = temp_df.melt(
        id_vars=id_vars,
        value_vars=[col for col in value_columns.keys() if col in temp_df.columns], # 존재하는 컬럼만 melt
        var_name='original_column',
        value_name='measure_value'
    )
    
    # melt 결과가 비어있으면 빈 DataFrame 반환
    if melted.empty:
        print("[WARN] BigQuery 변환 결과, 데이터가 비어있습니다.")
        return pd.DataFrame(columns=[
            'measure_time', 'measure_point', 'measure_value', 'measure_unit',
            'country', 'source_name', 'business_unit', 'site_unit', 'factory',
            'insertion_time'
        ])

    # measure_point, measure_unit 매핑 적용
    melted['measure_point'] = melted['original_column'].apply(lambda x: value_columns[x][0])
    melted['measure_unit'] = melted['original_column'].apply(lambda x: value_columns[x][1])

    melted['measure_value'] = pd.to_numeric(melted['measure_value'], errors='coerce')

    # 데이터 타입 변환 및 정리
    # 'DateTime' 컬럼이 문자열인 경우 datetime 객체로 변환
    try:
        melted['measure_time'] = pd.to_datetime(melted['DateTime'], format='%Y-%m-%d %H:%M')
    except:
        # 만약 형식이 다를 경우, pandas가 자동으로 추론하도록 시도
        melted['measure_time'] = pd.to_datetime(melted['DateTime'], errors='coerce') 

    # 기타 메타데이터 추가
    melted['country'] = 'South Korea'
    melted['source_name'] = 'kepco_power_planner_rpa'
    melted['business_unit'] = melted['Project']
    melted['site_unit'] = melted['Site_Unit']
    melted['factory'] = melted['Factory']
    # 삽입 시간은 UTC로 명시
    melted['insertion_time'] = datetime.now(timezone.utc) 

    # 최종 컬럼 순서
    final_cols = [
        'measure_time', 'measure_point', 'measure_value', 'measure_unit',
        'country', 'source_name',
        'business_unit', 'site_unit', 'factory',
        'insertion_time'
    ]

    result = melted[final_cols]
    
    print(f"[SUCCESS] BigQuery 변환 완료: {len(result)}행 x {len(result.columns)}열")
    print(f"[DEBUG] 최종 컬럼: {list(result.columns)}")
    
    # 샘플 데이터 출력
    if not result.empty:
        print("\n[SAMPLE] 변환된 데이터 샘플 (처음 5행):")
        print(result.head(5).to_string())
        
        print(f"\n[STATS] 측정항목별 데이터 수:")
        print(result['measure_point'].value_counts().to_string())

    return result