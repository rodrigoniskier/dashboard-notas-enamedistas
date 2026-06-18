import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# Define o título da aba do navegador e deixa a página larga (estilo Power BI)
# ==============================================================================
st.set_page_config(page_title="Dashboard Enamedistas", layout="wide")

st.title("📊 Dashboard de Evolução - Enamedistas")
st.markdown("Analise interativamente a evolução dos alunos do Simulado 1 para o Simulado 2.")

# ==============================================================================
# 2. CARREGAMENTO DOS DADOS E LIMPEZA
# ==============================================================================
@st.cache_data # Isso faz com que o arquivo não precise ser relido a cada clique
def carregar_dados():
    # Carrega a aba RESULTADOS, pulando as 2 primeiras linhas vazias/inúteis (header=2)
    arquivo = "Enamedistas 26.1 Notas (1).xlsx"
    df = pd.read_excel(arquivo, sheet_name="RESULTADOS", header=2)
    
    # Filtramos as colunas que realmente importam para esta análise
    colunas_desejadas = ['NOME', 'SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA', 'DIFERENÇA']
    df = df[colunas_desejadas]
    
    # Removemos da tabela alunos que não têm nota registrada
    df = df.dropna(subset=['SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA'])
    return df

df_notas = carregar_dados()

# ==============================================================================
# 3. REGRAS DE CLASSIFICAÇÃO DAS NOTAS
# ==============================================================================
def classificar_nota(nota):
    """Função que avalia o valor da nota e a classifica nos grupos pedidos."""
    if nota > 60:
        return "> 60"
    elif nota >= 50:
        return "50-60"
    else:
        return "< 50"

# Criamos duas colunas novas na tabela aplicando a regra acima
df_notas['Grupo S1'] = df_notas['SIMULADO 1 - NOTA'].apply(classificar_nota)
df_notas['Grupo S2'] = df_notas['SIMULADO 2 NOTA'].apply(classificar_nota)

# ==============================================================================
# 4. INTERFACE: BARRA LATERAL PARA FILTROS
# ==============================================================================
st.sidebar.header("🔍 Filtros")
aluno_busca = st.sidebar.selectbox(
    "Ver evolução de um aluno específico:", 
    options=["Todos os Alunos"] + sorted(list(df_notas['NOME'].unique()))
)

# Se o usuário escolheu um aluno, deixamos apenas aquele aluno na tabela
if aluno_busca != "Todos os Alunos":
    df_filtrado = df_notas[df_notas['NOME'] == aluno_busca]
else:
    df_filtrado = df_notas

# ==============================================================================
# 5. VISUALIZAÇÕES E INFOGRÁFICOS
# ==============================================================================

# -- Seção A: Gráficos de Proporção --
st.subheader("1. Distribuição dos Alunos por Grupo de Notas")
col1, col2 = st.columns(2) # Divide a tela em duas colunas

# Paleta de cores lógica: Vermelho para ruim, amarelo para atenção, verde para bom
cores_padrao = {"> 60": "green", "50-60": "orange", "< 50": "red"}

with col1:
    fig_s1 = px.pie(df_filtrado, names='Grupo S1', title="Grupos - Simulado 1",
                    color='Grupo S1', color_discrete_map=cores_padrao, hole=0.4)
    st.plotly_chart(fig_s1, use_container_width=True)

with col2:
    fig_s2 = px.pie(df_filtrado, names='Grupo S2', title="Grupos - Simulado 2",
                    color='Grupo S2', color_discrete_map=cores_padrao, hole=0.4)
    st.plotly_chart(fig_s2, use_container_width=True)


# -- Seção B: Gráfico de Evolução (Dispersão) --
st.subheader("2. Evolução das Notas: Simulado 1 vs Simulado 2")
st.markdown("💡 *Dica: Passe o mouse por cima dos pontos para ver o nome do aluno. Pontos acima da linha vermelha horizontal representam notas acima do corte no Simulado 2.*")

fig_evolucao = px.scatter(
    df_filtrado, 
    x="SIMULADO 1 - NOTA", 
    y="SIMULADO 2 NOTA", 
    hover_name="NOME",
    color="Grupo S2",
    color_discrete_map=cores_padrao,
    labels={"SIMULADO 1 - NOTA": "Nota no Simulado 1", "SIMULADO 2 NOTA": "Nota no Simulado 2"},
    size_max=10
)

# Desenhamos as linhas de corte no valor de 60!
fig_evolucao.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Corte Simulado 2 (60)")
fig_evolucao.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="Corte Simulado 1 (60)")

# Formatação visual do gráfico
st.plotly_chart(fig_evolucao, use_container_width=True)


# -- Seção C: Tabela de Dados --
st.subheader("3. Tabela Detalhada")
st.dataframe(df_filtrado[['NOME', 'SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA', 'DIFERENÇA', 'Grupo S1', 'Grupo S2']], use_container_width=True)
