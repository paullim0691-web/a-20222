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

# 커스텀 CSS (깔끔하고 세련된 카드 레이아웃 스타일)
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
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
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
    
    # 날짜형 변환 (openDt 컬럼)
    if 'openDt' in df.columns:
        df['openDt'] = pd.to_datetime(df['openDt'], errors='coerce')
    
    # 숫자형 컬럼 변환
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
# 헤더 섹션
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🎬 영화 데이터 그래프 도감 2 - 분포와 관계</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">KOBIS 박스오피스 상위권 영화 216편의 데이터로 살펴보는 장르별 분포와 흥행 요인 간의 관계 분석</div>', unsafe_allow_html=True)

# 사이드바 필터링
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

# 필터 적용
df = df_raw[(df_raw['nation'].isin(selected_nations)) & (df_raw['genre'].isin(selected_genres))].copy()

if df.empty:
    st.warning("선택한 필터 조건에 해당하는 영화 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

# 동적 인사이트 계산용 데이터
top_movie = df.loc[df['total_audi'].idxmax()]
top_movie_name = top_movie['movieNm']
top_movie_audi = int(top_movie['total_audi'])

# 주요 요약 지표 (Metrics)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("분석 대상 영화 수", f"{len(df):,}편")
with col_m2:
    st.metric("총 관객수 합계", f"{int(df['total_audi'].sum()):,}명")
with col_m3:
    st.metric("평균 10위권 유지일", f"{df['days_in_top10'].mean():.1f}일")
with col_m4:
    st.metric("평균 개봉 스크린수", f"{int(df['first_scrn'].mean()):,}개")

st.markdown("---")

# -----------------------------------------------------------------------------
# 1. 장르별 영화 편수 분포 (도넛 그래프)
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
        박스오피스 상위권 영화 중 특정 주력 장르(드라마, 액션 등)의 비중이 높게 형성되어 있어, 흥행 시장에서 관객 편의성이 높은 주요 장르 선호도가 뚜렷함을 알 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 장르별 영화 분포 및 관객수 트리맵
# -----------------------------------------------------------------------------
st.subheader("2. 🗺️ 장르별 영화 및 총 관객수 분포 (트리맵)")

fig2 = px.treemap(
    df,
    path=[px.Constant("전체 장르"), 'genre', 'movieNm'],
    values='total_audi',
    color='genre',
    color_discrete_sequence=px.colors.qualitative.Pastel,
    title="장르 및 영화별 총 관객수 계층 구조 (칸 크기: 총 관객수)"
)

fig2.update_traces(
    hovertemplate="<b>영화명: %{label}</b><br>총 관객수: %{value:,.0f}명<extra></extra>"
)

fig2.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    height=550
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        각 장르 내에서 어떤 영화가 전체 총 관객수 점유율에 크게 기여했는지 개별 영화별 관객 규모와 장르별 비중을 직관적으로 비교할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. 총 관객수 히스토그램
# -----------------------------------------------------------------------------
st.subheader("3. 📊 총 관객수 분포 (히스토그램)")

fig3 = px.histogram(
    df,
    x='total_audi',
    nbins=30,
    color_discrete_sequence=['#3B82F6'],
    labels={'total_audi': '총 관객수(명)', 'count': '영화 편수'},
    title="영화별 총 관객수 분포"
)

fig3.update_traces(
    hovertemplate="<b>관객수 구간: %{x:,.0f}명</b><br>영화 편수: %{y}편<extra></extra>"
)

fig3.update_layout(
    xaxis_tickformat=',',
    yaxis_title="영화 편수",
    height=480,
    bargap=0.1
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown(f"""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        대부분의 영화가 약 300만 명 이하 구간에 집중적으로 몰려 분포하고 있는 반면, 관객수가 가장 많은 영화는 <b>'{top_movie_name}'</b>({top_movie_audi:,}명)로 일부 대형 흥행작이 전체 관객수 분포의 오른쪽 긴 꼬리(Right-skewed)를 형성하고 있음을 알 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 개봉일 스크린수 vs 총 관객수 (산점도)
# -----------------------------------------------------------------------------
st.subheader("4. 🎯 개봉일 스크린수와 총 관객수의 관계 (산점도)")

fig4 = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    hover_data={'first_scrn': ':,', 'total_audi': ':,', 'genre': True},
    labels={
        'first_scrn': '개봉일 스크린수(개)',
        'total_audi': '총 관객수(명)',
        'genre': '장르'
    },
    title="개봉일 스크린수 대비 최종 총 관객수 관계"
)

fig4.update_traces(
    marker=dict(size=9, opacity=0.8)
)

fig4.update_layout(
    height=500,
    xaxis_tickformat=',',
    yaxis_tickformat=','
)

st.plotly_chart(fig4, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        개봉일 스크린수가 많을수록 대체로 높은 총 관객수를 기록하는 양의 상관관계를 보입니다. 다만, 스크린수가 적음에도 높은 관객수를 달성한 흥행 작(입소문 흥행작)이나 반대로 스크린을 많이 확보했음에도 총 관객수가 비교적 적은 영화 등 장르별/작품별 흥행 효율성의 차이를 확인할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 주요 장르별 총 관객수 분포 (박스 플롯)
# -----------------------------------------------------------------------------
st.subheader("5. 📦 주요 장르별 총 관객수 분포 (박스 플롯)")

genre_counts_df = df['genre'].value_counts()
major_genres = genre_counts_df[genre_counts_df >= 10].index.tolist()
df_major = df[df['genre'].isin(major_genres)].copy()

fig5 = px.box(
    df_major,
    x='genre',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    hover_data={'total_audi': ':,', 'first_scrn': ':,', 'days_in_top10': True},
    labels={'genre': '장르', 'total_audi': '총 관객수(명)'},
    title=f"주요 장르(10편 이상 보유 장르 {len(major_genres)}개)의 총 관객수 박스 플롯"
)

fig5.update_traces(
    boxpoints='outliers'
)

fig5.update_layout(
    showlegend=False,
    height=500,
    yaxis_tickformat=','
)

st.plotly_chart(fig5, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        표본 편수가 적은 소수 장르를 제외하고 10편 이상 제작된 주요 장르를 비교할 때, 각 장르의 총 관객수 중위값(중앙값)과 사분위수 범위를 명확히 비교할 수 있습니다. 특히 상자 밖의 이상치(아웃라이어) 점에 마우스를 올리면 해당 장르의 평균치를 대폭 상회한 슈퍼 흥행작의 이름을 직접 확인할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 개봉일 스크린수 vs 총 관객수 (버블 크기: 개봉 첫 주 관객수)
# -----------------------------------------------------------------------------
st.subheader("6. 🫧 개봉일 스크린수와 총 관객수의 관계 (버블 크기: 개봉 첫 주 관객수)")

fig6 = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    size='first_week_audi',
    color='genre',
    hover_name='movieNm',
    hover_data={'first_scrn': ':,', 'total_audi': ':,', 'first_week_audi': ':,', 'genre': True},
    labels={
        'first_scrn': '개봉일 스크린수(개)',
        'total_audi': '총 관객수(명)',
        'first_week_audi': '개봉 첫 주 관객수(명)',
        'genre': '장르'
    },
    title="스크린수 대비 총 관객수 버블 차트 (버블 크기: 개봉 첫 주 관객수)"
)

fig6.update_traces(
    marker=dict(sizeref=2 * max(df['first_week_audi']) / (40**2), sizemode='area', opacity=0.7)
)

fig6.update_layout(
    height=550,
    xaxis_tickformat=',',
    yaxis_tickformat=','
)

st.plotly_chart(fig6, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        네 번째 산점도에 <b>개봉 첫 주 관객수(버블 크기)</b> 차원을 추가함으로써, 초기 스크린 확보량이 첫 주 동원 관객력으로 직결되는지, 그리고 첫 주 폭발적인 관객 동원이 최종 관객수까지 지속적으로 이어졌는지 3개 주요 흥행 지표 간의 다차원 입체 관계를 한눈에 파악할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 국가별-장르별 영화 편수 선버스트 차트
# -----------------------------------------------------------------------------
st.subheader("7. ☀️ 제작 국가 및 장르별 영화 편수 분포 (선버스트 차트)")

df_sunburst = df.copy()
df_sunburst['movie_count'] = 1

fig7 = px.sunburst(
    df_sunburst,
    path=['nation', 'genre'],
    values='movie_count',
    color='nation',
    color_discrete_sequence=px.colors.qualitative.Pastel,
    title="제작 국가 → 장르 계층 구조 (칸 크기: 영화 편수)"
)

fig7.update_traces(
    textinfo="label+value+percent entry",
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<br>비율: %{percentEntry:.1%}<extra></extra>"
)

fig7.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    height=550
)

st.plotly_chart(fig7, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        제작 국가(`nation`)에서 장르(`genre`)로 이어지는 계층 구조를 통해 각 국가별로 어떤 장르의 영화가 주로 제작/개봉되었는지 영화 편수 비중을 직관적으로 비교 파악할 수 있습니다. 안쪽 원을 클릭하면 해당 국가의 장르 구성 비율로 드릴다운(Drill-down)하여 더욱 세부적으로 관찰할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 시계열 산점도 (개봉일에 따른 첫 주 관객 변화 - 새로 추가된 그래프)
# -----------------------------------------------------------------------------
st.subheader("8. 📈 개봉일에 따라 첫 주 관객이 차이가 많이 날까")

fig8 = px.scatter(
    df,
    x='openDt',
    y='first_week_audi',
    color='genre',
    hover_name='movieNm',
    hover_data={'openDt': '|%Y-%m-%d', 'first_week_audi': ':,', 'genre': True},
    labels={
        'openDt': '개봉일',
        'first_week_audi': '개봉 첫 주 관객수(명)',
        'genre': '장르'
    },
    title="개봉일에 따라 첫 주 관객이 차이가 많이 날까"
)

fig8.update_traces(
    marker=dict(size=9, opacity=0.8)
)

fig8.update_layout(
    height=520,
    xaxis_title="개봉일",
    yaxis_title="개봉 첫 주 관객수(명)",
    yaxis_tickformat=','
)

st.plotly_chart(fig8, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 이 그래프로 알 수 있는 것</div>
    <div class="insight-text">
        시계열 산점도를 통해 개봉 시점(연도별/계절별/월별)에 따라 개봉 첫 주 관객 수의 분포 추이와 변동 폭을 확인할 수 있습니다. 특정 성수기(여름 휴가철, 명절 등) 시점에 개봉한 작품들의 첫 주 관객 동원력이 크게 집중되었는지를 직관적으로 살펴볼 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)
