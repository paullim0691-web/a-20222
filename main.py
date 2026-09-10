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

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (깨짐 방지)
plt.rc('font', family='Malgun Gothic') # 맥 사용자는 'AppleGothic'으로 변경

# 1. 데이터 준비 (예시 데이터입니다. 실제 데이터프레임을 사용해 주세요)
data = {
    '기준일자': ['2023-12-01', '2023-12-02', '2023-12-03', '2023-12-04', '2023-12-05'],
    '누적관객수': [150000, 450000, 800000, 920000, 1050000]
}
df = pd.DataFrame(data)

# 2. 영역 차트(Area Chart) 그리기
plt.figure(figsize=(10, 5))
plt.fill_between(df['기준일자'], df['누적관객수'], color='skyblue', alpha=0.5)
plt.plot(df['기준일자'], df['누적관객수'], color='dodgerblue', alpha=0.8, linewidth=2)

# 3. 그래프 꾸미기
plt.title('기준일자별 누적관객수 변화', fontsize=16, pad=15)
plt.xlabel('기준일자', fontsize=12)
plt.ylabel('누적관객수 (명)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 4. 출력
plt.tight_layout()
plt.show()
