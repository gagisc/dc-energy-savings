"""dc-thermal-fusion Streamlit demo dashboard."""

from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="dc-thermal-fusion", page_icon="🌡️", layout="wide")
st.title("🌡️ dc-thermal-fusion — Live Hotspot Monitor")


@st.cache_data(ttl=10)
def load_fused() -> pd.DataFrame:
    p = Path("data/samples/fused_features.csv")
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


df = load_fused()
if df.empty:
    st.warning("No data yet. Run `python src/simulator/run_simulator.py` first.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Max Frame Temp (ADC)", f"{df['frame_max'].iloc[-1]:.0f}")
    col2.metric("Hotspot Fraction", f"{df['hotspot_fraction'].iloc[-1]*100:.1f}%")
    col3.metric("Avg Contact Temp (°C)", f"{df['ds18b20_mean'].iloc[-1]:.1f}")
    st.subheader("Hotspot Fraction Over Time")
    st.line_chart(df.set_index("timestamp")[["hotspot_fraction", "ds18b20_mean"]])
    st.subheader("Frame Statistics")
    st.dataframe(df.tail(20))
    frames = sorted(Path("data/samples/thermal_frames").glob("*.png"))
    if frames:
        st.subheader("Latest Thermal Frame")
        st.image(str(frames[-1]), caption=frames[-1].name, width=320)

st.sidebar.markdown("**Mode:** Simulation")
st.sidebar.markdown("[GitHub](https://github.com/gagisc/dc-thermal-fusion)")
