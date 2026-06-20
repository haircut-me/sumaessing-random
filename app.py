import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PDF 페이지 수를 체크하기 위한 라이브러리

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

st.set_page_config(page_title="수매씽 랜덤 문제 만들기", layout="wide")

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

# 🚀 무한 랜덤 모드를 위한 페이지 변수 설정
if 'current_target_page' not in st.session_state:
    st.session_state.current_target_page = None
if 'solved_count' not in st.session_state:
    st.session_state.solved_count = 0

is_pdf_broken = False
total_pages_count = 0

if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
        
        # 첫 구동 시 무작위 페이지 최초 1회 지정
        if total_pages_count > 0 and st.session_state.current_target_page is None:
            st.session_state.current_target_page = random.randint(1, total_pages_count)
    except:
        is_pdf_broken = True
else:
    is_pdf_broken = True

st.sidebar.title("🎮 수매씽 랜덤 문제 만들기")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 `{FIXED_PDF_NAME}` 파일이 없거나 올바르지 않습니다.")
        st.markdown("**해결 방법:** 바꾸고 싶은 수매씽 PDF 파일명을 `sumaessing.pdf`로 변경해서 깃허브에 업로드해 주세요!")
    else:
        st.success(f"✅ 새 수매씽 교재 연결 성공! (총 {total_pages_count}페이지 감지 완료)")
        st.info("💡 스포일러 방지를 위해 화면에 문제를 보여주는 대신, 풀이할 페이지 번호를 랜덤으로 띄워 드립니다.")
        st.info("🔄 현재 '무한 랜덤 모드'가 활성화되어 있어 제한 없이 계속해서 다음 문제가 생성됩니다.")
        
        if st.button("🔄 첫 문제 강제 새로고침"):
            if total_pages_count > 0:
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.success("🎯 첫 미션 페이지가 새로 지정되었습니다! '풀이 시험장'으로 가보세요.")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 페이지 미션")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 '자동 문제 은행 상태' 탭에서 PDF 교재 상태를 먼저 확인해 주세요.")
    else:
        target_page = st.session_state.current_target_page
        
        # 🎉 튼튼하고 직관적인 디자인으로 미션 페이지 노출 (에러 방지용 안전 문법)
        st.info("💡 아래 가이드에 따라 교재를 펼쳐 문제를 풀어보세요!")
        
        st.markdown("### 🎯 오늘의 미션 범위")
        st.subheader(f"📖 수매씽 원본 교재 [ {target_page} 페이지 ] 를 펼쳐주세요!")
            
        user_ans = st.text_input("메모 또는 정답 기록 채널:", key=f"ans_{target_page}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("풀이 완료 기록"):
                st.session_state.history_stats["total"] += 1
                st.success("풀이 완료가 대시보드에 기록되었습니다!")
        with c2:
            if st.checkbox("이 페이지를 오답노트에 등록하고 나중에 다시 풀겠습니다.", key=f"chk_{target_page}"):
                if target_page not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(target_page)
                    st.success(f"⚠️ {target_page} 페이지가 오답노트에 안전하게 저장되었습니다.")
                save_to_local()

        st.write("---")
        # ➡️ 누르면 다음 무작위 페이지가 끊임없이 나오는 마법의 버튼
        if st.button("다음 랜덤 문제 뽑기 ➡️", use_container_width=True):
            if total_pages_count > 0:
                st.session_state.solved_count += 1
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 페이지 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답 미션이 없습니다!")
    else:
        # 오답 노트를 보기 좋게 정렬해서 보여줌
        sorted_notes = sorted(st.session_state.wrong_notes)
        for w_page in sorted_notes:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.warning(f"📋 다시 풀어볼 교재 범위: **{w_page} 페이지**")
            with c2:
                if st.button("마스터 완료 (삭제)", key=f"del_page_{w_page}"):
                    st.session_state.wrong_notes.remove(w_page)
                    save_to_local()
                    st.success("제거되었습니다.")
                    st.rerun()
