import json
import os
import re
import pandas as pd
import streamlit as st

# Configuração visual da página
st.set_page_config(
    page_title="Dashboard - VIP DO DUDÃO",
    page_icon="⚡",
    layout="wide"
)

NOME_ARQUIVO_JSON = 'mensagens_vip_dudao.json'

@st.cache_data(ttl=5)  # Atualiza os dados a cada 5 segundos
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
    
    # Tratamento de datas e extração via RegEx
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    
    def extrair_unidade(texto):
        if not isinstance(texto, str):
            return 1.0
        match = re.search(r'(\d+[\.,]?\d*)\s*unidade', texto, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 1.0

    def identificar_resultado(texto):
        if not isinstance(texto, str):
            return "Pendente"
        texto_lower = texto.lower()
        if "green" in texto_lower or "✅" in texto or "bateu" in texto_lower:
            return "Green"
        elif "red" in texto_lower or "❌" in texto or "lost" in texto_lower:
            return "Red"
        return "Pendente"

    df['unidades'] = df['texto'].apply(extrair_unidade)
    df['resultado'] = df['texto'].apply(identificar_resultado)
    return df

# --- INTERFACE DO DASHBOARD ---
st.title("⚡ Gestão de Performance - VIP DO DUDÃO")
st.markdown("Acompanhamento em tempo real das mensagens e apostas.")

df = carregar_dados()

if df.empty:
    st.warning("Nenhuma mensagem registrada no arquivo local ainda. Garanta que o script `let.py` está rodando!")
else:
    # Filtros na barra lateral
    st.sidebar.header("Filtros")
    resultados_sel = st.sidebar.multiselect(
        "Status",
        options=["Green", "Red", "Pendente"],
        default=["Green", "Red", "Pendente"]
    )
    
    df_filtrado = df[df['resultado'].isin(resultados_sel)]

    # Indicadores
    col1, col2, col3, col4 = st.columns(4)
    total = len(df_filtrado)
    greens = len(df_filtrado[df_filtrado['resultado'] == 'Green'])
    reds = len(df_filtrado[df_filtrado['resultado'] == 'Red'])
    winrate = (greens / (greens + reds) * 100) if (greens + reds) > 0 else 0

    col1.metric("Total de Entradas", total)
    col2.metric("Greens ✅", greens)
    col3.metric("Reds ❌", reds)
    col4.metric("Winrate", f"{winrate:.1f}%")

    st.markdown("---")

    # Gráficos
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.subheader("📈 Volume Diário de Mensagens")
        df_diario = df_filtrado.set_index('data_hora').resample('D').size().reset_index(name='quantidade')
        st.line_chart(df_diario, x='data_hora', y='quantidade', use_container_width=True)

    with col_g2:
        st.subheader("🎯 Resumo de Desempenho")
        st.bar_chart(df_filtrado['resultado'].value_counts(), use_container_width=True)

    st.markdown("---")

    # Tabela detalhada
    st.subheader("📋 Mensagens Recebidas")
    st.dataframe(
        df_filtrado[['data_hora', 'resultado', 'unidades', 'texto']].sort_values(by='data_hora', ascending=False),
        use_container_width=True,
        column_config={
            "data_hora": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YYYY HH:mm"),
            "resultado": "Status",
            "unidades": st.column_config.NumberColumn("Stake", format="%.2f u"),
            "texto": "Mensagem"
        }
    )
