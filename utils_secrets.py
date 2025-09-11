# utils_secrets.py
import os
import streamlit as st

def get_secret(key: str, default: str | None = None):
    """
    Busca credenciais:
    1) st.secrets (Streamlit Cloud)
    2) variáveis de ambiente (dev local / containers)
    """
    # 1) Streamlit Secrets
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # 2) Ambiente
    return os.getenv(key, default)
