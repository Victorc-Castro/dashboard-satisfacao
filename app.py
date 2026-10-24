# Rode -> pip install -r requirements.txt

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Satisfação dos Pacientes", page_icon="🦷", layout="wide")
st.title("🦷 Painel de Satisfação dos Pacientes")

URL = st.secrets["CSV_URL"]

@st.cache_data(ttl=300)
def carregar_dados(url):
    return pd.read_csv(url)

df = carregar_dados(URL)

df = df.drop(columns=["Coluna 11"], errors="ignore")
df = df.dropna(subset=["Carimbo de data/hora"]).reset_index(drop=True)

df.columns = [
    "data", "faixa_etaria", "tipo_atendimento", "tempo_espera", "recepcao",
    "clareza", "limpeza", "resolucao", "elogios", "melhorias", "nps",
]

st.sidebar.header("Filtros")

tipos = sorted(df["tipo_atendimento"].dropna().unique())
faixas = sorted(df["faixa_etaria"].dropna().unique())

tipos_escolhidos = st.sidebar.multiselect("Tipo de atendimento", tipos, default=tipos)
faixas_escolhidas = st.sidebar.multiselect("Faixa etária", faixas, default=faixas)

df = df[
    (df["tipo_atendimento"].isin(tipos_escolhidos) | df["tipo_atendimento"].isna())
    & (df["faixa_etaria"].isin(faixas_escolhidas) | df["faixa_etaria"].isna())
]

if df.empty:
    st.warning("Nenhuma resposta para os filtros selecionados.")
    st.stop()

dimensoes = ["tempo_espera", "recepcao", "clareza", "limpeza", "resolucao"]

df[dimensoes + ["nps"]] = df[dimensoes + ["nps"]].apply(pd.to_numeric, errors="coerce")

total = len(df)
media_geral = df[dimensoes].mean().mean()

promotores = (df["nps"] >= 9).sum()
neutros = ((df["nps"] >= 7) & (df["nps"] <= 8)).sum()
detratores = (df["nps"] <= 6).sum()
nps = (promotores - detratores) / total * 100

c1, c2, c3 = st.columns(3)
c1.metric("Total de respostas", total)
c2.metric("Satisfação média (1 a 5)", f"{media_geral:.2f}")
c3.metric("NPS", f"{nps:.0f}")

nomes = {
    "tempo_espera": "Tempo de espera",
    "recepcao": "Recepção",
    "clareza": "Clareza das explicações",
    "limpeza": "Limpeza",
    "resolucao": "Resolução da queixa",
}

medias = df[dimensoes].mean().rename(index=nomes).reset_index()
medias.columns = ["Dimensão", "Média"]

fig = px.bar(
    medias,
    x="Dimensão",
    y="Média",
    range_y=[0, 5],
    text_auto=".2f",
    title="Média de satisfação por dimensão (1 a 5)",
)
st.plotly_chart(fig, width="stretch")

nps_df = pd.DataFrame({
    "Grupo": ["Promotores (9-10)", "Neutros (7-8)", "Detratores (0-6)"],
    "Respostas": [promotores, neutros, detratores],
})

fig_nps = px.pie(
    nps_df,
    names="Grupo",
    values="Respostas",
    title="Distribuição do NPS",
    color="Grupo",
    color_discrete_map={
        "Promotores (9-10)": "#2e9e5b",
        "Neutros (7-8)": "#f2b84b",
        "Detratores (0-6)": "#d9534f",
    },
)
st.plotly_chart(fig_nps, width="stretch")

col_a, col_b = st.columns(2)

fig_faixa = px.pie(df, names="faixa_etaria", title="Faixa etária")
col_a.plotly_chart(fig_faixa, width="stretch")

contagem = df["tipo_atendimento"].value_counts().reset_index()
contagem.columns = ["Tipo de atendimento", "Respostas"]

fig_tipo = px.bar(
    contagem,
    x="Tipo de atendimento",
    y="Respostas",
    title="Respostas por tipo de atendimento",
)
col_b.plotly_chart(fig_tipo, width="stretch")

def comentarios_validos(serie):
    serie = serie.dropna().astype(str).str.strip()
    ignorar = ["nada", "nenhum", "nenhuma", "não", "nao", "-", "."]
    return serie[~serie.str.lower().isin(ignorar) & (serie.str.len() > 1)]

elogios = comentarios_validos(df["elogios"])
melhorias = comentarios_validos(df["melhorias"])

st.subheader("O que os pacientes disseram")

aba1, aba2 = st.tabs(["Elogios", "Pontos a melhorar"])

aba1.dataframe(elogios.to_frame("Comentário"), width="stretch", hide_index=True)
aba2.dataframe(melhorias.to_frame("Comentário"), width="stretch", hide_index=True)

