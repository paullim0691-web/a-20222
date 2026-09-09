import datetime
import requests
import pandas as pd
import streamlit as st

# Streamlit 기본 페이지 설정 (제목 및 레이아웃 설정)
st.set_page_config(page_title="일별 박스오피스", layout="wide")

st.title("🎬 일별 박스오피스 순위")

# 1. 한국 시간(KST, UTC+9) 기준 어제 날짜 계산
# 배포 서버 시계 기준이 아닌 한국 시간 기준으로 어제 날짜 구합니다.
kst_timezone = datetime.timezone(datetime.timedelta(hours=9))
now_in_kst = datetime.datetime.now(tz=kst_timezone)
yesterday_in_kst = (now_in_kst - datetime.timedelta(days=1)).date()

# 2. 날짜 선택 달력(Date Input) 생성
# 고를 수 있는 가장 늦은 날짜는 어제(max_value=yesterday_in_kst)로 제한합니다.
selected_date = st.date_input(
    "📅 조회할 날짜를 선택해 주세요",
    value=yesterday_in_kst,
    max_value=yesterday_in_kst,
    min_value=datetime.date(2004, 1, 1), # KOBIS 응답 제공 최소 연도
    help="오늘 및 미래 날짜는 아직 집계 전이므로 선택할 수 없습니다."
)

# API 요청용 YYYYMMDD 날짜 문자열 변환
target_date_str = selected_date.strftime("%Y%m%d")

# 3. 데이터 수집 함수 (선택한 날짜별로 1시간 동안 결과 기억)
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # [오류 처리 1] 인증키 오류 등으로 faultInfo 응답이 올 경우
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "인증 오류가 발생했습니다.")
            return None, f"KOBIS API 오류: {error_message}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # [오류 처리 2] 영화 목록이 비어 있는 경우
        if not daily_list:
            return None, "그날은 아직 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException as req_err:
        return None, f"네트워크 연결에 실패했습니다: {req_err}"
    except Exception as err:
        return None, f"데이터 처리 중 알 수 없는 오류가 발생했습니다: {err}"

# 4. 데이터 불러오기
raw_data, error_msg = get_box_office_data(target_date_str)

if error_msg:
    # 데이터가 없거나 오류 발생 시 안내 메시지 표시
    if error_msg == "그날은 아직 집계 전입니다.":
        st.info(f"💡 {error_msg}")
    else:
        st.error(error_msg)
        st.warning(
            "💡 **확인해 보세요:**\n"
            "1. Streamlit Secrets에 `KOBIS_KEY`가 바르게 설정되어 있는지 확인해 주세요.\n"
            "2. KOBIS 오픈 API 마이페이지에서 키가 활성화 상태인지 확인해 주세요."
        )
else:
    # 5. 데이터 가공 및 숫자 타입 변환
    df = pd.DataFrame(raw_data)

    # 문자열로 온 숫자를 계산/정렬이 가능한 정수(int)형으로 변환
    numeric_columns = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 순위 기준 오름차순 정렬
    df = df.sort_values("rank").reset_index(drop=True)

    # 6. 전날 대비 순위 증감(rankInten) 화살표 표시 가공
    def format_rank_inten(val):
        if val > 0:
            return f"🔺 +{val}"  # 양수: 빨간 위 화살표
        elif val < 0:
            return f"🔹 {val}"   # 음수: 파란 아래 화살표
        else:
            return "-"          # 변동 없음

    df["rank_change"] = df["rankInten"].apply(format_rank_inten)

    # 7. 누적관객 100만 명 이상 영화에 트로피(🏆) 붙이기
    def format_movie_name(row):
        name = row["movieNm"]
        if row["audiAcc"] >= 1_000_000:
            return f"🏆 {name}"
        return name

    df["display_movie_nm"] = df.apply(format_movie_name, axis=1)

    # 8. 1위 영화 지표 카드 세 장
    top_1 = df.iloc[0]
    st.subheader(f"🏆 1위 영화: {top_1['display_movie_nm']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
    col2.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    col3.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.markdown("---")

    # 9. 관객수 상위 5편 막대그래프
    st.subheader("📊 당일 관객수 상위 5편")
    top5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
    st.bar_chart(top5_df)

    st.markdown("---")

    # 10. 전체 박스오피스 순위 표
    st.subheader(f"📋 {selected_date.strftime('%Y년 %m월 %d일')} 박스오피스 순위")
    
    # 출력할 컬럼 선택 및 이름 변경
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
