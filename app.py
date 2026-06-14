```python
import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # 정식 등록을 마쳤으므로 바로 로딩합니다!

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

# ⚙️ PDF 페이지를 고화질 이미지(PNG)로 변환하는 함수
def render_pdf_page(file_path, page_num):
    try:
        doc = fitz.open(file_path)
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=150)  # 150 DPI로 선명하게 렌더링
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
    except Exception as e:
        return None

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

if 'problems_pool' not in st.session_state:
    st.session_state.problems_pool = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

# 🚀 앱 구동 시 PDF의 전체 페이지 중 무작위 5개 페이지를 엄선
is_pdf_broken = False
total_pages_count = 0

if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
        
        if total_pages_count > 0 and not st.session_state.problems_pool:
            sample_size = min(5, total_pages_count)
            st.session_state.problems_pool = random.sample(range(total_pages_count), sample_size)
            st.session_state.current_idx = 0
    except Exception as e:
        is_pdf_broken = True
else:
    is_pdf_broken = True

st.sidebar.title("🎮 수매씽 랜덤 문제 만들기")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 있는 `{FIXED_PDF_NAME}` 파일이 없거나 손상되었습니다.")
        st.markdown("""
        **해결 방법:** 용량이 제대로 차 있는 진짜 수매씽 PDF 파일을 깃허브에 `sumaessing.pdf`라는 이름으로 업로드해 주세요.
        """)
    else:
        st.success(f"✅ 수매씽 문제집 연결 완벽 성공! (총 {total_pages_count}페이지 감지됨)")
        st.info("💡 교재 내부의 수식과 그래프를 훼손하지 않기 위해 '원본 페이지 고화질 스캔 모드'로 작동 중입니다.")
        
        if st.button("🔄 다른 5개 페이지 무작위 선별 (랜덤 셔플)"):
            if total_pages_count > 0:
                sample_size = min(5, total_pages_count)
                st.session_state.problems_pool = random.sample(range(total_pages_count), sample_size)
                st.session_state.current_idx = 0
                st.success("🎯 새로운 무작위 5개 시험 범주 페이지가 세팅되었습니다! '풀이 시험장'으로 가보세요.")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 원본 기출 테스트 모드")
    
    if is_pdf_broken or not st.session_state.problems_pool:
        st.error("📁 '자동 문제 은행 상태' 탭에서 PDF 파일 상태를 먼저 확인해 주세요.")
    else:
        idx = st.session_state.current_idx
        pool = st.session_state.problems_pool
        current_page = pool[idx]
        
        st.progress((idx + 1) / len(pool), text=f"현재 진행 페이지: {idx + 1} / {len(pool)}")
        st.markdown(f"### **[실제 범위 기출 - {current_page + 1} 페이지]**")
        
        # 🖼 * 현재 인덱스의 PDF 페이지를 고화질 이미지로 출력
        with st.spinner("원본 문항 해상도 최적화 중..."):
            img_bytes = render_pdf_page(FIXED_PDF_NAME, current_page)
        
        if img_bytes:
            st.image(img_bytes, use_container_width=True)
        else:
            st.error("해당 페이지의 수식 이미지를 복원하는 데 실패했습니다.")
            
        user_ans = st.text_input("정답 입력 및 풀이 메모:", key=f"ans_{idx}")

        if st.button("풀이 완료 및 기록"):
            st.session_state.history_stats["total"] += 1
            st.success("체크 완료! 아래 체크박스를 누르면 오답노트에 보관됩니다.")
            
        if st.checkbox("이 페이지를 오답노트에 등록하고 다시 풀겠습니다.", key=f"chk_{idx}"):
            existing = next((item for item in st.session_state.wrong_notes if item["page"] == current_page), None)
            if not existing:
                st.session_state.wrong_notes.append({"id": current_page + 1, "page": current_page})
                st.success(f"⚠️ {current_page + 1} 페이지가 오답노트에 안전하게 등록되었습니다.")
            save_to_local()

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅ * 이전 페이지", disabled=(idx == 0)):
                st.session_state.current_idx -= 1
                st.rerun()
        with c2:
            if st.button("다음 페이지 ➡️", disabled=(idx == len(pool) - 1)):
                st.session_state.current_idx += 1
                st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 PDF 원본 오답 정복")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답 페이지가 없습니다!")
    else:
        for w_idx, w_q in enumerate(st.session_state.wrong_notes):
            with st.expander(f"⚠️ 오답 등록 내역 ({w_q['id']} 페이지)"):
                img_bytes = render_pdf_page(FIXED_PDF_NAME, w_q["page"])
                if img_bytes:
                    st.image(img_bytes, use_container_width=True)
                if st.button("이 페이지 완벽 마스터 (삭제)", key=f"del_w_{w_idx}"):
                    st.session_state.wrong_notes.remove(w_q)
                    save_to_local()
                    st.success("오답노트에서 제거되었습니다.")
                    st.rerun()
