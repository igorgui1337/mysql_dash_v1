import os
from textwrap import dedent

DB_NAME = os.getenv("DB_NAME", "")
def TBL(t):  # usa `schema.tabela` quando DB_NAME existe
    return f"`{DB_NAME}`.{t}" if DB_NAME else t

BRT_TZ = "America/Sao_Paulo"

def base_fields_brt():
    return f"""
        p.id,
        p.amount / 100.0 AS amount_corrigido,
        p.client_id AS id_do_cliente,
        p.operation_type AS operacao,
        p.callback_type AS finalizado,
        DATE_FORMAT(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}'), '%Y-%m-%d %H:%i') AS registration_date_brt,
        p.processing_status
    """

def filtro_basico():
    return """
        p.processing_status = 'COMPLETED'
        AND p.callback_type IS NOT NULL
        AND p.callback_type <> 'NULL'
    """

def query_pagamentos_intervalo():
    return dedent(f"""
        SELECT
            {base_fields_brt()}
        FROM {TBL('payment')} p
        WHERE
            {filtro_basico()}
            AND p.create_time >= :start_utc
            AND p.create_time <  :end_utc
        ORDER BY p.id DESC
    """)

def query_resumo_por_dia():
    return dedent(f"""
        SELECT
            DATE(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}')) AS data_brt,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100.0 ELSE 0 END) AS total_depositos,
            SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100.0 ELSE 0 END) AS total_saques,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100.0 ELSE 0 END)
          - SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100.0 ELSE 0 END) AS net_deposit
        FROM {TBL('payment')} p
        WHERE
            {filtro_basico()}
            AND p.create_time >= :start_utc
            AND p.create_time <  :end_utc
        GROUP BY DATE(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}'))
        ORDER BY data_brt DESC
    """)

def query_resumo_por_hora():
    return dedent(f"""
        SELECT
            DATE(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}')) AS data_brt,
            HOUR(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}')) AS hora_brt,
            SUM(CASE WHEN p.operation_type LIKE 'depos%%'  THEN p.amount/100.0 ELSE 0 END) AS deposito_h,
            SUM(CASE WHEN p.operation_type LIKE 'withdr%%' THEN p.amount/100.0 ELSE 0 END) AS saque_h
        FROM {TBL('payment')} p
        WHERE
            {filtro_basico()}
            AND p.create_time >= :start_utc
            AND p.create_time <  :end_utc
        GROUP BY DATE(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}')), HOUR(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}'))
        ORDER BY data_brt ASC, hora_brt ASC
    """)
def query_top30_saques_diarios():
    return dedent(f"""
        WITH saques AS (
            SELECT
                p.client_id,
                DATE(CONVERT_TZ(p.create_time,'UTC','{BRT_TZ}')) AS data_brt,
                p.amount/100.0 AS valor_saque
            FROM {TBL('payment')} p
            WHERE
                {filtro_basico()}
                AND p.operation_type LIKE 'withdr%%'
                AND p.create_time >= :start_utc
                AND p.create_time <  :end_utc
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
    """)

def query_top_ids_valor(tipo="saque"):
    op = "withdr%%" if tipo == "saque" else "depos%%"
    return dedent(f"""
        SELECT
            p.client_id AS id_do_cliente,
            SUM(p.amount/100.0) AS total_valor,
            COUNT(*) AS qtd_ops
        FROM {TBL('payment')} p
        WHERE
            {filtro_basico()}
            AND p.operation_type LIKE '{op}'
            AND p.create_time >= :start_utc
            AND p.create_time <  :end_utc
        GROUP BY p.client_id
        ORDER BY total_valor DESC
        LIMIT 30
    """)

def query_top_ids_qtd(tipo="saque"):
    op = "withdr%%" if tipo == "saque" else "depos%%"
    return dedent(f"""
        SELECT
            p.client_id AS id_do_cliente,
            COUNT(*) AS qtd_ops,
            SUM(p.amount/100.0) AS total_valor
        FROM {TBL('payment')} p
        WHERE
            {filtro_basico()}
            AND p.operation_type LIKE '{op}'
            AND p.create_time >= :start_utc
            AND p.create_time <  :end_utc
        GROUP BY p.client_id
        ORDER BY qtd_ops DESC
        LIMIT 30
    """)
