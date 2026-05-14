import os
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox
from geopy.geocoders import Photon
import requests
from datetime import datetime
from database import (get_db, User, Vehicle, Warehouse, Route, Stop,
                      Notification, hash_password)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Routr", layout="wide", page_icon="🛰️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

:root {
    --bg:            #0b0b10;
    --text:          #e4e4f0;
    --text-dim:      #8888a0;
    --text-muted:    #44445a;
    --glass-bg:      rgba(255,255,255,0.035);
    --glass-border:  rgba(255,255,255,0.07);
    --glass-hover:   rgba(255,255,255,0.065);
    --sidebar-bg:    rgba(8,8,13,0.9);
    --input-bg:      rgba(255,255,255,0.05);
    --input-border:  rgba(255,255,255,0.1);
    --divider:       rgba(255,255,255,0.06);
    --shadow:        rgba(0,0,0,0.5);
    --scrollbar:     rgba(255,255,255,0.1);
    /* Neutral accent — white/silver, not purple */
    --accent:        #c8c8d8;
    --accent-soft:   rgba(200,200,216,0.08);
    --accent-border: rgba(200,200,216,0.18);
    /* Glow for text readability */
    --text-glow:     0 0 18px rgba(220,220,255,0.25);
    --dim-glow:      0 0 12px rgba(160,160,200,0.15);
}

.stApp {
    background: #0b0b10 !important;
    color: var(--text) !important;
    min-height: 100vh;
}

/* ── Animated lilac orbs (decorative only) ── */
.stApp::before {
    content: '';
    position: fixed; top: -15%; left: -8%;
    width: 700px; height: 700px;
    background: radial-gradient(circle,
        rgba(148,130,230,0.07) 0%,
        rgba(120,100,210,0.03) 40%,
        transparent 70%);
    border-radius: 50%; pointer-events: none;
    animation: orb1 24s ease-in-out infinite; z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed; bottom: -20%; right: -8%;
    width: 600px; height: 600px;
    background: radial-gradient(circle,
        rgba(160,120,255,0.05) 0%,
        rgba(130,100,220,0.02) 40%,
        transparent 70%);
    border-radius: 50%; pointer-events: none;
    animation: orb2 30s ease-in-out infinite; z-index: 0;
}
/* Third small orb for depth */
.stMainBlockContainer::before {
    content: '';
    position: fixed; top: 50%; left: 55%;
    width: 400px; height: 400px;
    background: radial-gradient(circle,
        rgba(100,90,180,0.04) 0%,
        transparent 65%);
    border-radius: 50%; pointer-events: none;
    animation: orb3 18s ease-in-out infinite reverse; z-index: 0;
}
@keyframes orb1 {
    0%,100% { transform: translate(0,0) scale(1); }
    30%      { transform: translate(80px,50px) scale(1.08); }
    65%      { transform: translate(-30px,80px) scale(0.94); }
}
@keyframes orb2 {
    0%,100% { transform: translate(0,0) scale(1); }
    35%      { transform: translate(-70px,-40px) scale(1.06); }
    70%      { transform: translate(50px,-60px) scale(0.92); }
}
@keyframes orb3 {
    0%,100% { transform: translate(0,0) scale(1); }
    50%      { transform: translate(-60px,40px) scale(1.12); }
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    backdrop-filter: blur(28px) !important;
    border-right: 1px solid var(--glass-border) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--text-dim) !important;
}

/* ── Text glow for readability ── */
h1 {
    color: #f0f0ff !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    text-shadow: var(--text-glow) !important;
    -webkit-text-fill-color: unset !important;
}
h2, h3 {
    color: #d8d8ec !important;
    font-weight: 600 !important;
    text-shadow: var(--dim-glow) !important;
}
p, li, label, span, div {
    color: var(--text) !important;
    text-shadow: var(--dim-glow) !important;
}
.stCaption, small {
    color: var(--text-muted) !important;
    text-shadow: none !important;
}
hr { border-color: var(--divider) !important; }

/* ── Buttons — neutral glass, no purple ── */
.stButton > button {
    background: var(--glass-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
    backdrop-filter: blur(10px) !important;
    text-shadow: none !important;
}
.stButton > button:hover {
    background: var(--glass-hover) !important;
    border-color: var(--accent-border) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px var(--shadow) !important;
}
.stButton > button[kind="primary"] {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(255,255,255,0.18) !important;
    box-shadow: 0 6px 28px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transform: translateY(-2px) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--input-bg) !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    text-shadow: var(--dim-glow) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(200,200,216,0.4) !important;
    box-shadow: 0 0 0 3px rgba(200,200,216,0.08), 0 0 12px rgba(200,200,216,0.06) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 14px !important;
    padding: 4px !important;
    border: 1px solid var(--glass-border) !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
    text-shadow: none !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.08) !important;
    color: var(--text) !important;
    box-shadow: 0 1px 8px rgba(0,0,0,0.3) !important;
    text-shadow: var(--dim-glow) !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    backdrop-filter: blur(12px) !important;
}
.streamlit-expanderHeader:hover {
    background: var(--glass-hover) !important;
    border-color: var(--accent-border) !important;
}
.streamlit-expanderContent {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid var(--glass-border) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    backdrop-filter: blur(12px) !important;
}

/* ── Metrics / dataframes ── */
[data-testid="stMetric"] {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stDataFrame"] {
    border-radius: 12px !important; overflow: hidden !important;
}

/* ── Alerts ── */
.stAlert {
    background: var(--glass-bg) !important;
    border-radius: 12px !important;
    border: 1px solid var(--glass-border) !important;
    backdrop-filter: blur(12px) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-border); }

/* ── Login box — wider, proper padding so text stays inside ── */
.login-box {
    max-width: 420px;
    width: 100%;
    margin: 60px auto;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    padding: 48px 44px;
    box-shadow:
        0 8px 48px rgba(0,0,0,0.5),
        0 1px 0 rgba(255,255,255,0.08) inset,
        0 0 60px rgba(140,120,220,0.06);
    animation: fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1);
    position: relative;
    overflow: visible;
    box-sizing: border-box;
}
.login-box * {
    position: relative;
    z-index: 2;
}
.login-box h1, .login-box h2, .login-box h3 {
    color: #f0f0ff !important;
    text-shadow: 0 0 20px rgba(200,190,255,0.3) !important;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Glass card ── */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 20px; margin-bottom: 14px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.2s ease;
}
.glass-card:hover {
    border-color: var(--accent-border);
    box-shadow: 0 6px 28px var(--shadow);
    transform: translateY(-1px);
}

/* ── Stop row ── */
.stop-row {
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px;
    border-left: 4px solid rgba(200,200,220,0.3);
    transition: background 0.2s ease, transform 0.15s ease;
}
.stop-row:hover {
    background: var(--glass-hover);
    transform: translateX(2px);
}
.stop-row b { text-shadow: var(--dim-glow); }

/* ── Notif row ── */
.notif-row {
    background: rgba(245,158,11,0.05);
    backdrop-filter: blur(12px);
    border-left: 3px solid rgba(245,158,11,0.45);
    border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px;
    font-size: 0.875em;
    transition: background 0.2s ease;
}
.notif-row:hover { background: rgba(245,158,11,0.09); }

/* ── Tag ── */
.tag {
    font-size: 0.72em; padding: 2px 8px;
    border-radius: 20px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    margin-left: 6px; font-weight: 500;
    color: var(--text-dim);
    text-shadow: none;
}

/* ── Progress bar ── */
.progress-bar-bg {
    background: var(--glass-border);
    border-radius: 99px; height: 6px;
    margin-top: 6px; overflow: hidden;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #34d399, #10b981);
    border-radius: 99px; height: 6px;
    transition: width 0.6s ease;
    box-shadow: 0 0 10px rgba(52,211,153,0.5);
}

/* ── Stat card ── */
.stat-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px; padding: 20px; margin-bottom: 14px;
    transition: all 0.25s ease; animation: fadeInUp 0.4s ease;
}
.stat-card:hover {
    background: var(--glass-hover);
    border-color: var(--accent-border);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px var(--shadow);
}
.stat-card table td { padding: 4px 0; color: var(--text-dim); text-shadow: none; }
.stat-card table td:last-child { color: var(--text); font-weight: 500; text-shadow: var(--dim-glow); }
</style>
""", unsafe_allow_html=True)


STOP_STATUSES = {
    "pending":          "🕐 Pending",
    "out_for_delivery": "🚚 Out for Delivery",
    "delivered":        "✅ Delivered",
    "delayed":          "⚠️ Delayed",
    "rescheduled":      "📅 Rescheduled",
    "cancelled":        "❌ Cancelled",
}
STOP_COLORS = {
    "pending": "#94a3b8", "out_for_delivery": "#60a5fa", "delivered": "#34d399",
    "delayed": "#fbbf24", "rescheduled": "#f97316",      "cancelled": "#f87171",
}
ROUTE_STATUSES = {
    "draft": "📝 Draft", "active": "🟢 Active",
    "in_progress": "🚚 In Progress", "completed": "✅ Completed", "cancelled": "❌ Cancelled",
}
PALETTE = ["#6C8AFF","#34d399","#f97316","#f87171","#a78bfa","#60a5fa","#fbbf24","#e879f9"]

for k in ["user_id","user_role","username"]:
    if k not in st.session_state: st.session_state[k] = None


# ── FIX 10: db per-render, not module-level singleton ────
def get_db_session():
    return get_db()

# Use a cached-per-session db handle via session_state
# if "_db" not in st.session_state:
#     st.session_state["_db"] = get_db()
# db = st.session_state["_db"]


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
def search_places(q):
    if not q: return []
    try:
        locs = Photon(user_agent="fleet_app").geocode(q, exactly_one=False, limit=5)
        return [(l.address, (l.latitude, l.longitude)) for l in locs] if locs else []
    except: return []

def notify(msg, tag=""):
    db.add(Notification(message=msg, tag=tag)); db.commit()

def rcolor(rid): return PALETTE[rid % len(PALETTE)]

def get_ordered_stops(route):
    stops = list(route.stops)
    if route.order:
        try:
            idx = [int(i) for i in route.order.split(",") if i]
            if len(idx) == len(stops): return [stops[i] for i in idx]
        except: pass
    return stops

def wh_options():
    return {"— None —": None, **{w.name: w.id for w in db.query(Warehouse).all()}}

# ── FIX 9: Confirmation helper ───────────────────────────
def confirm_button(label, key, confirm_label="⚠️ Confirm?"):
    """Two-click confirmation. Returns True only on the second click."""
    armed_key = f"_armed_{key}"
    if not st.session_state.get(armed_key):
        if st.button(label, key=key, width='stretch'):
            st.session_state[armed_key] = True
            st.rerun()
        return False
    else:
        st.warning(confirm_label)
        c1, c2 = st.columns(2)
        if c1.button("Yes, delete", key=f"{key}_yes", width='stretch'):
            st.session_state[armed_key] = False
            return True
        if c2.button("Cancel", key=f"{key}_no", width='stretch'):
            st.session_state[armed_key] = False
            st.rerun()
        return False

# ── Route progress summary ────────────────────────────────
def route_progress(route):
    """Returns (delivered, total) counts for a route."""
    stops = list(route.stops)
    delivered = sum(1 for s in stops if s.status == "delivered")
    return delivered, len(stops)


# ──────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────
def show_login():
    # Inject a full-page centering wrapper and the glass card as a background layer.
    # Streamlit widgets render inside the center column naturally.
    st.markdown("""
    <style>
        /* Hide default padding so the login fills the viewport nicely */
        .stMainBlockContainer { padding-top: 0 !important; }

        /* Full-page vertical centering */
        .login-page-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
            width: 100%;
        }

        /* The glass card — sits behind the column via negative margin trick */
        .login-card {
            position: relative;
            width: 420px;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(40px);
            -webkit-backdrop-filter: blur(40px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 28px;
            padding: 48px 40px 40px 40px;
            box-shadow:
                0 8px 48px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.08),
                0 0 80px rgba(140,120,220,0.07);
            animation: fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1);
            margin: 0 auto;
        }
        .login-card h1 {
            color: #f0f0ff !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            margin-bottom: 4px !important;
            text-shadow: 0 0 20px rgba(200,190,255,0.35) !important;
        }
        .login-card .subtitle {
            color: #6666880 !important;
            font-size: 0.875rem;
            margin-bottom: 28px;
            color: #88889a;
        }
        /* Make inputs inside card look right */
        .login-card .stTextInput > div > div > input {
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #e8e8f8 !important;
            font-size: 0.95rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Use columns to center the content — blank | content | blank
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
            <div style="text-align:center; padding: 80px 0 20px 0;">
                <div style="font-size:2.4rem; margin-bottom:8px;">🛰️</div>
                <h1 style="color:#f0f0ff; font-size:2rem; font-weight:700;
                           text-shadow: 0 0 24px rgba(200,190,255,0.4);
                           margin:0 0 4px 0;">Routr</h1>
                <p style="color:#66667a; font-size:0.875rem; margin:0 0 32px 0;">
                    Fleet management & route optimization
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Glass card wrapper — uses st.container with custom CSS
        with st.container():
            st.markdown("""
                <div style="
                    background: rgba(255,255,255,0.05);
                    backdrop-filter: blur(40px);
                    -webkit-backdrop-filter: blur(40px);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 24px;
                    padding: 36px 32px 28px 32px;
                    box-shadow: 0 8px 48px rgba(0,0,0,0.5),
                                inset 0 1px 0 rgba(255,255,255,0.08),
                                0 0 80px rgba(140,120,220,0.08);
                    margin-bottom: 12px;
                ">
                <p style="color:#8888a0; font-size:0.8rem; margin:0 0 20px 0;
                          letter-spacing:0.08em; text-transform:uppercase;">
                    Sign in to continue
                </p>
                </div>
            """, unsafe_allow_html=True)

            u = st.text_input("Username", placeholder="Enter username")
            p = st.text_input("Password", type="password", placeholder="Enter password")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if st.button("Sign In →", width='stretch', type="primary"):
                user = db.query(User).filter(User.username == u).first()
                if user and user.password == hash_password(p):
                    st.session_state.update(user_id=user.id,
                                            user_role=user.role,
                                            username=user.username)
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

            st.markdown("""
                <p style="text-align:center; color:#44445a;
                          font-size:0.78rem; margin-top:16px;">
                    Default: admin / admin123
                </p>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# STOP DETAIL EXPANDER
# ──────────────────────────────────────────────────────────
def stop_detail(stop, ctx=""):
    """ctx must be unique per call site to avoid duplicate widget keys."""
    k     = f"{ctx}_{stop.id}"
    label = STOP_STATUSES.get(stop.status, stop.status)
    with st.expander(f"📦 {stop.name}  ·  {label}"):

        # ── FIX 7: Show recipient info read-only first so driver sees it clearly ──
        if stop.recipient_name or stop.recipient_phone or stop.recipient_note:
            st.markdown(
                f"**👤 {stop.recipient_name or '—'}**"
                + (f"  ·  📞 {stop.recipient_phone}" if stop.recipient_phone else "")
                + (f"\n\n📝 {stop.recipient_note}" if stop.recipient_note else "")
            )
            st.divider()

        # Editable recipient fields
        c1, c2 = st.columns(2)
        rname  = c1.text_input("Recipient",  value=stop.recipient_name  or "", key=f"rn_{k}")
        rphone = c2.text_input("Phone",      value=stop.recipient_phone or "", key=f"rp_{k}")
        rnote  = st.text_area("Note",        value=stop.recipient_note  or "", key=f"rnote_{k}", height=60)
        if st.button("Save details", key=f"save_{k}"):
            stop.recipient_name=rname; stop.recipient_phone=rphone; stop.recipient_note=rnote
            db.commit(); st.success("Saved.")

        st.divider()
        new_st = st.selectbox("Status", list(STOP_STATUSES.keys()),
                              index=list(STOP_STATUSES.keys()).index(stop.status)
                                    if stop.status in STOP_STATUSES else 0,
                              format_func=lambda s: STOP_STATUSES[s], key=f"st_{k}")
        msg = ""
        if new_st in ("delayed","rescheduled","cancelled"):
            msg = st.text_area("Reason:", value=stop.status_message or "",
                               key=f"msg_{k}", height=60)
        if st.button("📣 Send update", key=f"upd_{k}", type="primary"):
            stop.status=new_st; stop.status_message=msg
            stop.updated_at=datetime.utcnow(); db.commit()
            recip = stop.recipient_name or stop.recipient_phone or "recipient"
            notify(f"{STOP_STATUSES[new_st]} — '{stop.name}' for {recip} "
                   f"by '{st.session_state.username}'" + (f": {msg}" if msg else ""),
                   tag="delivery")
            if stop.recipient_phone:
                st.info(f"📱 SMS → {stop.recipient_phone}: {STOP_STATUSES[new_st]}"
                        + (f" — {msg}" if msg else ""))
            st.rerun()


# ──────────────────────────────────────────────────────────
# MAP
# ──────────────────────────────────────────────────────────
def route_map(routes, height=460, key="map"):
    all_stops = [s for r in routes for s in r.stops]
    whs       = [r.warehouse for r in routes if r.warehouse]

    # Set initial center once — never update it again so the map
    # never jumps when Streamlit reruns.
    sc_key = f"_mapcenter_{key}"
    if sc_key not in st.session_state:
        st.session_state[sc_key] = (
            [whs[0].lat, whs[0].lon] if whs else
            ([all_stops[0].lat, all_stops[0].lon] if all_stops else [11.25, 75.78])
        )

    m = folium.Map(location=st.session_state[sc_key],
                   zoom_start=12,
                   tiles="CartoDB dark_matter")

    seen_wh = set()
    for r in routes:
        if r.warehouse and r.warehouse.id not in seen_wh:
            folium.Marker([r.warehouse.lat, r.warehouse.lon],
                          tooltip=f"🏭 {r.warehouse.name}",
                          icon=folium.Icon(color="orange", icon="home")).add_to(m)
            seen_wh.add(r.warehouse.id)

        color = rcolor(r.id)
        stops = get_ordered_stops(r)
        for i, s in enumerate(stops):
            sc = STOP_COLORS.get(s.status, color)
            folium.CircleMarker([s.lat, s.lon], radius=8, color=sc,
                                fill=True, fill_color=sc, fill_opacity=0.85,
                                tooltip=f"[{r.name}] {i+1}. {s.name}").add_to(m)
        if len(stops) > 1:
            pts = ([[r.warehouse.lat, r.warehouse.lon]] if r.warehouse else []) + \
                  [[s.lat, s.lon] for s in stops]
            folium.PolyLine(pts, color=color, weight=3, opacity=0.8).add_to(m)

    return st_folium(m, height=height, width='stretch', key=key)


# ──────────────────────────────────────────────────────────
# WAREHOUSE TAB
# ──────────────────────────────────────────────────────────
def tab_warehouses():
    warehouses = db.query(Warehouse).all()

    for wh in warehouses:
        c1, c2, c3 = st.columns([4, 3, 1])
        c1.markdown(f"**🏭 {wh.name}**")
        c2.caption(f"{round(wh.lat,5)}, {round(wh.lon,5)}")
        # ── FIX 9: confirmation on delete ──
        if c3.button("🗑️", key=f"delwh_{wh.id}"):
            st.session_state[f"_armed_delwh_{wh.id}"] = True
            st.rerun()
        if st.session_state.get(f"_armed_delwh_{wh.id}"):
            st.warning(f"Delete **{wh.name}**? Routes using it will lose their warehouse.")
            y, n = st.columns(2)
            if y.button("Yes, delete", key=f"delwh_yes_{wh.id}", width='stretch'):
                for r in wh.routes: r.warehouse_id = None
                db.delete(wh); db.commit()
                st.session_state.pop(f"_armed_delwh_{wh.id}", None)
                st.rerun()
            if n.button("Cancel", key=f"delwh_no_{wh.id}", width='stretch'):
                st.session_state.pop(f"_armed_delwh_{wh.id}", None)
                st.rerun()

    if warehouses: st.divider()

    st.subheader("➕ Add Warehouse")
    w_name = st.text_input("Name", placeholder="e.g. North Depot", key="new_wh_name")
    w_loc  = st_searchbox(search_places, key="wh_search", placeholder="Search address…")
    if w_loc:
        st.session_state["wh_lat"] = w_loc[0]
        st.session_state["wh_lon"] = w_loc[1]

    plat = st.session_state.get("wh_lat")
    plon = st.session_state.get("wh_lon")

    sc_key = "_mapcenter_wh_add_map"
    if sc_key not in st.session_state:
        st.session_state[sc_key] = (
            [plat, plon] if plat else
            ([warehouses[0].lat, warehouses[0].lon] if warehouses else [11.25, 75.78])
        )

    wm = folium.Map(location=st.session_state[sc_key],
                    zoom_start=13 if plat else 5,
                    tiles="CartoDB dark_matter")
    for wh in warehouses:
        folium.Marker([wh.lat, wh.lon], tooltip=wh.name,
                      icon=folium.Icon(color="orange", icon="home")).add_to(wm)
    if plat:
        folium.Marker([plat, plon], tooltip="New pin",
                      icon=folium.Icon(color="blue", icon="map-marker")).add_to(wm)

    st.caption("Click map to pin, or use search above.")
    md = st_folium(wm, height=360, width='stretch', key="wh_add_map")
    if md and md.get("last_clicked"):
        lc = md["last_clicked"]
        st.session_state["wh_lat"] = lc["lat"]
        st.session_state["wh_lon"] = lc["lng"]
        # Don't rerun — show a "Use this location" button instead
    if plat:
        if st.button("📍 Use pinned location", key="wh_use_pin"):
            st.rerun()

    if plat: st.info(f"📍 {round(plat,5)}, {round(plon,5)}")

    if st.button("💾 Save Warehouse", type="primary", width='stretch'):
        if not w_name: st.error("Enter a name.")
        elif not plat:  st.error("Pin a location first.")
        else:
            db.add(Warehouse(name=w_name, lat=plat, lon=plon)); db.commit()
            st.session_state.pop("wh_lat", None); st.session_state.pop("wh_lon", None)
            st.session_state.pop(sc_key, None)
            st.success("Saved."); st.rerun()


# ──────────────────────────────────────────────────────────
# ROUTES TAB
# ──────────────────────────────────────────────────────────
def tab_routes():
    all_routes      = db.query(Route).all()
    active_routes   = [r for r in all_routes if r.status not in ("completed","cancelled")]
    archived_routes = [r for r in all_routes if r.status in ("completed","cancelled")]
    all_drivers     = db.query(User).filter(User.role=="driver").all()
    all_vehicles    = db.query(Vehicle).all()
    wh_opts         = wh_options()

    # Overview map + progress summary
    if active_routes:
        route_map(active_routes, height=360, key="overview")

        # ── FIX 6: Route progress summary ──
        st.subheader("📊 Route Progress")
        cols = st.columns(min(len(active_routes), 4))
        for i, route in enumerate(active_routes):
            delivered, total = route_progress(route)
            pct = int((delivered / total * 100) if total else 0)
            with cols[i % 4]:
                st.markdown(
                    f"**{route.name}**  "
                    f"<span class='tag'>{ROUTE_STATUSES.get(route.status,'')}</span><br>"
                    f"<small>{delivered}/{total} delivered ({pct}%)</small>"
                    f"<div class='progress-bar-bg'>"
                    f"<div class='progress-bar-fill' style='width:{pct}%'></div></div>",
                    unsafe_allow_html=True
                )
        st.divider()

    col_new, col_split = st.columns(2)

    with col_new:
        st.subheader("➕ New Route")
        rname  = st.text_input("Name", placeholder="Zone A", key="nr_name")
        wh_sel = st.selectbox("Warehouse", list(wh_opts.keys()), key="nr_wh")
        d_opts = {"— None —": None, **{d.username: d.id for d in all_drivers}}
        v_opts = {"— None —": None, **{v.name: v.id for v in all_vehicles}}
        rd = st.selectbox("Driver",  list(d_opts.keys()), key="nr_d")
        rv = st.selectbox("Vehicle", list(v_opts.keys()), key="nr_v")
        if st.button("Create Route", width='stretch', type="primary"):
            if rname:
                db.add(Route(name=rname, warehouse_id=wh_opts.get(wh_sel),
                             driver_id=d_opts.get(rd), vehicle_id=v_opts.get(rv)))
                db.commit(); st.rerun()
            else: st.warning("Enter a name.")

    with col_split:
        st.subheader("⚡ Auto-Split Unassigned")
        unassigned = db.query(Stop).filter(Stop.route_id==None).all()
        st.caption(f"{len(unassigned)} unassigned stops in pool")
        n_routes = st.number_input("Routes to create", 1, 20, 2, key="split_n")
        prefix   = st.text_input("Name prefix", "Route", key="split_pfx")
        wh_split = st.selectbox("Warehouse", list(wh_opts.keys()), key="split_wh")
        if st.button("⚡ Split & Optimize", width='stretch', type="primary"):
            if len(unassigned) < 2:
                st.warning("Need at least 2 stops in the pool.")
            else:
                wh_id  = wh_opts.get(wh_split)
                wh_obj = db.query(Warehouse).filter(Warehouse.id==wh_id).first() if wh_id else None
                payload = {"stops": [{"lat":s.lat,"lon":s.lon} for s in unassigned],
                           "num_routes": int(n_routes)}
                if wh_obj: payload["warehouse"] = {"lat":wh_obj.lat,"lon":wh_obj.lon}
                try:
                    res = requests.post(f"{BACKEND_URL}/api/split", json=payload, timeout=60)
                    if res.status_code == 200:
                        for ri, grp in enumerate(res.json()["routes"]):
                            r = Route(name=f"{prefix} {ri+1}", warehouse_id=wh_id)
                            db.add(r); db.flush()
                            for cp in grp["optimized_order"]:
                                unassigned[grp["stop_indices"][cp]].route_id = r.id
                            r.order = ",".join(str(i) for i in range(len(grp["stop_indices"])))
                        db.commit(); st.success("Done!"); st.rerun()
                    else: st.error(f"Backend error {res.status_code}")
                except Exception as e: st.error(f"Engine offline: {e}")

    st.divider()

    if not active_routes and not archived_routes:
        st.info("No routes yet.")
        return

    if not active_routes:
        st.info("No active routes — all routes are completed or cancelled.")

    for route in active_routes:
        color = rcolor(route.id)
        delivered, total = route_progress(route)
        pct = int((delivered / total * 100) if total else 0)
        with st.expander(
            f"{ROUTE_STATUSES.get(route.status,'')}  **{route.name}**"
            f"  ·  {delivered}/{total} delivered"
            + (f"  ·  🏭 {route.warehouse.name}" if route.warehouse else "")
            + (f"  ·  👤 {route.driver.username}" if route.driver else "")
        ):
            ec1,ec2,ec3,ec4 = st.columns(4)
            new_name = ec1.text_input("Name", value=route.name, key=f"rname_{route.id}")
            wh_list  = list(wh_opts.keys())
            cur_wh   = route.warehouse.name if route.warehouse else "— None —"
            new_wh   = ec2.selectbox("Warehouse", wh_list,
                                     index=wh_list.index(cur_wh) if cur_wh in wh_list else 0,
                                     key=f"rwh_{route.id}")
            d_list = ["— None —"] + [d.username for d in all_drivers]
            cur_d  = route.driver.username if route.driver else "— None —"
            new_d  = ec3.selectbox("Driver", d_list,
                                   index=d_list.index(cur_d) if cur_d in d_list else 0,
                                   key=f"rdrv_{route.id}")
            v_list = ["— None —"] + [v.name for v in all_vehicles]
            cur_v  = route.vehicle.name if route.vehicle else "— None —"
            new_v  = ec4.selectbox("Vehicle", v_list,
                                   index=v_list.index(cur_v) if cur_v in v_list else 0,
                                   key=f"rveh_{route.id}")

            s_list   = list(ROUTE_STATUSES.keys())
            new_stat = st.selectbox("Status", s_list,
                                    index=s_list.index(route.status) if route.status in s_list else 0,
                                    format_func=lambda s: ROUTE_STATUSES[s],
                                    key=f"rstat_{route.id}")

            bc1, bc2, bc3 = st.columns(3)
            if bc1.button("💾 Save", key=f"rsave_{route.id}", width='stretch'):
                d_map = {d.username: d.id for d in all_drivers}
                v_map = {v.name: v.id for v in all_vehicles}
                route.name=new_name; route.status=new_stat
                route.warehouse_id=wh_opts.get(new_wh)
                route.driver_id=d_map.get(new_d)
                route.vehicle_id=v_map.get(new_v)
                db.commit(); st.rerun()

            stored_count   = len(route.order.split(",")) if route.order else 0
            needs_optimize = not route.order or stored_count != len(route.stops)
            if needs_optimize:
                if bc2.button("🚀 Optimize", key=f"ropt_{route.id}", width='stretch'):
                    stops = list(route.stops)
                    if len(stops) > 1:
                        payload = {"stops": [{"lat":s.lat,"lon":s.lon} for s in stops]}
                        if route.warehouse:
                            payload["warehouse"] = {"lat":route.warehouse.lat,
                                                    "lon":route.warehouse.lon}
                        try:
                            res = requests.post(f"{BACKEND_URL}/api/optimize",
                                                json=payload, timeout=20)
                            if res.status_code == 200:
                                route.order = ",".join(
                                    str(i) for i in res.json()["optimized_indices"])
                                db.commit(); st.success("Optimized!"); st.rerun()
                        except: st.error("Engine offline.")
            else:
                # ── FIX 4: was bc2.success() which doesn't exist ──
                bc2.markdown("✅ Optimized")

            # ── FIX 9: confirmation on route delete ──
            if confirm_button("🗑️ Delete Route", key=f"rdel_{route.id}"):
                db.delete(route); db.commit(); st.rerun()

            st.divider()
            o_stops = get_ordered_stops(route)
            for i, s in enumerate(o_stops):
                sc = STOP_COLORS.get(s.status, color)
                rc1, rc2 = st.columns([6, 1])
                rc1.markdown(
                    f"<div class='stop-row' style='border-left-color:{sc}'>"
                    f"<b>{i+1}. {s.name}</b>"
                    f"<span class='tag'>{STOP_STATUSES.get(s.status,'')}</span>"
                    + (f"<span class='tag'>👤 {s.recipient_name}</span>" if s.recipient_name else "")
                    + "</div>", unsafe_allow_html=True)
                if rc2.button("❌", key=f"sdel_{route.id}_{s.id}"):
                    db.delete(s); db.commit(); st.rerun()
                stop_detail(s, ctx=f"admin_{route.id}")

            new_s = st_searchbox(search_places, key=f"radd_{route.id}",
                                 placeholder="Add stop…")
            if new_s:
                db.add(Stop(route_id=route.id, lat=new_s[0], lon=new_s[1],
                            name=f"Stop {len(route.stops)+1}"))
                db.commit(); st.rerun()

            if route.stops:
                route_map([route], height=300, key=f"rmap_{route.id}")

    # ── Archive ──
    if archived_routes:
        st.divider()
        with st.expander(f"🗄️ Archive — {len(archived_routes)} completed / cancelled route(s)"):
            for route in archived_routes:
                color = rcolor(route.id)
                delivered, total = route_progress(route)
                pct = int(delivered / total * 100) if total else 0
                st.markdown(
                    f"<div style='background:var(--glass-bg);border:1px solid var(--glass-border);"
                    f"border-radius:12px;padding:14px 16px;margin-bottom:8px;"
                    f"border-left:4px solid {color};opacity:0.7'>"
                    f"<b>{ROUTE_STATUSES.get(route.status,'')}  {route.name}</b>"
                    f"  <span class='tag'>{delivered}/{total} delivered ({pct}%)</span>"
                    + (f"  <span class='tag'>👤 {route.driver.username}</span>" if route.driver else "")
                    + (f"  <span class='tag'>🏭 {route.warehouse.name}</span>" if route.warehouse else "")
                    + "</div>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 6])
                if c1.button("🗑️ Delete", key=f"arc_del_{route.id}", width='stretch'):
                    db.delete(route); db.commit(); st.rerun()
                if c2.button("↩️ Restore to active", key=f"arc_restore_{route.id}", width='stretch'):
                    route.status = "active"; db.commit(); st.rerun()


# ──────────────────────────────────────────────────────────
# STOP POOL TAB
# ──────────────────────────────────────────────────────────
def tab_pool():
    st.subheader("📥 Stop Pool")
    st.caption("Add stops here with full details, then assign to routes or use Auto-Split.")
    unassigned = db.query(Stop).filter(Stop.route_id==None).all()

    with st.expander("➕ Add New Stop", expanded=len(unassigned)==0):
        new_loc = st_searchbox(search_places, key="pool_srch", placeholder="Search address…")
        if new_loc:
            st.session_state["pool_pending_lat"] = new_loc[0]
            st.session_state["pool_pending_lon"] = new_loc[1]

        plat = st.session_state.get("pool_pending_lat")
        plon = st.session_state.get("pool_pending_lon")

        sc_key = "_mapcenter_pool_map"
        if sc_key not in st.session_state:
            st.session_state[sc_key] = (
                [plat, plon] if plat else
                ([unassigned[0].lat, unassigned[0].lon] if unassigned else [11.25, 75.78])
            )

        pm = folium.Map(location=st.session_state[sc_key],
                        zoom_start=12,
                        tiles="CartoDB dark_matter")
        for s in unassigned:
            folium.CircleMarker([s.lat,s.lon], radius=6, color="#6C8AFF",
                                fill=True, tooltip=s.name).add_to(pm)
        if plat:
            folium.Marker([plat, plon], tooltip="New stop",
                          icon=folium.Icon(color="blue", icon="map-marker")).add_to(pm)

        st.caption("🖱️ Click map to pin, or search above.")
        pmd = st_folium(pm, height=280, width='stretch', key="pool_map")
        if pmd and pmd.get("last_clicked"):
            c = pmd["last_clicked"]
            st.session_state["pool_pending_lat"] = c["lat"]
            st.session_state["pool_pending_lon"] = c["lng"]
            # Don't rerun — button below will confirm

        if plat: st.info(f"📍 Pinned: {round(plat,5)}, {round(plon,5)}")

        fc1, fc2 = st.columns(2)
        sname  = fc1.text_input("Stop Label",      key="pool_sname",
                                placeholder=f"Stop {len(unassigned)+1}")
        rname  = fc2.text_input("Recipient Name",  key="pool_rname",
                                placeholder="e.g. John Smith")
        fc3, fc4 = st.columns(2)
        rphone = fc3.text_input("Recipient Phone", key="pool_rphone",
                                placeholder="+91 98765 43210")
        rnote  = fc4.text_input("Delivery Note",   key="pool_rnote",
                                placeholder="Leave at gate")

        if st.button("➕ Add to Pool", type="primary", width='stretch'):
            if not plat:
                st.error("Pin a location first — search or click the map.")
            else:
                label = sname.strip() or f"Stop {len(unassigned)+1}"
                db.add(Stop(lat=plat, lon=plon, name=label,
                            recipient_name=rname, recipient_phone=rphone,
                            recipient_note=rnote))
                db.commit()
                for k in ["pool_pending_lat","pool_pending_lon",
                          "pool_sname","pool_rname","pool_rphone","pool_rnote"]:
                    st.session_state.pop(k, None)
                st.rerun()

    if not unassigned:
        st.info("Pool is empty. Add stops above.")
        return

    st.divider()
    st.write(f"**{len(unassigned)} stop(s) in pool**")
    all_routes = db.query(Route).filter(
        Route.status.notin_(["completed", "cancelled"])).all()
    r_opts = {"— Keep unassigned —": None, **{r.name: r.id for r in all_routes}}

    for s in unassigned:
        with st.expander(
            f"📍 **{s.name}**"
            + (f"  ·  👤 {s.recipient_name}" if s.recipient_name else "  ·  No recipient")
            + (f"  ·  📞 {s.recipient_phone}" if s.recipient_phone else "")
        ):
            ec1, ec2 = st.columns(2)
            new_name   = ec1.text_input("Stop Label",      value=s.name,             key=f"pn_{s.id}")
            new_rname  = ec2.text_input("Recipient Name",  value=s.recipient_name  or "", key=f"prn_{s.id}")
            ec3, ec4   = st.columns(2)
            new_rphone = ec3.text_input("Recipient Phone", value=s.recipient_phone or "", key=f"prp_{s.id}")
            new_rnote  = ec4.text_input("Delivery Note",   value=s.recipient_note  or "", key=f"prnote_{s.id}")

            sc1, sc2, sc3 = st.columns(3)
            if sc1.button("💾 Save", key=f"psave_{s.id}", width='stretch'):
                s.name=new_name; s.recipient_name=new_rname
                s.recipient_phone=new_rphone; s.recipient_note=new_rnote
                db.commit(); st.success("Saved.")

            new_r = sc2.selectbox("Assign to route", list(r_opts.keys()),
                                  index=0, key=f"passign_{s.id}")
            if sc2.button("Move →", key=f"pmove_{s.id}", width='stretch'):
                s.route_id = r_opts.get(new_r); db.commit(); st.rerun()

            if confirm_button("🗑️ Delete", key=f"pdel_{s.id}"):
                db.delete(s); db.commit(); st.rerun()



# ──────────────────────────────────────────────────────────
# DRIVER STATS
# ──────────────────────────────────────────────────────────
def driver_stats(driver):
    """Compute delivery stats for a driver from existing route/stop/notification data."""
    routes = db.query(Route).filter(Route.driver_id == driver.id).all()

    all_stops      = [s for r in routes for s in r.stops]
    delivered      = [s for s in all_stops if s.status == "delivered"]
    delayed        = [s for s in all_stops if s.status == "delayed"]
    rescheduled    = [s for s in all_stops if s.status == "rescheduled"]
    cancelled      = [s for s in all_stops if s.status == "cancelled"]
    pending        = [s for s in all_stops if s.status == "pending"]
    out            = [s for s in all_stops if s.status == "out_for_delivery"]

    completed_routes = [r for r in routes if r.status == "completed"]
    active_routes    = [r for r in routes if r.status in ("active", "in_progress")]

    issues   = db.query(Notification).filter(
        Notification.message.like(f"%'{driver.username}'%"),
        Notification.tag == "route_event",
        Notification.message.like("%issue%")
    ).count()

    messages = db.query(Notification).filter(
        Notification.message.like(f"💬 '{driver.username}'%"),
    ).count()

    total = len(all_stops)
    rate  = round(len(delivered) / total * 100) if total else 0

    return {
        "total_stops":        total,
        "delivered":          len(delivered),
        "pending":            len(pending),
        "out_for_delivery":   len(out),
        "delayed":            len(delayed),
        "rescheduled":        len(rescheduled),
        "cancelled":          len(cancelled),
        "delivery_rate":      rate,
        "total_routes":       len(routes),
        "completed_routes":   len(completed_routes),
        "active_routes":      len(active_routes),
        "issues_reported":    issues,
        "messages_sent":      messages,
    }


def tab_driver_stats():
    drivers = db.query(User).filter(User.role == "driver").all()
    if not drivers:
        st.info("No drivers yet. Create them in the Drivers tab.")
        return

    # Summary table across all drivers
    st.subheader("📊 All Drivers Overview")
    rows = []
    for d in drivers:
        s = driver_stats(d)
        rows.append({
            "Driver":       d.username,
            "Routes":       s["total_routes"],
            "Done":         s["completed_routes"],
            "Active":       s["active_routes"],
            "Stops":        s["total_stops"],
            "✅ Delivered":  s["delivered"],
            "❌ Cancelled":  s["cancelled"],
            "⚠️ Delayed":   s["delayed"],
            "📅 Rescheduled": s["rescheduled"],
            "🎯 Rate":       f"{s['delivery_rate']}%",
            "Issues":       s["issues_reported"],
            "Messages":     s["messages_sent"],
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, width='stretch', hide_index=True)

    st.divider()

    # Per-driver detail cards
    st.subheader("👤 Per-Driver Breakdown")
    cols = st.columns(min(len(drivers), 3))
    for i, driver in enumerate(drivers):
        s = driver_stats(driver)
        with cols[i % 3]:
            rate  = s["delivery_rate"]
            color = "#34d399" if rate >= 80 else "#fbbf24" if rate >= 50 else "#f87171"
            st.markdown(
                f"<div class='stat-card' style='border-left:4px solid {color}'>"
                f"<h4 style='margin:0 0 8px 0'>👤 {driver.username}</h4>"
                f"<div style='font-size:2em;font-weight:bold;color:{color}'>{rate}%</div>"
                f"<div style='font-size:0.8em;color:#94a3b8;margin-bottom:10px'>delivery rate</div>"
                f"<table style='width:100%;font-size:0.85em;border-collapse:collapse'>"
                f"<tr><td>✅ Delivered</td><td align='right'><b>{s['delivered']}</b></td></tr>"
                f"<tr><td>🕐 Pending</td><td align='right'>{s['pending']}</td></tr>"
                f"<tr><td>🚚 Out for delivery</td><td align='right'>{s['out_for_delivery']}</td></tr>"
                f"<tr><td>⚠️ Delayed</td><td align='right'>{s['delayed']}</td></tr>"
                f"<tr><td>📅 Rescheduled</td><td align='right'>{s['rescheduled']}</td></tr>"
                f"<tr><td>❌ Cancelled</td><td align='right'>{s['cancelled']}</td></tr>"
                f"<tr><td colspan='2'><hr style='border-color:rgba(255,255,255,0.1);margin:6px 0'></td></tr>"
                f"<tr><td>🗺️ Total routes</td><td align='right'>{s['total_routes']}</td></tr>"
                f"<tr><td>✅ Completed routes</td><td align='right'>{s['completed_routes']}</td></tr>"
                f"<tr><td>🟢 Active routes</td><td align='right'>{s['active_routes']}</td></tr>"
                f"<tr><td>⚠️ Issues reported</td><td align='right'>{s['issues_reported']}</td></tr>"
                f"<tr><td>💬 Messages sent</td><td align='right'>{s['messages_sent']}</td></tr>"
                f"</table></div>",
                unsafe_allow_html=True
            )

            # Recent route history for this driver
            routes = db.query(Route).filter(Route.driver_id == driver.id).all()
            if routes:
                with st.expander(f"Route history ({len(routes)})"):
                    for r in routes:
                        d_count, t_count = route_progress(r)
                        pct = int(d_count / t_count * 100) if t_count else 0
                        status_label = ROUTE_STATUSES.get(r.status, r.status)
                        st.markdown(
                            f"**{r.name}** — {status_label}  "
                            f"·  {d_count}/{t_count} delivered ({pct}%)"
                        )

# ──────────────────────────────────────────────────────────
# ADMIN VIEW
# ──────────────────────────────────────────────────────────
def show_admin():
    with st.sidebar:
        st.title("🛰️ Routr")
        st.caption(f"**{st.session_state.username}** · Admin")
        unread = db.query(Notification).filter(Notification.is_read==False).count()
        if unread: st.warning(f"🔔 {unread} unread")
        if st.button("Logout", width='stretch'):
            for k in ["user_id","user_role","username"]: st.session_state[k]=None
            st.rerun()

    st.title("Routr")
    t_routes, t_pool, t_wh, t_vehicles, t_drivers, t_stats, t_notifs = st.tabs([
        "🗺️ Routes", "📥 Stop Pool", "🏭 Warehouses",
        "🚛 Vehicles", "👤 Drivers", "📊 Driver Stats", "🔔 Notifications"
    ])

    with t_routes:   tab_routes()
    with t_pool:     tab_pool()
    with t_wh:       tab_warehouses()

    with t_vehicles:
        st.subheader("Vehicles")
        c1, c2 = st.columns([3,1])
        n_in = c1.text_input("Name", key="v_name_in")
        c_in = c2.color_picker("Color", "#6C8AFF")
        if st.button("Add Vehicle"):
            if n_in: db.add(Vehicle(name=n_in, color=c_in)); db.commit(); st.rerun()
        st.divider()
        for v in db.query(Vehicle).all():
            vc, va = st.columns([4,1])
            vc.write(f"🚛 **{v.name}**")
            # ── FIX 3: unlink routes before delete ──
            if va.button("🗑️", key=f"vdel_{v.id}"):
                for r in db.query(Route).filter(Route.vehicle_id==v.id).all():
                    r.vehicle_id = None
                db.delete(v); db.commit(); st.rerun()

    with t_drivers:
        st.subheader("Driver Accounts")
        d1, d2 = st.columns(2)
        du = d1.text_input("Username", key="new_du")
        dp = d2.text_input("Password", type="password", key="new_dp")
        if st.button("Create Driver"):
            if du and dp:
                if db.query(User).filter(User.username==du).first():
                    st.error("Username taken.")
                else:
                    db.add(User(username=du, password=hash_password(dp), role="driver"))
                    db.commit(); st.rerun()
        st.divider()
        for drv in db.query(User).filter(User.role=="driver").all():
            dc, db_col, da = st.columns([3, 2, 1])
            dc.write(f"👤 **{drv.username}**")
            # ── FIX 5: change password ──
            if db_col.button("🔑 Reset pwd", key=f"rpwd_{drv.id}", width='stretch'):
                st.session_state[f"reset_pwd_{drv.id}"] = True
            if st.session_state.get(f"reset_pwd_{drv.id}"):
                new_pwd = st.text_input(f"New password for {drv.username}",
                                        type="password", key=f"newpwd_{drv.id}")
                if st.button("Set password", key=f"setpwd_{drv.id}"):
                    if new_pwd:
                        drv.password = hash_password(new_pwd)
                        db.commit()
                        st.session_state.pop(f"reset_pwd_{drv.id}", None)
                        st.success("Password updated.")
            if confirm_button("🗑️", key=f"ddel_{drv.id}"):
                db.delete(drv); db.commit(); st.rerun()

    with t_stats:    tab_driver_stats()

    with t_notifs:
        st.subheader("Notifications")
        all_n = db.query(Notification).order_by(
            Notification.created_at.desc()).limit(200).all()
        tabs2 = st.tabs(["All", "🚚 Route", "📦 Delivery"])
        for tab, filt in zip(tabs2, [None, "route_event", "delivery"]):
            with tab:
                lst = [n for n in all_n if filt is None or n.tag==filt]
                if not lst: st.info("Nothing yet."); continue
                mc1, mc2 = st.columns(2)
                if mc1.button("✅ Mark all read", key=f"mark_{filt}"):
                    for n in lst: n.is_read = True
                    db.commit(); st.rerun()
                # ── FIX 8: allow clearing old notifications ──
                if mc2.button("🗑️ Clear read", key=f"clear_{filt}"):
                    for n in lst:
                        if n.is_read: db.delete(n)
                    db.commit(); st.rerun()
                for n in lst:
                    ts    = n.created_at.strftime("%d %b, %H:%M") if n.created_at else ""
                    badge = "" if n.is_read else "🆕 "
                    st.markdown(
                        f"<div class='notif-row'>{badge}<b>{ts}</b> — {n.message}</div>",
                        unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# DRIVER VIEW
# ──────────────────────────────────────────────────────────
def show_driver():
    user = db.query(User).filter(User.id==st.session_state.user_id).first()

    # ── FIX 2: only show truly available routes (active + unassigned) ──
    my_routes = db.query(Route).filter(Route.driver_id==user.id).all()
    available = db.query(Route).filter(
        Route.status=="active",
        Route.driver_id==None
    ).all()

    with st.sidebar:
        st.title("🚛 Routr")
        st.caption(f"**{st.session_state.username}**")
        if my_routes:
            st.session_state.setdefault("drv_route", my_routes[0].name)
            st.selectbox("My routes", [r.name for r in my_routes], key="drv_route")
        else:
            st.warning("No routes assigned.")
        if available:
            st.divider(); st.write("**Available routes**")
            for r in available:
                lbl = f"{r.name}" + (f" · 🏭 {r.warehouse.name}" if r.warehouse else "")
                if st.button(f"Take: {lbl}", key=f"take_{r.id}"):
                    r.driver_id = user.id; db.commit()
                    notify(f"🔄 '{user.username}' took '{r.name}'.", tag="route_event")
                    st.rerun()
        if st.button("Logout", width='stretch'):
            for k in ["user_id","user_role","username"]: st.session_state[k]=None
            st.rerun()

    if not my_routes:
        st.title("My Route")
        st.info("No routes assigned yet. Check available routes in the sidebar.")
        return

    route = next((r for r in my_routes
                  if r.name==st.session_state.get("drv_route")), my_routes[0])
    wh = route.warehouse

    st.title(route.name)
    delivered, total = route_progress(route)
    pct = int((delivered / total * 100) if total else 0)
    st.caption(
        ROUTE_STATUSES.get(route.status,"")
        + (f"  ·  🏭 {wh.name}" if wh else "")
        + f"  ·  {delivered}/{total} delivered"
    )
    # Progress bar
    st.markdown(
        f"<div class='progress-bar-bg'>"
        f"<div class='progress-bar-fill' style='width:{pct}%'></div></div>",
        unsafe_allow_html=True)

    st.divider()
    a1, a2, a3, a4 = st.columns(4)
    if a1.button("▶️ Start",    width='stretch'):
        route.status="in_progress"; db.commit()
        notify(f"▶️ '{user.username}' started '{route.name}'.", tag="route_event")
        st.rerun()
    if a2.button("✅ Complete", width='stretch'):
        route.status="completed"; db.commit()
        notify(f"✅ '{user.username}' completed '{route.name}'.", tag="route_event")
        st.rerun()
    if a3.button("⚠️ Issue",   width='stretch'):
        st.session_state[f"show_issue_{route.id}"] = True
    if a4.button("💬 Message", width='stretch'):
        st.session_state[f"show_msg_{route.id}"]   = True

    if st.session_state.get(f"show_issue_{route.id}"):
        txt = st.text_area("Describe the issue:", key=f"itxt_{route.id}")
        if st.button("Send", key=f"isend_{route.id}"):
            if txt:
                notify(f"⚠️ '{user.username}' issue on '{route.name}': {txt}",
                       tag="route_event")
                st.session_state[f"show_issue_{route.id}"] = False
                st.success("Sent."); st.rerun()

    if st.session_state.get(f"show_msg_{route.id}"):
        txt = st.text_area("Message to admin:", key=f"mtxt_{route.id}")
        if st.button("Send", key=f"msend_{route.id}"):
            if txt:
                notify(f"💬 '{user.username}': {txt}", tag="route_event")
                st.session_state[f"show_msg_{route.id}"] = False
                st.success("Sent."); st.rerun()

    st.divider()
    route_map([route], height=420, key=f"dmap_{route.id}")

    # ── FIX 1: correct Google Maps waypoints ──
    stops = get_ordered_stops(route)
    if stops:
        origin = f"{wh.lat},{wh.lon}" if wh else f"{stops[0].lat},{stops[0].lon}"
        dest   = f"{stops[-1].lat},{stops[-1].lon}"
        # waypoints = middle stops only (not origin or destination)
        mid    = stops[1:-1] if not wh else stops[:-1]
        wpts   = "|".join(f"{s.lat},{s.lon}" for s in mid)
        gurl   = (f"https://www.google.com/maps/dir/?api=1&origin={origin}"
                  f"&destination={dest}"
                  + (f"&waypoints={wpts}" if wpts else "")
                  + "&travelmode=driving")
        st.markdown(
            f'<a href="{gurl}" target="_blank">'
            f'<button style="width:100%;background:#4285F4;color:white;border:none;'
            f'padding:11px;border-radius:8px;cursor:pointer;font-weight:bold;'
            f'margin-bottom:12px;">🛰️ Open in Google Maps</button></a>',
            unsafe_allow_html=True)

    st.subheader("Stops")
    color = rcolor(route.id)
    pending_stops   = [s for s in stops if s.status not in ("delivered", "cancelled")]
    completed_stops = [s for s in stops if s.status in ("delivered", "cancelled")]

    if not pending_stops and completed_stops:
        st.success("All stops completed! 🎉")

    for i, s in enumerate(pending_stops):
        sc = STOP_COLORS.get(s.status, color)
        st.markdown(
            f"<div class='stop-row' style='border-left-color:{sc}'>"
            f"<b>{i+1}. {s.name}</b>"
            f"<span class='tag'>{STOP_STATUSES.get(s.status,'')}</span>"
            + (f"<span class='tag'>👤 {s.recipient_name}</span>" if s.recipient_name else "")
            + "</div>", unsafe_allow_html=True)
        stop_detail(s, ctx=f"driver_{route.id}")

    if completed_stops:
        with st.expander(f"✅ Completed stops ({len(completed_stops)})"):
            for s in completed_stops:
                sc = STOP_COLORS.get(s.status, color)
                st.markdown(
                    f"<div class='stop-row' style='border-left-color:{sc};opacity:0.5'>"
                    f"<b>{s.name}</b>"
                    f"<span class='tag'>{STOP_STATUSES.get(s.status,'')}</span>"
                    + (f"<span class='tag'>👤 {s.recipient_name}</span>" if s.recipient_name else "")
                    + "</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────
if not st.session_state.user_id:
    show_login()
elif st.session_state.user_role == "admin":
    show_admin()
else:
    show_driver()
