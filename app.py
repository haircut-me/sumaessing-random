import streamlit as st
import random
import json
import os
import re
from datetime import datetime
try:
    import pypdf
except ImportError:
    os.system("pip install pypdf")
    import pypdf

SAVE_FILE = "math_pilot_solo_data.json"
# 🎯 고정으로 읽어올 PDF 파일 이름 설정
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

# 🎯 간판 이름 반영: 수매씽 랜덤 문제 만들기
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

# 🛠️ 경로로 직접 PDF를 읽어들이도록 함수 개선
def extract_problems_strictly_from_pdf_path(file_path):
    reader = pypdf.PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    raw_blocks = re.split(r'(?=\b\d{1,2}\s*[.\],、])|(?=\[문항\s*\d{1,2}\])', full_text)
    cleaned_problems = []
    prob_id = 1
    
    for block in raw_blocks:
        block_content = block.strip()
        if len(block_content) > 15:
            cleaned_problems.append({
                "id": prob_id,
                "type": "short_answer",
                "question": block_content,
                "answer": "정답지 확인 필요",
                "explanation": "업로드하신 원본 PDF 파일의 실제 출제 문항 본문입니다."
            })
            prob_id += 1
            
    if not cleaned_problems:
        cleaned_problems.append({
            "id": 1,
            "type": "short_answer",
            "question": full_text.strip(),
            "answer": "정답지 확인 필요",
            "explanation": "PDF 전체 본문 텍스트입니다."
        })
        
    return cleaned_problems

# 🚀 앱 시작하자마자 내장된 PDF를 자동으로 분석하여 문제 배치하는 로직
if not st.session_state.problems_pool:
    if os.path.exists(FIXED_PDF_NAME):
        all_problems = extract_problems_strictly_from_pdf_path(FIXED_PDF_NAME)
        if len(all_problems) >= 5:
            st.session_state.problems_pool = random.sample(all_problems, 5)
        else:
            st.session_state.problems_pool = all_problems
        st.session_state.current_idx = 0

# 🎯 사이드바 이름 반영: 수매씽 랜덤 문제 만들기
st.sidebar.title("🎮 수매씽 랜덤 문제 만들기")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    
    if os.path.exists(FIXED_PDF_NAME):
        st.success(f"✅ 현재 시스템에 `{FIXED_PDF_NAME}` 문제집 파일이 정상적으로 박혀있습니다!")
        st.info("💡 앱을 켤 때마다 자동으로 문제를 엄선합니다. 다른 문제 조합으로 새로 학습하고 싶다면 아래 버튼을 누르세요.")
        
        if st.button("🔄 다른 5문항 새로 복제하기 (랜덤 셔플)"):
            with st.spinner("PDF 내부 실제 문제 완벽 분석 중..."):
                all_problems = extract_problems_strictly_from_pdf_path(FIXED_PDF_NAME)
                if len(all_problems) >= 5:
                    st.session_state.problems_pool = random.sample(all_problems, 5)
                else:
                    st.session_state.problems_pool = all_problems
                st.session_state.current_idx = 0
                st.success("🎯 새로운 무작위 5문항이 시험장에 완벽히 엄선 배치되었습니다! '풀이 시험장'으로 이동해 보세요.")
    else:
        st.error(f"⚠️ 깃허브 저장소에 `{FIXED_PDF_NAME}` 파일이 없습니다!")
        st.markdown("""
        **해결 방법:**
        1. 사용하시는 수매씽 PDF 파일 이름을 영어 소문자 **`sumaessing.pdf`** 로 바꿉니다.
        2. 깃허브 저장소(`haircut-me/sumaessing-random`)에 이 PDF 파일을 다시 업로드해 줍니다.
        """)

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 원본 기출 테스트 모드")
    
    if not st.session_state.problems_pool:
        st.warning("시스템에 내장된 PDF 문제집을 불러오지 못했습니다. 깃허브에 파일이 있는지 확인해 주세요.")
    else:
        idx = st.session_state.current_idx
        pool = st.session_state.problems_pool
        
        st.progress((idx + 1) / len(pool), text=f"현재 진행 문항: {idx + 1} / {len(pool)}")
        
        q = pool[idx]
        st.markdown(f"### **[실제 범위 문항 {idx + 1}]**")
        st.info(q["question"])
        
        user_ans = st.text_input("직접 푼 정답 또는 풀이 메모 입력:", key=f"ans_{idx}")

        if st.button("풀이 완료 및 기록 (오답 체크용)"):
            st.session_state.history_stats["total"] += 1
            st.warning("💡 원본 PDF 기반 모드입니다. 스스로 판단하여 틀렸거나 다시 볼 문제라면 아래 오답노트에 등록하세요.")
            
            if st.checkbox("이 문제를 오답노트에 보관하고 다시 풀겠습니다.", key=f"chk_{idx}"):
                existing = next((item for item in st.session_state.wrong_notes if item["id"] == q["id"]), None)
                if not existing:
                    q["error_type"] = "다시 확인 필요"
                    st.session_state.wrong_notes.append(q)
                st.success("⚠️ 해당 원본 문제가 오답노트에 보관되었습니다.")
            save_to_local()

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ 이전 문제", disabled=(idx == 0)):
                st.session_state.current_idx -= 1
                st.rerun()
        with c2:
            if st.button("다음 문제 ➡️", disabled=(idx == len(pool) - 1)):
                st.session_state.current_idx += 1
                st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 PDF 원본 오답 정복")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답이 없습니다!")
    else:
        for w_idx, w_q in enumerate(st.session_state.wrong_notes):
            with w_idx, w_q in enumerate(st.session_state.wrong_notes):
            with st.expander(f"⚠️ 원본 PDF 추출 문항 (ID: {w_q['id']})"):
                st.write(w_q["question"])
                if st.button("이 문제 완벽 마스터 (삭제)", key=f"del_w_{w_idx}"):
                    st.session_state.wrong_notes.remove(w_q)
                    save_to_local()
                    st.success("제거되었습니다.")
                    st.rerun()
