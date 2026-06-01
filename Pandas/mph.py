import streamlit as st
from datetime import datetime

st.set_page_config(page_title="3D Model Tracker", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
        .block-container { padding-top: 2rem; }

        .big-metric {
            font-family: 'Space Mono', monospace;
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            padding: 1.2rem 1rem 0.5rem;
            border-radius: 14px;
            letter-spacing: -2px;
        }
        .analyze-card { background: #0f1e2e; border: 2px solid #e94560; color: #f0f0f0; }
        .review-card  { background: #0e2218; border: 2px solid #00c48c; color: #f0f0f0; }
        .card-label {
            font-size: 0.72rem;
            letter-spacing: 4px;
            text-transform: uppercase;
            text-align: center;
            padding-bottom: 0.8rem;
            font-family: 'Space Mono', monospace;
        }
        .analyze-label { color: #e94560; }
        .review-label  { color: #00c48c; }

        .stat-box {
            background: #1a1a2e;
            border: 1px solid #2a2a4e;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            text-align: center;
            font-family: 'Space Mono', monospace;
        }
        .stat-val { font-size: 1.5rem; font-weight: 700; color: #f0f0f0; }
        .stat-lbl { font-size: 0.65rem; letter-spacing: 3px; text-transform: uppercase; color: #888; margin-top: 0.2rem; }

        .log-table { width: 100%; border-collapse: collapse; font-family: 'Space Mono', monospace; font-size: 0.78rem; }
        .log-table th { text-align: left; color: #888; font-weight: 400; letter-spacing: 2px; text-transform: uppercase; padding: 0.4rem 0.6rem; border-bottom: 1px solid #2a2a4e; }
        .log-table td { padding: 0.45rem 0.6rem; border-bottom: 1px solid #1a1a2e; color: #ccc; }
        .tag-analyze { color: #e94560; }
        .tag-review  { color: #00c48c; }

        textarea { font-family: 'Space Mono', monospace !important; font-size: 0.8rem !important; }
    </style>
""", unsafe_allow_html=True)


def parse_time(t):
    """Parse time string like '6:50 PM' into a datetime object."""
    try:
        return datetime.strptime(t.strip(), "%I:%M %p")
    except:
        return None


def parse_table(raw_text):
    """Parse tab-separated table rows into structured task list."""
    tasks = []
    skipped = []
    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]

    for line in lines:
        parts = line.split("\t")
        if len(parts) < 7:
            skipped.append(line[:60])
            continue

        address   = parts[0].strip()
        task_type = parts[1].strip().lower()   # "analyzing" or "reviewing"
        start_str = parts[3].strip()
        end_str   = parts[4].strip()

        if task_type not in ("analyzing", "reviewing"):
            skipped.append(line[:60])
            continue

        start = parse_time(start_str)
        end   = parse_time(end_str)

        if not start or not end:
            skipped.append(line[:60])
            continue

        diff = (end - start).total_seconds() / 60
        if diff < 0:
            diff += 24 * 60   # handle midnight crossover
        if diff == 0:
            diff = 0.1        # 0-min entries → 0.1

        tasks.append({
            "address":   address,
            "type":      task_type,
            "start":     start_str,
            "end":       end_str,
            "minutes":   diff,
        })

    return tasks, skipped


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🏗️ 3D Model & Review Tracker")
st.caption("Paste your task log to calculate Models Per Hour and Reviews Per Hour.")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋 Paste Table Data", "✏️ Manual Entry"])

# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Paste table
# ════════════════════════════════════════════════════════════════════════
with tab1:
    raw = st.text_area(
        "Paste your tab-separated task table here:",
        height=200,
        placeholder="2444 North Franklin Avenue...   Analyzing   Roof   6:50 PM   7:01 PM   30   9   11"
    )

    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        parse_btn = st.button("⚡ Calculate", use_container_width=True, key="parse_btn")

    if parse_btn and raw.strip():
        tasks, skipped = parse_table(raw)
        st.session_state.parsed_tasks = tasks
        st.session_state.parsed_skipped = skipped

    if "parsed_tasks" in st.session_state and st.session_state.parsed_tasks:
        tasks   = st.session_state.parsed_tasks
        skipped = st.session_state.get("parsed_skipped", [])

        analyze_tasks = [t for t in tasks if t["type"] == "analyzing"]
        review_tasks  = [t for t in tasks if t["type"] == "reviewing"]

        a_count = len(analyze_tasks)
        a_mins  = sum(t["minutes"] for t in analyze_tasks)
        r_count = len(review_tasks)
        r_mins  = sum(t["minutes"] for t in review_tasks)

        mph = (a_count / a_mins * 60) if a_mins > 0 else 0
        rph = (r_count / r_mins * 60) if r_mins > 0 else 0

        st.divider()

        # ── Big metrics ──
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f'<div class="big-metric analyze-card">{mph:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-label analyze-label">Models Per Hour (Analyzing)</div>', unsafe_allow_html=True)
        with mc2:
            st.markdown(f'<div class="big-metric review-card">{rph:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-label review-label">Reviews Per Hour (Reviewing)</div>', unsafe_allow_html=True)

        st.markdown("")

        # ── Sub stats ──
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        def stat(col, val, lbl):
            col.markdown(f'<div class="stat-box"><div class="stat-val">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

        stat(s1, a_count,          "Models Done")
        stat(s2, f"{a_mins:.0f}",  "Analyze Mins")
        stat(s3, f"{a_mins/60:.2f}","Analyze Hrs")
        stat(s4, r_count,          "Reviews Done")
        stat(s5, f"{r_mins:.0f}",  "Review Mins")
        stat(s6, f"{r_mins/60:.2f}","Review Hrs")

        st.divider()

        # ── Log table ──
        st.markdown("**Task Log**")
        rows_html = ""
        for i, t in enumerate(tasks, 1):
            tag_class = "tag-analyze" if t["type"] == "analyzing" else "tag-review"
            tag_label = "Analyzing"  if t["type"] == "analyzing" else "Reviewing"
            rows_html += f"""
            <tr>
                <td>{i}</td>
                <td>{t['address']}</td>
                <td class="{tag_class}">{tag_label}</td>
                <td>{t['start']}</td>
                <td>{t['end']}</td>
                <td>{t['minutes']:.1f}</td>
            </tr>"""

        st.markdown(f"""
        <table class="log-table">
            <thead><tr>
                <th>#</th><th>Address</th><th>Type</th>
                <th>Start</th><th>End</th><th>Mins</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

        if skipped:
            with st.expander(f"⚠️ {len(skipped)} rows skipped (unrecognized format)"):
                for s in skipped:
                    st.text(s)


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — Manual Entry (original feature)
# ════════════════════════════════════════════════════════════════════════
with tab2:
    if "manual_tasks" not in st.session_state:
        st.session_state.manual_tasks = []

    entry_type = st.radio("Task type:", ["Analyzing", "Reviewing"], horizontal=True)
    minutes_input = st.number_input("Time taken (minutes):", min_value=0.0, step=1.0, format="%.1f")

    mc1, mc2 = st.columns([1, 1])
    with mc1:
        if st.button("✅ Add Entry", use_container_width=True):
            mins = minutes_input if minutes_input > 0 else 0.1
            st.session_state.manual_tasks.append({"type": entry_type.lower(), "minutes": mins})
            st.rerun()
    with mc2:
        if st.button("🗑️ Reset", use_container_width=True):
            st.session_state.manual_tasks = []
            st.rerun()

    if st.session_state.manual_tasks:
        mt = st.session_state.manual_tasks
        a_tasks = [t for t in mt if t["type"] == "analyzing"]
        r_tasks = [t for t in mt if t["type"] == "reviewing"]

        a_mins = sum(t["minutes"] for t in a_tasks)
        r_mins = sum(t["minutes"] for t in r_tasks)
        mph = (len(a_tasks) / a_mins * 60) if a_mins > 0 else 0
        rph = (len(r_tasks) / r_mins * 60) if r_mins > 0 else 0

        st.divider()
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f'<div class="big-metric analyze-card">{mph:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-label analyze-label">Models Per Hour</div>', unsafe_allow_html=True)
        with mc2:
            st.markdown(f'<div class="big-metric review-card">{rph:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-label review-label">Reviews Per Hour</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("**Log**")
        for i, t in enumerate(mt, 1):
            tag = "🔴 Analyzing" if t["type"] == "analyzing" else "🟢 Reviewing"
            st.markdown(
                f'<div style="font-family:Space Mono,monospace;font-size:0.82rem;padding:0.4rem 0;border-bottom:1px solid #1a1a2e;color:#aaa">'
                f'<b>{i}.</b> {tag} — {t["minutes"]:.1f} mins</div>',
                unsafe_allow_html=True
            )