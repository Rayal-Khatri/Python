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
            font-size: 3.5rem; font-weight: 700;
            text-align: center;
            padding: 1.2rem 1rem 0.5rem;
            border-radius: 14px; letter-spacing: -2px;
        }
        .analyze-card  { background: #0f1e2e; border: 2px solid #e94560; color: #f0f0f0; }
        .review-card   { background: #0e2218; border: 2px solid #00c48c; color: #f0f0f0; }
        .accuracy-card { background: #1e1a0e; border: 2px solid #f5a623; color: #f0f0f0; }
        .productivity-card { background: #1a0e2e; border: 2px solid #a78bfa; color: #f0f0f0; }

        .card-label {
            font-size: 0.72rem; letter-spacing: 4px;
            text-transform: uppercase; text-align: center;
            padding-bottom: 0.8rem;
            font-family: 'Space Mono', monospace;
        }
        .analyze-label    { color: #e94560; }
        .review-label     { color: #00c48c; }
        .accuracy-label   { color: #f5a623; }
        .productivity-label { color: #a78bfa; }

        .stat-box {
            background: #1a1a2e; border: 1px solid #2a2a4e;
            border-radius: 10px; padding: 0.8rem 1rem;
            text-align: center; font-family: 'Space Mono', monospace;
        }
        .stat-val { font-size: 1.5rem; font-weight: 700; color: #f0f0f0; }
        .stat-lbl { font-size: 0.65rem; letter-spacing: 3px; text-transform: uppercase; color: #888; margin-top: 0.2rem; }

        textarea { font-family: 'Space Mono', monospace !important; font-size: 0.8rem !important; }

        div[data-testid="stNumberInput"] input { font-family: 'Space Mono', monospace; }
    </style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_time(t):
    t = t.strip()
    t = t.split(",")[-1].strip()  # removes date part if present

    for fmt in ("%I:%M %p", "%H:%M", "%I:%M%p"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


def duration_minutes(start_str, end_str):
    """Return duration in minutes between two time strings, handling midnight rollover."""
    start = parse_time(start_str)
    end   = parse_time(end_str)
    if not start or not end:
        return None
    diff = (end - start).total_seconds() / 60
    if diff < 0:
        diff += 24 * 60   # crossed midnight
    if diff == 0:
        diff = 0.1        # avoid divide-by-zero
    return diff


def parse_table(raw_text):
    """
    Expected columns (tab-separated, 8 cols):
    Address | Activity | Type | Start | End | Guides Added | Facets Added | Minutes

    Activity values accepted: Analyzing / Reviewing (case-insensitive)
    Type column is ignored for metrics but stored.
    Minutes column (col 7) is used as the authoritative duration when available.
    """
    tasks, skipped = [], []

    for line in [l.strip() for l in raw_text.strip().splitlines() if l.strip()]:
        parts = [p.strip() for p in line.split("\t")]

        if len(parts) < 5:
            skipped.append(line[:80])
            continue

        address    = parts[0]
        activity   = parts[1].lower()
        model_type = parts[2] if len(parts) > 2 else ""
        start_str  = parts[3]
        end_str    = parts[4]
        guides     = parts[5] if len(parts) > 5 else ""
        facets     = parts[6] if len(parts) > 6 else ""
        mins_raw   = parts[7] if len(parts) > 7 else ""

        if activity not in ("analyzing", "reviewing"):
            skipped.append(f"[unknown activity '{parts[1]}'] {line[:60]}")
            continue

        # Prefer the explicit Minutes column; fall back to computing from times
        minutes = None
        if mins_raw:
            try:
                minutes = float(mins_raw)
                if minutes <= 0:
                    minutes = None
            except ValueError:
                pass

        if minutes is None:
            minutes = duration_minutes(start_str, end_str)

        if minutes is None:
            skipped.append(f"[bad times] {line[:60]}")
            continue

        # Parse guides/facets as integers where possible
        def safe_int(s):
            try:
                return int(float(s))
            except (ValueError, TypeError):
                return 0

        tasks.append({
            "address":    address,
            "activity":   activity,
            "type":       model_type,
            "start":      start_str,
            "end":        end_str,
            "guides":     safe_int(guides),
            "facets":     safe_int(facets),
            "minutes":    minutes,
            "failed":     False,
        })

    return tasks, skipped


def calc_productivity(task_mins, total_hours):
    """
    Available time = total hours − (30 min break per 4 hours worked).
    Target = 90 % of available time.
    Productivity % = task_mins / target * 90
    """
    if total_hours <= 0:
        return 0, 0, 0
    break_mins     = (total_hours / 4) * 30
    available_mins = (total_hours * 60) - break_mins
    target_90      = available_mins * 0.90
    productivity   = (task_mins / target_90 * 90) if target_90 > 0 else 0
    return productivity, available_mins, target_90


def calc_stats(tasks):
    """Returns mph, rph, accuracy, total_task_mins."""
    completed = [t for t in tasks if not t["failed"]]
    a_done    = [t for t in completed if t["activity"] == "analyzing"]
    r_done = [
                t for t in tasks
                if t["activity"] == "reviewing" and not t["failed"]
            ]
    a_all     = [t for t in tasks     if t["activity"] == "analyzing"]
    r_all     = [t for t in tasks     if t["activity"] == "reviewing"]

    a_mins = sum(t["minutes"] for t in a_all)
    r_mins = sum(t["minutes"] for t in r_all)

    analyzing_tasks = [t for t in tasks if t["activity"] == "analyzing"]

    total_analyzing  = len(analyzing_tasks)
    failed_analyzing = sum(1 for t in analyzing_tasks if t["failed"])

    accuracy = (
        (total_analyzing - failed_analyzing) / total_analyzing * 100
        if total_analyzing > 0 else 100
    )

    mph = (len(a_done) / a_mins * 60) if a_mins > 0 else 0
    rph = (len(r_done) / r_mins * 60) if r_mins > 0 else 0
    total_task_mins = sum(t["minutes"] for t in tasks)
    return mph, rph, accuracy, total_task_mins


def render_metrics(tasks, total_hours=0.0, show_productivity=False, key_prefix=""):
    mph, rph, accuracy, total_task_mins = calc_stats(tasks)

    # ── Top metric cards ──────────────────────────────────────────────────────
    cols = st.columns(4) if show_productivity else st.columns(3)

    with cols[0]:
        st.markdown(f'<div class="big-metric analyze-card">{mph:.2f}</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-label analyze-label">Models Per Hour</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="big-metric review-card">{rph:.2f}</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-label review-label">Reviews Per Hour</div>', unsafe_allow_html=True)
    with cols[2]:
        acc_color = "#f5a623" if accuracy >= 90 else "#e94560"
        st.markdown(f'<div class="big-metric accuracy-card" style="border-color:{acc_color}">{accuracy:.1f}%</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-label accuracy-label">Accuracy</div>', unsafe_allow_html=True)

    if show_productivity and total_hours > 0:
        prod, avail, target = calc_productivity(total_task_mins, total_hours)
        prod = min(prod, 999)
        prod_color = "#a78bfa" if prod >= 90 else "#e94560"
        with cols[3]:
            st.markdown(f'<div class="big-metric productivity-card" style="border-color:{prod_color}">{prod:.1f}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-label productivity-label">Productivity</div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Sub-stats row ─────────────────────────────────────────────────────────
    completed = [t for t in tasks if not t["failed"]]
    failed    = [t for t in tasks if t["failed"]]
    a_all     = [t for t in tasks if t["activity"] == "analyzing"]
    r_all     = [t for t in tasks if t["activity"] == "reviewing"]
    a_mins    = sum(t["minutes"] for t in a_all)
    r_mins    = sum(t["minutes"] for t in r_all)

    s_cols = st.columns(6)

    def stat(col, val, lbl):
        col.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-val">{val}</div>'
            f'<div class="stat-lbl">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    stat(s_cols[0], len([t for t in completed if t["activity"] == "analyzing"]), "Models Done")
    stat(s_cols[1], len([t for t in completed if t["activity"] == "reviewing"]), "Reviews Done")
    stat(s_cols[2], len(failed),                                                  "Failed Tasks")
    stat(s_cols[3], f"{a_mins:.0f}m",                                             "Analyze Time")
    stat(s_cols[4], f"{r_mins:.0f}m",                                             "Review Time")

    if show_productivity and total_hours > 0:
        _, avail, target = calc_productivity(total_task_mins, total_hours)
        stat(s_cols[5], f"{target:.0f}m", "90% Target")
    else:
        stat(s_cols[5], f"{total_task_mins:.0f}m", "Total Time")


def render_log_table(tasks, session_key, key_prefix):
    """Render the task log with per-row Failed checkboxes. Mutates session state on toggle."""
    st.markdown("**Task Log** — tick to mark a task as failed")
    st.markdown("")

    # Header
    h_cols = st.columns([3, 1.2, 1, 1, 0.7, 0.7, 0.7, 0.7])
    labels = ["Address", "Activity", "Start", "End", "Mins", "Guides", "Facets", "Failed"]
    for col, lbl in zip(h_cols, labels):
        col.markdown(
            f"<span style='font-size:0.68rem;letter-spacing:2px;text-transform:uppercase;"
            f"color:#888;font-family:Space Mono,monospace'>{lbl}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("<hr style='margin:4px 0;border-color:#2a2a4e'>", unsafe_allow_html=True)

    for i, task in enumerate(tasks):
        c_cols = st.columns([3, 1.2, 1, 1, 0.7, 0.7, 0.7, 0.7])
        is_failed  = task["failed"]
        row_style  = "color:#ff6b6b;text-decoration:line-through;opacity:0.7;" if is_failed else "color:#ccc;"
        act_color  = "#e94560" if task["activity"] == "analyzing" else "#00c48c"
        act_label  = "Analyzing" if task["activity"] == "analyzing" else "Reviewing"
        mono       = "font-family:Space Mono,monospace;font-size:0.78rem;"

        c_cols[0].markdown(f"<span style='{mono}{row_style}'>{task['address'][:45]}</span>", unsafe_allow_html=True)
        c_cols[1].markdown(f"<span style='{mono}color:{act_color}'>{act_label}</span>",       unsafe_allow_html=True)
        c_cols[2].markdown(f"<span style='{mono}{row_style}'>{task['start']}</span>",          unsafe_allow_html=True)
        c_cols[3].markdown(f"<span style='{mono}{row_style}'>{task['end']}</span>",            unsafe_allow_html=True)
        c_cols[4].markdown(f"<span style='{mono}{row_style}'>{task['minutes']:.1f}</span>",    unsafe_allow_html=True)
        c_cols[5].markdown(f"<span style='{mono}{row_style}'>{task.get('guides', '—')}</span>", unsafe_allow_html=True)
        c_cols[6].markdown(f"<span style='{mono}{row_style}'>{task.get('facets', '—')}</span>", unsafe_allow_html=True)

        if task["activity"] == "analyzing":
            new_failed = c_cols[7].checkbox(
                "",
                value=is_failed,
                key=f"{key_prefix}_fail_{i}"
            )

            if new_failed != is_failed:
                st.session_state[session_key][i]["failed"] = new_failed
                st.rerun()
        else:
            c_cols[7].markdown("—")
        if new_failed != is_failed:
            st.session_state[session_key][i]["failed"] = new_failed
            st.rerun()

        st.markdown("<hr style='margin:2px 0;border-color:#1a1a2e'>", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🏗️ 3D Model & Review Tracker")
st.caption("Track Models Per Hour · Reviews Per Hour · Accuracy · Productivity")
st.divider()

tab1, tab2 = st.tabs(["📋 Paste Table Data", "✏️ Manual Entry"])


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Paste Table
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        "<span style='font-family:Space Mono,monospace;font-size:0.75rem;color:#888'>"
        "Expected columns: Address · Activity · Type · Start · End · Guides Added · Facets Added · Minutes"
        "</span>",
        unsafe_allow_html=True,
    )
    raw = st.text_area(
        "Paste your tab-separated task table here:",
        height=180,
        placeholder="2444 North Franklin Ave\tAnalyzing\tRoof\t6:50 PM\t7:01 PM\t3\t5\t11",
        label_visibility="collapsed",
    )

    col_b1, col_b2, col_b3 = st.columns([1, 1, 4])
    with col_b1:
        parse_btn = st.button("⚡ Calculate", use_container_width=True, key="parse_btn")
    with col_b2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_parsed"):
            st.session_state.parsed_tasks   = []
            st.session_state.parsed_skipped = []
            st.rerun()

    if parse_btn and raw.strip():
        tasks, skipped = parse_table(raw)
        st.session_state.parsed_tasks   = tasks
        st.session_state.parsed_skipped = skipped
        if not tasks:
            st.warning("No valid rows found. Check the column order and that Activity is 'Analyzing' or 'Reviewing'.")
        st.rerun()

    if st.session_state.get("parsed_tasks"):
        tasks   = st.session_state.parsed_tasks
        skipped = st.session_state.get("parsed_skipped", [])

        st.write("Parsed rows:", len(tasks))
        st.write("Skipped rows:", len(skipped))

        st.divider()

        p_col1, p_col2 = st.columns([1, 3])
        with p_col1:
            total_hours = st.number_input(
                "Total hours worked:",
                min_value=0.0, step=0.5, format="%.1f",
                key="p_hours_tab1",
            )

        render_metrics(tasks, total_hours, show_productivity=(total_hours > 0), key_prefix="t1")
        st.divider()
        render_log_table(tasks, "parsed_tasks", key_prefix="t1")

        if skipped:
            with st.expander(f"⚠️ {len(skipped)} row(s) skipped — click to inspect"):
                for s in skipped:
                    st.text(s)


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — Manual Entry
# ════════════════════════════════════════════════════════════════════════
with tab2:
    if "manual_tasks" not in st.session_state:
        st.session_state.manual_tasks = []

    mc1, mc2, mc3 = st.columns([1, 1, 1])
    with mc1:
        entry_type = st.radio("Task type:", ["Analyzing", "Reviewing"], horizontal=True)
    with mc2:
        minutes_input = st.number_input("Time taken (minutes):", min_value=0.0, step=1.0, format="%.1f")
    with mc3:
        total_hours_m = st.number_input(
            "Total hours worked:", min_value=0.0, step=0.5, format="%.1f",
            key="p_hours_tab2",
        )

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("✅ Add Entry", use_container_width=True):
            mins = minutes_input if minutes_input > 0 else 0.1
            st.session_state.manual_tasks.append({
                "address":  f"Entry {len(st.session_state.manual_tasks) + 1}",
                "activity": entry_type.lower(),
                "type":     "",
                "start":    "—",
                "end":      "—",
                "guides":   0,
                "facets":   0,
                "minutes":  mins,
                "failed":   False,
            })
            st.rerun()
    with b2:
        if st.button("🗑️ Reset All", use_container_width=True):
            st.session_state.manual_tasks = []
            st.rerun()

    if st.session_state.manual_tasks:
        mt = st.session_state.manual_tasks
        st.divider()
        render_metrics(mt, total_hours_m, show_productivity=(total_hours_m > 0), key_prefix="t2")
        st.divider()
        render_log_table(mt, "manual_tasks", key_prefix="t2")