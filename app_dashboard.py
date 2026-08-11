import json
import os
import re
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Dashboard - VIP DO DUDÃO",
    page_icon="⚡",
    layout="wide"
)

NOME_ARQUIVO_JSON = 'mensagens_vip_dudao.json'

@st.cache_data(ttl=10)  # Atualiza os dados a cada 10 segundos
def carregar_dados():
    if not os.path.exists(NOME_ARQUIVO_JSON):
        return pd.DataFrame()
    
    with open(NOME_ARQUIVO_JSON, 'r', encoding='utf-8') as f:
        try:
            dados = json.load(f)
        except json.JSONDecodeError:
            return pd.DataFrame()
            
    if not dados:
        return pd.DataFrame()
        
    df = pd.DataFrame(dados)
    
    # Tratamento basico dos dados das mensagens
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    
    # Extração simples de unidades/stake via RegEx (ex: "0.25 unidade" ou "1 unidade")
    def extrair_unidade(texto):
        if not isinstance(texto, str):
            return 1.0
        match = re.search(r'(\d+[\.,]?\d*)\s*unidade', texto, re.IGNORECASE)
        if match:
            val = match.group(1).replace(',', '.')
            return float(val)
        return 1.0  # Padrão 1 unidade se não encontrar

    df['unidades'] = df['texto'].apply(extrair_unidade)
    
    # Identifica se a mensagem contém indicadores de resultado (Green/Red)
    def identificar_resultado(texto):
        if not isinstance(texto, str):
            return "Pendente"
        texto_lower = texto.lower()
        if "green" in texto_lower or "✅" in texto or "bateu" in texto_lower:
            return "Green"
        elif "red" in texto_lower or "❌" in texto or "lost" in texto_lower:
            return "Red"
        return "Pendente"

    df['resultado'] = df['texto'].apply(identificar_resultado)
    return df

# --- TÍTULO E CABEÇALHO ---
st.title("⚡ Gestão de Performance - VIP DO DUDÃO")
st.markdown("Acompanhamento automatizado de entradas e desempenho extraídos do Telegram.")

df = carregar_dados()

if df.empty:
    st.warning("Nenhuma mensagem ou aposta encontrada no arquivo JSON ainda. Aguarde novas entradas!")
else:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro por Resultado
    resultados_sel = st.sidebar.multiselect(
        "Status da Aposta",
        options=["Green", "Red", "Pendente"],
        default=["Green", "Red", "Pendente"]
    )
    
    df_filtrado = df[df['resultado'].isin(resultados_sel)]

    # --- CARDS DE MÉTRICAS PRINCIPAIS ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_apostas = len(df_filtrado)
    total_greens = len(df_filtrado[df_filtrado['resultado'] == 'Green'])
    total_reds = len(df_filtrado[df_filtrado['resultado'] == 'Red'])
    
    taxa_win = (total_greens / (total_greens + total_reds) * 100) if (total_greens + total_reds) > 0 else 0

    col1.metric("Total de Entradas", total_apostas)
    col2.metric("Greens ✅", total_greens)
    col3.metric("Reds ❌", total_reds)
    col4.metric("Taxa de Acerto (Winrate)", f"{taxa_win:.1f}%")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns([2, 1])

    with col_graf1:
        st.subheader("📈 Histórico de Mensagens / Entradas por Dia")
        df_diario = df_filtrado.set_index('data_hora').resample('D').size().reset_index(name='quantidade')
        st.line_chart(df_diario, x='data_hora', y='quantidade', use_container_width=True)

    with col_graf2:
        st.subheader("🎯 Distribuição dos Resultados")
        contagem_res = df_filtrado['resultado'].value_counts()
        st.bar_chart(contagem_res, use_container_width=True)

    st.markdown("---")

    # --- TABELA DE DADOS DETALHADA ---
    st.subheader("📋 Registro Detalhado das Mensagens")
    
    # Seleção de colunas para exibição na tabela
    colunas_exibir = ['data_hora', 'resultado', 'unidades', 'texto']
    st.dataframe(
        df_filtrado[colunas_exibir].sort_values(by='data_hora', ascending=False),
        use_container_width=True,
        column_config={
            "data_hora": st.column_config.DatetimeColumn("Data / Hora", format="DD/MM/YYYY HH:mm"),
            "resultado": "Status",
            "unidades": st.column_config.NumberColumn("Stake (Unidades)", format="%.2f u"),
            "texto": "Conteúdo da Mensagem"
        }
    )
