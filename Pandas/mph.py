import streamlit as st

st.set_page_config(page_title="3D Model Per Hour Tracker", page_icon="🏗️", layout="centered")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Syne', sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        .mph-display {
            font-family: 'Space Mono', monospace;
            font-size: 4rem;
            font-weight: 700;
            color: #f0f0f0;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 2px solid #e94560;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            text-align: center;
            margin: 1rem 0;
            letter-spacing: -2px;
        }
        .mph-label {
            font-size: 0.85rem;
            color: #e94560;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .stat-box {
            background: #1a1a2e;
            border: 1px solid #2a2a4e;
            border-radius: 10px;
            padding: 1rem 1.5rem;
            text-align: center;
            color: #ccc;
            font-family: 'Space Mono', monospace;
        }
        .stat-val {
            font-size: 1.8rem;
            font-weight: 700;
            color: #f0f0f0;
        }
        .stat-lbl {
            font-size: 0.7rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #888;
            margin-top: 0.2rem;
        }
        .log-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #2a2a4e;
            font-family: 'Space Mono', monospace;
            font-size: 0.85rem;
            color: #aaa;
        }
        .log-row span.accent { color: #e94560; }
    </style>
""", unsafe_allow_html=True)

# --- State ---
if "models" not in st.session_state:
    st.session_state.models = []  # list of minutes per model

# --- Header ---
st.markdown("## 🏗️ 3D Model Per Hour")
st.caption("Track how fast you're producing building models — in real time.")
st.divider()

# --- Input ---
model_num = len(st.session_state.models) + 1
minutes_input = st.number_input(
    f"Time for Model {model_num} (minutes)",
    min_value=0.0,
    step=1.0,
    format="%.1f",
    key="minutes_input"
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("✅ Add Model", use_container_width=True):
        mins = minutes_input if minutes_input > 0 else 0.1
        st.session_state.models.append(mins)
        st.rerun()
with col2:
    if st.button("🗑️ Reset All", use_container_width=True):
        st.session_state.models = []
        st.rerun()

st.divider()

# --- Stats ---
if st.session_state.models:
    total_models = len(st.session_state.models)
    total_minutes = sum(st.session_state.models)
    mph = (total_models / total_minutes) * 60

    st.markdown('<div class="mph-label">Models Per Hour</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mph-display">{mph:.2f}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{total_models}</div><div class="stat-lbl">Models Done</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{total_minutes:.1f}</div><div class="stat-lbl">Total Mins</div></div>', unsafe_allow_html=True)
    with c3:
        hrs = total_minutes / 60
        st.markdown(f'<div class="stat-box"><div class="stat-val">{hrs:.2f}</div><div class="stat-lbl">Total Hours</div></div>', unsafe_allow_html=True)

    st.divider()

    # --- Log ---
    st.markdown("**Model Log**")
    for i, m in enumerate(st.session_state.models, 1):
        st.markdown(
            f'<div class="log-row"><span>Model {i}</span><span><span class="accent">{m:.1f} mins</span></span></div>',
            unsafe_allow_html=True
        )
else:
    st.info("Add your first model's time above to start tracking.")