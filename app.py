import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="Dashboard Enamedistas Avançado", layout="wide")

st.title("📊 Dashboard de Evolução Acadêmica")
st.markdown("Análise estatística e acompanhamento de mudanças de faixas entre simulados.")

# ==============================================================================
# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
# ==============================================================================
@st.cache_data
def carregar_dados():
    arquivo = "Enamedistas 26.1 Notas (1).xlsx"
    # Carrega a aba RESULTADOS pulando as duas primeiras linhas
    df = pd.read_excel(arquivo, sheet_name="RESULTADOS", header=2)
    
    # Incluímos 'SERIE' e 'TURMA' nas colunas importantes
    colunas_desejadas = ['NOME', 'SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA', 'DIFERENÇA', 'SERIE', 'TURMA']
    df = df[colunas_desejadas]
    
    # Remove linhas onde faltam as notas dos simulados
    df = df.dropna(subset=['SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA'])
    
    # Garantimos que Série e Turma sejam tratados como texto para evitar erros de exibição
    df['SERIE'] = df['SERIE'].astype(str).str.strip()
    df['TURMA'] = df['TURMA'].astype(str).str.strip()
    return df

df_notas = carregar_dados()

# ==============================================================================
# 3. REGRAS DE CLASSIFICAÇÃO (FAIXAS DE NOTAS)
# ==============================================================================
def classificar_nota(nota):
    if nota > 60:
        return "> 60"
    elif nota >= 50:
        return "50-60"
    else:
        return "< 50"

df_notas['Grupo S1'] = df_notas['SIMULADO 1 - NOTA'].apply(classificar_nota)
df_notas['Grupo S2'] = df_notas['SIMULADO 2 NOTA'].apply(classificar_nota)

# ==============================================================================
# 4. PAINEL DE FILTROS NA BARRA LATERAL (DINÂMICOS)
# ==============================================================================
st.sidebar.header("🔍 Filtros de Segmentação")

# Filtro 1: Série (P7, P9, P11, etc.)
series_disponiveis = sorted(list(df_notas['SERIE'].unique()))
series_selecionadas = st.sidebar.multiselect("Selecione a(s) Série(s):", options=series_disponiveis, default=series_disponiveis)

# Filtragem intermediária para alimentar o filtro de turmas
df_filtrado_por_serie = df_notas[df_notas['SERIE'].isin(series_selected_ou_nao := series_selecionadas)]

# Filtro 2: Turma (Atualiza dependendo da Série escolhida acima)
turmas_disponiveis = sorted(list(df_filtrado_por_serie['TURMA'].unique()))
turmas_selecionadas = st.sidebar.multiselect("Selecione a(s) Turma(s):", options=turmas_disponiveis, default=turmas_disponiveis)

# Aplicação final dos filtros de Série e Turma na nossa base de dados
df_dashboard = df_filtrado_por_serie[df_filtrado_por_serie['TURMA'].isin(turmas_selecionadas)]

# Opção extra: Destacar um aluno específico se desejado
aluno_busca = st.sidebar.selectbox("Pesquisar Aluno Específico:", options=["Todos"] + sorted(list(df_dashboard['NOME'].unique())))
if aluno_busca != "Todos":
    df_dashboard = df_dashboard[df_dashboard['NOME'] == aluno_busca]

# ==============================================================================
# 5. EXIBIÇÃO DE MÉTRICAS ESTATÍSTICAS (CARDS ESTILO POWER BI)
# ==============================================================================
st.subheader("📈 Visão Geral Estatística")

if not df_dashboard.empty:
    # Agrupamos os cards em colunas: 3 para o Simulado 1 e 3 para o Simulado 2
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    # Cálculos Estatísticos - Simulado 1
    media_s1 = df_dashboard['SIMULADO 1 - NOTA'].mean()
    mediana_s1 = df_dashboard['SIMULADO 1 - NOTA'].median()
    desvio_s1 = df_dashboard['SIMULADO 1 - NOTA'].std()
    
    # Cálculos Estatísticos - Simulado 2
    media_s2 = df_dashboard['SIMULADO 2 NOTA'].mean()
    mediana_s2 = df_dashboard['SIMULADO 2 NOTA'].median()
    desvio_s2 = df_dashboard['SIMULADO 2 NOTA'].std()
    
    # Renderização dos Cards na tela (.2f limita para 2 casas decimais)
    c1.metric(label="Média (Simulado 1)", value=f"{media_s1:.2f}")
    c2.metric(label="Mediana (Simulado 1)", value=f"{mediana_s1:.2f}")
    c3.metric(label="Desvio Padrão (S1)", value=f"{desvio_s1:.2f}" if not pd.isna(desvio_s1) else "0.00")
    
    c4.metric(label="Média (Simulado 2)", value=f"{media_s2:.2f}")
    c5.metric(label="Mediana (Simulado 2)", value=f"{mediana_s2:.2f}")
    c6.metric(label="Desvio Padrão (S2)", value=f"{desvio_s2:.2f}" if not pd.isna(desvio_s2) else "0.00")
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

st.markdown("---")

# ==============================================================================
# 6. MATRIZ DE TRANSIÇÃO (PERCENTUAL DE MUDANÇA DE FAIXA)
# ==============================================================================
st.subheader("🔄 Matriz de Transição de Faixas (%)")
st.markdown("Esta tabela mostra a proporção de alunos que migraram de uma faixa para outra. As **linhas** indicam onde os alunos começaram (S1) e as **colunas** indicam onde terminaram (S2).")

if not df_dashboard.empty:
    # Criamos a tabela cruzada com valores percentuais globais
    matriz_percentual = pd.crosstab(
        df_dashboard['Grupo S1'], 
        df_dashboard['Grupo S2'], 
        normalize='all' # Calcula a porcentagem sobre o total de alunos filtrados
    ) * 100
    
    # Forçamos a ordenação correta das linhas e colunas para ficar intuitivo
    ordem_faixas = ['< 50', '50-60', '> 60']
    matriz_percentual = matriz_percentual.reindex(index=ordem_faixas, columns=ordem_faixas, fill_value=0.0)
    
    # Formatamos visualmente para exibir o símbolo de porcentagem '%'
    matriz_formatada = matriz_percentual.style.format("{:.2f}%").background_gradient(cmap="Blues")
    
    st.table(matriz_formatada)
else:
    st.info("Sem dados para gerar a matriz de transição.")

st.markdown("---")

# ==============================================================================
# 7. INFOGRÁFICOS VISUAIS
# ==============================================================================
st.subheader("📊 Análise Gráfica Complementar")
col_esq, col_dir = st.columns(2)

cores_padrao = {"> 60": "green", "50-60": "orange", "< 50": "red"}

with col_esq:
    fig_evolucao = px.scatter(
        df_dashboard, x="SIMULADO 1 - NOTA", y="SIMULADO 2 NOTA", 
        hover_name="NOME", color="Grupo S2", color_discrete_map=cores_padrao,
        title="Dispersão: Aluno por Aluno (Linhas de Corte em 60)"
    )
    fig_evolucao.add_hline(y=60, line_dash="dash", line_color="red")
    fig_evolucao.add_vline(x=60, line_dash="dash", line_color="red")
    st.plotly_chart(fig_evolucao, use_container_width=True)

with col_dir:
    # Gráfico de barras mostrando quem subiu ou desceu na média
    fig_dif = px.bar(
        df_dashboard.sort_values(by="DIFERENÇA"), x="NOME", y="DIFERENÇA",
        title="Diferença de Pontos (Simulado 2 - Simulado 1)",
        labels={"DIFERENÇA": "Evolução de Pontos", "NOME": "Aluno"}
    )
    st.plotly_chart(fig_dif, use_container_width=True)

# Tabela geral no fim da página
st.subheader("📋 Listagem dos Dados Filtrados")
st.dataframe(df_dashboard[['NOME', 'SERIE', 'TURMA', 'SIMULADO 1 - NOTA', 'SIMULADO 2 NOTA', 'DIFERENÇA', 'Grupo S1', 'Grupo S2']], use_container_width=True)
