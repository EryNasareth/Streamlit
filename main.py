import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard SUS AIH",
    page_icon="📈",
    layout="wide",
)

# Esconder a barra de menu e rodapé padrão do Streamlit
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Faixa azul superior
st.markdown(
    """
    <style>
        .faixa-azul {
            background-color: #022857;
            color: white;
            padding: 30px;
            text-align: center;
            font-size: 40px;
            font-weight: bold;
            border-radius: 15px 15px 0 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="faixa-azul">SUS AIH 2024</div>', unsafe_allow_html=True)

# Leitura e tratamento da base
df_tabela = pd.read_csv("table_SUS_RIDE_DF_AIH.csv", sep=';', encoding='utf-8')

df_tabela["latitude"] = pd.to_numeric(df_tabela["latitude"].astype(str).str.replace(",", ".", regex=False).str.strip(), errors="coerce")
df_tabela["longitude"] = pd.to_numeric(df_tabela["longitude"].astype(str).str.replace(",", ".", regex=False).str.strip(), errors="coerce")
df_tabela["qtd_total"] = pd.to_numeric(
    df_tabela["qtd_total"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
    errors="coerce"
)
df_tabela["vl_total"] = pd.to_numeric(
    df_tabela["vl_total"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
    errors="coerce"
)

# Filtro para ano de 2024 apenas
df_tabela = df_tabela[df_tabela["ano_aih"] == 2024]

# Nome dos meses
meses_nome = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
df_tabela["mes_nome"] = df_tabela["mes_aih"].map(meses_nome)

# Agrupamento por município para a tabela
df_resumo = df_tabela.groupby(["regiao_nome", "nome_municipio"], as_index=False).agg({
    "qtd_total": "sum",
    "vl_total": "sum"
}).sort_values("vl_total", ascending=False).reset_index(drop=True)

# ========================
# LAYOUT SUPERIOR
# ========================
col_filtros, col_metricas = st.columns([2, 1])

with col_filtros:
    municipio_sel = st.selectbox("Município:", options=["Todos"] + sorted(df_tabela["nome_municipio"].dropna().unique()))
    mes_sel = st.selectbox("Mês:", options=["Todos"] + list(meses_nome.values()))

df_filtrado = df_tabela.copy()
if municipio_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["nome_municipio"] == municipio_sel]
if mes_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["mes_nome"] == mes_sel]

with col_metricas:
    st.metric("Quantidade Total de Procedimentos", f"{df_filtrado['qtd_total'].sum()/1_000_000:.1f} mi")
    st.metric("Valor Total Gasto", f"R$ {df_filtrado['vl_total'].sum()/1_000_000:.2f} mi")

# ========================
# GRÁFICO DE BARRAS COMPARATIVO
# ========================
col1, col2 = st.columns(2)

with col1:
    df_barra = df_filtrado.groupby("mes_nome", as_index=False).agg({
        "qtd_total": "sum",
        "vl_total": "sum"
    })
    df_barra["mes_num"] = df_barra["mes_nome"].map({v: k for k, v in meses_nome.items()})
    df_barra = df_barra.sort_values("mes_num")

    # Normaliza para igualar visualmente as alturas
    df_barra["qtd_total_normalizada"] = df_barra["qtd_total"] / df_barra["qtd_total"].max()
    df_barra["vl_total_normalizada"] = df_barra["vl_total"] / df_barra["vl_total"].max()

    fig_bar = px.bar(
        df_barra,
        x="mes_nome",
        y=["qtd_total_normalizada", "vl_total_normalizada"],
        barmode="group",
        title="Comparativo por Mês - Quantidade vs Valor",
        color_discrete_sequence=["mediumseagreen", "darkred"]
    )
    fig_bar.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valores Normalizados",
        legend_title=None,
        bargap=0.2
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ========================
# GRÁFICO DE LINHA VALOR
# ========================
with col2:
    df_linha = df_filtrado.groupby("mes_nome", as_index=False)["vl_total"].sum()
    df_linha["mes_num"] = df_linha["mes_nome"].map({v: k for k, v in meses_nome.items()})
    df_linha = df_linha.sort_values("mes_num")

    fig_valor = px.line(
        df_linha,
        x="mes_nome",
        y="vl_total",
        title="Valor Total por Mês em 2024",
        markers=True
    )
    fig_valor.update_traces(line_color="darkred", marker_color="darkred",
                            text=[f"{v/1_000_000:.0f} mi" for v in df_linha["vl_total"]],
                            textposition="top center")
    fig_valor.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        showlegend=False
    )
    st.plotly_chart(fig_valor, use_container_width=True)

# ========================
# TABELA E GRÁFICO DE QTD (ALINHADOS COM OS GRÁFICOS ACIMA)
# ========================

col1, col2 = st.columns(2)

with col1:
    st.dataframe(
        df_resumo.style
        .format({"qtd_total": "{:,.0f}", "vl_total": "R$ {:,.2f}"})
        .hide(axis="index")
        .apply(lambda x: ['background-color: #fbeaea' if i % 2 == 0 else '' for i in range(len(x))], axis=0),
        use_container_width=True
    )

with col2:
    df_qtd = df_filtrado.groupby("mes_nome", as_index=False)["qtd_total"].sum()
    df_qtd["mes_num"] = df_qtd["mes_nome"].map({v: k for k, v in meses_nome.items()})
    df_qtd = df_qtd.sort_values("mes_num")

    fig_qtd = px.line(
        df_qtd,
        x="mes_nome",
        y="qtd_total",
        title="Quantidade Total por Mês em 2024",
        markers=True
    )
    fig_qtd.update_traces(
        line=dict(color="mediumseagreen", width=3),
        marker=dict(size=8),
        text=[f"{v/1_000_000:.1f} mi" for v in df_qtd["qtd_total"]],
        textposition="middle right",
        textfont=dict(color="mediumseagreen", size=12)
    )
    fig_qtd.update_layout(
        xaxis_title="Mês",
        yaxis_title="Quantidade",
        showlegend=False
    )
    st.plotly_chart(fig_qtd, use_container_width=True)

# ================================
# MAPA DE ATENDIMENTOS POR MUNICÍPIO
# ================================

# Filtrar dados com coordenadas válidas
df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])

# Separar Brasília para não distorcer o mapa
df_brasilia = df_mapa[df_mapa["nome_municipio"].str.upper().str.contains("BRASÍLIA")]
df_outros = df_mapa[~df_mapa["nome_municipio"].str.upper().str.contains("BRASÍLIA")]

# Agrupar dados
df_outros_agrupado = df_outros.groupby(["nome_municipio", "latitude", "longitude"], as_index=False).agg({"qtd_total": "sum"})
df_brasilia_agrupado = df_brasilia.groupby(["nome_municipio", "latitude", "longitude"], as_index=False).agg({"qtd_total": "sum"})

# Mapa para outros municípios
fig_mapa = px.scatter_mapbox(
    df_outros_agrupado,
    lat="latitude",
    lon="longitude",
    color="qtd_total",
    hover_name="nome_municipio",
    color_continuous_scale="YlOrRd",  # Cor fria para quente
    size_max=15,
    zoom=6,
    title="Quantidade de Atendimentos Por Município"
)
fig_mapa.update_traces(marker=dict(size=15, sizemode='diameter', opacity=0.8))

# Adiciona Brasília ao mapa
fig_mapa.add_trace(px.scatter_mapbox(
    df_brasilia_agrupado,
    lat="latitude",
    lon="longitude",
    color="qtd_total",
    hover_name="nome_municipio",
    color_continuous_scale="YlOrRd"
).update_traces(marker=dict(size=15, sizemode='diameter', opacity=0.8)).data[0])

# Layout final
fig_mapa.update_layout(
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title="Qtd Procedimentos")
)

st.plotly_chart(fig_mapa, use_container_width=True)