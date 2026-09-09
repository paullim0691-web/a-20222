import datetime
import requests
import pandas as pd
import streamlit as st

# Streamlit 기본 페이지 설정 (제목 및 레이아웃 설정)
st.set_page_config(page_title="어제 박스오피스", layout="wide")

st.title("🎬 어제자 박스오피스 순위")

# 1. 한국 시간(KST, UTC+9) 기준 계산
# 배포 서버의 기본 시계가 해외 기준(UTC)이어도 정확한 한국 어제 날짜를 구합니다.
kst_timezone = datetime.timezone(datetime.timedelta(hours=9))
now_in_kst = datetime.datetime.now(tz=kst_timezone)
yesterday_in_kst = now_in_kst - datetime.timedelta(days=1)

# API 요청에 필요한 YYYYMMDD 형식 문자열로 변환 (예: 20260330)
target_date_str = yesterday_in_kst.strftime("%Y%m%d")
display_date_str = yesterday_in_kst.strftime("%Y년 %m월 %d일")

st.caption(f"📅 조회 기준일: {display_date_str} (한국 시간 기준 어제)")

# 2. 데이터 수집 함수 (1시간 동안 캐싱 처리)
# 같은 날짜 요청이 오면 API를 다시 부르지 않고 기존 저장 데이터를 보여줍니다.
@st.cache_data(ttl=3600)
def get_box_office_data(target_dt):
    # 비밀 금고(secrets)에서 KOBIS_KEY 가져오기
    if "KOBIS_KEY" not in st.secrets:
        return None, "secrets.toml 또는 Cloud Secrets 설정에서 'KOBIS_KEY'를 찾을 수 없습니다."

    api_key = st.secrets["KOBIS_KEY"]
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    
    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        # KOBIS API 호출
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # [오류 처리 1] API 키 오류 시 faultInfo 상자가 들어오는 경우
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "인증 오류가 발생했습니다.")
            return None, f"KOBIS API 오류 발생: {error_message}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # [오류 처리 2] 영화 목록이 비어 있는 경우
        if not daily_list:
            return None, "해당 날짜의 박스오피스 데이터가 존재하지 않거나 집계 중입니다."

        return daily_list, None

    except requests.exceptions.RequestException as req_err:
        # [오류 처리 3] 네트워크 요청 실패 시
        return None, f"네트워크 연결에 실패했습니다: {req_err}"
    except Exception as err:
        return None, f"데이터 처리 중 알 수 없는 오류가 발생했습니다: {err}"

# 3. 데이터 불러오기 및 예외 처리 안내
raw_data, error_msg = get_box_office_data(target_date_str)

if error_msg:
    # 요청 실패 시 안내 메시지 출력
    st.error(error_msg)
    st.warning(
        "💡 **문제가 발생했을 때 확인해야 할 사항:**\n"
        "1. Streamlit Secrets 설정에 `KOBIS_KEY` 가 올바르게 입력되어 있는지 확인하세요.\n"
        "2. KOBIS 오픈 API 마이페이지에서 발급받은 키의 상태가 활성화되어 있는지 확인하세요.\n"
        "3. 날짜 집계 시점에 따라 아직 어제 데이터가 업데이트되지 않았을 수 있습니다."
    )
else:
    # 4. 데이터 가공 및 숫자형 변환
    df = pd.DataFrame(raw_data)

    # 문자열로 들어오는 숫자 데이터를 정수(int) 타입으로 변환
    numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 순위 기준 오름차순 정렬
    df = df.sort_values("rank").reset_index(drop=True)

    # 5. 1위 영화 지표 카드 세 장 표시
    top_1 = df.iloc[0]
    st.subheader(f"🏆 1위 영화: {top_1['movieNm']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="어제 관객수", value=f"{top_1['audiCnt']:,} 명")
    col2.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    col3.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.markdown("---")

    # 6. 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5편")
    top5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
    st.bar_chart(top5_df)

    st.markdown("---")

    # 7. 전체 순위 표 출력
    st.subheader("📋 어제 박스오피스 순위 표")
    
    # 필요한 컬럼만 추출 및 이름 변경
    table_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    table_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

    # 표 형식 설정 및 표시
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적관객": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        }
    )
