import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# [1. 데이터 불러오기 및 2. 날짜 전처리]
# ---------------------------------------------------------
# @st.cache_data 데코레이터: 데이터를 한 번만 불러와서 메모리에 저장(캐싱)합니다.
# 앱을 조작할 때마다 파일을 다시 다운로드하지 않으므로 앱이 매우 빠릅니다.
@st.cache_data
def load_and_preprocess_data():
    # 깃허브에 있는 CSV 파일 주소
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    
    # pandas를 사용해 CSV 파일을 표(데이터프레임) 형태로 불러오기
    df = pd.read_csv(url)
    
    # 결측치(비어있는 값)가 있는 행 삭제하기
    df = df.dropna()
    
    # "기준일자" 컬럼을 글자에서 날짜(datetime) 형식으로 바꾸기
    df['기준일자'] = pd.to_datetime(df['기준일자'])
    
    # 전체 데이터를 "기준일자" 순서대로(과거에서 최신순으로) 정렬하기
    df = df.sort_values(by='기준일자')
    
    return df

# 함수를 실행하여 데이터프레임(df) 가져오기
df = load_and_preprocess_data()


# ---------------------------------------------------------
# 웹앱 화면 구성 시작
# ---------------------------------------------------------
st.title("🍿 박스오피스 영화 분석 앱")
st.write("스트림릿과 Plotly를 활용한 데이터 시각화 대시보드입니다.")

# ---------------------------------------------------------
# [3. 영화 선택 기능]
# ---------------------------------------------------------
# '누적관객수'를 기준으로 영화명 정렬하기
# 영화별로 가장 높은 누적관객수를 구한 뒤, 내림차순(큰 숫자부터)으로 정렬합니다.
movie_max_audience = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False)

# 정렬된 영화 이름들만 뽑아서 리스트로 만들기 (중복 없음)
movie_list = movie_max_audience.index.tolist()

# 화면에 드롭다운(선택 상자)을 만들고 사용자가 영화를 고르게 하기
selected_movie = st.selectbox("분석할 영화를 선택해 주세요:", movie_list)

# 사용자가 선택한 영화 데이터만 추려내기
filtered_df = df[df['영화명'] == selected_movie]


# ---------------------------------------------------------
# [4. 선그래프 그리기 및 5. 구역 나누기]
# ---------------------------------------------------------

# 첫 번째 그래프 구역
st.subheader(f"📈 1. '{selected_movie}' 일별 관객수 추이")

# Plotly를 이용해 선 그래프 만들기 (x축: 기준일자, y축: 해당일관객수)
fig1 = px.line(filtered_df, x='기준일자', y='해당일관객수', markers=True)

# 스트림릿 화면에 만들어진 그래프 띄우기
st.plotly_chart(fig1, use_container_width=True)

# 그래프 아래에 분석 내용을 적을 자리 만들기
st.info("💡 이 그래프로 알 수 있는 것: (이곳에 데이터 분석 결과나 인사이트를 한 문장으로 적어주세요.)")

st.divider() # 구역을 나누는 가로줄 긋기

# 두 번째 그래프 구역 (앞으로 추가할 자리)
st.subheader("📊 2. (추가 분석 그래프 자리)")
st.write("여기에 새로운 그래프(예: 누적관객수 변화, 다른 영화와의 비교 등)를 추가할 수 있습니다.")

# 두 번째 그래프 아래에 분석 내용을 적을 자리 만들기
st.info("💡 이 그래프로 알 수 있는 것: (이곳에 데이터 분석 결과나 인사이트를 한 문장으로 적어주세요.)")
# ---------------------------------------------------------
# [4. 선그래프 그리기 및 5. 구역 나누기] (아래쪽 이어서)
# ---------------------------------------------------------

st.divider() # 구역을 나누는 가로줄 긋기

# 두 번째 그래프 구역
st.subheader(f"📊 2. '{selected_movie}' 누적관객수 변화")

# Plotly를 이용해 영역 차트 만들기 (x축: 기준일자, y축: 누적관객수)
fig2 = px.area(filtered_df, x='기준일자', y='누적관객수', 
               color_discrete_sequence=['#636EFA']) # 색상 지정 (원하는 색상으로 변경 가능)

# 스트림릿 화면에 만들어진 영역 차트 띄우기
st.plotly_chart(fig2, use_container_width=True)

# 두 번째 그래프 아래에 분석 내용을 적을 자리 만들기
st.info("💡 이 그래프로 알 수 있는 것: (예: 특정 공휴일이나 주말을 기점으로 누적관객수가 가파르게 상승하는 구간을 확인할 수 있습니다.)")

# ---------------------------------------------------------
# [6. 세 번째 그래프: (20일 이상 등장) TOP 5 영화 다중 선 그래프]
# ---------------------------------------------------------

st.divider() # 구역을 나누는 가로줄 긋기

st.subheader("📈 3. 장기 흥행(20일 이상) TOP 5 영화 누적관객수 비교")

# 1. 영화별 등장 일수(데이터에 등장한 횟수) 계산하기
movie_counts = df['영화명'].value_counts()

# 2. 등장 일수가 20일 이상인 영화 목록 필터링하기
movies_over_20days = movie_counts[movie_counts >= 20].index

# 3. 20일 이상 등장한 영화들 중에서만 누적관객수 기준 TOP 5 영화 뽑기
top5_filtered_movies = (
    df[df['영화명'].isin(movies_over_20days)]
    .groupby('영화명')['누적관객수'].max()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

# 4. 선별된 TOP 5 영화의 데이터만 추출하기
top5_df = df[df['영화명'].isin(top5_filtered_movies)]

# 5. 다중 선 그래프 그리기 (x축: 기준일자, y축: 누적관객수, 색상: 영화명)
fig3 = px.line(top5_df, 
               x='기준일자', 
               y='누적관객수', 
               color='영화명', # 영화별로 다른 색상과 범례 자동 생성
               markers=False)

# 6. 스트림릿 화면에 만들어진 다중 선 그래프 띄우기
st.plotly_chart(fig3, use_container_width=True)

# 7. 그래프 아래에 분석 내용을 적을 자리 만들기
st.info("💡 이 그래프로 알 수 있는 것: (예: 20일 이상 상위권에 머무른 장기 흥행작 중에서, 개봉 초반 관객 수 모객 속도와 최종 완만해지는 구간의 누적 관객 수 차이를 한눈에 비교할 수 있습니다.)")














# ---------------------------------------------------------
# [7. 네 번째 그래프: 전체 관객수 합계 및 7일 이동평균선]
# ---------------------------------------------------------

st.divider() # 구역을 나누는 가로줄 긋기

st.subheader("📉 4. 전체 박스오피스 관객수 추이 (7일 이동평균)")

# 1. 기준일자별로 전체 영화의 해당일관객수 합계 계산하기
daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()

# 2. 7일 이동평균(Rolling Mean) 계산하기
# 최근 7일간의 데이터를 평균 내어 주말/평일 변동 효과를 부드럽게 만들어 줍니다.
daily_total['7일이동평균'] = daily_total['해당일관객수'].rolling(window=7).mean()

# 3. Plotly graph_objects를 사용해 두 개의 선을 겹쳐서 그리기
import plotly.graph_objects as go

fig4 = go.Figure()

# ① 원본 데이터 선 (연한 하늘색, 얇은 선)
fig4.add_trace(go.Scatter(
    x=daily_total['기준일자'],
    y=daily_total['해당일관객수'],
    mode='lines',
    name='일별 총 관객수 (원본)',
    line=dict(color='lightblue', width=1.5),
    opacity=0.6 # 투명도를 살짝 주어 연하게 만듭니다.
))

# ② 7일 이동평균 선 (진한 빨간색, 두꺼운 선)
fig4.add_trace(go.Scatter(
    x=daily_total['기준일자'],
    y=daily_total['7일이동평균'],
    mode='lines',
    name='7일 이동평균',
    line=dict(color='#E50914', width=3) # 강조할 색상과 두께 설정
))

# 그래프 레이아웃 설정 (축 이름 지정 및 마우스 호버 효과)
fig4.update_layout(
    xaxis_title='기준일자',
    yaxis_title='해당일 총 관객수',
    hovermode='x unified' # 마우스를 올렸을 때 두 선의 값을 동시에 비교
)

# 4. 스트림릿 화면에 만들어진 그래프 띄우기
st.plotly_chart(fig4, use_container_width=True)

# 5. 그래프 아래에 분석 내용을 적을 자리 만들기
st.info("💡 이 그래프로 알 수 있는 것: (예: 주말과 평일의 일시적인 관객수 등락을 제외하고, 전체 영화 시장의 성수기/비성수기 흐름과 전반적인 시장 규모의 변화 트렌드를 한눈에 파악할 수 있습니다.)")
