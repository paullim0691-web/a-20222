import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (깔끔한 카드 및 강조 스타일 적용)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .insight-box {
        background-color: #F0F9FF;
        border-left: 5px solid #0284C7;
        padding: 1rem 1.2rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .insight-title {
        font-weight: 700;
        color: #0369A1;
        font-size: 1.05rem;
        margin-bottom: 0.3rem;
    }
    .insight-text {
        color: #334155;
        font-size: 0.98rem;
        line-height: 1.5;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # 장르 전처리: 세로막대(|) 기호로 여러 개 적힌 영화는 첫 번째 장르만 추출
    df['genre'] = df['genre'].astype(str).apply(lambda x: x.split('|')[0] if '|' in x else x)
    
    # 숫자형 컬럼 변환 및 결측치 처리
    numeric_cols = ['first_scrn', 'first_show', 'first_week_audi', 'total_audi', 'days_in_top10']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 헤더 및 필터 섹션
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🎬 영화 데이터 그래프 도감 2 - 분포와 관계</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">KOBIS 박스오피스 상위권 영화 216편의 데이터로 살펴보는 장르별 분포와 흥행 요인 간의 관계 분석</div>', unsafe_allow_html=True)

# 사이드바 필터
st.sidebar.header("🔍 데이터 필터 옵션")
selected_nations = st.sidebar.multiselect(
    "제작 국가 선택",
    options=sorted(df_raw['nation'].dropna().unique()),
    default=sorted(df_raw['nation'].dropna().unique())
)

selected_genres = st.sidebar.multiselect(
    "장르 선택",
    options=sorted(df_raw['genre'].dropna().unique()),
    default=sorted(df_raw['genre'].dropna().unique())
)

# 필터링 적용
df = df_raw[(df_raw['nation'].isin(selected_nations)) & (df_raw['genre'].isin(selected_genres))].copy()

if df.empty:
    st.warning("선택한 필터 조건에 해당하는 영화 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

# 요약 지표 (Metrics)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("분석 대상 영화 수", f"{len(df):,}편")
with col_m2:
    st.metric("총 관객수 합계", f"{int(df['total_audi'].sum()):,}명")
with col_m3:
    st.metric("평균 Top 10 유지일", f"{df['days_in_top10'].mean():.1f}일")
with col_m4:
    st.metric("평균 개봉 스크린수", f"{int(df['first_scrn'].mean()):,}개")

st.markdown("---")

# -----------------------------------------------------------------------------
# 1. 장르별 영화 편수 (Plotly 도넛 그래프 - 범주형 분포)
# -----------------------------------------------------------------------------
st.subheader("1. 🍩 장르별 영화 편수 분포 (범주형 분포)")

genre_counts = df['genre'].value_counts().reset_index()
genre_counts.columns = ['genre', 'count']

fig1 = px.pie(
    genre_counts,
    names='genre',
    values='count',
    hole=0.45,
    color_discrete_sequence=px.colors.qualitative.Pastel,
    title="장르별 영화 편수 비율"
)

# 마우스 호버 시 편수와 비율 표시
fig1.update_traces(
    textposition='inside',
    textinfo='percent+label',
    hovertemplate="<b>장르: %{label}</b><br>영화 편수: %{value}편<br>비율: %{percent}<extra></extra>"
)

fig1.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    height=450
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        박스오피스 상위권 영화 중 특정 주력 장르(드라마, 액션 등)의 비중이 높게 형성되어 있어, 흥행 시장에서 관객 접근성이 높은 주요 장르 선호도가 뚜렷함을 알 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 장르별 총 관객수 분포 (박스 플롯 - 수치형 분포)
# -----------------------------------------------------------------------------
st.subheader("2. 📊 장르별 총 관객수 분포 (수치형 분포)")

fig2 = px.box(
    df,
    x='genre',
    y='total_audi',
    color='genre',
    points="all",
    hover_name='movieNm',
    hover_data={'total_audi': ':,', 'days_in_top10': True, 'first_scrn': True},
    labels={'genre': '장르', 'total_audi': '총 관객수(명)'},
    title="장르별 총 관객수 분포 및 아웃라이어 영화"
)

fig2.update_layout(
    showlegend=False,
    height=480,
    yaxis_tickformat=','
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        대부분 장르의 관객수 중앙값은 특정 수준에 모여 있으나, 상위 굵직한 흥행 대작(아웃라이어)이 전체 평균 관객수를 이끌고 있음을 확인할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. 개봉 첫 주 관객수 vs 총 관객수 (관계 산점도)
# -----------------------------------------------------------------------------
st.subheader("3. 📈 개봉 첫 주 관객수와 총 관객수의 관계 (흥행 선행 지표)")

fig3 = px.scatter(
    df,
    x='first_week_audi',
    y='total_audi',
    color='genre',
    size='days_in_top10',
    hover_name='movieNm',
    hover_data={'first_week_audi': ':,', 'total_audi': ':,', 'days_in_top10': True},
    labels={
        'first_week_audi': '개봉 첫 주 관객수(명)',
        'total_audi': '최종 총 관객수(명)',
        'genre': '장르',
        'days_in_top10': 'Top 10 유지일'
    },
    title="첫 주 관객수 대비 최종 총 관객수 (점 크기: Top 10 머문 날수)"
)

fig3.update_layout(
    height=500,
    xaxis_tickformat=',',
    yaxis_tickformat=','
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        개봉 첫 주 관객수가 많을수록 최종 총 관객수도 높아지는 강한 양의 상관관계를 보이며, 특히 버블 크기(Top 10 유지일)가 큰 영화일수록 지속적인 입소문으로 최종 관객수가 크게 증폭됩니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 개봉일 스크린수 vs Top 10 유지 일수 (관계 버블 차트)
# -----------------------------------------------------------------------------
st.subheader("4. 🎬 개봉일 스크린수와 Top 10 유지 일수의 관계 (스크린 확보와 흥행 지속성)")

fig4 = px.scatter(
    df,
    x='first_scrn',
    y='days_in_top10',
    color='nation',
    size='total_audi',
    hover_name='movieNm',
    hover_data={'first_scrn': ':,', 'days_in_top10': True, 'total_audi': ':,'},
    labels={
        'first_scrn': '개봉일 스크린수(개)',
        'days_in_top10': 'Top 10 유지 일수(일)',
        'nation': '제작 국가',
        'total_audi': '총 관객수'
    },
    title="개봉일 스크린수 대비 Box Office Top 10 유지 일수 (점 크기: 총 관객수)"
)

fig4.update_layout(
    height=500,
    xaxis_tickformat=','
)

st.plotly_chart(fig4, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        개봉 초기 스크린 확보량이 상위권 진입에는 필수적이지만 장기 흥행(Top 10 유지 일수)을 보장하는 유일한 요소는 아니며, 제작 국가 및 콘텐츠 자체의 매력이 장기 흥행의 핵심 변수임을 보여줍니다.
    </div>
</div>
""", unsafe_allow_html=True)
