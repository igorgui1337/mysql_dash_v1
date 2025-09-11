# Dash de Monitoramento

Dashboard Streamlit conectado ao MySQL (Kinghost), lendo `payment` e exibindo KPIs, gráficos e rankings.

## Requisitos
- Python 3.10+
- MySQL/MariaDB acessível
- `.env` com credenciais e nome do database

## Instalação
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
