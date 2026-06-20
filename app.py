import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PDF 페이지를 고화질 이미지로 변환해서 보여주는 라이브러리

SAVE_FILE = "math_pilot_solo_data.json"
FIXED_PDF_NAME = "sumaessing.pdf"

def save_to_local():
    data = {
        "wrong_notes": st.session_state.wrong_notes,
        "history_stats": st.session_state.history_stats,
        "streak": st.session_state.streak,
        "last_login": st.session_state.last_login
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_local():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.wrong_notes = data.get("wrong_notes", [])
                st.session_state.history_stats = data.get("history_stats", {"correct": 0, "total": 0})
                st.session_state.streak = data.get("streak", 0)
                st.session_state.last_login = data.get("last_login", "")
        except:
            pass

st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

if 'initialized' not in st.session_state:
    st.session_state.wrong_notes = []
    st.session_state.history_stats = {"correct": 0, "total": 0}
    st.session_state.streak = 0
    st.session_state.last_login = ""
    load_from_local()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_login:
        if st.session_state.last_login != today_str:
            st.session_state.streak += 1
    else:
        st.session_state.streak = 1
    st.session_state.last_login = today_str
    st.session_state.initialized = True
    save_to_local()

# 🚀 무한 랜덤 출제를 위한 세션 변수 설정
if 'current_target_page' not in st.session_state:
    st.session_state.current_target_page = None
if 'solved_count' not in st.session_state:
    st.session_state.solved_count = 0

is_pdf_broken = False
total_pages_count = 0

# 📁 깃허브에 올라온 sumaessing.pdf를 읽어서 전체 페이지 수 확인
if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
        
        # 첫 실행 시 무작위로 한 페이지를 타겟으로 지정
        if total_pages_count > 0 and st.session_state.current_target_page is None:
            st.session_state.current_target_page = random.randint(1, total_pages_count)
    except:
        is_pdf_broken = True
else:
    is_pdf_broken = True

st.sidebar.title("🎮 수매씽 무한 랜덤 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 `{FIXED_PDF_NAME}` 파일이 없거나 올바르지 않습니다.")
        st.markdown("**해결 방법:** 직접 자르고 편집하신 PDF 파일명을 정확히 `sumaessing.pdf`로 변경해서 깃허브에 업로드해 주세요!")
    else:
        st.success(f"✅ 수매씽 편집본 교재 연결 성공! (총 {total_pages_count}페이지 감지 완료)")
        st.info("💡 유저님이 편집하신 페이지가 통째로 고화질 스캔 이미지 형태로 화면에 출제됩니다.")
        st.info("🔄 '무한 랜덤 모드'가 켜져 있어, 하단 버튼을 누르면 제한 없이 다음 무작위 페이지가 계속 나옵니다.")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 먼저 확인해 주세요.")
    else:
        target_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 범위:** [ 원본 {target_page} 페이지 ]")
        
        # 📸 PDF의 해당 페이지를 통째로 선명한 이미지(PNG)로 렌더링하여 화면에 출력
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(target_page - 1)  # 0부터 시작하므로 -1
            
            # 선명도를 높이기 위한 2배 줌 설정
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            
            # 🖼️ 유저님이 잘라두신 페이지를 화면에 그대로 통째로 노출!
            st.image(img_bytes, caption=f"수매씽 {target_page}페이지", use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 페이지 이미지를 불러오는 중 오류가 발생했습니다: {e}")

        st.write("")
        user_ans = st.text_input("직접 푼 정답 또는 풀이 메모 입력:", key=f"ans_{target_page}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("풀이 완료 기록"):
                st.session_state.history_stats["total"] += 1
                st.success("체크 완료! 오늘의 풀이 카운트가 올라갔습니다.")
        with c2:
            if st.checkbox("이 페이지를 오답노트에 보관하고 나중에 다시 풀겠습니다.", key=f"chk_{target_page}"):
                if target_page not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(target_page)
                    st.success(f"⚠️ {target_page} 페이지가 오답노트에 안전하게 보관되었습니다.")
                save_to_local()

        st.write("---")
        # ➡️ 누르면 다음 무작위 페이지가 끊임없이 나오는 마법의 버튼
        if st.button("다음 랜덤 문제 뽑기 ➡️", use_container_width=True):
            if total_pages_count > 0:
                st.session_state.solved_count += 1
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답 페이지가 없습니다!")
    else:
        sorted_notes = sorted(st.session_state.wrong_notes)
        for w_page in sorted_notes:
            st.warning(f"📋 복습 범위: **{w_page} 페이지**")
            
            # 오답노트에서도 유저님이 잘라두신 해당 페이지를 그대로 보면서 복습
            try:
                doc = fitz.open(FIXED_PDF_NAME)
                page = doc.load_page(w_page - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                st.image(pix.tobytes("png"), use_container_width=True)
                doc.close()
            except:
                pass
                
            if st.button("이 페이지 완벽 마스터 (삭제)", key=f"del_page_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.success("제거되었습니다.")
                st.rerun()
            st.write("---")
