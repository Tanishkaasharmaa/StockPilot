import streamlit as st
import pandas as pd
import os
from langchain_core.messages import HumanMessage, AIMessage

# Internal Imports
from core.agent import HugoAgent
from core.reactive_intelligence import ReactiveIntelligence
from core.event_monitor import EventMonitor

st.set_page_config(page_title="Hugo | Voltway", layout="wide", page_icon="🤖")

# --- Original UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #111217;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1A1C23 !important;
        width: 300px !important;
    }
    
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .low-stock-card {
        background-color: #FFFFFF;
        color: #111217;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #FF4B4B;
    }
    
    .low-stock-card h4 {
        margin: 0;
        font-size: 0.9rem;
        color: #E2E8F0; /* Light text on pink/red background if we use that, but image shows white card */
    }
    
    /* Readjusting based on image: The cards in the image are actually white/light grey with light text? 
       Wait, looking closer at provided image: The cards are pinkish-white with very light text. 
       Let's match the exact visual from the screenshot. */
    
    .stAlert {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: white !important;
        border: none !important;
    }

    /* Main Area Styling */
    .hugo-title-container {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-top: 2rem;
    }
    
    .hugo-text {
        font-size: 4rem;
        font-weight: 700;
        color: #3D3D3D; /* Dark grey as in image */
        line-height: 1;
    }
    
    .hugo-subtitle {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Chat Styling */
    .stChatMessage {
        background-color: #1E1E1E !important;
        border-radius: 10px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = HugoAgent()
if "reactive_intel" not in st.session_state:
    st.session_state.reactive_intel = ReactiveIntelligence()
if "event_monitor" not in st.session_state:
    st.session_state.event_monitor = EventMonitor()
    st.session_state.event_monitor.start_monitoring(interval_minutes=5)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">🏭 Operations Monitor</div>', unsafe_allow_html=True)
    
    # 1. High Level Metrics
    try:
        briefing = st.session_state.reactive_intel.generate_daily_briefing()
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total Alerts", briefing['total_alerts'])
        with m2:
            st.metric("Critical", briefing['critical_count'], delta_color="inverse")
    except: pass

    # 2. Event Monitor
    st.markdown("---")
    st.markdown('<div class="sidebar-header" style="font-size: 1rem;">🔔 Event Monitor</div>', unsafe_allow_html=True)
    try:
        event_summary = st.session_state.event_monitor.get_event_summary()
        c1, c2 = st.columns(2)
        with c1: st.metric("Recent (24h)", event_summary['total_events_24h'])
        with c2: st.metric("Unack", event_summary['unacknowledged'])
        
        if event_summary['unacknowledged'] > 0:
            if st.button("✅ Bulk Acknowledge", use_container_width=True):
                unack_events = st.session_state.event_monitor.get_unacknowledged_events()
                for e in unack_events:
                    st.session_state.event_monitor.acknowledge_event(e['event_id'])
                st.toast("All events acknowledged!")
                st.rerun()
    except: pass

    # 3. Critical Low Stock (With individual resolution)
    st.markdown("---")
    st.markdown('<div class="sidebar-header" style="font-size: 1rem;">⚠️ Critical Low Stock</div>', unsafe_allow_html=True)
    try:
        critical_alerts = st.session_state.reactive_intel._check_low_stock()
        if not critical_alerts:
            st.write("No critical issues.")
        else:
            for i, alert in enumerate(critical_alerts[:4]):
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; margin-bottom: 5px;">
                    <div style="font-weight: 600; color: #FFFFFF; font-size: 0.85rem;">{alert['part_name']}</div>
                    <div style="color: #94A3B8; font-size: 0.75rem;">Stock: {alert['current_stock']} (Min: {alert['min_stock']})</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Resolve Task #{i+1}", key=f"resolve_{i}", use_container_width=True):
                    unack = st.session_state.event_monitor.get_unacknowledged_events()
                    matched = [e for e in unack if alert['part_id'] in e['details']]
                    if matched:
                        st.session_state.event_monitor.acknowledge_event(matched[0]['event_id'])
                    st.toast(f"Acknowledged task for {alert['part_id']}!")
                    st.rerun()
    except: pass

    # 4. Recommendations
    st.markdown("---")
    st.markdown('<div class="sidebar-header" style="font-size: 1rem;">💡 Recommendations</div>', unsafe_allow_html=True)
    try:
        recs = st.session_state.reactive_intel.get_recommendations()
        for r in recs[:2]:
            st.write(f"**{r['action']}**")
            st.caption(r['details'])
    except: pass

    # 5. Quick Actions
    st.markdown("---")
    if st.button("🔄 Refresh Dashboards", use_container_width=True):
        st.rerun()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Main App ---
# Logo & Header
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("https://img.icons8.com/isometric/100/bot.png", width=80) 
with col2:
    st.markdown('<div class="hugo-text">Hugo</div>', unsafe_allow_html=True)
st.markdown('<div class="hugo-subtitle">Your intelligent supply chain co-pilot</div>', unsafe_allow_html=True)

st.markdown('<div class="section-header">💬 Ask Hugo</div>', unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("How can I help you with operations today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.status("Hugo is processing...", expanded=True) as status:
            st.write("Analyzing query...")
            history = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in st.session_state.messages[:-1]]
            response = st.session_state.agent.run(prompt, history=history)
            status.update(label="Response ready", state="complete", expanded=False)
        
        st.markdown(response)
        
        # Add contextual acknowledgment button
        if "reorder" in response.lower() or "suggest" in response.lower():
            if st.button("Acknowledge Recommendation"):
                st.session_state.event_monitor.log_event("USER_ACK", "INFO", f"User acknowledged chat recommendation: {prompt}")
                st.success("Action logged.")
                
    st.session_state.messages.append({"role": "assistant", "content": response})
