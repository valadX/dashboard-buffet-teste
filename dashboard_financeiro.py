import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
import plotly.express as px
from datetime import date, timedelta
import calendar
import re
import os # <-- ADICIONADO para checar se o arquivo .json existe localmente

# --- Configurações Iniciais do Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro Buffet")

# Initialize session state for calendar month/year
if 'current_calendar_month' not in st.session_state:
    st.session_state['current_calendar_month'] = date.today().month
if 'current_calendar_year' not in st.session_state:
    st.session_state['current_calendar_year'] = date.today().year

# Initialize session state for finance tab month/year selector
if 'finance_selected_month' not in st.session_state:
    st.session_state['finance_selected_month'] = date.today().month
if 'finance_selected_year' not in st.session_state:
    st.session_state['finance_selected_year'] = date.today().year

# --- Customização de Cores e Estilo via CSS ---
# (Seu CSS original, mantido intacto)
st.markdown(
    """
    <style>
    /* Estilos Globais e Fundo Principal - Forçando a cor roxa */
    html, body {
        background-color: #7F6C9F !important;
        font-family: 'Inter', sans-serif;
    }
    /* Streamlit main app containers */
    [data-testid="stAppViewContainer"] {
        background-color: #7F6C9F !important;
    }
    /* Adicional seletor para garantir o fundo roxo em áreas específicas */
    .stApp, section.main, [data-testid="stVerticalBlock"] > div {
        background-color: #7F6C9F !important;
    }
    .st-emotion-cache-z5fcl4 { /* Common global container in Streamlit */
        background-color: #7F6C9F !important;
    }

    /* Cor do texto padrão para elementos que aparecem sobre o fundo roxo principal */
    p, .stMarkdown, label, a, li, .stText {
        color: #F0F0F0 !important; /* Cinza Claro para contraste com o fundo roxo */
    }

    /* Sidebar */
    [data-testid="stSidebar"] { /* More direct selector for the sidebar itself */
        background-color: #6D5A92 !important; /* Roxo um pouco mais escuro para a sidebar */
        padding: 20px;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label { /* Ensure all text within sidebar is light */
        color: #F0F0F0 !important;
    }
    /* Ajusta a cor do label do selectbox na sidebar */
    .st-bw .st-cb { /* Combobox */
        color: #F0F0F0 !important;
    }


    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important; /* Branco para todos os títulos */
    }
    /* Cor para o ícone de dashboard no título (se for SVG ou parte do texto) */
    .st-emotion-cache-1r7r3h0 { /* Seletor para o ícone do título principal (pode variar) */
        color: #FF7F00 !important; /* Laranja para o ícone */
    }


    /* Botões */
    .stButton>button {
        background-color: #4CAF50 !important; /* Verde */
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049 !important; /* Verde mais escuro no hover */
    }

    /* Métricas (KPIs) */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important; /* Fundo branco das caixas de métrica */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Rótulo da Métrica - O MAIS IMPORTANTE PARA LEGIBILIDADE */
    /* Target any text inside the metric label to ensure it's black */
    [data-testid="stMetricLabel"] *, [data-testid="stMetricLabel"] {
        color: #000000 !important; /* PRETO para o rótulo para alta legibilidade */
        font-weight: bold;
    }
    /* Valor da Métrica */
    [data-testid="stMetricValue"] {
        color: #FF7F00 !important; /* Laranja para o valor principal */
        font-size: 2.5em;
    }
    /* Delta da Métrica (se aplicável) */
    [data-testid="stMetricDelta"] {
        color: #4CAF50 !important; /* Verde para variação */
    }


    /* Expander e Mensagens de Alerta */
    .streamlit-expander {
        background-color: #EBE6F3 !important; /* Roxo claro */
        border-radius: 10px;
        border: 1px solid #D1C4E9;
    }
    .streamlit-expanderHeader {
        color: #2C3E50 !important; /* Texto escuro para o título do expander */
        font-weight: bold;
    }
    .streamlit-expanderContent p, .streamlit-expanderContent div, .streamlit-expanderContent span { /* Garante texto legível dentro do expander */
        color: #333333 !important;
    }

    .st.info, .st.warning, .st.error {
        border-radius: 8px;
    }
    .st.info { background-color: #E6F7FF !important; border-color: #91D5FF !important; color: #333333 !important;}
    .st.warning { background-color: #FFFBE6 !important; border-color: #FFE58F !important; color: #333333 !important;}
    .st.error { background-color: #FFF0F0 !important; border-color: #FF7875 !important; color: #333333 !important;}

    /* Estilo das Tabelas (Dataframes) */
    .dataframe {
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        background-color: #FFFFFF !important; /* Fundo branco */
    }
    .dataframe th { /* Cabeçalho da Tabela */
        background-color: #D1C4E9 !important; /* Roxo claro */
        color: #2C3E50 !important; /* Texto escuro */
        font-weight: bold;
    }
    /* Cor da letra da tabela de detalhes dos contratos (sobrepõe o padrão) */
    .stDataFrame table td {
        color: #000000 !important; /* PRETO para o texto das células da tabela */
    }
    /* Adicionei esta regra para garantir que o texto dentro das células da tabela seja preto */
    .stDataFrame table tbody tr td {
        color: #000000 !important;
    }
    .dataframe td { /* Células da Tabela (mantém este seletor para outros usos ou fallback) */
        color: #333333 !important; /* Texto escuro para as células (pode ser sobreposto pelo .stDataFrame table td) */
    }

    /* Estilos dos Gráficos Plotly */
    .js-plotly-plot .plotly .modebar {
        background-color: rgba(255, 255, 255, 0.7) !important; /* Fundo semi-transparente para o modebar */
        color: #333333 !important; /* Cor do texto no modebar */
    }
    .js-plotly-plot .plotly .modebar-btn {
        color: #333333 !important; /* Cor dos botões do modebar */
    }
    .js-plotly-plot .plotly .modebar-btn.active {
        color: #6D5A92 !important; /* Cor dos botões ativos do modebar */
    }


    /* Estilos do Calendário */
    .calendar-container {
        display: flex;
        justify-content: center; /* Centraliza o conteúdo do calendário */
        width: 100%;
    }
    .calendar {
        width: 100%;
        max-width: 800px; /* Limite a largura para melhor visualização */
        font-family: 'Inter', sans-serif;
        border-collapse: collapse;
        text-align: center;
        background-color: white !important;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .calendar th {
        background-color: #f2f2f2 !important;
        padding: 10px;
        border: 1px solid #ddd;
        color: #333333 !important;
    }
    .calendar td {
        padding: 10px;
        border: 1px solid #ddd;
        min-height: 80px;
        vertical-align: top;
        color: #333333 !important;
    }
    .calendar .month { /* This class is no longer used for the month name, but kept for consistency */
        font-size: 1.5em;
        font-weight: bold;
        padding: 15px;
        background-color: #6D5A92 !important;
        color: white !important;
        border-bottom: 2px solid #5A4982;
    }
    .calendar .day, .calendar .sat, .calendar .sun { /* Apply these to all valid days */
        background-color: #f9f9f9 !important;
        min-height: 80px;
    }
    .calendar .sat, .calendar .sun {
        background-color: #EBE6F3 !important;
    }
    .calendar .noday {
        background-color: #e6e6e6 !important;
        color: #aaaaaa !important;
    }
    .calendar table {
            width: 100%;
        }
    /* Destaque para o dia atual no calendário */
    .calendar .today {
        background-color: #ADD8E6 !important; /* Azul claro */
        border: 2px solid #4682B4 !important; /* Borda azul mais escura */
        font-weight: bold;
    }

    /* Estilos para a legenda do calendário */
    .calendar-legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
        color: #333333 !important;
    }
    .calendar-legend-color {
        width: 15px;
        height: 15px;
        border-radius: 50%;
        margin-right: 8px;
        border: 1px solid #ccc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Google Sheets Initialization (MODIFICADO) ---

# Nome do seu arquivo JSON local
# IMPORTANTE: Este nome DEVE ser o mesmo do arquivo que está na sua pasta
# e que também está no seu .gitignore
SERVICE_ACCOUNT_FILE = 'poetic-chariot-476818-f5-b6a7fda3268f.json'

# Use st.cache_resource for the gspread client as it's a resource
@st.cache_resource(ttl=3600) # Cache por 1 hora
def connect_to_gspread():
    """
    Conecta ao Google Sheets usando st.secrets (produção) 
    ou um arquivo .json local (desenvolvimento).
    """
    try:
        # 1. Tenta usar o Streamlit Secrets (quando está na nuvem)
        # O [gcp_service_account] é o nome da "seção" que você colou no Secrets
        if "gcp_service_account" in st.secrets:
            creds = st.secrets["gcp_service_account"]
            gc = gspread.service_account_from_dict(creds)
            return gc
        
        # 2. Tenta usar o arquivo .json local (quando está no seu PC)
        elif os.path.exists(SERVICE_ACCOUNT_FILE):
            gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
            return gc
            
        # 3. Se nenhum funcionar
        else:
            st.error(f"Erro: O arquivo de credenciais '{SERVICE_ACCOUNT_FILE}' não foi encontrado.")
            st.error("Por favor, verifique se o arquivo está na mesma pasta do script ou se o st.secrets está configurado no Streamlit Cloud.")
            st.stop()
            
    except Exception as e:
        st.error(f"Erro ao carregar as credenciais do Google Sheets: {e}")
        st.stop()

# Chama a função de conexão
gc = connect_to_gspread()

# Adiciona uma verificação de sucesso na barra lateral
if gc:
    st.sidebar.success("Conexão com Google Sheets estabelecida!")
else:
    st.error("Falha ao estabelecer conexão com Google Sheets.")
    st.stop()
    
# --- Funções Auxiliares de Processamento de Dados ---
# (Seu código original, mantido intacto)

def clean_currency_to_float(series):
    """Limpa e converte valores monetários para float."""
    series_str = series.astype(str).str.strip()
    series_str = series_str.str.replace(r'<\w+ ?\w+>', '', regex=True)
    series_str = series_str.str.replace('NaN', '', regex=False)
    series_str = series_str.str.replace('None', '', regex=False)
    series_str = series_str.str.replace(r'=.*', '', regex=True)

    cleaned_series = series_str.str.replace('.', '', regex=False)
    cleaned_series = cleaned_series.str.replace(',', '.', regex=False)
    cleaned_series = cleaned_series.str.replace('R$', '', regex=False).str.strip()

    return pd.to_numeric(cleaned_series, errors='coerce').fillna(0)

def normalize_contract_number(contract_series):
    """Normaliza o número do contrato, removendo caracteres não numéricos do início."""
    contract_series_str = contract_series.astype(str).str.strip()
    return contract_series_str.apply(lambda x: re.sub(r'^\D*', '', x))

def format_currency(value):
    """Formata um valor numérico para o formato de moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Função Principal para Carregar e Processar os Dados ---
@st.cache_data(ttl=600)
def load_and_process_data():
    """
    Carrega dados de contratos e pagamentos do Google Sheets,
    processa, limpa e mescla-os para criar o dataframe final.
    """
    global gc # Garante que estamos usando o cliente 'gc' global conectado
    
    with st.spinner("Carregando e processando dados das planilhas..."):

        # --- Carregar Planilha de Contratos NOVOS (Google Forms) ---
        df_novos_contratos = pd.DataFrame()
        try:
            spreadsheet_novos_contratos_name = "Contrato Alegria (respostas)"
            worksheet_novos_contratos_name = "Respostas ao formulário 1"

            spreadsheet_novos_contratos = gc.open(spreadsheet_novos_contratos_name)
            worksheet_novos_contratos = spreadsheet_novos_contratos.worksheets()[0]

            data_novos = worksheet_novos_contratos.get_all_values()

            if not data_novos or len(data_novos) < 2:
                st.warning(f"Aviso: Planilha '{spreadsheet_novos_contratos_name}' (aba '{worksheet_novos_contratos_name}') está vazia ou contém apenas cabeçalhos.")
                df_novos_contratos = pd.DataFrame(columns=['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Valor Total', 'Valor Total Pago na Conta', 'Data Fechamento'])
            else:
                df_novos_contratos = pd.DataFrame(data_novos[1:], columns=data_novos[0])
                df_novos_contratos.columns = df_novos_contratos.columns.str.strip()

                col_map_novos = {
                    'Numero do contrato': 'Numero Contrato',
                    'Nome completo': 'Nome Cliente',
                    'Data da festa': 'Data Festa',
                    'Valor total do contrato': 'Valor Total',
                    'Carimbo de data/hora': 'Data Fechamento' # Adicionado o campo de data de fechamento
                }

                for old_col, new_col in col_map_novos.items():
                    if old_col not in df_novos_contratos.columns:
                        st.error(f"Erro Crítico: Coluna esperada '{old_col}' NÃO encontrada na planilha '{spreadsheet_novos_contratos_name}' (aba '{worksheet_novos_contratos_name}'). Verifique o nome da coluna no seu Forms/Planilha.")
                        st.stop()

                df_novos_contratos = df_novos_contratos.rename(columns=col_map_novos)

                df_novos_contratos['Valor Total'] = clean_currency_to_float(df_novos_contratos['Valor Total'])
                df_novos_contratos['Valor Total Pago na Conta'] = 0
                df_novos_contratos['Numero Contrato'] = normalize_contract_number(df_novos_contratos['Numero Contrato'])
                # Converte 'Data Fechamento' para datetime com formato explícito
                df_novos_contratos['Data Fechamento'] = pd.to_datetime(df_novos_contratos['Data Fechamento'], format='%d/%m/%Y %H:%M:%S', errors='coerce')


        except Exception as e:
            st.error(f"Erro ao carregar a planilha de Contratos NOVOS ('{spreadsheet_novos_contratos_name}' - aba '{worksheet_novos_contratos_name}'):")
            st.error(f"Detalhes do erro: {e}")
            st.error("Verifique: 1. Nomes da planilha/aba. 2. Permissões de compartilhamento. 3. Nomes das colunas no bloco 'col_map_novos' conforme sua planilha (ATENÇÃO A ESPAÇOS E CARACTERES OCULTOS).")
            st.stop()


        # --- Carregar Planilha de Contratos ANTIGOS (da sua planilha de gestão) ---
        df_antigos_contratos = pd.DataFrame()
        try:
            spreadsheet_gestao_name = "Planilha sem título"
            spreadsheet_gestao = gc.open(spreadsheet_gestao_name)
            worksheet_antigos_contratos = spreadsheet_gestao.worksheet("Contratos")

            data_antigos = worksheet_antigos_contratos.get_all_values()

            if not data_antigos or len(data_antigos) < 2:
                st.warning(f"Aviso: Planilha '{spreadsheet_gestao_name}' (aba 'Contratos') está vazia ou contém apenas cabeçalhos.")
                df_antigos_contratos = pd.DataFrame(columns=['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Valor Total', 'Valor Total Pago na Conta', 'Data Fechamento'])
            else:
                df_antigos_contratos = pd.DataFrame(data_antigos[1:], columns=data_antigos[0])
                df_antigos_contratos.columns = df_antigos_contratos.columns.str.strip()

                col_map_antigos = {
                    'N.º contrato': 'Numero Contrato',
                    'Data Festa': 'Data Festa',
                    'Valor Contrato': 'Valor Total',
                    'Valor recebido': 'Valor Total Pago na Conta',
                }

                for old_col, new_col in col_map_antigos.items():
                    if old_col not in df_antigos_contratos.columns:
                        st.error(f"Erro Crítico: Coluna esperada '{old_col}' NÃO encontrada na planilha '{spreadsheet_gestao_name}' (aba 'Contratos'). Verifique o nome da coluna na sua planilha.")
                        st.stop()

                df_antigos_contratos = df_antigos_contratos.rename(columns=col_map_antigos)

                df_antigos_contratos['Valor Total'] = clean_currency_to_float(df_antigos_contratos['Valor Total'])
                df_antigos_contratos['Valor Total Pago na Conta'] = clean_currency_to_float(df_antigos_contratos['Valor Total Pago na Conta'])
                df_antigos_contratos['Numero Contrato'] = normalize_contract_number(df_antigos_contratos['Numero Contrato'])
                # Para contratos antigos, não há 'Carimbo de data/hora', então preenche com NaT
                df_antigos_contratos['Data Fechamento'] = pd.NaT


        except Exception as e:
            st.error(f"Erro ao carregar a planilha de Contratos ANTIGOS ('{spreadsheet_gestao_name}' - aba 'Contratos'):")
            st.error(f"Detalhes do erro: {e}")
            st.error("Verifique: 1. Nomes da planilha/aba. 2. Permissões de compartilhamento. 3. Nomes das colunas no bloco 'col_map_antigos' conforme sua planilha.")
            st.info("O dashboard tentará carregar com dados incompletos dos pagamentos.")
            df_antigos_contratos = pd.DataFrame(columns=['Numero Contrato', 'Valor Total', 'Valor Total Pago na Conta', 'Data Fechamento'])


        # --- Combinar Todos os Contratos (Novos + Antigos) ---
        common_cols_for_concat = ['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Valor Total', 'Valor Total Pago na Conta', 'Data Fechamento']

        for col in common_cols_for_concat:
            if col not in df_novos_contratos.columns:
                df_novos_contratos[col] = pd.NA
            if col not in df_antigos_contratos.columns:
                df_antigos_contratos[col] = pd.NA


        df_todos_contratos = pd.concat(
            [
                df_novos_contratos[common_cols_for_concat],
                df_antigos_contratos[common_cols_for_concat]
            ],
            ignore_index=True
        )

        df_todos_contratos['Nome Cliente'] = df_todos_contratos['Nome Cliente'].astype(str).fillna('').str.strip()


        df_todos_contratos['Numero Contrato'] = df_todos_contratos['Numero Contrato'].astype(str).str.strip()
        df_todos_contratos = df_todos_contratos[df_todos_contratos['Numero Contrato'] != ''].copy()
        df_todos_contratos = df_todos_contratos.dropna(subset=['Numero Contrato']).copy()

        duplicados = df_todos_contratos[df_todos_contratos.duplicated(subset=['Numero Contrato'], keep=False)]
        if not duplicados.empty:
            st.warning(f"Atenção: Foram encontrados {len(duplicados['Numero Contrato'].unique())} Números de Contrato duplicados no conjunto total APÓS NORMALIZAÇÃO. Isso pode causar problemas nos cálculos. Duplicados: {duplicados['Numero Contrato'].unique()}")


        # --- Carregar Planilha de PAGAMENTOS (da sua planilha de gestão) ---
        df_pagamentos = pd.DataFrame()
        worksheet_pagamentos_name = "Pagamentos"
        try:
            spreadsheet_gestao_name = "Planilha sem título"
            spreadsheet_gestao = gc.open(spreadsheet_gestao_name)
            worksheet_pagamentos = spreadsheet_gestao.worksheet(worksheet_pagamentos_name)

            data_pagamentos = worksheet_pagamentos.get_all_values()

            if not data_pagamentos or len(data_pagamentos) < 2:
                st.warning(f"Aviso: Planilha '{spreadsheet_gestao_name}' (aba '{worksheet_pagamentos_name}') está vazia ou contém apenas cabeçalhos.")
                df_pagamentos = pd.DataFrame(columns=['Numero Contrato', 'Valor Parcial Pago', 'Data Pagamento'])
            else:
                df_pagamentos = pd.DataFrame(data_pagamentos[1:], columns=data_pagamentos[0])
                df_pagamentos.columns = df_pagamentos.columns.str.strip()

                col_map_pagamentos = {
                    'N.º Contrato': 'Numero Contrato',
                    'Valor recebido': 'Valor Parcial Pago',
                    'Data Pagamento': 'Data Pagamento'
                }

                original_date_col_name = 'Data Pagamento'
                if original_date_col_name not in df_pagamentos.columns:
                    st.error(
                        f"🚨 ERRO CRÍTICO: A coluna '{original_date_col_name}' não foi encontrada na aba '{worksheet_pagamentos_name}'. "
                        f"Por favor, verifique o nome EXATO da coluna na sua planilha. "
                        f"As colunas disponíveis são: {df_pagamentos.columns.tolist()}. "
                        f"O dashboard continuará, mas a seção 'Fluxo de Caixa Realizado' pode estar incompleta."
                    )
                    df_pagamentos['Data Pagamento'] = pd.NaT

                df_pagamentos = df_pagamentos.rename(columns=col_map_pagamentos)

                df_pagamentos['Numero Contrato'] = df_pagamentos['Numero Contrato'].astype(str)
                df_pagamentos['Numero Contrato'] = normalize_contract_number(df_pagamentos['Numero Contrato'])

                df_pagamentos['Valor Parcial Pago'] = clean_currency_to_float(df_pagamentos['Valor Parcial Pago'])
                df_pagamentos['Data Pagamento'] = pd.to_datetime(df_pagamentos['Data Pagamento'], format='%d/%m/%Y', errors='coerce')


        except Exception as e:
            st.error(f"Erro ao carregar a aba de Pagamentos ('{worksheet_pagamentos_name}'):")
            st.error(f"Detalhes do erro: {e}")
            st.error("Verifique: 1. Nome da aba. 2. Permissões de compartilhamento. 3. Nomes das colunas no bloco 'col_map_pagamentos' conforme sua planilha (ATENÇÃO A ESPAÇOS E CARACTERES OCULTOS).")
            st.info("O dashboard tentará carregar com dados incompletos dos pagamentos.")
            df_pagamentos = pd.DataFrame(columns=['Numero Contrato', 'Valor Parcial Pago', 'Data Pagamento'])

        # --- Removida a parte de Carregar Planilha de CUSTOS (NOVA ABA) ---
        # df_custos = pd.DataFrame() # Não carregamos mais df_custos aqui


        # --- Unir e Processar os Dados (Contratos + Pagamentos) ---

        df_pagamentos_agrupado = df_pagamentos.groupby('Numero Contrato')['Valor Parcial Pago'].sum().reset_index()
        df_pagamentos_agrupado.rename(columns={'Valor Parcial Pago': 'Soma Pagamentos Avulsos'}, inplace=True)

        # --- Removida a lógica de separar custos diretos e gerais ---
        # df_custos_diretos = df_custos[df_custos['Numero Contrato'].apply(lambda x: x != '' and not x.startswith('GERAL'))].copy()
        # df_custos_gerais = df_custos[df_custos['Numero Contrato'].apply(lambda x: x == '' or x.startswith('GERAL'))].copy()

        # df_custos_diretos_agrupado = df_custos_diretos.groupby('Numero Contrato')['Valor Custo'].sum().reset_index()
        # df_custos_diretos_agrupado.rename(columns={'Valor Custo': 'Custo Direto por Festa'}, inplace=True)


        df_final = pd.merge(df_todos_contratos, df_pagamentos_agrupado, on='Numero Contrato', how='left')
        # --- Removida a linha de merge com custos diretos ---
        # df_final = pd.merge(df_final, df_custos_diretos_agrupado, on='Numero Contrato', how='left')

        df_final['Valor Total Pago na Conta'] = df_final['Soma Pagamentos Avulsos'].fillna(0)
        # --- Removida a linha de preenchimento de Custo Direto por Festa ---
        # df_final['Custo Direto por Festa'] = df_final['Custo Direto por Festa'].fillna(0)

        df_final['Valor a Pagar'] = df_final['Valor Total'] - df_final['Valor Total Pago na Conta']

        # --- Removida a linha de cálculo de Lucro Bruto ---
        # df_final['Lucro Bruto por Festa'] = df_final['Valor Total'] - df_final['Custo Direto por Festa']


        def get_status_pagamento(row):
            if row['Valor Total'] <= 0:
                return 'Não Aplicável'
            elif row['Valor a Pagar'] <= 0:
                return 'Pago Integralmente'
            elif row['Valor Total Pago na Conta'] > 0 and row['Valor a Pagar'] > 0:
                return 'Pagamento Parcial'
            else:
                return 'Aberto'
        df_final['Status Pagamento Festa'] = df_final.apply(get_status_pagamento, axis=1)

        hoje = pd.to_datetime('today').date()

        # Convert 'Data Festa' and handle errors
        df_final['Data Festa'] = pd.to_datetime(df_final['Data Festa'], format='%d/%m/%Y', errors='coerce')

        # Check for NaT values after conversion and warn the user
        initial_rows_df_final = df_final.shape[0]
        df_final_cleaned_dates = df_final.dropna(subset=['Data Festa']).copy()
        rows_with_nan_dates = initial_rows_df_final - df_final_cleaned_dates.shape[0]
        if rows_with_nan_dates > 0:
            st.warning(f"⚠️ Atenção: {rows_with_nan_dates} contrato(s) foram excluídos porque a 'Data Festa' não pôde ser convertida para uma data válida (formato esperado: DD/MM/AAAA). Por favor, verifique as datas nas suas planilhas.")
        df_final = df_final_cleaned_dates


        df_final['Status Festa'] = df_final['Data Festa'].apply(
            lambda d: 'Realizada' if pd.notna(d) and d.date() < hoje else 'Agendada'
        )

        df_final['Numero Contrato'] = df_final['Numero Contrato'].astype(str).str.strip()
        df_final = df_final[df_final['Numero Contrato'] != ''].copy()
        df_final = df_final.dropna(subset=['Numero Contrato']).copy()

    return df_final, df_pagamentos # Não retorna mais df_custos

# --- Funções de Renderização de Componentes da UI ---
# (Seu código original, mantido intacto)

def render_kpis(df_filtered, page_type):
    """Exibe os KPIs principais do dashboard de forma mais responsiva."""
    st.markdown("---")
    if not df_filtered.empty:
        # **MELHORIA DE RESPONSIVIDADE**: KPIs são agrupados em linhas para melhor visualização em telas pequenas.
        kpi_cols_1 = st.columns(3)
        kpi_cols_1[0].metric(label=f"Total de Contratos {page_type}", value=df_filtered.shape[0])
        kpi_cols_1[1].metric(label=f"Valor Total Contratado ({page_type})", value=format_currency(df_filtered['Valor Total'].sum()))
        avg_contract_value = df_filtered['Valor Total'].mean() if not df_filtered['Valor Total'].empty else 0
        kpi_cols_1[2].metric(label=f"Receita Média por Contrato ({page_type})", value=format_currency(avg_contract_value))

        kpi_cols_2 = st.columns(2)
        kpi_cols_2[0].metric(label=f"Valor Já Recebido ({page_type})", value=format_currency(df_filtered['Valor Total Pago na Conta'].sum()))
        kpi_cols_2[1].metric(label=f"Valor Total a Receber ({page_type})", value=format_currency(df_filtered['Valor a Pagar'].sum()))

        st.markdown("---")
        
        kpi_cols_3 = st.columns(3)
        kpi_cols_3[0].metric(label=f"Contratos Pagos Integralmente ({page_type})", value=df_filtered[df_filtered['Status Pagamento Festa'] == 'Pago Integralmente'].shape[0])
        kpi_cols_3[1].metric(label=f"Contratos com Pagamento Parcial ({page_type})", value=df_filtered[df_filtered['Status Pagamento Festa'] == 'Pagamento Parcial'].shape[0])
        kpi_cols_3[2].metric(label=f"Contratos com Pagamento Aberto ({page_type})", value=df_filtered[df_filtered['Status Pagamento Festa'] == 'Aberto'].shape[0])
    else:
        st.warning(f"Nenhum dado de contrato {page_type} encontrado. Verifique suas planilhas e as configurações no código.")

def render_weekly_summary(df_contracts_agendadas):
    """
    Exibe um resumo das festas agendadas para a próxima semana,
    com destaque para hoje e o próximo sábado.
    """
    st.markdown("---")
    st.header("✨ Assistente Semanal de Festas Agendadas")

    today = pd.to_datetime('today').date()
    # Define the end of the next 8 days (inclusive, from today to next 7 days)
    end_of_next_8_days = today + timedelta(days=7) # 7 days from today makes it 8 days total (today + 7 more)

    # Filter contracts for the next 8 days
    df_next_8_days = df_contracts_agendadas[
        (df_contracts_agendadas['Data Festa'].dt.date >= today) &
        (df_contracts_agendadas['Data Festa'].dt.date <= end_of_next_8_days)
    ].copy()

    if df_next_8_days.empty:
        st.info("🎉 Parabéns! Nenhuma festa agendada para os próximos 8 dias.")
        return

    # Summary for the next 8 days
    total_contracts_next_8_days = df_next_8_days.shape[0]
    total_value_next_8_days = df_next_8_days['Valor Total'].sum()
    total_to_receive_next_8_days = df_next_8_days['Valor a Pagar'].sum()

    st.info(f"**Visão Geral dos Próximos 8 Dias (até {end_of_next_8_days.strftime('%d/%m/%Y')}):**\n"
            f"- Você tem **{total_contracts_next_8_days}** festa(s) agendada(s).\n"
            f"- Valor total contratado: **{format_currency(total_value_next_8_days)}**.\n"
            f"- Valor ainda a receber: **{format_currency(total_to_receive_next_8_days)}**.")

    with st.expander("Ver detalhes do resumo semanal"):
        # Details for Today
        df_today = df_next_8_days[df_next_8_days['Data Festa'].dt.date == today].copy() # Added .copy()
        if not df_today.empty:
            st.subheader(f"Hoje ({today.strftime('%d/%m/%Y')}):")
            st.write(f"Você tem **{df_today.shape[0]}** festa(s) agendada(s) para hoje.")
            st.write(f"Valor a receber hoje: **{format_currency(df_today['Valor a Pagar'].sum())}**.")

            # Apply currency formatting before displaying
            df_display_today = df_today.copy()
            df_display_today['Valor Total'] = df_display_today['Valor Total'].apply(format_currency)
            df_display_today['Valor a Pagar'] = df_display_today['Valor a Pagar'].apply(format_currency)

            st.dataframe(df_display_today[['Nome Cliente', 'Numero Contrato', 'Valor Total', 'Valor a Pagar', 'Status Pagamento Festa']].style.apply(
                lambda r: ['background-color: #e6ffe6; color: #000000;' if r['Status Pagamento Festa'] == 'Pago Integralmente' else
                           'background-color: #fffacd; color: #000000;' if r['Status Pagamento Festa'] == 'Pagamento Parcial' else
                           'background-color: #ffe6e6; color: #000000;' for _ in r], axis=1
            ), use_container_width=True)
        else:
            st.write(f"Nenhuma festa agendada para hoje ({today.strftime('%d/%m/%Y')}).")

        # Removida a seção do "Próximo Sábado" conforme solicitado.

        # Details for all contracts in the next 8 days
        st.subheader("Todos os Contratos no Período do Assistente Semanal:")
        if not df_next_8_days.empty:
            df_display_next_8_days = df_next_8_days.copy()
            df_display_next_8_days['Data Festa'] = df_display_next_8_days['Data Festa'].dt.strftime('%d/%m/%Y')
            df_display_next_8_days['Valor Total'] = df_display_next_8_days['Valor Total'].apply(format_currency)
            df_display_next_8_days['Valor a Pagar'] = df_display_next_8_days['Valor a Pagar'].apply(format_currency)

            st.dataframe(df_display_next_8_days[['Nome Cliente', 'Numero Contrato', 'Data Festa', 'Valor Total', 'Valor a Pagar', 'Status Pagamento Festa']].style.apply(
                lambda r: ['background-color: #e6ffe6; color: #000000;' if r['Status Pagamento Festa'] == 'Pago Integralmente' else
                           'background-color: #fffacd; color: #000000;' if r['Status Pagamento Festa'] == 'Pagamento Parcial' else
                           'background-color: #ffe6e6; color: #000000;' for _ in r], axis=1
            ), use_container_width=True)
        else:
            st.write("Nenhum contrato encontrado para o período do Assistente Semanal.")


def render_alerts(df_filtered, page_type):
    """Exibe avisos e alertas importantes sobre os dados, ajustados pelo tipo de página."""
    st.markdown("---")
    st.header("🔔 Avisos Importantes")
    if page_type == 'Agendadas':
        contratos_sem_data_festa = df_filtered[df_filtered['Data Festa'].isna()]
        if not contratos_sem_data_festa.empty:
            st.warning(f"⚠️ Atenção! {len(contratos_sem_data_festa)} contrato(s) sem 'Data Festa' definida. Isso afeta o cálculo do 'Status Festa'.")
            with st.expander("Ver detalhes dos contratos sem data"):
                st.dataframe(contratos_sem_data_festa[['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Status Festa']])
    elif page_type == 'Realizadas':
        hoje = pd.to_datetime('today').date()
        contratos_vencidos_a_pagar = df_filtered[(df_filtered['Status Festa'] == 'Realizada') & (df_filtered['Valor a Pagar'] > 0)]
        if not contratos_vencidos_a_pagar.empty:
            st.error(f"🚨 Alerta Crítico! {len(contratos_vencidos_a_pagar)} contrato(s) com festas já realizadas e 'Valor a Pagar' pendente.")
            with st.expander("Ver detalhes dos contratos vencidos e pendentes"):
                st.dataframe(contratos_vencidos_a_pagar[['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Valor Total', 'Valor Total Pago na Conta', 'Valor a Pagar', 'Status Pagamento Festa']])

def render_contract_details(df_contracts, page_type):
    """Exibe a tabela detalhada de contratos com filtros, ajustados pelo tipo de página."""
    st.markdown("---")
    st.header(f"📝 Detalhes dos Contratos ({page_type})")

    # Filter df_contracts based on page_type before applying date filters
    if page_type == 'Agendadas':
        df_base_filter = df_contracts[df_contracts['Status Festa'] == 'Agendada'].copy()
    elif page_type == 'Realizadas':
        df_base_filter = df_contracts[df_contracts['Status Festa'] == 'Realizada'].copy()
    else: # Should not happen with selectbox, but as a fallback
        df_base_filter = df_contracts.copy()

    st.sidebar.header(f"Filtros de Período ({page_type})")
    min_date = df_base_filter['Data Festa'].min().date() if not df_base_filter['Data Festa'].empty and pd.notna(df_base_filter['Data Festa'].min()) else date(2020, 1, 1)
    max_date = df_base_filter['Data Festa'].max().date() if not df_base_filter['Data Festa'].empty and pd.notna(df_base_filter['Data Festa'].max()) else date(2030, 12, 31)

    data_inicio, data_fim = st.sidebar.date_input(
        "Filtrar por Data da Festa:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        key=f'date_filter_{page_type}' # Unique key for each page
    )
    if data_inicio > data_fim:
        st.sidebar.error("A data de início não pode ser maior que a data de fim.")
        data_inicio = data_fim

    st.sidebar.header(f"Outros Filtros ({page_type})")
    status_pagamento_options = sorted(df_base_filter['Status Pagamento Festa'].unique().tolist()) if not df_base_filter.empty else []
    # No need for status_festa_options as it's already filtered by page_type

    filtro_status_pagamento = st.sidebar.multiselect(
        "Filtrar por Status de Pagamento:",
        options=status_pagamento_options,
        default=status_pagamento_options,
        key=f'payment_status_filter_{page_type}' # Unique key
    )

    df_filtrado = df_base_filter[
        (df_base_filter['Data Festa'].dt.date >= data_inicio) &
        (df_base_filter['Data Festa'].dt.date <= data_fim) &
        (df_base_filter['Status Pagamento Festa'].isin(filtro_status_pagamento))
    ].sort_values(by='Data Festa', ascending=True)

    if not df_filtrado.empty:
        df_display = df_filtrado.copy()
        df_display['Data Festa'] = df_display['Data Festa'].dt.strftime('%d/%m/%Y')
        df_display['Valor Total'] = df_display['Valor Total'].apply(format_currency)
        df_display['Valor Total Pago na Conta'] = df_display['Valor Total Pago na Conta'].apply(format_currency)
        df_display['Valor a Pagar'] = df_display['Valor a Pagar'].apply(format_currency)
        # Removidas as linhas de formatação de custo e lucro
        # df_display['Custo Direto por Festa'] = df_display['Custo Direto por Festa'].apply(format_currency)
        # df_display['Lucro Bruto por Festa'] = df_display['Lucro Bruto por Festa'].apply(format_currency)


        def highlight_payment_status(row):
            styles = [''] * len(row)
            bg_color = ''
            if row['Status Pagamento Festa'] == 'Pago Integralmente':
                bg_color = '#e6ffe6'
            elif row['Status Pagamento Festa'] == 'Pagamento Parcial':
                bg_color = '#fffacd'
            elif row['Status Pagamento Festa'] == 'Aberto':
                bg_color = '#ffe6e6'
            text_color = '#000000' # Definir a cor do texto para preto
            for i in range(len(row)):
                styles[i] = f'background-color: {bg_color}; color: {text_color};'
            return styles

        st.dataframe(
            df_display[[
                'Numero Contrato', 'Nome Cliente', 'Data Festa',
                'Valor Total', 'Valor Total Pago na Conta', 'Valor a Pagar',
                # Removidas as colunas de custo e lucro
                # 'Custo Direto por Festa', 'Lucro Bruto por Festa',
                'Status Pagamento Festa', 'Status Festa'
            ]].style.apply(highlight_payment_status, axis=1),
            use_container_width=True
        )
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📅 Baixar dados filtrados ({page_type}) (CSV)",
            data=csv,
            file_name=f"contratos_{page_type.lower()}_filtrados.csv",
            mime="text/csv",
        )
    else:
        st.info(f"Nenhum contrato {page_type} encontrado com os filtros selecionados. Altere os filtros na barra lateral.")

def render_future_cash_flow(df_contracts_agendadas):
    """Exibe a previsão de fluxo de caixa futuro para contratos agendados."""
    st.markdown("---")
    st.header("💰 Previsão de Fluxo de Caixa Futuro (Próximos Meses)")
    if not df_contracts_agendadas.empty:
        hoje = pd.to_datetime('today')
        df_futuro = df_contracts_agendadas[
            (df_contracts_agendadas['Data Festa'].dt.date >= hoje.date()) &
            (df_contracts_agendadas['Valor a Pagar'] > 0)
        ].copy()

        if not df_futuro.empty:
            df_futuro['AnoMes'] = df_futuro['Data Festa'].dt.to_period('M').astype(str)
            previsao_fluxo = df_futuro.groupby('AnoMes')['Valor a Pagar'].sum().reset_index()
            previsao_fluxo.columns = ['Mês/Ano', 'Valor Previsto a Receber']
            previsao_fluxo['Mês/Ano'] = pd.to_datetime(previsao_fluxo['Mês/Ano'])
            previsao_fluxo = previsao_fluxo.sort_values('Mês/Ano').reset_index(drop=True)
            previsao_fluxo['Mês/Ano'] = previsao_fluxo['Mês/Ano'].dt.strftime('%Y-%m')

            st.subheader("Valores Previstos a Receber por Mês")
            df_previsao_display = previsao_fluxo.copy()
            df_previsao_display['Valor Previsto a Receber'] = df_previsao_display['Valor Previsto a Receber'].apply(format_currency)
            st.dataframe(df_previsao_display, use_container_width=True, hide_index=True)

            st.subheader("Gráfico de Previsão de Recebíveis")
            fig_cash_flow = px.bar(previsao_fluxo, x='Mês/Ano', y='Valor Previsto a Receber',
                                   title='Previsão Mensal de Recebíveis',
                                   labels={'Mês/Ano': 'Mês', 'Valor Previsto a Receber': 'Valor (R$)'},
                                   color_discrete_sequence=['#FF7F00'])
            st.plotly_chart(fig_cash_flow, use_container_width=True)
        else:
            st.info("Não há contratos futuros com valores a receber para gerar uma previsão de fluxo de caixa.")
    else:
        st.info("Não há dados de contrato agendados disponíveis para gerar uma previsão de fluxo de caixa.")

def render_realized_cash_flow(df_pagamentos):
    """Exibe o fluxo de caixa realizado (entradas por mês)."""
    st.markdown("---")
    st.header("💸 Fluxo de Caixa Realizado (Entradas por Mês)")
    if not df_pagamentos.empty:
        df_pagamentos_valid = df_pagamentos.dropna(subset=['Data Pagamento']).copy()

        if not df_pagamentos_valid.empty:
            df_pagamentos_valid['AnoMes'] = df_pagamentos_valid['Data Pagamento'].dt.to_period('M').astype(str)
            entradas_mensais = df_pagamentos_valid.groupby('AnoMes')['Valor Parcial Pago'].sum().reset_index()
            entradas_mensais.columns = ['Mês/Ano', 'Valor Recebido']
            entradas_mensais['Mês/Ano'] = pd.to_datetime(entradas_mensais['Mês/Ano'])
            entradas_mensais = entradas_mensais.sort_values('Mês/Ano').reset_index(drop=True)
            entradas_mensais['Mês/Ano'] = entradas_mensais['Mês/Ano'].dt.strftime('%Y-%m') # Corrected column name here

            st.subheader("Valores Efetivamente Recebidos por Mês")
            df_entradas_display = entradas_mensais.copy()
            df_entradas_display['Valor Recebido'] = df_entradas_display['Valor Recebido'].apply(format_currency)
            st.dataframe(df_entradas_display, use_container_width=True, hide_index=True)

            st.subheader("Gráfico de Entradas Mensais")
            fig_entradas = px.bar(entradas_mensais, x='Mês/Ano', y='Valor Recebido',
                                   title='Total Recebido por Mês na Conta',
                                   labels={'Mês/Ano': 'Mês', 'Valor Recebido': 'Valor (R$)'},
                                   color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig_entradas, use_container_width=True)
        else:
            st.info("Não há pagamentos com datas válidas para calcular o fluxo de caixa realizado.")
    else:
        st.info("Nenhum dado de pagamento encontrado para calcular o fluxo de caixa realizado. Verifique a planilha 'Pagamentos'.")

def render_charts_realizadas(df_contracts_realizadas):
    """Exibe os gráficos visuais para festas realizadas."""
    st.markdown("---")
    st.header("📈 Gráficos Visuais (Festas Realizadas)")
    if not df_contracts_realizadas.empty:
        # O gráfico de Distribuição do Status de Pagamento (Realizadas) foi removido.
        # O gráfico de Tendência de Contratos e Receita por Mês (Realizadas) foi removido.
        # O gráfico de Distribuição do Status de Pagamento por Mês (Realizadas) foi removido.

        # Layout ajustado para exibir apenas o gráfico de sazonalidade
        st.subheader("Sazonalidade de Festas por Mês (Realizadas)")
        df_sazonalidade = df_contracts_realizadas.dropna(subset=['Data Festa']).copy()
        df_sazonalidade['Mes'] = df_sazonalidade['Data Festa'].dt.month
        df_sazonalidade['Mes_Nome'] = df_sazonalidade['Data Festa'].dt.strftime('%b')
        df_sazonalidade['Mes_Ordenacao'] = df_sazonalidade['Mes'].astype(int)
        sazonalidade_contagem = df_sazonalidade.groupby(['Mes_Ordenacao', 'Mes_Nome', 'Status Festa']).size().reset_index(name='Contagem')
        sazonalidade_contagem = sazonalidade_contagem.sort_values('Mes_Ordenacao')

        fig_sazonalidade = px.bar(sazonalidade_contagem, x='Mes_Nome', y='Contagem', color='Status Festa',
                                  title='Número de Festas por Mês (Sazonalidade - Realizadas)',
                                  labels={'Mes_Nome': 'Mês', 'Contagem': 'Número de Festas'},
                                  barmode='group',
                                  color_discrete_map={
                                      'Agendada': '#6D5A92', # This might not appear if only 'Realizada' is present
                                      'Realizada': '#FF7F00'
                                  })
        st.plotly_chart(fig_sazonalidade, use_container_width=True)

    else:
        st.info("Não há dados de festas realizadas para exibir nos gráficos.")

def render_risk_analysis(df_contracts_agendadas):
    """Exibe a análise de contratos a vencer/vencidos para festas agendadas."""
    st.markdown("---")
    st.header("📊 Análise de Contratos a Vencer/Vencidos (Riscos de Recebimento)")
    df_vencimento = df_contracts_agendadas[df_contracts_agendadas['Valor a Pagar'] > 0].dropna(subset=['Data Festa']).copy()

    hoje_dt = pd.to_datetime(date.today())
    proximos_30dias_dt = hoje_dt + timedelta(days=30)
    proximos_60dias_dt = hoje_dt + timedelta(days=60)

    def classificar_vencimento(data_festa):
        if data_festa < hoje_dt:
            return "Vencido"
        elif data_festa <= proximos_30dias_dt:
            return "Próximos 30 dias"
        elif data_festa <= proximos_60dias_dt:
            return "Próximos 31-60 dias"
        else:
            return "Acima de 60 dias"

    df_vencimento['Faixa de Vencimento'] = df_vencimento['Data Festa'].apply(classificar_vencimento)

    if not df_vencimento.empty:
        sum_vencimento = df_vencimento.groupby('Faixa de Vencimento').agg(
            Contagem=('Numero Contrato', 'count'),
            Valor_a_Receber=('Valor a Pagar', 'sum')
        ).reset_index()

        ordem_faixas = ["Vencido", "Próximos 30 dias", "Próximos 31-60 dias", "Acima de 60 dias"]
        sum_vencimento['Faixa de Vencimento'] = pd.Categorical(sum_vencimento['Faixa de Vencimento'], categories=ordem_faixas, ordered=True)

        sum_vencimento['Contagem'] = sum_vencimento['Contagem'].fillna(0)
        sum_vencimento['Valor_a_Receber'] = sum_vencimento['Valor_a_Receber'].fillna(0)

        sum_vencimento = sum_vencimento.sort_values('Faixa de Vencimento')

        st.subheader("Contratos Pendentes por Faixa de Vencimento")

        df_vencimento_display = sum_vencimento.copy()
        df_vencimento_display['Valor_a_Receber'] = df_vencimento_display['Valor_a_Receber'].apply(format_currency)
        df_vencimento_display.rename(columns={'Contagem': 'Número de Contratos', 'Valor_a_Receber': 'Total a Receber'}, inplace=True)
        st.dataframe(df_vencimento_display, hide_index=True, use_container_width=True)

        fig_vencimento_value = px.bar(sum_vencimento, x='Faixa de Vencimento', y='Valor_a_Receber',
                                    title='Valor Total a Receber por Faixa de Vencimento',
                                    labels={'Valor_a_Receber': 'Valor (R$)', 'Faixa de Vencimento': 'Faixa de Tempo'},
                                    color='Faixa de Vencimento',
                                    color_discrete_map={
                                        "Vencido": "#FF4500",
                                        "Próximos 30 dias": "#FF7F00",
                                        "Próximos 31-60 dias": "#FFA500",
                                        "Acima de 60 dias": "#4CAF50"
                                    })
        st.plotly_chart(fig_vencimento_value, use_container_width=True)

    else:
        st.info("Não há contratos agendados pendentes ou vencidos com data de festa definida para esta análise.")

def render_calendar(df_contracts_agendadas):
    """Exibe o calendário interativo de festas agendadas."""
    st.markdown("---")
    st.header("📅 Calendário de Festas Agendadas")

    if not df_contracts_agendadas.empty:
        today_date = date.today()

        # Use session state for month and year
        month_selected = st.session_state['current_calendar_month']
        year_selected = st.session_state['current_calendar_year']

        # Mapeamento de nomes de meses para português
        month_names_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        # Mapeamento de nomes de dias da semana para português (abreviado)
        day_names_pt = {
            'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui',
            'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
        }

        # Navigation buttons
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

        with col_nav1:
            if st.button("Mês Anterior", key='prev_month_calendar'):
                st.session_state['current_calendar_month'] -= 1
                if st.session_state['current_calendar_month'] < 1:
                    st.session_state['current_calendar_month'] = 12
                    st.session_state['current_calendar_year'] -= 1
                st.rerun()

        with col_nav2:
            # Centralizando o título do mês com inline CSS
            st.markdown(f"<h3 style='text-align: center;'>{month_names_pt[month_selected]} {year_selected}</h3>", unsafe_allow_html=True)

        with col_nav3:
            if st.button("Próximo Mês", key='next_month_calendar'):
                st.session_state['current_calendar_month'] += 1
                if st.session_state['current_calendar_month'] > 12:
                    st.session_state['current_calendar_month'] = 1
                    st.session_state['current_calendar_year'] += 1
                st.rerun()

        # We will build the HTML manually to have full control over classes and content
        df_month = df_contracts_agendadas[(df_contracts_agendadas['Data Festa'].dt.month == month_selected) & (df_contracts_agendadas['Data Festa'].dt.year == year_selected)].copy()

        # Debugging: Show filtered data for the selected month/year
        if st.checkbox("Mostrar dados filtrados para o mês do calendário (debug)"):
            st.write(f"Contratos para {month_names_pt[month_selected]}/{year_selected}:") # Usando nomes em português
            st.dataframe(df_month[['Numero Contrato', 'Nome Cliente', 'Data Festa', 'Status Pagamento Festa', 'Valor Total', 'Valor a Pagar']])


        status_colors_calendar = {
            'Pago Integralmente': '#4CAF50',
            'Pagamento Parcial': '#FF7F00',
            'Aberto': '#FF4500',
            'Não Aplicável': '#CCCCCC'
        }

        # Build the calendar HTML manually for more control
        week_headers = "".join([f"<th>{day_names_pt[calendar.day_abbr[i]]}</th>" for i in range(7)]) # Day names in Portuguese
        month_html_parts = [f'<table class="calendar">',
                            f'<thead><tr>{week_headers}</tr></thead>',
                            f'<tbody>']

        # Use calendar.monthcalendar directly
        cal_matrix = calendar.monthcalendar(year_selected, month_selected)

        for week in cal_matrix:
            month_html_parts.append('<tr>')
            for day_num in week:
                if day_num == 0: # Day belongs to previous/next month
                    month_html_parts.append(f'<td class="noday"></td>')
                else:
                    date_check = date(year_selected, month_selected, day_num)
                    festas_no_dia = df_month[df_month['Data Festa'].dt.date == date_check]

                    day_classes = []
                    if date_check == today_date:
                        day_classes.append("today")

                    # Determine day type for CSS (sat, sun, or day)
                    if date_check.weekday() == calendar.SATURDAY:
                        day_classes.append("sat")
                    elif date_check.weekday() == calendar.SUNDAY:
                        day_classes.append("sun")
                    else:
                        day_classes.append("day")

                    class_attr = f'class="{" ".join(day_classes)}"' if day_classes else ''

                    day_content = f"<div style='font-weight: bold;'>{day_num}</div>"

                    if not festas_no_dia.empty:
                        for idx, row in festas_no_dia.iterrows():
                            status = row['Status Pagamento Festa']
                            color = status_colors_calendar.get(status, '#CCCCCC')
                            client_name = row['Nome Cliente']
                            contract_num = row['Numero Contrato']

                            # Use &#10; for line breaks in HTML title attribute
                            tooltip_text = (
                                f"Cliente: {client_name.replace('\"', '&quot;')}&#10;"
                                f"Contrato: {contract_num.replace('\"', '&quot;')}&#10;"
                                f"Status: {status.replace('\"', '&quot;')}&#10;"
                                f"Valor Total: {format_currency(row['Valor Total']).replace('\"', '&quot;')}&#10;"
                                f"Valor a Pagar: {format_currency(row['Valor a Pagar']).replace('\"', '&quot;')}"
                            )
                            # Use &#x2022; for a bullet point or a small div
                            day_content += f"<div style='width: 10px; height: 10px; background-color: {color}; border-radius: 50%; display: inline-block; margin: 0 2px; vertical-align: middle;' title='{tooltip_text}'></div>"

                    month_html_parts.append(f'<td {class_attr}><div style="text-align: center; display: flex; flex-direction: column; align-items: center;">{day_content}</div></td>')
            month_html_parts.append('</tr>')
        month_html_parts.append('</tbody></table>')
        final_month_html = "".join(month_html_parts)


        calendar_css_local = """
        <style>
        .calendar-container {
            display: flex;
            justify-content: center; /* Centraliza o conteúdo do calendário */
            width: 100%;
        }
        .calendar {
            width: 100%;
            max-width: 800px;
            font-family: 'Inter', sans-serif;
            border-collapse: collapse;
            text-align: center;
            background-color: white !important;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .calendar th {
            background-color: #f2f2f2 !important;
            padding: 10px;
            border: 1px solid #ddd;
            color: #333333 !important;
        }
        .calendar td {
            padding: 10px;
            border: 1px solid #ddd;
            min-height: 80px;
            vertical-align: top;
            color: #333333 !important;
        }
        .calendar .month { /* This class is no longer used for the month name, but kept for consistency */
            font-size: 1.5em;
            font-weight: bold;
            padding: 15px;
            background-color: #6D5A92 !important;
            color: white !important;
            border-bottom: 2px solid #5A4982;
        }
        .calendar .day, .calendar .sat, .calendar .sun { /* Apply these to all valid days */
            background-color: #f9f9f9 !important;
            min-height: 80px;
        }
        .calendar .sat, .calendar .sun {
            background-color: #EBE6F3 !important;
        }
        .calendar .noday {
            background-color: #e6e6e6 !important;
            color: #aaaaaa !important;
        }
        .calendar table {
            width: 100%;
        }
        /* Destaque para o dia atual no calendário */
        .calendar .today {
            background-color: #ADD8E6 !important; /* Azul claro */
            border: 2px solid #4682B4 !important; /* Borda azul mais escura */
            font-weight: bold;
        }
        </style>
        """

        st.markdown(calendar_css_local, unsafe_allow_html=True)
        # Wrap the calendar HTML in a div for centering
        st.markdown(f'<div class="calendar-container">{final_month_html}</div>', unsafe_allow_html=True)


        st.subheader("Legenda do Calendário")
        st.markdown(f"""
            <div class="calendar-legend-item">
                <div class="calendar-legend-color" style="background-color: {status_colors_calendar['Pago Integralmente']};"></div>
                Pago Integralmente
            </div>
            <div class="calendar-legend-item">
                <div class="calendar-legend-color" style="background-color: {status_colors_calendar['Pagamento Parcial']};"></div>
                Pagamento Parcial
            </div>
            <div class="calendar-legend-item">
                <div class="calendar-legend-color" style="background-color: {status_colors_calendar['Aberto']};"></div>
                Aberto
            </div>
            <div class="calendar-legend-item">
                <div class="calendar-legend-color" style="background-color: {status_colors_calendar['Não Aplicável']};"></div>
                Não Aplicável
            </div>
             <div class="calendar-legend-item">
                <div class="calendar-legend-color" style="background-color: #ADD8E6; border: 1px solid #4682B4;"></div>
                Dia Atual
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado de contrato agendado disponível para gerar o calendário.")

def render_financeiro_tab(df_contracts, df_payments): # Removido df_custos do parâmetro
    """
    Exibe a aba de informações financeiras com meta mensal,
    contratos fechados no mês, valor vendido no mês e valor recebido no mês,
    com seletor de mês e ano.
    """
    st.markdown("---")
    st.header("📊 Resumo Financeiro Mensal")

    # Definir a meta mensal
    META_MENSAL = 80000

    # Seletor de Mês e Ano
    col_selector_month, col_selector_year = st.columns(2)
    with col_selector_month:
        month_names_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        selected_month_name = st.selectbox(
            "Selecione o Mês:",
            options=list(month_names_pt.values()),
            index=list(month_names_pt.keys()).index(st.session_state['finance_selected_month']),
            key='finance_month_selector'
        )
        # Convert back to month number
        selected_month = {v: k for k, v in month_names_pt.items()}[selected_month_name]
        st.session_state['finance_selected_month'] = selected_month

    with col_selector_year:
        current_year = date.today().year
        # Generate a range of years, e.g., current year +/- 5 years
        year_options = list(range(current_year - 5, current_year + 6))
        selected_year = st.selectbox(
            "Selecione o Ano:",
            options=year_options,
            index=year_options.index(st.session_state['finance_selected_year']),
            key='finance_year_selector'
        )
        st.session_state['finance_selected_year'] = selected_year

    st.subheader(f"Dados para {month_names_pt[selected_month]} de {selected_year}")

    # Filtrar contratos fechados no mês e ano selecionados (usando 'Data Fechamento')
    df_contracts_closed_selected_month = df_contracts[
        (df_contracts['Data Fechamento'].notna()) &
        (df_contracts['Data Fechamento'].dt.month == selected_month) &
        (df_contracts['Data Fechamento'].dt.year == selected_year)
    ].copy()
    num_contracts_closed = df_contracts_closed_selected_month.shape[0]
    total_sold_this_month = df_contracts_closed_selected_month['Valor Total'].sum()

    # Filtrar pagamentos recebidos no mês e ano selecionados
    df_payments_selected_month = df_payments[
        (df_payments['Data Pagamento'].notna()) & # Adicionado .notna() para segurança
        (df_payments['Data Pagamento'].dt.month == selected_month) &
        (df_payments['Data Pagamento'].dt.year == selected_year)
    ].copy()
    total_received_this_month = df_payments_selected_month['Valor Parcial Pago'].sum()

    # --- Removida a lógica de custos gerais e lucro bruto ---
    # total_cost_this_month = df_contracts_closed_selected_month['Custo Total por Festa'].sum()
    # lucro_bruto_mensal = total_sold_this_month - total_cost_this_month
    lucro_bruto_mensal = total_received_this_month # Temporariamente, lucro é o valor recebido


    # Calcular o progresso em relação à meta com base no VALOR VENDIDO
    progress_percentage = (total_sold_this_month / META_MENSAL) * 100 if META_MENSAL > 0 else 0

    # **MELHORIA DE RESPONSIVIDADE**: Agrupando as métricas em duas linhas de duas colunas.
    cols1 = st.columns(2)
    with cols1[0]:
        st.metric(label="Meta Mensal de Vendas", value=format_currency(META_MENSAL))
    with cols1[1]:
        st.metric(label="Contratos Fechados no Mês", value=num_contracts_closed)

    cols2 = st.columns(2)
    with cols2[0]:
        st.metric(label="Valor Vendido no Mês", value=format_currency(total_sold_this_month))
    with cols2[1]:
        st.metric(label="Valor Recebido no Mês", value=format_currency(total_received_this_month))
    # Removida a métrica de Lucro Bruto


    st.markdown("---")
    st.subheader("Progresso em Relação à Meta de Vendas")
    st.progress(min(100, int(progress_percentage)))
    st.info(f"Você já alcançou **{progress_percentage:.2f}%** da meta de vendas de R$ {META_MENSAL:,.2f}!")

    if total_sold_this_month >= META_MENSAL:
        st.balloons()
        st.success("🎉 Parabéns! Você atingiu ou superou a meta de vendas mensal!")
    elif total_sold_this_month < META_MENSAL:
        st.warning(f"Ainda faltam **{format_currency(META_MENSAL - total_sold_this_month)}** para atingir a meta de vendas deste mês.")

    st.markdown("---")
    st.subheader("Detalhes dos Contratos Fechados no Mês")
    if not df_contracts_closed_selected_month.empty:
        df_display_contracts = df_contracts_closed_selected_month.copy()
        df_display_contracts['Data Festa'] = df_display_contracts['Data Festa'].dt.strftime('%d/%m/%Y')
        df_display_contracts['Data Fechamento'] = df_display_contracts['Data Fechamento'].dt.strftime('%d/%m/%Y %H:%M')
        df_display_contracts['Valor Total'] = df_display_contracts['Valor Total'].apply(format_currency)
        df_display_contracts['Valor Total Pago na Conta'] = df_display_contracts['Valor Total Pago na Conta'].apply(format_currency)
        df_display_contracts['Valor a Pagar'] = df_display_contracts['Valor a Pagar'].apply(format_currency)
        # Removidas as linhas de formatação de custo e lucro
        # df_display_contracts['Custo Direto por Festa'] = df_display_contracts['Custo Direto por Festa'].apply(format_currency)
        # df_display_contracts['Custo Alocado'] = df_display_contracts['Custo Alocado'].apply(format_currency)
        # df_display_contracts['Custo Total por Festa'] = df_display_contracts['Custo Total por Festa'].apply(format_currency)
        # df_display_contracts['Lucro Bruto por Festa'] = df_display_contracts['Lucro Bruto por Festa'].apply(format_currency)

        st.dataframe(df_display_contracts[[
            'Numero Contrato', 'Nome Cliente', 'Data Fechamento', 'Data Festa',
            'Valor Total',
            # Removidas as colunas de custo e lucro
            # 'Custo Direto por Festa', 'Custo Alocado', 'Custo Total por Festa', 'Lucro Bruto por Festa',
            'Status Pagamento Festa'
        ]], use_container_width=True)
    else:
        st.info("Nenhum contrato fechado neste mês ainda.")

    st.markdown("---")
    st.subheader("Detalhes dos Pagamentos Recebidos no Mês")
    if not df_payments_selected_month.empty:
        df_display_payments = df_payments_selected_month.copy()
        df_display_payments['Data Pagamento'] = df_display_payments['Data Pagamento'].dt.strftime('%d/%m/%Y')
        df_display_payments['Valor Parcial Pago'] = df_display_payments['Valor Parcial Pago'].apply(format_currency)
        st.dataframe(df_display_payments[['Numero Contrato', 'Valor Parcial Pago', 'Data Pagamento']], use_container_width=True)
    else:
        st.info("Nenhum pagamento recebido neste mês ainda.")

    # --- NOVA SEÇÃO DE CONSULTA DE PAGAMENTOS ---
    st.markdown("---")
    st.header("🔍 Consulta de Pagamentos por Contrato")

    search_contract_nr = st.text_input("Digite o número do contrato para ver os detalhes de pagamento:", key="contract_search_input")

    if search_contract_nr:
        # Normaliza o número do contrato inserido para corresponder ao formato do dataframe
        normalized_search_nr = normalize_contract_number(pd.Series([search_contract_nr])).iloc[0]

        # Busca os detalhes do contrato no dataframe principal
        contract_details = df_contracts[df_contracts['Numero Contrato'] == normalized_search_nr]

        if contract_details.empty:
            st.warning(f"Nenhum contrato encontrado com o número '{search_contract_nr}'.")
        else:
            # Pega a primeira linha (deve ser única)
            contract_info = contract_details.iloc[0]

            st.subheader(f"Detalhes do Contrato: {contract_info['Numero Contrato']}")
            st.write(f"**Cliente:** {contract_info['Nome Cliente']}")

            # Exibe os KPIs do contrato específico
            cols_contract_kpi = st.columns(3)
            cols_contract_kpi[0].metric("Valor Total do Contrato", format_currency(contract_info['Valor Total']))
            cols_contract_kpi[1].metric("Total Já Pago", format_currency(contract_info['Valor Total Pago na Conta']))
            cols_contract_kpi[2].metric("Valor Restante a Pagar", format_currency(contract_info['Valor a Pagar']))

            st.markdown("---")
            st.subheader("Histórico de Pagamentos Registrados")

            # Filtra a tabela de pagamentos para este contrato
            payments_for_contract = df_payments[df_payments['Numero Contrato'] == normalized_search_nr].copy()

            if payments_for_contract.empty:
                st.info("Ainda não há pagamentos registrados para este contrato na aba 'Pagamentos'.")
            else:
                # Formata o dataframe para exibição
                payments_for_contract['Data Pagamento'] = pd.to_datetime(payments_for_contract['Data Pagamento'], errors='coerce').dt.strftime('%d/%m/%Y')
                payments_for_contract['Valor Parcial Pago'] = payments_for_contract['Valor Parcial Pago'].apply(format_currency)
                payments_for_contract = payments_for_contract.sort_values(by='Data Pagamento', ascending=False)
                st.dataframe(payments_for_contract[['Data Pagamento', 'Valor Parcial Pago']], use_container_width=True)


# --- Lógica Principal da Aplicação ---

# --- Sistema Simples de Login Hardcoded ---
def login():
    st.sidebar.title("🔒 Login")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        username_input = st.sidebar.text_input("Usuário")
        password_input = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Entrar"):
            # ATENÇÃO: Senhas "hardcoded" não são seguras para produção.
            # Considere usar o sistema de Secrets do Streamlit para senhas
            if username_input == "lanbele" and password_input == "Festa123":
                st.session_state.logged_in = True
                st.success("Login realizado com sucesso!")
                st.rerun() # Use st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.stop()  # Impede execução do app até login válido


def main():
    """Função principal que orquestra o dashboard."""
    LOGO_URL = "https://lh3.googleusercontent.com/p/AF1QipPtxNaXQQmEsROetMvfeCZCWVh-uhv-wXy9qlRl=s680-w680-h510-rw"
    st.sidebar.image(LOGO_URL, use_container_width=True)
    
    # --- Executa o login ANTES de mais nada ---
    # login() # Descomente esta linha se quiser reativar o login

    st.sidebar.markdown("---")
    page_selection = st.sidebar.selectbox(
        "Navegar para:",
        options=["Festas Agendadas", "Festas Realizadas", "Financeiro"],
        index=0 # Default to "Festas Agendadas"
    )
    st.sidebar.markdown("---")

    st.title("📊 Dashboard Financeiro - Buffet LanBele")
    st.subheader(f"Visão Integrada de Contratos e Pagamentos - {page_selection}")


    if st.sidebar.button("Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear() # Limpa os dois caches
        st.rerun()

    df_contracts, df_payments = load_and_process_data() # Não recebe mais df_custos

    if not df_contracts.empty:
        df_agendadas = df_contracts[df_contracts['Status Festa'] == 'Agendada'].copy()
        df_realizadas = df_contracts[df_contracts['Status Festa'] == 'Realizada'].copy()

        if page_selection == "Festas Agendadas":
            render_kpis(df_agendadas, 'Agendadas')
            render_weekly_summary(df_agendadas) # New weekly summary assistant
            render_alerts(df_agendadas, 'Agendadas')
            render_contract_details(df_agendadas, 'Agendadas') # Pass df_agendadas for filtering
            render_future_cash_flow(df_agendadas)
            render_risk_analysis(df_agendadas)
            render_calendar(df_agendadas)
        elif page_selection == "Festas Realizadas":
            render_kpis(df_realizadas, 'Realizadas')
            render_alerts(df_realizadas, 'Realizadas')
            render_contract_details(df_realizadas, 'Realizadas') # Pass df_realizadas for filtering
            render_realized_cash_flow(df_payments) # This is the "entrada de dinheiro no mês" chart
            render_charts_realizadas(df_realizadas) # New function for charts specific to realized
        elif page_selection == "Financeiro": # Nova aba
            render_financeiro_tab(df_contracts, df_payments) # Não passa mais df_custos
    else:
        st.warning("Não foi possível carregar os dados. Verifique as configurações e as planilhas.")

    st.markdown("---")
    st.info("Última atualização dos dados: " + pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S"))

if __name__ == "__main__":
    main()