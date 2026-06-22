import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import io
import streamlit.components.v1 as components

SAVE_FILE = "math_pilot_solo_data.json"
FIXED_PDF_NAME = "sumaessing.pdf"
ANSWER_PDF_NAME = "answer.pdf"

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
        except Exception:
            pass

# 1. 페이지 초기화
st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

# 2. 세션 상태 안전하게 초기화
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

if 'current_target_page' not in st.session_state:
    st.session_state.current_target_page = None
if 'solved_count' not in st.session_state:
    st.session_state.solved_count = 0
if 'show_answer_trigger' not in st.session_state:
    st.session_state.show_answer_trigger = False
if 'ans_offset' not in st.session_state:
    st.session_state.ans_offset = 0

# 3. PDF 파일 연결 상태 확인 체크
is_pdf_broken = False
total_pages_count = 0

if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
    except Exception:
        is_pdf_broken = True
else:
    is_pdf_broken = True

if not is_pdf_broken and total_pages_count > 0:
    if st.session_state.current_target_page is None:
        st.session_state.current_target_page = random.randint(1, total_pages_count)

has_answer_pdf = os.path.exists(ANSWER_PDF_NAME)

# 하단 공백을 감지하고 크롭(Crop)하는 스마트 헬퍼 함수
def get_cropped_image_bytes(pdf_path, page_idx, zoom=2.0):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_idx)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_data = pix.tobytes("png")
    doc.close()
    
    img = Image.open(io.BytesIO(img_data))
    gray_img = img.convert("L")
    
    width, height = gray_img.size
    content_bottom = height
    step = 4
    
    for y in range(height - 1, 0, -step):
        is_row_white = True
        for x in range(0, width, 10):
            if gray_img.getpixel((x, y)) < 245:
                is_row_white = False
                break
        if not is_row_white:
            content_bottom = min(y + 35, height)
            break
            
    if content_bottom < height and content_bottom > 250:
        img = img.crop((0, 0, width, content_bottom))
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 4. 사이드바 구성
st.sidebar.title("🎮 수매씽 1:1 매칭 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 시스템 연결 상태", "📝 1:1 랜덤 시험장", "🔥 오답노트 관리"])

# 5. [메뉴 1] 상태 확인 구역
if menu == "📁 시스템 연결 상태":
    st.header("📁 교재 및 해설지 파일 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브 저장소에 {FIXED_PDF_NAME} 파일이 누락되었거나 손상되었습니다.")
    else:
        st.success(f"✅ 편집본 문제집 연결 성공! (총 {total_pages_count}개 문항 탑재)")
        
    if has_answer_pdf:
        st.success(f"✅ 1:1 매칭 해설지({ANSWER_PDF_NAME}) 연결 성공!")
    else:
        st.warning(f"⚠️ 깃허브 저장소에 해설지 {ANSWER_PDF_NAME} 파일이 아직 보이지 않습니다.")

# 6. [메뉴 2] 1:1 랜덤 시험장 구역
elif menu == "📝 1:1 랜덤 시험장":
    st.header("📝 1:1 매칭 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 사이드바 메뉴에서 확인해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        
        # 상단 레이아웃 분할: 문제 제목과 실시간 인터랙티브 스톱워치 배치
        t_col1, t_col2 = st.columns([2, 1])
        with t_col1:
            st.markdown(f"### 🎯 **현재 출제 문항:** [ 발췌 파일 내 {file_page}번째 문제 ]")
        with t_col2:
            init_running = "false" if st.session_state.show_answer_trigger else "true"
            
            # 💡 [문제 변경 감지형 자동 리셋 타이머 고도화]
            # 스크립트 내부에서 현재 문제 번호(file_page)를 저장하고, 이 번호가 달라지면 강제로 0초 초기화합니다.
            stopwatch_html = f"""
            <div id="sw-box" style="background-color: #FFF3CD; padding: 12px; border-radius: 10px; border: 1px solid #FFEBAA; font-family: sans-serif; text-align: center; box-sizing: border-box;">
                <span style="color: #856404; font-weight: bold; font-size: 14px;">⏱️ 문제 풀이 시간</span>
                <div id="stopwatch-display" style="font-size: 22px; font-weight: bold; color: #856404; margin: 6px 0;">0분 00초</div>
                <button id="btn-toggle" onclick="toggleTimer()" style="padding: 5px 16px; background-color: #856404; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 12px; font-weight: bold; min-height: 28px;">⏸️ 일시정지</button>
            </div>
            <script>
                (function() {{
                    const currentId = "{file_page}";
                    const savedId = localStorage.getItem('math_current_page_id');
                    
                    // 핵심: 문제 페이지 번호가 바뀌었거나 패스를 한 경우 시간을 무조건 0으로 강제 초기화
                    if (savedId !== currentId) {{
                        localStorage.setItem('math_timer_sec', '0');
                        localStorage.setItem('math_current_page_id', currentId);
                    }}
                    
                    let totalSeconds = parseInt(localStorage.getItem('math_timer_sec') || '0');
                    let isRunning = {init_running};
                    
                    const display = document.getElementById('stopwatch-display');
                    const btnToggle = document.getElementById('btn-toggle');
                    
                    if (!isRunning) {{
                        btnToggle.textContent = "▶️ 다시 시작";
                        btnToggle.style.backgroundColor = "#28A745";
                    }}
                    
                    updateDisplay(totalSeconds);
                    
                    function updateDisplay(secs) {{
                        const minutes = Math.floor(secs / 60);
                        const seconds = secs % 60;
                        const paddedSeconds = seconds < 10 ? '0' + seconds : seconds;
                        display.textContent = minutes + '분 ' + paddedSeconds + '초';
                    }}
                    
                    const intervalId = setInterval(() => {{
                        if (isRunning) {{
                            totalSeconds++;
                            localStorage.setItem('math_timer_sec', totalSeconds);
                            updateDisplay(totalSeconds);
                        }}
                    }}, 1000);
                    
                    window.toggleTimer = function() {{
                        isRunning = !isRunning;
                        if (isRunning) {{
                            btnToggle.textContent = "⏸️ 일시정지";
                            btnToggle.style.backgroundColor = "#856404";
                        }} else {{
                            btnToggle.textContent = "▶️ 다시 시작";
                            btnToggle.style.backgroundColor = "#28A745";
                        }}
                    }};
                    
                    window.onbeforeunload = function() {{
                        clearInterval(intervalId);
                    }};
                }})();
            </script>
            """
            components.html(stopwatch_html, height=115, scrolling=False)
        
        try:
            cropped_bytes = get_cropped_image_bytes(FIXED_PDF_NAME, file_page - 1, zoom=2.0)
            st.image(cropped_bytes, use_container_width=True)
        except Exception as e:
            st.error(f"❌ 문제 스캔 이미지를 로드하지 못했습니다: {e}")

        st.write("")
        st.markdown("✍️ **여기에 패드로 자유롭게 풀이를 적으세요:**")
        
        canvas_html = """
        <div style="background-color: #F8F9FA; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; font-family: sans-serif;">
            <div style="margin-bottom: 8px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <button id="btnPen" onclick="setMode('pen')" style="padding: 6px 14px; background-color: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">✏️ 연필 모드</button>
                <button id="btnEraser" onclick="setMode('eraser')" style="padding: 6px 14px; background-color: #6C757D; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">🧽 부분 지우개</button>
                <button onclick="clearCanvas()" style="padding: 6px 12px; background-color: #FF4B4B; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">🗑️ 풀이 싹 지우기</button>
                <span id="modeStatus" style="color: #007BFF; font-size: 12px; font-weight: bold; margin-left: 5px;">[현재: 연필 쓰기 모드]</span>
            </div>
            <canvas id="paintCanvas" style="background-color: #FFFFFF; border: 1px solid #D3D3D3; border-radius: 4px; touch-action: none; cursor: crosshair; width: 100%; height: 280px;"></canvas>
        </div>
        <script>
            const canvas = document.getElementById('paintCanvas'); const ctx = canvas.getContext('2d');
            const btnPen = document.getElementById('btnPen'); const btnEraser = document.getElementById('btnEraser');
            const modeStatus = document.getElementById('modeStatus');
            let isDrawing = false; let lastX = 0; let lastY = 0; let currentMode = 'pen';
            
            function resizeCanvas() {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = canvas.width; tempCanvas.height = canvas.height;
                const tempCtx = tempCanvas.getContext('2d'); tempCtx.drawImage(canvas, 0, 0);
                canvas.width = canvas.offsetWidth; canvas.height = 280;
                ctx.drawImage(tempCanvas, 0, 0); applyModeSettings();
            }
            
            function applyModeSettings() {
                ctx.lineCap = 'round'; ctx.lineJoin = 'round';
                if (currentMode === 'pen') {
                    ctx.globalCompositeOperation = 'source-over'; ctx.strokeStyle = '#1E1E1E'; ctx.lineWidth = 3;
                    btnPen.style.backgroundColor = '#007BFF'; btnEraser.style.backgroundColor = '#6C757D';
                    modeStatus.textContent = '[현재: 연필 쓰기 모드]'; modeStatus.style.color = '#007BFF';
                } else {
                    ctx.globalCompositeOperation = 'destination-out'; ctx.lineWidth = 24;
                    btnPen.style.backgroundColor = '#6C757D'; btnEraser.style.backgroundColor = '#E0A800';
                    modeStatus.textContent = '[현재: 부분 지우개 모드]'; modeStatus.style.color = '#E0A800';
                }
            }
            function setMode(mode) { currentMode = mode; applyModeSettings(); }
            window.addEventListener('resize', resizeCanvas); setTimeout(resizeCanvas, 200);
            function getPos(e) {
                const rect = canvas.getBoundingClientRect();
                return { x: (e.touches ? e.touches[0].clientX : e.clientX) - rect.left, y: (e.touches ? e.touches[0].clientY : e.clientY) - rect.top };
            }
            canvas.addEventListener('mousedown', (e) => { isDrawing = true; const p = getPos(e); lastX = p.x; lastY = p.y; });
            canvas.addEventListener('mousemove', (e) => {
                if (!isDrawing) return; e.preventDefault(); const p = getPos(e);
                ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke(); lastX = p.x; lastY = p.y;
            });
            window.addEventListener('mouseup', () => isDrawing = false);
            canvas.addEventListener('touchstart', (e) => { isDrawing = true; const p = getPos(e); lastX = p.x; lastY = p.y; }, {passive:false});
            canvas.addEventListener('touchmove', (e) => {
                if (!isDrawing) return; e.preventDefault(); const p = getPos(e);
                ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke(); lastX = p.x; lastY = p.y;
            }, {passive:false});
            canvas.addEventListener('touchend', () => isDrawing = false);
            function clearCanvas() { 
                const prevComposite = ctx.globalCompositeOperation; ctx.globalCompositeOperation = 'destination-out';
                ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.globalCompositeOperation = prevComposite;
            }
        </script>
        """
        components.html(canvas_html, height=360, scrolling=False)

        st.write("")
        st.markdown("🎯 **최종 정답을 아래 사각형 안에 손글씨로 적으세요:**")

        ans_pad_html = """
        <div style="background-color: #EBF3FF; padding: 10px; border-radius: 8px; border: 1px solid #A3C7FF; font-family: sans-serif;">
            <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span style="color: #004085; font-weight: bold; font-size: 13px;">✏️ 손글씨 정답 적는 칸</span>
                <button onclick="clearAns()" style="padding: 3px 8px; background-color: #6C757D; color: white; border: none; border-radius: 4px; cursor: pointer; font-size:11px;">다시 쓰기</button>
            </div>
            <canvas id="ansCanvas" style="background-color: #FFFFFF; border: 2px dashed #7FB3FF; border-radius: 4px; touch-action: none; width: 100%; height: 110px; cursor: crosshair;"></canvas>
        </div>
        <script>
            const aCanvas = document.getElementById('ansCanvas'); const aCtx = aCanvas.getContext('2d');
            function resizeAnsCanvas() {
                aCanvas.width = aCanvas.offsetWidth; aCanvas.height = 110;
                aCtx.strokeStyle = '#0056B3'; aCtx.lineWidth = 4; aCtx.lineCap = 'round'; aCtx.lineJoin = 'round';
            }
            window.addEventListener('resize', resizeAnsCanvas); setTimeout(resizeAnsCanvas, 200);
            let aDrawing = false; let aX = 0; let aY = 0;
            function getAPos(e) {
                const r = aCanvas.getBoundingClientRect();
                return { x: (e.touches ? e.touches[0].clientX : e.clientX) - r.left, y: (e.touches ? e.touches[0].clientY : e.clientY) - r.top };
            }
            aCanvas.addEventListener('mousedown', (e) => { aDrawing = true; const p = getAPos(e); aX = p.x; aY = p.y; });
            aCanvas.addEventListener('mousemove', (e) => {
                if (!aDrawing) return; e.preventDefault(); const p = getAPos(e);
                aCtx.beginPath(); aCtx.moveTo(aX, aY); aCtx.lineTo(p.x, p.y); aCtx.stroke(); aX = p.x; aY = p.y;
            });
            window.addEventListener('mouseup', () => aDrawing = false);
            aCanvas.addEventListener('touchstart', (e) => { aDrawing = true; const p = getAPos(e); aX = p.x; aY = p.y; }, {passive:false});
            aCanvas.addEventListener('touchmove', (e) => {
                if (!aDrawing) return; e.preventDefault(); const p = getAPos(e);
                aCtx.beginPath(); aCtx.moveTo(aX, aY); aCtx.lineTo(p.x, p.y); aCtx.stroke(); aX = p.x; aY = p.y;
            }, {passive:false});
            aCanvas.addEventListener('touchend', () => aDrawing = false);
            function clearAns() { aCtx.clearRect(0, 0, aCanvas.width, aCanvas.height); }
        </script>
        """
        components.html(ans_pad_html, height=170, scrolling=False)

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 정답 제출하고 해설지 즉시 보기", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 1:1 매칭된 answer.pdf 파일이 깃허브에 필요합니다.")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                
                # 새로운 문제 번호를 뽑음으로써 타이머 내장 스크립트가 '페이지 ID 변경'을 감지하고 리셋하게 유도
                old_page = st.session_state.current_target_page
                new_page = random.randint(1, total_pages_count)
                while total_pages_count > 1 and new_page == old_page:
                    new_page = random.randint(1, total_pages_count)
                    
                st.session_state.current_target_page = new_page
                st.rerun()

        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 1:1 매칭 해설 확인창")
            
            st.markdown("🔧 **해설지 페이지 번호가 맞지 않으면 아래 버튼으로 조절하세요:**")
            move_col1, move_col2, move_col3 = st.columns([1, 2, 1])
            with move_col1:
                if st.button("⬅️ 해설지 1장 앞으로", use_container_width=True):
                    st.session_state.ans_offset -= 1
                    st.rerun()
            with move_col2:
                st.markdown(f"<p style='text-align: center; font-weight: bold; margin-top: 6px;'>현재 해설지 조정 값: {st.session_state.ans_offset} 장</p>", unsafe_allow_html=True)
            with move_col3:
                if st.button("해설지 1장 뒤로 ➡️", use_container_width=True):
                    st.session_state.ans_offset += 1
                    st.rerun()
            
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                target_ans_page = (file_page - 1) + st.session_state.ans_offset
                
                if 0 <= target_ans_page < len(ans_doc):
                    ans_cropped_bytes = get_cropped_image_bytes(ANSWER_PDF_NAME, target_ans_page, zoom=1.8)
                    st.image(ans_cropped_bytes, caption=f"현재 매칭된 해설지 화면 (오프셋 반영: {target_ans_page + 1}쪽)", use_container_width=True)
                else:
                    st.error(f"❌ 설정된 해설지 페이지가 범위를 벗어났습니다. 조절 버튼을 다시 이용해 주세요.")
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 화면을 불러오지 못했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설을 확인하신 후 채점 버튼을 눌러주세요:")
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 정답입니다! (맞춤 처리)", use_container_width=True):
                    st.session_state.history_stats["correct"] += 1
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    st.session_state.show_answer_trigger = False
                    
                    old_page = st.session_state.current_target_page
                    new_page = random.randint(1, total_pages_count)
                    while total_pages_count > 1 and new_page == old_page:
                        new_page = random.randint(1, total_pages_count)
                        
                    st.session_state.current_target_page = new_page
                    save_to_local()
                    st.rerun()
            with b2:
                if st.button("❌ 틀렸습니다... (오답노트행)", use_container_width=True):
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    if file_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(file_page)
                    save_to_local()
                    st.session_state.show_answer_trigger = False
                    
                    old_page = st.session_state.current_target_page
                    new_page = random.randint(1, total_pages_count)
                    while total_pages_count > 1 and new_page == old_page:
                        new_page = random.randint(1, total_pages_count)
                        
                    st.session_state.current_target_page = new_page
                    save_to_local()
                    st.rerun()

# 7. [메뉴 3] 오답노트 관리 구역
elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 누적된 오답 문항이 없습니다!")
    else:
        for w_page in sorted(st.session_state.wrong_notes):
            st.warning(f"📋 복습 대상: 편집 파일 내 {w_page}번째 문항")
            try:
                w_cropped_bytes = get_cropped_image_bytes(FIXED_PDF_NAME, w_page - 1, zoom=1.5)
                st.image(w_cropped_bytes, use_container_width=True)
            except Exception:
                pass
                
            if st.button("이 문항 복습 완료 (삭제)", key=f"del_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.rerun()
            st.write("---")
