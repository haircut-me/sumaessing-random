import streamlit as st
import random
import os
import fitz  # PyMuPDF

PDF_FILE = "sumaessing.pdf"
ANSWER_FILE = "answer.pdf"

st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

st.title("🎯 수매씽 무한 랜덤 문제 은행")
st.write("패드로 필기 기능 추가 전, 가장 잘 돌아가던 안정 버전입니다.")

# 페이지 번호를 기억하기 위한 세션 설정
if 'current_page' not in st.session_state:
    st.session_state.current_page = None

if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False

# PDF 파일이 존재하는지 확인 및 총 페이지 수 계산
if os.path.exists(PDF_FILE):
    try:
        doc = fitz.open(PDF_FILE)
        total_pages = len(doc)
        doc.close()
        
        # 처음에 무작위로 첫 문제 뽑기
        if st.session_state.current_page is None and total_pages > 0:
            st.session_state.current_page = random.randint(1, total_pages)
    except Exception as e:
        st.error(f"문제집 PDF 파일을 읽는 중 오류가 발생했습니다: {e}")
        total_pages = 0
else:
    st.error(f"❌ 깃허브 저장소에 '{PDF_FILE}' 파일이 없습니다. 파일을 업로드해 주세요.")
    total_pages = 0

# 문제 출력 구역
if st.session_state.current_page is not None:
    page_num = st.session_state.current_page
    st.subheader(f"📋 현재 출제된 문항 (총 {total_pages}문제 중 {page_num}번째 페이지)")
    
    # 문제 이미지 렌더링
    try:
        doc = fitz.open(PDF_FILE)
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        st.image(pix.tobytes("png"), use_container_width=True)
        doc.close()
    except Exception as e:
        st.error(f"문제를 화면에 그리는 데 실패했습니다: {e}")

    st.write("---")

    # 버튼 제어 영역
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 이 문제 정답 및 해설지 보기", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()
            
    with col2:
        if st.button("➡️ 다른 문제 새로 뽑기 (랜덤 출제)", use_container_width=True):
            st.session_state.show_answer = False
            st.session_state.current_page = random.randint(1, total_pages)
            st.rerun()

    # 해설지 출력 구역
    if st.session_state.show_answer:
        st.write("### 📖 1:1 매칭 정답 및 해설")
        if os.path.exists(ANSWER_FILE):
            try:
                ans_doc = fitz.open(ANSWER_FILE)
                if (page_num - 1) < len(ans_doc):
                    ans_page = ans_doc[page_num - 1]
                    ans_pix = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                    st.image(ans_pix.tobytes("png"), use_container_width=True)
                else:
                    st.error("❌ 문제집 페이지에 대응하는 해설지 페이지가 부족합니다.")
                ans_doc.close()
            except Exception as e:
                st.error(f"해설지를 여는 중 오류가 발생했습니다: {e}")
        else:
            st.warning(f"⚠️ 저장소에 '{ANSWER_FILE}' 파일이 없어서 해설을 볼 수 없습니다.")
