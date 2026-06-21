import streamlit as st
import random
import os
import fitz

PDF = "sumaessing.pdf"
ANS = "answer.pdf"

st.set_page_config(page_title="Sumaessing Exam", layout="wide")
st.sidebar.title("🎮 수매씽 스마트 시험장")

if 'wrong_notes' not in st.session_state:
    st.session_state.wrong_notes = []
    st.session_state.page = 1

is_ok = os.path.exists(PDF)
total_p = len(fitz.open(PDF)) if is_ok else 0

if is_ok and st.session_state.page == 1 and total_p > 0:
    st.session_state.page = random.randint(1, total_p)

p_num = st.session_state.page
st.markdown(f"### 🎯 **현재 문항:** [ 발췌본 내 {p_num}번째 문제 ]")

if is_ok:
    doc = fitz.open(PDF)
    page = doc.load_page(p_num - 1)
    st.image(page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)).tobytes("png"), use_container_width=True)
    doc.close()
else:
    st.error("❌ sumaessing.pdf 파일이 저장소에 없습니다.")

if st.button("🔍 이 문제 해설지 보기", use_container_width=True):
    if os.path.exists(ANS):
        st.write("---")
        a_doc = fitz.open(ANS)
        if (p_num - 1) < len(a_doc):
            a_page = a_doc[p_num - 1]
            st.image(a_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8)).tobytes("png"), use_container_width=True)
        else:
            st.error("❌ 해설지 페이지 부족")
        a_doc.close()
    else:
        st.error("❌ answer.pdf 파일이 없습니다.")

if st.button("다른 문제 새로 뽑기 ➡️", use_container_width=True):
    st.session_state.page = random.randint(1, total_p)
    st.rerun()
