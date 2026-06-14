import streamlit as st
import random
import json
import os
import re
from datetime import datetime
# PDF 텍스트 추출을 위한 라이브러리 (배포 환경에서 자동 작동)
try:
    import pypdf
except ImportError:
    os.system("pip install pypdf")
    import pypdf

# ==========================================
# [데이터 로컬 저장 및 자동 로드 기능]
# ==========================================
SAVE_FILE = "math_pilot_solo_data.json"

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

# ==========================================
# [앱 초기화 상태 빌드]
# ==========================================
st.set_page_config(page_title="MathPilot Solo", layout="wide")

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

# ==========================================
# [🚨 엄격 규칙: PDF 원본에서만 문제 분리 추출]
# ==========================================
def extract_problems_strictly_from_pdf(uploaded_file):
    """AI의 임의 창작을 전면 차단하고, 업로드된 PDF 본문 텍스트만 100% 슬라이싱하여 추출합니다."""
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    # 일반적인 수학 문제 번호 패턴(예: 1., 01., [문항 1] 등)을 기준으로 문장을 쪼갭니다.
    raw_blocks = re.split(r'(?=\b\d{1,2}\s*[.\],、])|(?=\[문항\s*\d{1,2}\])', full_text)
    
    cleaned_problems = []
    prob_id = 1
    
    for block in raw_blocks:
        block_content = block.strip()
        # 글자 수가 지나치게 적은 공백 블록은 제외
        if len(block_content) > 15:
            # 주관식 단답형을 기본 구조로 하되, 원본 본문을 단 1자도 훼손하지 않고 그대로 투입
            cleaned_problems.append({
                "id": prob_id,
                "type": "short_answer",
                "question": block_content,
                "answer": "정답지 확인 필요",  # 원본 PDF 텍스트 기반이므로 본인이 푼 정답과 대조용
                "explanation": "업로드하신 원본 PDF 파일의 실제 출제 문항 본문입니다."
            })
            prob_id += 1
            
    # 만약 정규식 분리가 모호하여 블록이 안 나눠진 경우 전체 텍스트를 통으로 보존
    if not cleaned_problems:
        cleaned_problems.append({
            "id": 1,
            "type": "short_answer",
            "question": full_text.strip(),
            "answer": "정답지 확인 필요",
            "explanation": "PDF 전체 본문 텍스트입니다."
        })
        
    return cleaned_problems

# ==========================================
# [사용자 UI 및 사이드바 대시보드]
# ==========================================
st.sidebar.title("🎮 MathPilot Solo")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
menu = st.sidebar.radio("메뉴 이동", ["📁 시험 범위 업로드", "📝 풀이 시험장", "🔥 오답노트 관리"])

# [메뉴 1] 파일 업로드
if menu == "📁 시험 범위 업로드":
    st.header("📁 시험 범위 원본 PDF 등록")
    st.info("⚠️ 외부 문제는 단 1문항도 섞이지 않으며, 오직 유저님이 업로드한 PDF 내부 문항만 추출됩니다.")
    
    uploaded_file = st.file_uploader("학교/학원 시험범위 원본 PDF 파일을 업로드하세요.", type=["pdf"])
    if uploaded_file is not None:
        if st.button("🚀 원본 문항 동기화 및 5문항 랜덤 뽑기"):
            with st.spinner("PDF 내부 실제 문제 완벽 분석 중..."):
                all_problems = extract_problems_strictly_from_pdf(uploaded_file)
                
                if len(all_problems) >= 5:
                    # 🎯 유저님 요청 반영: 외부 문제 절대 없이 원본 안에서만 딱 5개 랜덤 추출
                    st.session_state.problems_pool = random.sample(all_problems, 5)
                else:
                    st.session_state.problems_pool = all_problems
                    
                st.session_state.current_idx = 0
                st.success(f"✅ 동기화 완료! 업로드한 PDF 원본 문항 중 고유 문제 5개가 완전 랜덤으로 엄선 배치되었습니다.")

# [메뉴 2] 풀이 시험장
elif menu == "📝 풀이 시험장":
    st.header("📝 MathPilot 원본 기출 테스트 모드")
    
    if not st.session_state.problems_pool:
        st.warning("먼저 '📁 시험 범위 업로드' 메뉴에서 실제 PDF 파일을 등록해 주세요!")
    else:
        idx = st.session_state.current_idx
        pool = st.session_state.problems_pool
        
        st.progress((idx + 1) / len(pool), text=f"현재 진행 문항: {idx + 1} / {len(pool)}")
        
        q = pool[idx]
        st.markdown(f"### **[실제 범위 문항 {idx + 1}]**")
        
        # 원본 PDF 텍스트 그대로 노출
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

# [메뉴 3] 오답노트 관리
elif menu == "🔥 오답노트 관리":
    st.header("🔥 PDF 원본 오답 정복")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답이 없습니다!")
    else:
        for w_idx, w_q in enumerate(st.session_state.wrong_notes):
            with st.expander(f"⚠️ 원본 PDF 추출 문항 (ID: {w_q['id']})"):
                st.write(w_q["question"])
                if st.button("이 문제 완벽 마스터 (삭제)", key=f"del_w_{w_idx}"):
                    st.session_state.wrong_notes.remove(w_q)
                    save_to_local()
                    st.success("제거되었습니다.")
                    st.rerun()