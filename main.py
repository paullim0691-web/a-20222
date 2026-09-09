import datetime
import requests
import pandas as pd
import streamlit as st

# Streamlit 기본 페이지 설정
st.set_page_config(page_title="일별 박스오피스", layout="wide")

st.title("🎬 일별 박스오피스 순위")

# 1. 한국 시간(KST, UTC+9) 기준 어제 날짜 계산
kst_timezone = datetime.timezone(datetime.timedelta(hours=9))
now_in_kst = datetime.datetime.now(tz=kst_timezone)
yesterday_in_kst = (now_in_kst - datetime.timedelta(days=1)).date()

# 2. 날짜 선택 달력 (최대 선택 가능일: 어제)
selected_date = st.date_input(
    "📅 조회할 날짜를 선택해 주세요",
    value=yesterday_in_kst,
    max_value=yesterday_in_kst,
    min_value=datetime.date(2004, 1, 1),
    help="오늘 및 미래 날짜는 아직 집계 전이므로 선택할 수 없습니다."
)

target_date_str = selected_date.strftime("%Y%m%d")

# 3. 데이터 수집 함수 (1시간 캐싱)
@st.cache_data(ttl=3600)
def get_box_office_data(target_dt):
    if "KOBIS_KEY" not in st.secrets:
        return None, "secrets.toml 또는 Cloud Secrets 설정에서 'KOBIS_KEY'를 찾을 수 없습니다."

    api_key = st.secrets["KOBIS_KEY"]
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    
    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # faultInfo 오류 상자 응답 처리
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "인증 오류가 발생했습니다.")
            return None, f"KOBIS API 오류: {error_message}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        if not daily_list:
            return None, "그날은 아직 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException:
        # req_err를 직접 출력하면 URL에 포함된 KOBIS_KEY가 노출되므로 보안상 커스텀 문구만 반환합니다.
        return None, "KOBIS 서버와 통신할 수 없습니다. 네트워크 상태나 DNS 연결을 확인해 주세요."
    except Exception as err:
        return None, f"데이터 처리 중 오류가 발생했습니다: {err}"

# 4. 데이터 불러오기 및 예외 안내
raw_data, error_msg = get_box_office_data(target_date_str)

if error_msg:
    if error_msg == "그날은 아직 집계 전입니다.":
        st.info(f"💡 {error_msg}")
    else:
        st.error(error_msg)
        st.warning(
            "💡 **점검해 볼 사항:**\n"
            "1. 배포 서버의 일시적인 네트워크/DNS 장애일 수 있으니 앱을 Reboot해 보세요.\n"
            "2. Streamlit Secrets의 `KOBIS_KEY`가 올바른지 확인해 주세요.\n"
            "3. KOBIS 오픈 API 마이페이지에서 키 상태를 점검해 보세요."
        )
else:
    # 5. 데이터 가공
    df = pd.DataFrame(raw_data)

    numeric_columns = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.sort_values("rank").reset_index(drop=True)

    # 순위 증감 화살표 가공
    def format_rank_inten(val):
        if val > 0:
            return f"🔺 +{val}"
        elif val < 0:
            return f"🔹 {val}"
        else:
            return "-"

    df["rank_change"] = df["rankInten"].apply(format_rank_inten)

    # 100만 관객 이상 트로피 표시
    def format_movie_name(row):
        name = row["movieNm"]
        if row["audiAcc"] >= 1_000_000:
            return f"🏆 {name}"
        return name

    df["display_movie_nm"] = df.apply(format_movie_name, axis=1)

    # 6. 1위 영화 지표 카드
    top_1 = df.iloc[0]
    st.subheader(f"🏆 1위 영화: {top_1['display_movie_nm']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
    col2.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    col3.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.markdown("---")

    # 7. 관객수 상위 5편 막대그래프
    st.subheader("📊 당일 관객수 상위 5편")
    top5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
    st.bar_chart(top5_df)

    st.markdown("---")

    # 8. 박스오피스 순위 표
    st.subheader(f"📋 {selected_date.strftime('%Y년 %m월 %d일')} 박스오피스 순위")
    
    table_df = df[["rank", "rank_change", "display_movie_nm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    table_df.columns = ["순위", "변동", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

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
