import streamlit as st
import random
import json
import os
import fitz

SF = "math_pilot_solo_data.json"
PDF = "sumaessing.pdf"
ANS = "answer.pdf"

if 'wrong_notes' not in st.session_state:
    st.session_state.wrong_notes = []
    st.session_state.solved_count = 0
    st.session_state.show_ans = False
    st.session_state.u_ans = ""
    if os.path.exists(SF):
        try:
            with open(SF, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wrong_notes = d.get("wrong_notes", [])
        except: pass

st.set_page_config(page_title="Sumaessing Bank", layout="wide")
st.sidebar.title("🎮 수매씽 스마트 시험장")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴", ["📝 랜덤 시험장", "🔥 오답노트"])

is_ok = os.path.exists(PDF)
total_p = len(fitz.open(PDF)) if is_ok else 0

if 'page' not in st.session_state and total_p > 0:
    st.session_state.page = random.randint(1, total_p)

if menu == "📝 랜덤 시험장":
    if not is_ok:
        st.error("❌ sumaessing.pdf 파일이 없습니다.")
    else:
        p_num = st.session_state.page
        st.markdown(f"### 🎯 **현재 문항:** [ {p_num}번째 문제 ]")
        
        doc = fitz.open(PDF)
        page = doc.load_page(p_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        st.image(pix.tobytes("png"), use_container_width=True)
        doc.close()
        
        st.write("")
        st.session_state.u_ans = st.text_input("🎯 최종 정답 입력:", key=f"a_{p_num}").strip()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 해설지 확인", use_container_width=True):
                st.session_state.show_ans = True
                st.rerun()
        with c2:
            if st.button("다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_ans = False
                st.session_state.page = random.randint(1, total_p)
                st.rerun()

        if st.session_state.show_ans and os.path.exists(ANS):
            st.write("---")
            st.info(f"내가 입력한 정답: {st.session_state.u_ans}")
            a_doc = fitz.open(ANS)
            if (p_num - 1) < len(a_doc):
                a_page = a_doc[p_num - 1]
                st.image(a_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8)).tobytes("png"), use_container_width=True)
            a_doc.close()
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 맞았습니다!", use_container_width=True):
                    st.session_state.solved_count += 1
                    st.session_state.show_ans = False
                    st.session_state.page = random.randint(1, total_p)
                    st.rerun()
            with b2:
                if st.button("❌ 틀렸습니다 (오답저장)", use_container_width=True):
                    st.session_state.solved_count += 1
                    if p_num not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(p_num)
                        with open(SF, "w", encoding="utf-8") as f:
                            json.dump({"wrong_notes": st.session_state.wrong_notes}, f)
                    st.session_state.show_ans = False
                    st.session_state.page = random.randint(1, total_p)
                    st.rerun()

elif menu == "🔥 오답노트":
    st.header("🔥 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 틀린 문제가 없습니다!")
    else:
        for wp in sorted(st.session_state.wrong_notes):
            st.warning(f"📋 복습 문항: {wp}번째 문제")
            if is_ok:
                doc = fitz.open(PDF)
                st.image(doc.load_page(wp - 1).get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes("png"), use_container_width=True)
                doc.close()
            if st.button("삭제", key=f"del_{wp}"):
                st.session_state.wrong_notes.remove(wp)
                with open(SF, "w", encoding="utf-8") as f:
                    json.dump({"wrong_notes": st.session_state.wrong_notes}, f)
                st.rerun()
            st.write("---")
