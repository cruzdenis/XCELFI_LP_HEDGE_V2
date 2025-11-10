"""
Minimal test app to debug Railway deployment
"""
import streamlit as st

st.set_page_config(
    page_title="Test App",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Test App - Railway Deployment")

st.success("✅ Streamlit is working!")

st.write("If you see this, the basic Streamlit setup is OK.")

# Test imports
try:
    from core.config import config
    st.success("✅ core.config imported")
except Exception as e:
    st.error(f"❌ core.config failed: {e}")

try:
    from core.settings_manager import SettingsManager
    st.success("✅ core.settings_manager imported")
except Exception as e:
    st.error(f"❌ core.settings_manager failed: {e}")

try:
    from ui.settings_tab import render_settings_tab
    st.success("✅ ui.settings_tab imported")
except Exception as e:
    st.error(f"❌ ui.settings_tab failed: {e}")

try:
    from integrations.hyperliquid import HyperliquidClient
    st.success("✅ integrations.hyperliquid imported")
except Exception as e:
    st.error(f"❌ integrations.hyperliquid failed: {e}")

st.write("---")
st.write("All tests completed!")
