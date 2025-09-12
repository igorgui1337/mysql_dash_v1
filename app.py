# app.py  (v5 – Legibilidade + Calendário Inline + TZ-safe SQL) — versão com áreas isoladas
import os
import base64
from datetime import datetime, date, time, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sqlalchemy import text
import plotly.io as pio
import plotly.graph_objects as go

from db import get_engine

import os, streamlit as st
import os, streamlit as st

def get_secret(key: str, default: str | None = None):
    # 1º: Streamlit Secrets; 2º: variáveis de ambiente
    return st.secrets.get(key, os.getenv(key, default))
load_dotenv()

# ======= Paleta =======
COLOR_BG = "#F5F0DE"        # desert sand
COLOR_TEXT = "#270644"      # Milka Dark
COLOR_ACCENT = "#7FDD24"    # Lemon
COLOR_SECONDARY = "#4A1A5C" # Purple variant
COLOR_LIGHT = "#FEFCF5"     # Lighter background
COLOR_DARK = "#1A0428"      # Darker text

def enable_dark_chart_text():
    template = go.layout.Template(
        layout=go.Layout(
            font=dict(color=COLOR_DARK, size=13),
            title=dict(font=dict(color=COLOR_DARK, size=18)),
            legend=dict(font=dict(color=COLOR_DARK)),
            xaxis=dict(
                tickfont=dict(color=COLOR_DARK),
                gridcolor="rgba(39,6,68,.18)",
                linecolor="rgba(39,6,68,.28)",
            ),
            yaxis=dict(
                tickfont=dict(color=COLOR_DARK),
                gridcolor="rgba(39,6,68,.18)",
                linecolor="rgba(39,6,68,.28)",
            ),
            coloraxis=dict(
                colorbar=dict(
                    tickfont=dict(color=COLOR_DARK),
                    title=dict(font=dict(color=COLOR_DARK))
                )
            ),
        )
    )
    pio.templates["tropa_dark_text"] = template
    pio.templates.default = "tropa_dark_text"

enable_dark_chart_text()
st.set_page_config(
    page_title="Start Dashboard - Monitoramento MySQL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======= CSS (contraste + alinhamento calendário + botões claros) =======
st.markdown(f"""
    <style>
    :root {{
        --bg: {COLOR_LIGHT};
        --card: {COLOR_BG};
        --text: {COLOR_TEXT};
        --text-dark: {COLOR_DARK};
        --accent: {COLOR_ACCENT};
        --secondary: {COLOR_SECONDARY};
    }}
    html, body, .stApp {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    .css-1d391kg, .css-1lcbmhc {{ background-color: var(--card) !important; }}

    .main-header {{
        background: linear-gradient(135deg, var(--text) 0%, var(--secondary) 100%);
        padding: 20px; border-radius: 15px; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(39,6,68,.18);
    }}
    .title {{
        font-size: 34px; font-weight: 800; color: var(--card); letter-spacing: .3px;
        margin: 0; text-shadow: 0 1px 2px rgba(0,0,0,.25);
    }}
    .subtitle {{ color: var(--card); opacity: .95; font-size: 15px; margin-top: 6px; font-weight: 600; }}
    .section-header {{
        background: var(--card); padding: 14px 16px; border-radius: 12px; margin: 22px 0 12px 0;
        border-left: 5px solid var(--accent); box-shadow: 0 1px 8px rgba(39,6,68,.08);
    }}
    .section-title {{ color: var(--text-dark); font-size: 19px; font-weight: 900; margin: 0; letter-spacing: .2px; }}
    .metric-card {{
        background: var(--card); padding: 18px 16px; border-radius: 14px; margin-bottom: 14px;
        border-left: 5px solid var(--accent); box-shadow: 0 2px 12px rgba(39,6,68,.10);
    }}
    .metric-title {{
        color: var(--text-dark); font-size: 12.5px; font-weight: 800; text-transform: uppercase;
        letter-spacing: .6px; opacity: .9; margin-bottom: 6px;
    }}
    .metric-value {{ color: var(--text); font-size: 26px; font-weight: 900; line-height: 1.15; margin-bottom: 4px; }}
    .metric-delta {{ color: var(--accent); font-size: 12.5px; font-weight: 700; letter-spacing: .2px; }}
    .stDataFrame, .stTable {{ border-radius: 10px !important; overflow: hidden;
        box-shadow: 0 2px 12px rgba(39,6,68,.10); }}
    .stDataFrame thead th {{ color: var(--text-dark) !important; font-weight: 900 !important; font-size: 13px !important; }}
    .stDataFrame tbody td {{ color: var(--text) !important; font-weight: 600 !important; font-size: 12.5px !important; }}
    .stInfo, .stWarning, .stSuccess {{ background-color: var(--card) !important; color: var(--text) !important;
        border-left: 5px solid var(--accent) !important; }}
    .logo-container {{ text-align: center; margin-bottom: 18px; padding: 8px; }}
    .inline-row {{ margin-top: -6px; }}
    .inline-card {{
        background: var(--card); border-left: 5px solid var(--accent); border-radius: 12px;
        padding: 10px 12px; box-shadow: 0 1px 8px rgba(39,6,68,.08);
    }}
    .inline-card .stDateInput label {{ display: none !important; }}
    .stForm button[kind="primary"] {{
        background-color: var(--accent) !important; color: var(--text-dark) !important; border: none !important;
        border-radius: 10px !important; font-weight: 800 !important;
        box-shadow: 0 2px 10px rgba(127,221,36,.28); transition: transform .15s ease, box-shadow .15s ease;
    }}
    .stForm button[kind="primary"]:hover {{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(127,221,36,.35); }}
    .stForm button[kind="secondary"] {{
        background: transparent !important; color: var(--text-dark) !important; border: 2px solid var(--text-dark) !important;
        border-radius: 10px !important; font-weight: 800 !important;
    }}
    .stForm button[kind="secondary"]:hover {{ filter: brightness(0.95); }}
    </style>
""", unsafe_allow_html=True)
st.markdown(f"""
    <style>
    .stTabs [role="tab"] {{
        color: {COLOR_TEXT} !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.25);
    }}
    .stTabs [role="tab"][aria-selected="true"] {{
        color: {COLOR_DARK} !important;
        font-weight: 800 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.35);
        border-bottom: 3px solid {COLOR_ACCENT} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ======= Logo + Título =======
def get_logo_base64():
    svg = f'''
    <svg width="200" height="60" viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="60" fill="{COLOR_BG}" rx="8"/>
        <text x="20" y="35" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="{COLOR_TEXT}">
            START
        </text>
        <rect x="140" y="15" width="30" height="30" fill="{COLOR_ACCENT}" rx="4"/>
        <polygon points="150,25 160,30 150,35" fill="{COLOR_TEXT}"/>
    </svg>
    '''
    return base64.b64encode(svg.encode()).decode()

col_logo, col_title = st.columns([1, 3])
with col_logo:
    st.markdown(f'<div class="logo-container"><img src="data:image/svg+xml;base64,{get_logo_base64()}" /></div>', unsafe_allow_html=True)
with col_title:
    st.markdown('''
        <div class="main-header">
            <div class="title">📊 Dashboard de Monitoramento</div>
            <div class="subtitle">MySQL • Payments • Timezone Configurável • Real-time Analytics</div>
        </div>
    ''', unsafe_allow_html=True)

engine = get_engine()
db_name = os.getenv("DB_NAME")
st.caption(f"🔗 Conectado ao Database: **{db_name}**")

# ======= Tempo e TZ =======
TZ_BRT = timezone(timedelta(hours=-3))

def brt_bounds_for_days(days: int):
    now_brt = datetime.now(TZ_BRT)
    end_brt = now_brt.replace(hour=23, minute=59, second=59, microsecond=0)
    start_brt = (end_brt - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_brt_inclusive = end_brt + timedelta(seconds=1)  # meia-noite exclusiva
    return start_brt, end_brt_inclusive

def utc_bounds_from_brt_bounds(start_brt: datetime, end_brt_inclusive: datetime):
    return start_brt.astimezone(timezone.utc), end_brt_inclusive.astimezone(timezone.utc)

def fmt(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ======= Estado do calendário inline =======
if "inline_start" not in st.session_state:
    st.session_state["inline_start"] = date.today()
if "inline_end" not in st.session_state:
    st.session_state["inline_end"] = date.today()
if "inline_use" not in st.session_state:
    st.session_state["inline_use"] = False

# ======= Sidebar =======
with st.sidebar:
    st.markdown(f'''
        <div style="background: {COLOR_BG}; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: {COLOR_TEXT}; margin: 0;">⚙️ Configurações</h3>
        </div>
    ''', unsafe_allow_html=True)

    # 🔀 seletor de área
    area = st.selectbox("🔀 Área de análise", ["NetDepósito", "Cassino"])

    # 🔒 TZ fixo BRT
    mode = "BRT"

    st.markdown("---")

    quick = st.radio(
        "📅 Período:",
        ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"],
        help="Selecione o período para análise"
    )

    # Período base do rádio
    if quick == "Hoje":
        start_brt, end_brt_inclusive = brt_bounds_for_days(1)
    elif quick == "Últimos 7 dias":
        start_brt, end_brt_inclusive = brt_bounds_for_days(7)
    elif quick == "Últimos 30 dias":
        start_brt, end_brt_inclusive = brt_bounds_for_days(30)
    else:
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.date_input("📅 Início", value=date.today())
        with c2:
            d2 = st.date_input("📅 Fim", value=date.today())
        if d2 < d1:
            d1, d2 = d2, d1
        start_brt = datetime.combine(d1, time(0, 0)).replace(tzinfo=TZ_BRT)
        end_brt_inclusive = datetime.combine(d2, time(23, 59, 59)).replace(tzinfo=TZ_BRT) + timedelta(seconds=1)

    # Override pelo calendário inline, se ativo
    if st.session_state.get("inline_use", False):
        d1 = st.session_state.get("inline_start", date.today())
        d2 = st.session_state.get("inline_end", date.today())
        if d2 < d1:
            d1, d2 = d2, d1
        start_brt = datetime.combine(d1, time(0, 0)).replace(tzinfo=TZ_BRT)
        end_brt_inclusive = datetime.combine(d2, time(23, 59, 59)).replace(tzinfo=TZ_BRT) + timedelta(seconds=1)
        if st.button("Limpar período inline"):
            st.session_state["inline_use"] = False
            st.rerun()

    # Como o modo é BRT, não converte aqui
    start_ts, end_ts = start_brt, end_brt_inclusive

    st.markdown("---")

    # Filtros específicos de NetDepósito
    client_filter = st.text_input("🔍 Client ID (NetDepósito)", value="", placeholder="Filtrar por ID…")
    op_filter = st.selectbox("💰 Operação (NetDepósito)", ["Todos", "Depósitos", "Saques"])

    st.markdown(f'''
        <div style="background: {COLOR_BG}; padding: 10px; border-radius: 8px; border-left: 4px solid {COLOR_ACCENT}; margin-top: 20px;">
            <small style="color: {COLOR_TEXT};">
                <strong>⏰ Período Ativo:</strong><br>
                {fmt(start_brt)} → {fmt(end_brt_inclusive)}<br>
                <em>Horário: BRT (UTC-3)</em>
            </small>
        </div>
    ''', unsafe_allow_html=True)

    with st.expander("🔍 Diagnóstico Avançado"):
        if st.button("Executar Diagnóstico"):
            q = "SELECT @@global.time_zone AS global_tz, @@session.time_zone AS session_tz, NOW() AS server_now"
            with engine.connect() as conn:
                st.write(pd.read_sql(text(q), conn))

params = {"start_ts": fmt(start_ts), "end_ts": fmt(end_ts)}

# ======= Helpers =======
@st.cache_data(show_spinner=False, ttl=60)
def fetch_df(sql_text, params):
    with engine.connect() as conn:
        return pd.read_sql(text(sql_text), conn, params=params)

def create_download_button(df: pd.DataFrame, label: str, fname: str):
    if df is None or df.empty:
        st.button(label, disabled=True)
    else:
        st.download_button(
            label=label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=fname,
            mime="text/csv",
            use_container_width=True,
        )

def to_brl(x: float) -> str:
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ======= SQL Builders (Pagamentos / NetDepósito) =======
def tbl(name: str):
    return f"`{db_name}`.{name}" if db_name else name

def sql_pagamentos_intervalo(mode: str):
    if mode == "UTC":
        display_ts = "DATE_FORMAT(DATE_ADD(p.create_time, INTERVAL -3 HOUR), '%Y-%m-%d %H:%i')"
    else:
        display_ts = "DATE_FORMAT(p.create_time, '%Y-%m-%d %H:%i')"
    return f"""
        SELECT
            p.id,
            p.amount/100 AS amount_corrigido,
            p.client_id AS id_do_cliente,
            p.operation_type AS operacao,
            p.callback_type AS finalizado,
            {display_ts} AS registration_date_brt,
            p.processing_status
        FROM {tbl('payment')} p
        WHERE
            p.processing_status = 'COMPLETED'
            AND p.callback_type IS NOT NULL
            AND p.callback_type <> 'NULL'
            AND p.create_time >= :start_ts
            AND p.create_time <  :end_ts
        ORDER BY p.id DESC
    """

def sql_resumo_por_dia(mode: str):
    grp_date = "DATE(DATE_ADD(p.create_time, INTERVAL -3 HOUR))" if mode == "UTC" else "DATE(p.create_time)"
    return f"""
        SELECT
            {grp_date} AS data_brt,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100 ELSE 0 END) AS total_depositos,
            SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100 ELSE 0 END) AS total_saques,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100 ELSE 0 END)
          - SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100 ELSE 0 END) AS net_deposit
        FROM {tbl('payment')} p
        WHERE
            p.processing_status = 'COMPLETED'
            AND p.callback_type IS NOT NULL
            AND p.callback_type <> 'NULL'
            AND p.create_time >= :start_ts
            AND p.create_time <  :end_ts
        GROUP BY {grp_date}
        ORDER BY data_brt ASC
    """

def sql_resumo_por_hora(mode: str):
    grp_date = "DATE(DATE_ADD(p.create_time, INTERVAL -3 HOUR))" if mode == "UTC" else "DATE(p.create_time)"
    grp_hour = "HOUR(DATE_ADD(p.create_time, INTERVAL -3 HOUR))" if mode == "UTC" else "HOUR(p.create_time)"
    return f"""
        SELECT
            {grp_date} AS data_brt,
            {grp_hour} AS hora_brt,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100 ELSE 0 END) AS deposito_h,
            SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100 ELSE 0 END) AS saque_h
        FROM {tbl('payment')} p
        WHERE
            p.processing_status = 'COMPLETED'
            AND p.callback_type IS NOT NULL
            AND p.callback_type <> 'NULL'
            AND p.create_time >= :start_ts
            AND p.create_time <  :end_ts
        GROUP BY {grp_date}, {grp_hour}
        ORDER BY data_brt ASC, hora_brt ASC
    """

def sql_top_ids_valor(mode: str, tipo: str):
    op = "withdr%%" if tipo == "saque" else "depos%%"
    return f"""
        SELECT
            p.client_id AS id_do_cliente,
            SUM(p.amount/100) AS total_valor,
            COUNT(*) AS qtd_ops
        FROM {tbl('payment')} p
        WHERE
            p.processing_status = 'COMPLETED'
            AND p.callback_type IS NOT NULL
            AND p.callback_type <> 'NULL'
            AND p.operation_type LIKE '{op}'
            AND p.create_time >= :start_ts
            AND p.create_time <  :end_ts
        GROUP BY p.client_id
        ORDER BY total_valor DESC
        LIMIT 30
    """

def sql_top_ids_qtd(mode: str, tipo: str):
    op = "withdr%%" if tipo == "saque" else "depos%%"
    return f"""
        SELECT
            p.client_id AS id_do_cliente,
            COUNT(*) AS qtd_ops,
            SUM(p.amount/100) AS total_valor
        FROM {tbl('payment')} p
        WHERE
            p.processing_status = 'COMPLETED'
            AND p.callback_type IS NOT NULL
            AND p.callback_type <> 'NULL'
            AND p.operation_type LIKE '{op}'
            AND p.create_time >= :start_ts
            AND p.create_time <  :end_ts
        GROUP BY p.client_id
        ORDER BY qtd_ops DESC
        LIMIT 30
    """

def sql_top30_saques_diarios(mode: str):
    data_expr = "DATE(DATE_ADD(p.create_time, INTERVAL -3 HOUR))" if mode == "UTC" else "DATE(p.create_time)"
    return f"""
        WITH saques AS (
            SELECT
                p.client_id,
                {data_expr} AS data_brt,
                p.amount/100 AS valor_saque
            FROM {tbl('payment')} p
            WHERE
                p.processing_status = 'COMPLETED'
                AND p.callback_type IS NOT NULL
                AND p.callback_type <> 'NULL'
                AND p.operation_type LIKE 'withdr%%'
                AND p.create_time >= :start_ts
                AND p.create_time <  :end_ts
        ),
        agreg AS (
            SELECT
                client_id,
                data_brt,
                COUNT(*) AS qtd_saques,
                SUM(valor_saque) AS total_sacado
            FROM saques
            GROUP BY client_id, data_brt
        )
        SELECT
            client_id AS id_do_cliente,
            data_brt,
            qtd_saques,
            total_sacado
        FROM agreg
        ORDER BY qtd_saques DESC, total_sacado DESC
        LIMIT 30
    """

# ======= Builders / Utils (Cassino) =======
def _last_minutes_bounds_brt(minutes: int = 60):
    now_brt = datetime.now(TZ_BRT)
    start_brt = now_brt - timedelta(minutes=minutes)
    end_brt_inclusive = now_brt + timedelta(seconds=1)  # janela [start, end)
    return start_brt, end_brt_inclusive

def _to_mode_bounds(start_brt: datetime, end_brt_inclusive: datetime, mode: str):
    if mode == "UTC":
        return utc_bounds_from_brt_bounds(start_brt, end_brt_inclusive)
    return start_brt, end_brt_inclusive

@st.cache_data(show_spinner=False, ttl=120)
def _get_table_columns(schema: str, table: str) -> set[str]:
    q = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
    """
    with engine.connect() as conn:
        cols = pd.read_sql(text(q), conn, params={"schema": schema, "table": table})
    return set(c.lower() for c in cols["COLUMN_NAME"].astype(str))

def _pick(existing: set[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c.lower() in existing:
            return c
    return None

@st.cache_data(show_spinner=False, ttl=120)
def _get_column_info(schema: str, table: str, column: str) -> dict:
    q = """
        SELECT
            DATA_TYPE               AS data_type,
            COLUMN_TYPE             AS column_type,
            NUMERIC_PRECISION       AS numeric_precision,
            NUMERIC_SCALE           AS numeric_scale,
            DATETIME_PRECISION      AS datetime_precision,
            CHARACTER_MAXIMUM_LENGTH AS char_len
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table AND COLUMN_NAME = :col
        LIMIT 1
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(q), conn, params={"schema": schema, "table": table, "col": column})
    return {} if df.empty else df.iloc[0].to_dict()

def _build_ts_base_expr(created_col: str) -> str:
    info = _get_column_info(db_name or "", "rodadas_cliente", created_col)
    dt = (info.get("data_type") or "").lower()
    col_sql = f"r.`{created_col}`"
    if dt in ("timestamp", "datetime", "date"):
        return col_sql
    if dt in ("int", "integer", "bigint", "smallint", "mediumint", "tinyint", "decimal", "numeric", "double", "float", "real"):
        numeric_precision = info.get("numeric_precision")
        numeric_scale = info.get("numeric_scale")
        if numeric_precision is not None:
            try:
                if int(numeric_precision) >= 13 and (numeric_scale is None or int(numeric_scale) == 0):
                    return f"FROM_UNIXTIME({col_sql}/1000.0)"
            except Exception:
                pass
        return f"FROM_UNIXTIME({col_sql})"
    if dt in ("varchar", "char", "text", "longtext", "mediumtext", "tinytext"):
        return f"STR_TO_DATE({col_sql}, '%Y-%m-%d %H:%i:%s')"
    return col_sql

@st.cache_data(show_spinner=False, ttl=120)
def _resolve_rounds_columns() -> dict:
    existing = _get_table_columns(db_name or "", "rodadas_cliente")
    col_cliente   = _pick(existing, ["cliente_id","client_id","player_id","user_id","id_cliente"])
    col_game      = _pick(existing, ["game_name","game","game_title","nome_jogo"])
    col_provider  = _pick(existing, ["provider_name","provider","vendor","studio"])
    col_gastos    = _pick(existing, ["gastos","bet","bet_value","wager","amount_bet","stake","valor_apostado"])
    col_ganhos    = _pick(existing, ["ganhos","win","win_value","amount_win","payout","lucro"])
    col_created   = _pick(existing, ["created_at","create_time","timestamp","createdat","inserted_at","dt_created"])

    faltando = [lbl for lbl, real in [
        ("cliente_id", col_cliente),
        ("game_name", col_game),
        ("provider_name", col_provider),
        ("gastos", col_gastos),
        ("ganhos", col_ganhos),
        ("created_at", col_created),
    ] if real is None]

    return {
        "existing": existing,
        "map": {
            "cliente_id": col_cliente,
            "game_name": col_game,
            "provider_name": col_provider,
            "gastos": col_gastos,
            "ganhos": col_ganhos,
            "created_at": col_created,
        },
        "missing": faltando
    }

def _sql_rodadas_clientes(mode: str, divide_por_100: bool):
    res = _resolve_rounds_columns()
    COLS = res["map"]
    gastos_expr = f"r.`{COLS['gastos']}`/100" if divide_por_100 else f"r.`{COLS['gastos']}`"
    ganhos_expr = f"r.`{COLS['ganhos']}`/100" if divide_por_100 else f"r.`{COLS['ganhos']}`"
    ts_base = _build_ts_base_expr(COLS["created_at"])
    ts_expr = (
        f"DATE_FORMAT(DATE_ADD({ts_base}, INTERVAL -3 HOUR), '%Y-%m-%d %H:%i:%s')"
        if mode == "UTC" else
        f"DATE_FORMAT({ts_base}, '%Y-%m-%d %H:%i:%s')"
    )
    return f"""
        SELECT
            r.`{COLS['cliente_id']}`    AS cliente_id,
            r.`{COLS['game_name']}`     AS game_name,
            r.`{COLS['provider_name']}` AS provider_name,
            {gastos_expr} AS gastos,
            {ganhos_expr} AS ganhos,
            {ts_expr}     AS created_at_brt
        FROM {tbl('rodadas_cliente')} r
        WHERE
            {ts_base} >= :start_ts
            AND {ts_base} <  :end_ts
        ORDER BY {ts_base} DESC
        LIMIT 50000
    """

def _sanitize_rounds(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    keep = ["cliente_id","game_name","provider_name","gastos","ganhos","created_at_brt"]
    df = df[[c for c in keep if c in df.columns]].copy()
    for col in ["gastos","ganhos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

# =====================================================================
# ========================== ÁREA: NET DEPÓSITO ========================
# =====================================================================
if area == "NetDepósito":

    # ======= Coleta (somente quando NetDepósito) =======
    with st.spinner("🔄 Carregando dados..."):
        df_list = fetch_df(sql_pagamentos_intervalo(mode), params)
        df_day  = fetch_df(sql_resumo_por_dia(mode), params)
        df_hour = fetch_df(sql_resumo_por_hora(mode), params)
        df_top30_saques_dia = fetch_df(sql_top30_saques_diarios(mode), params)
        df_top_val_saques   = fetch_df(sql_top_ids_valor(mode, "saque"), params)
        df_top_qtd_saques   = fetch_df(sql_top_ids_qtd(mode, "saque"), params)
        df_top_val_deps     = fetch_df(sql_top_ids_valor(mode, "deposito"), params)
        df_top_qtd_deps     = fetch_df(sql_top_ids_qtd(mode, "deposito"), params)

    # ======= Sanitização/Filtros =======
    if not df_list.empty:
        df_list["amount_corrigido"] = pd.to_numeric(df_list["amount_corrigido"], errors="coerce").fillna(0.0)
        df_list["operacao"] = df_list["operacao"].astype(str)
        df_list["id_do_cliente"] = df_list["id_do_cliente"].astype(str)
        if client_filter:
            df_list = df_list[df_list["id_do_cliente"].str.contains(client_filter, case=False, na=False)]
        ops_lower = df_list["operacao"].str.lower()
        if op_filter == "Depósitos":
            df_list = df_list[ops_lower.str.startswith("depos", na=False) | ops_lower.str.contains("deposit", na=False)]
        elif op_filter == "Saques":
            df_list = df_list[ops_lower.str.startswith("withdr", na=False) | ops_lower.str.contains("withdraw", na=False)]

    if not df_day.empty:
        df_day["data_brt"] = pd.to_datetime(df_day["data_brt"], errors="coerce")
        df_day["total_depositos"] = pd.to_numeric(df_day["total_depositos"], errors="coerce").fillna(0.0)
        df_day["total_saques"]    = pd.to_numeric(df_day["total_saques"],    errors="coerce").fillna(0.0)
        df_day = df_day[df_day["data_brt"].notna()]
        df_day = (df_day.groupby("data_brt", as_index=False)
                  .agg(total_depositos=("total_depositos","sum"),
                       total_saques=("total_saques","sum"))
                  .sort_values("data_brt").reset_index(drop=True))

    if not df_hour.empty:
        df_hour["data_brt"]  = pd.to_datetime(df_hour["data_brt"], errors="coerce")
        df_hour = df_hour[df_hour["data_brt"].notna()]
        df_hour["hora_brt"]  = pd.to_numeric(df_hour["hora_brt"], errors="coerce").fillna(0).astype(int).clip(0, 23)
        df_hour["deposito_h"] = pd.to_numeric(df_hour["deposito_h"], errors="coerce").fillna(0.0)
        df_hour["saque_h"]    = pd.to_numeric(df_hour["saque_h"],    errors="coerce").fillna(0.0)
        df_hour["hora_ts"] = df_hour["data_brt"] + pd.to_timedelta(df_hour["hora_brt"], unit="h")

    # ======= KPIs + Calendário Inline =======
    def safe_sum(series):
        return float(series.fillna(0).sum()) if series is not None else 0.0

    if not df_list.empty:
        ops_lower = df_list["operacao"].str.lower()
        is_dep = ops_lower.str.startswith("depos", na=False) | ops_lower.str.contains("deposit", na=False)
        is_wdr = ops_lower.str.startswith("withdr", na=False) | ops_lower.str.contains("withdraw", na=False)
        total_deps = safe_sum(df_list.loc[is_dep, "amount_corrigido"])
        total_saques = safe_sum(df_list.loc[is_wdr, "amount_corrigido"])
        total_transactions = int(len(df_list))
        avg_transaction = (total_deps + total_saques) / total_transactions if total_transactions > 0 else 0.0
    else:
        total_deps = total_saques = avg_transaction = 0.0
        total_transactions = 0

    net = total_deps - total_saques

    left, right = st.columns([3, 3])
    with left:
        st.markdown(f'''
            <div class="section-header inline-row">
                <div class="section-title">📊 Métricas Principais</div>
            </div>
        ''', unsafe_allow_html=True)
    with right:
        with st.form("inline_date_form", clear_on_submit=False):
            st.markdown('<div class="inline-card">', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([1.2, 1.2, 0.9, 0.9])
            with c1:
                start_pick = st.date_input("Início", value=date.today(), key="inline_start_picker", label_visibility="collapsed")
            with c2:
                end_pick = st.date_input("Fim", value=st.session_state.get("inline_end", date.today()), key="inline_end_picker", label_visibility="collapsed")
            with c3:
                apply_inline = st.form_submit_button("Aplicar", type="primary", use_container_width=True)
            with c4:
                clear_inline = st.form_submit_button("Limpar", type="secondary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if apply_inline:
                st.session_state["inline_start"] = start_pick
                st.session_state["inline_end"] = end_pick
                st.session_state["inline_use"] = True
                st.rerun()
            if clear_inline:
                st.session_state["inline_use"] = False
                st.rerun()

    # Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">💰 Total Depósitos</div>
                <div class="metric-value">{to_brl(total_deps)}</div>
                <div class="metric-delta">↗️ Entrada de capital</div>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">💸 Total Saques</div>
                <div class="metric-value">{to_brl(total_saques)}</div>
                <div class="metric-delta">↙️ Saída de capital</div>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        delta_color = COLOR_ACCENT if net >= 0 else "#E74C3C"
        net_icon = "📈" if net >= 0 else "📉"
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">⚖️ Saldo Líquido</div>
                <div class="metric-value" style="color: {delta_color};">{to_brl(net)}</div>
                <div class="metric-delta">{net_icon} {"Positivo" if net >= 0 else "Negativo"}</div>
            </div>
        ''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">🔢 Transações</div>
                <div class="metric-value">{total_transactions:,}</div>
                <div class="metric-delta">💳 Ticket médio: {to_brl(avg_transaction)}</div>
            </div>
        ''', unsafe_allow_html=True)

    st.write("")
    create_download_button(df_list, "📥 Exportar Lista Completa", "lista_pagamentos.csv")

    # ======= Evolução diária =======
    st.markdown(f'''
        <div class="section-header">
            <div class="section-title">📈 Evolução Temporal</div>
        </div>
    ''', unsafe_allow_html=True)

    if df_day.empty:
        st.info("ℹ️ Sem dados disponíveis no período selecionado.")
    else:
        df_day_plot = df_day.sort_values("data_brt").copy()

        def fit_and_forecast_daily(df_day_in: pd.DataFrame, horizon_days: int = 7):
            if df_day_in is None or df_day_in.empty:
                return None
            work = df_day_in.copy().sort_values("data_brt").reset_index(drop=True)
        # garante sequência diária contínua
            full_idx = pd.date_range(work["data_brt"].min(), work["data_brt"].max(), freq="D")
            work = work.set_index("data_brt").reindex(full_idx)
            work.index.name = "data_brt"

            # corrigido: passa a série diretamente para pd.to_numeric
            for col in ["total_depositos", "total_saques"]:
                work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)

            work = work.reset_index().rename(columns={"index": "data_brt"})

            work["t"] = np.arange(len(work), dtype=float)
            out = {}
            for col in ["total_depositos", "total_saques"]:
                y = work[col].to_numpy(dtype=np.float64).reshape(-1, 1)
                X = work["t"].to_numpy(dtype=np.float64).reshape(-1, 1)
                if len(work) < 3 or np.allclose(y, y.mean()):
                    out[col] = None
                    continue
                model = LinearRegression().fit(X, y)
                max_t = work["t"].max()
                h = max(horizon_days, 1)
                t_future = np.arange(max_t + 1, max_t + 1 + h).reshape(-1, 1)
                y_pred = model.predict(t_future).ravel()
                future_dates = pd.date_range(work["data_brt"].max() + pd.Timedelta(days=1), periods=h, freq="D")
                out[col] = pd.DataFrame({
                    "data_brt": future_dates,
                    f"{col}_pred": np.clip(y_pred, 0, None)
                })
            if out["total_depositos"] is None and out["total_saques"] is None:
                return None
            df_fut = None
            for piece in [out["total_depositos"], out["total_saques"]]:
                if piece is None:
                    continue
                df_fut = piece if df_fut is None else df_fut.merge(piece, on="data_brt", how="outer")
            return df_fut

        tab_all, tab_7d, tab_ml = st.tabs(["📊 Período selecionado", "📆 Últimos 7 dias", "🔮 Projeção (ML)"])

        with tab_all:
            fig_all = go.Figure()
            fig_all.add_trace(go.Bar(
                x=df_day_plot["data_brt"], y=df_day_plot["total_depositos"],
                name="Depósitos", marker_color=COLOR_ACCENT, opacity=0.85
            ))
            fig_all.add_trace(go.Bar(
                x=df_day_plot["data_brt"], y=df_day_plot["total_saques"],
                name="Saques", marker_color=COLOR_TEXT, opacity=0.85
            ))
            fig_all.update_layout(
                barmode="group", height=420, paper_bgcolor=COLOR_LIGHT, plot_bgcolor=COLOR_BG,
                font=dict(color=COLOR_TEXT), title="Evolução Diária (Período Selecionado)",
                yaxis_title="Valor (R$)", yaxis_tickformat="R$ ,.0f"
            )
            st.plotly_chart(fig_all, use_container_width=True)
            create_download_button(df_day_plot, "📥 Baixar dados do período", "agregado_diario_periodo.csv")

        with tab_7d:
            if not df_day_plot.empty:
                last_date = df_day_plot["data_brt"].max()
                start_7d = (last_date - pd.Timedelta(days=6)).normalize()
                df_7d = df_day_plot[df_day_plot["data_brt"] >= start_7d].copy()
                full_idx = pd.date_range(start_7d.normalize(), last_date.normalize(), freq="D")
                df_7d = (
                    df_7d.set_index("data_brt")
                        .reindex(full_idx)
                        .rename_axis("data_brt")
                        .fillna({"total_depositos": 0.0, "total_saques": 0.0})
                        .reset_index()
                )
                fig_7d = go.Figure()
                fig_7d.add_trace(go.Bar(
                    x=df_7d["data_brt"], y=df_7d["total_depositos"],
                    name="Depósitos (dia)", marker_color=COLOR_ACCENT, opacity=0.9
                ))
                fig_7d.add_trace(go.Bar(
                    x=df_7d["data_brt"], y=df_7d["total_saques"],
                    name="Saques (dia)", marker_color=COLOR_TEXT, opacity=0.9
                ))
                fig_7d.update_layout(
                    barmode="group", height=420, paper_bgcolor=COLOR_LIGHT, plot_bgcolor=COLOR_BG,
                    font=dict(color=COLOR_TEXT), title="Evolução Diária – Últimos 7 Dias",
                    yaxis_title="Valor (R$)", yaxis_tickformat="R$ ,.0f"
                )
                st.plotly_chart(fig_7d, use_container_width=True)
                create_download_button(df_7d, "📥 Baixar últimos 7 dias", "agregado_diario_7d.csv")
            else:
                st.info("Sem dados para compor a janela de 7 dias.")

        with tab_ml:
            df_forecast = fit_and_forecast_daily(df_day_plot, horizon_days=7)
            if df_forecast is None or df_forecast.empty:
                st.info("Sem dados suficientes para projetar.")
            else:
                fig_ml = go.Figure()
                fig_ml.add_trace(go.Scatter(
                    x=df_day_plot["data_brt"], y=df_day_plot["total_depositos"],
                    mode="lines+markers", name="Depósitos (histórico)", line=dict(width=3)
                ))
                fig_ml.add_trace(go.Scatter(
                    x=df_day_plot["data_brt"], y=df_day_plot["total_saques"],
                    mode="lines+markers", name="Saques (histórico)", line=dict(width=3)
                ))
                if "total_depositos_pred" in df_forecast.columns:
                    fig_ml.add_trace(go.Scatter(
                        x=df_forecast["data_brt"], y=df_forecast["total_depositos_pred"],
                        mode="lines+markers", name="Projeção Depósitos (7d)", line=dict(dash="dash", width=3)
                    ))
                if "total_saques_pred" in df_forecast.columns:
                    fig_ml.add_trace(go.Scatter(
                        x=df_forecast["data_brt"], y=df_forecast["total_saques_pred"],
                        mode="lines+markers", name="Projeção Saques (7d)", line=dict(dash="dash", width=3)
                    ))
                fig_ml.update_layout(
                    height=420, paper_bgcolor=COLOR_LIGHT, plot_bgcolor=COLOR_BG,
                    font=dict(color=COLOR_TEXT), title="Projeção (Linear) – Próximos 7 Dias",
                    yaxis_title="Valor (R$)", yaxis_tickformat="R$ ,.0f"
                )
                st.plotly_chart(fig_ml, use_container_width=True)
                create_download_button(df_forecast, "🔮 Baixar projeções (7d)", "projecoes_ml_7d.csv")

    # ======= Análise Horária =======
    st.markdown(f'''
        <div class="section-header">
            <div class="section-title">⏰ Análise Horária</div>
        </div>
    ''', unsafe_allow_html=True)

    if df_hour.empty:
        st.info("ℹ️ Sem dados horários disponíveis.")
    else:
        df_hour_pivot = df_hour.pivot_table(
            index=df_hour["data_brt"].dt.date,
            columns="hora_brt",
            values=["deposito_h", "saque_h"],
            aggfunc="sum",
            fill_value=0,
        )
        tab1, tab2 = st.tabs(["📈 Evolução Horária", "🔥 Heatmap de Atividade"])
        with tab1:
            ordered = df_hour.sort_values("hora_ts")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=ordered["hora_ts"], y=ordered["deposito_h"],
                                      mode="lines+markers", name="Depósitos",
                                      line=dict(color=COLOR_ACCENT, width=3), marker=dict(size=6, color=COLOR_ACCENT)))
            fig2.add_trace(go.Scatter(x=ordered["hora_ts"], y=ordered["saque_h"],
                                      mode="lines+markers", name="Saques",
                                      line=dict(color=COLOR_TEXT, width=3), marker=dict(size=6, color=COLOR_TEXT)))
            fig2.update_layout(
                title="Atividade Financeira por Hora", paper_bgcolor=COLOR_LIGHT, plot_bgcolor=COLOR_BG,
                font=dict(color=COLOR_TEXT), xaxis_title="Data e Hora", yaxis_title="Valor (R$)",
                yaxis_tickformat="R$ ,.0f", height=400,
            )
            st.plotly_chart(fig2, use_container_width=True)
        with tab2:
            if not df_hour_pivot.empty:
                depositos_data = df_hour_pivot["deposito_h"].fillna(0).values
                fig3 = go.Figure(data=go.Heatmap(
                    z=depositos_data, x=list(range(24)), y=[str(d) for d in df_hour_pivot.index],
                    colorscale=[[0, COLOR_BG], [1, COLOR_ACCENT]], showscale=True,
                    hovertemplate='Data: %{y}<br>Hora: %{x}:00<br>Depósitos: R$ %{z:,.2f}<extra></extra>'
                ))
                fig3.update_layout(
                    title="🔥 Heatmap - Depósitos por Hora", xaxis_title="Hora do Dia", yaxis_title="Data",
                    paper_bgcolor=COLOR_LIGHT, plot_bgcolor=COLOR_BG, font=dict(color=COLOR_TEXT), height=400,
                    coloraxis_colorbar=dict(
                        tickfont=dict(color=COLOR_DARK),
                        title=dict(text="", font=dict(color=COLOR_DARK))
                    )
                )
                st.plotly_chart(fig3, use_container_width=True)
        create_download_button(df_hour, "📥 Dados Horários", "agregado_horario.csv")

    # ======= Rankings =======
    st.markdown(f'''
        <div class="section-header">
            <div class="section-title">🏆 Rankings e Top Performers</div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown("### 🥇 Top 30 - Maior Atividade de Saques por Dia")
    if not df_top30_saques_dia.empty:
        df_top30 = df_top30_saques_dia.copy()
        df_top30["id_do_cliente"] = df_top30["id_do_cliente"].astype(str)
        df_top30 = df_top30.sort_values("total_sacado", ascending=True).head(15)
        fig_top = px.bar(
            df_top30,
            x="total_sacado",
            y="id_do_cliente",
            orientation="h",
            color="qtd_saques",
            color_continuous_scale=[
                [0.0, COLOR_BG],
                [0.5, "#BFF288"],
                [1.0, COLOR_ACCENT]
            ],
            labels={
                "total_sacado": "Total Sacado (R$)",
                "id_do_cliente": "Cliente (ID)",
                "qtd_saques": "Qtd. saques"
            },
            height=440,
        )
        fig_top.update_yaxes(
            type="category",
            categoryorder="array",
            categoryarray=df_top30["id_do_cliente"].tolist(),
            tickfont=dict(size=11, color=COLOR_TEXT)
        )
        fig_top.update_xaxes(
            tickformat="R$ ,.0f",
            gridcolor="rgba(39,6,68,.15)"
        )
        fig_top.update_layout(
            paper_bgcolor=COLOR_LIGHT,
            plot_bgcolor=COLOR_BG,
            font=dict(color=COLOR_TEXT),
            margin=dict(l=150, r=40, t=50, b=40),
            coloraxis_colorbar=dict(title="Qtd saques")
        )
        fig_top.update_traces(
            customdata=df_top30[["qtd_saques"]],
            hovertemplate="ID: %{y}<br>Total: R$ %{x:,.2f}<br>Qtd saques: %{customdata[0]}<extra></extra>",
            text=df_top30["total_sacado"].map(to_brl),
            textposition="outside",
            cliponaxis=False
        )
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.plotly_chart(fig_top, use_container_width=True)
        with col_table:
            st.dataframe(
                df_top30_saques_dia,
                use_container_width=True,
                height=500,
                column_config={"total_sacado": st.column_config.NumberColumn("Total Sacado (R$)", format="R$ %.2f")},
            )
        create_download_button(df_top30_saques_dia, "📥 Baixar Top 30 Saques/Dia", "top30_saques_dia.csv")
    else:
        st.info("Sem registros para Top 30 no período.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 💸 Top Valor – Saques")
        st.dataframe(df_top_val_saques, use_container_width=True)
        create_download_button(df_top_val_saques, "📥 Baixar Top Valor Saques", "top_val_saques.csv")
        st.markdown("### 🧮 Top Qtd – Saques")
        st.dataframe(df_top_qtd_saques, use_container_width=True)
        create_download_button(df_top_qtd_saques, "📥 Baixar Top Qtd Saques", "top_qtd_saques.csv")
    with c2:
        st.markdown("### 💰 Top Valor – Depósitos")
        st.dataframe(df_top_val_deps, use_container_width=True)
        create_download_button(df_top_val_deps, "📥 Baixar Top Valor Depósitos", "top_val_depositos.csv")
        st.markdown("### 🧮 Top Qtd – Depósitos")
        st.dataframe(df_top_qtd_deps, use_container_width=True)
        create_download_button(df_top_qtd_deps, "📥 Baixar Top Qtd Depósitos", "top_qtd_depositos.csv")

# =====================================================================
# ============================ ÁREA: CASSINO ===========================
# =====================================================================
elif area == "Cassino":

    st.markdown(f'''
        <div class="section-header">
            <div class="section-title">🎮 Rodadas por Cliente</div>
        </div>
    ''', unsafe_allow_html=True)

    # Diagnóstico de colunas
    res = _resolve_rounds_columns()
    if res["missing"]:
        with st.expander("⚠️ Diagnóstico de colunas ausentes em rodadas_cliente"):
            st.write("Colunas encontradas na tabela:", sorted(list(res["existing"])))
            st.error(f"As colunas lógicas abaixo não foram mapeadas no banco: {', '.join(res['missing'])}")
        st.stop()

    COLS = res["map"]

    st.caption("Se *gastos/ganhos* estiverem em centavos, marque para dividir por 100.")
    dividir_por_100 = st.checkbox("↘️ Valores em centavos (dividir por 100)", value=False)

    # Dados: período ativo
    with st.spinner("🔄 Carregando rodadas do período..."):
        df_rodadas = fetch_df(_sql_rodadas_clientes(mode, dividir_por_100), params)

    # Dados: últimos 60 minutos com fallback de fuso
    _60_start_brt, _60_end_brt_inc = _last_minutes_bounds_brt(60)
    _60_start_ts, _60_end_ts = _to_mode_bounds(_60_start_brt, _60_end_brt_inc, mode)
    params60 = {"start_ts": fmt(_60_start_ts), "end_ts": fmt(_60_end_ts)}

    with st.spinner("⏱️ Carregando rodadas (últimos 60 minutos)..."):
        df_rodadas_60 = fetch_df(_sql_rodadas_clientes(mode, dividir_por_100), params60)

        df_rodadas_60_fb = None
        if (df_rodadas_60 is None or df_rodadas_60.empty):
            if mode == "UTC":
                params60_fallback = {"start_ts": fmt(_60_start_brt), "end_ts": fmt(_60_end_brt_inc)}
                df_rodadas_60_fb = fetch_df(_sql_rodadas_clientes("BRT", dividir_por_100), params60_fallback)
            else:
                fb_start_ts, fb_end_ts = utc_bounds_from_brt_bounds(_60_start_brt, _60_end_brt_inc)
                params60_fallback = {"start_ts": fmt(fb_start_ts), "end_ts": fmt(fb_end_ts)}
                df_rodadas_60_fb = fetch_df(_sql_rodadas_clientes("UTC", dividir_por_100), params60_fallback)

            if df_rodadas_60_fb is not None and not df_rodadas_60_fb.empty:
                st.info("ℹ️ Nenhum resultado na interpretação de fuso atual; resultados mostrados usando fallback de fuso.")
                df_rodadas_60 = df_rodadas_60_fb

    # Sanitização
    df_rodadas    = _sanitize_rounds(df_rodadas)
    df_rodadas_60 = _sanitize_rounds(df_rodadas_60)

    # Abas: Tabela geral + Métricas 60m
    tab_tbl, tab_metrics = st.tabs(["📋 Tabela (período ativo)", "📊 Métricas – últimos 60 min"])

    with tab_tbl:
        if df_rodadas is None or df_rodadas.empty:
            st.info("ℹ️ Nenhuma rodada encontrada no período selecionado.")
        else:
            st.dataframe(
                df_rodadas,
                use_container_width=True,
                height=480,
                column_config={
                    "gastos": st.column_config.NumberColumn("Gastos (R$)", format="R$ %.2f"),
                    "ganhos": st.column_config.NumberColumn("Ganhos (R$)", format="R$ %.2f"),
                    "created_at_brt": "Data/Hora (BRT)",
                }
            )
            create_download_button(df_rodadas, "📥 Exportar rodadas do período", "rodadas_periodo.csv")

    with tab_metrics:
        st.caption(f"Janela analisada: **{fmt(_60_start_brt)} → {fmt(_60_end_brt_inc)}** (BRT)")

        if df_rodadas_60 is None or df_rodadas_60.empty:
            st.warning("Sem rodadas nos últimos 60 minutos.")
        else:
            media_gastos = float(df_rodadas_60["gastos"].mean()) if "gastos" in df_rodadas_60 else 0.0
            media_ganhos = float(df_rodadas_60["ganhos"].mean()) if "ganhos" in df_rodadas_60 else 0.0
            max_aposta = float(df_rodadas_60["gastos"].max()) if "gastos" in df_rodadas_60 else 0.0
            max_ganho  = float(df_rodadas_60["ganhos"].max()) if "ganhos" in df_rodadas_60 else 0.0
            total_gasto_60 = float(df_rodadas_60["gastos"].sum()) if "gastos" in df_rodadas_60 else 0.0
            total_ganho_60 = float(df_rodadas_60["ganhos"].sum()) if "ganhos" in df_rodadas_60 else 0.0

            jogo_mais_jogado, qtd_jogo_mais = "—", 0
            if "game_name" in df_rodadas_60 and not df_rodadas_60["game_name"].isna().all():
                vc = df_rodadas_60["game_name"].value_counts(dropna=True)
                if not vc.empty:
                    jogo_mais_jogado = str(vc.index[0])
                    qtd_jogo_mais = int(vc.iloc[0])

            top_ganhos_clientes = pd.DataFrame()
            top_rodadas_clientes = pd.DataFrame()

            if set(["cliente_id","ganhos"]).issubset(df_rodadas_60.columns):
                top_ganhos_clientes = (df_rodadas_60.groupby("cliente_id", as_index=False)
                                       .agg(ganhos_totais=("ganhos","sum"),
                                            rodadas=("cliente_id","count"))
                                       .sort_values("ganhos_totais", ascending=False)
                                       .head(15))

            if "cliente_id" in df_rodadas_60.columns:
                top_rodadas_clientes = (df_rodadas_60.groupby("cliente_id", as_index=False)
                                        .agg(rodadas=("cliente_id","count"),
                                             ganhos_totais=("ganhos","sum") if "ganhos" in df_rodadas_60.columns else ("cliente_id","count"))
                                        .sort_values("rodadas", ascending=False)
                                        .head(15))

            best_ganhos_id, best_ganhos_val = "—", 0.0
            if not top_ganhos_clientes.empty:
                best_ganhos_id  = str(top_ganhos_clientes.iloc[0]["cliente_id"])
                best_ganhos_val = float(top_ganhos_clientes.iloc[0]["ganhos_totais"])

            best_rodadas_id, best_rodadas_qtd = "—", 0
            if not top_rodadas_clientes.empty:
                best_rodadas_id  = str(top_rodadas_clientes.iloc[0]["cliente_id"])
                best_rodadas_qtd = int(top_rodadas_clientes.iloc[0]["rodadas"])

            n1, n2, n3, n4 = st.columns(4)
            with n1:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">⬆️ Aposta mais alta (60m)</div>
                        <div class="metric-value">{to_brl(max_aposta)}</div>
                        <div class="metric-delta">Maior "gastos"</div>
                    </div>
                ''', unsafe_allow_html=True)
            with n2:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">🏅 Maior ganho (60m)</div>
                        <div class="metric-value">{to_brl(max_ganho)}</div>
                        <div class="metric-delta">Pico de "ganhos"</div>
                    </div>
                ''', unsafe_allow_html=True)
            with n3:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">🧾 Total gasto (60m)</div>
                        <div class="metric-value">{to_brl(total_gasto_60)}</div>
                        <div class="metric-delta">Somatório de "gastos"</div>
                    </div>
                ''', unsafe_allow_html=True)
            with n4:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">💎 Total ganho (60m)</div>
                        <div class="metric-value">{to_brl(total_ganho_60)}</div>
                        <div class="metric-delta">Somatório de "ganhos"</div>
                    </div>
                ''', unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">💳 Média Gastos (60m)</div>
                        <div class="metric-value">{to_brl(media_gastos)}</div>
                        <div class="metric-delta">Ticket médio de aposta</div>
                    </div>
                ''', unsafe_allow_html=True)
            with m2:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">🏆 Média Ganhos (60m)</div>
                        <div class="metric-value">{to_brl(media_ganhos)}</div>
                        <div class="metric-delta">Retorno médio por rodada</div>
                    </div>
                ''', unsafe_allow_html=True)
            with m3:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">🎯 Jogo mais jogado</div>
                        <div class="metric-value">{jogo_mais_jogado}</div>
                        <div class="metric-delta">Rodadas: {qtd_jogo_mais:,}</div>
                    </div>
                ''', unsafe_allow_html=True)
            with m4:
                total_rodadas = int(len(df_rodadas_60))
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">⏱️ Rodadas (60m)</div>
                        <div class="metric-value">{total_rodadas:,}</div>
                        <div class="metric-delta">Volume recente</div>
                    </div>
                ''', unsafe_allow_html=True)

            k1, k2 = st.columns(2)
            with k1:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">👑 Cliente com mais ganhos (60m)</div>
                        <div class="metric-value">{best_ganhos_id}</div>
                        <div class="metric-delta">Total: {to_brl(best_ganhos_val)}</div>
                    </div>
                ''', unsafe_allow_html=True)
            with k2:
                st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">🏃 Cliente com mais jogadas (60m)</div>
                        <div class="metric-value">{best_rodadas_id}</div>
                        <div class="metric-delta">Rodadas: {best_rodadas_qtd:,}</div>
                    </div>
                ''', unsafe_allow_html=True)

            st.markdown("### 🥇 Top clientes por ganhos (60m)")
            if top_ganhos_clientes.empty:
                st.info("Sem clientes com ganhos nesta janela.")
            else:
                st.dataframe(
                    top_ganhos_clientes,
                    use_container_width=True,
                    height=380,
                    column_config={
                        "ganhos_totais": st.column_config.NumberColumn("Ganhos Totais (R$)", format="R$ %.2f"),
                        "rodadas": "Qtd. Rodadas"
                    }
                )
                create_download_button(top_ganhos_clientes, "📥 Exportar Top Ganhos (60m)", "top_ganhos_60m.csv")

            st.markdown("### 🎮 Top clientes por número de jogadas (60m)")
            if top_rodadas_clientes.empty:
                st.info("Sem volume de jogadas nesta janela.")
            else:
                st.dataframe(
                    top_rodadas_clientes,
                    use_container_width=True,
                    height=380,
                    column_config={
                        "rodadas": "Qtd. Rodadas",
                        "ganhos_totais": st.column_config.NumberColumn("Ganhos Totais (R$)", format="R$ %.2f") if "ganhos_totais" in top_rodadas_clientes.columns else "Ganhos Totais"
                    }
                )
                create_download_button(top_rodadas_clientes, "📥 Exportar Top Jogadas (60m)", "top_jogadas_60m.csv")
