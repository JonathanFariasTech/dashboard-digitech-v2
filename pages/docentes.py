"""
Página: Análise de Docentes (RH)
Análise de instrutores, carga horária e não regência
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import (
    obter_periodo_por_referencia,
    listar_instrutores,
    listar_nao_regencia,
    obter_ranking_nao_regencia
)
from src.auth import inicializar_sessao
from src.utils import formatar_numero, formatar_data, botao_download_csv


# ============================================================
# CONFIGURAÇÃO
# ============================================================

def safe_number(value, default=0):
    """Converte valor para número de forma segura"""
    if value is None:
        return default
    try:
        import pandas as pd
        if isinstance(value, (int, float)) and pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

st.set_page_config(page_title="Docentes", page_icon="👥", layout="wide")

inicializar_sessao()


# ============================================================
# VERIFICAÇÕES
# ============================================================

periodo_atual = st.session_state.get('periodo_selecionado')

if not periodo_atual:
    st.warning("⚠️ Nenhum período selecionado. Volte à página inicial.")
    st.stop()

periodo_data = obter_periodo_por_referencia(periodo_atual)
if not periodo_data:
    st.error("Erro ao carregar dados do período.")
    st.stop()

periodo_id = periodo_data['id']


# ============================================================
# TÍTULO
# ============================================================

st.title("👥 Análise de Docentes e Recursos Humanos")
st.markdown(f"**Período:** {periodo_atual}")

st.divider()


# ============================================================
# KPIS GERAIS
# ============================================================

df_instrutores = listar_instrutores(periodo_id)
df_nr = listar_nao_regencia(periodo_id, com_instrutor=True)

if df_instrutores.empty:
    st.warning("Nenhum instrutor cadastrado neste período.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

total_instrutores = len(df_instrutores)
instrutores_ativos = len(df_instrutores[df_instrutores['ativo'] == True])
total_horas_nr = df_nr['horas'].sum() if not df_nr.empty else 0
media_horas_nr = total_horas_nr / total_instrutores if total_instrutores > 0 else 0

col1.metric("👨‍🏫 Total de Instrutores", total_instrutores)
col2.metric("✅ Ativos", instrutores_ativos)
col3.metric("⏰ Total Horas NR", formatar_numero(total_horas_nr, 1))
col4.metric("📊 Média Horas NR", formatar_numero(media_horas_nr, 1))

st.divider()


# ============================================================
# RANKING DE NÃO REGÊNCIA
# ============================================================

st.markdown("### 📊 Ranking de Horas de Não Regência")

if df_nr.empty:
    st.info("Nenhum registro de não regência neste período.")
else:
    # Usar a VIEW do banco se disponível
    df_ranking = obter_ranking_nao_regencia(periodo_id)
    
    if df_ranking.empty:
        # Fallback: calcular manualmente
        df_ranking = df_nr.groupby('instrutor_nome_completo')['horas'].sum().reset_index()
        df_ranking.columns = ['nome_completo', 'total_horas_nr']
        df_ranking = df_ranking.sort_values('total_horas_nr', ascending=False)
    else:
        df_ranking = df_ranking.sort_values('total_horas_nr', ascending=True)
    
    # Limitar top 15 para visualização
    top_15 = df_ranking.head(15).copy()
    
    # Gráfico de barras horizontais
    fig = px.bar(
        top_15,
        x='total_horas_nr',
        y='nome_completo',
        orientation='h',
        text='total_horas_nr',
        color='total_horas_nr',
        color_continuous_scale='Oranges',
        labels={'total_horas_nr': 'Horas', 'nome_completo': 'Instrutor'}
    )
    
    fig.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
    fig.update_layout(
        showlegend=False,
        height=max(400, len(top_15) * 35)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar se há percentual disponível
    if 'percentual_nr' in df_ranking.columns:
        st.caption("💡 O percentual indica a proporção das horas de não regência em relação à carga horária contratual.")

st.divider()


# ============================================================
# DETALHAMENTO POR TIPO DE ATIVIDADE
# ============================================================

if not df_nr.empty:
    st.markdown("### 📋 Distribuição por Tipo de Atividade")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de Pizza
        atividades = df_nr.groupby('tipo_atividade')['horas'].sum().reset_index()
        atividades = atividades.sort_values('horas', ascending=False)
        
        fig_pizza = px.pie(
            atividades,
            names='tipo_atividade',
            values='horas',
            title='Horas por Tipo de Atividade',
            hole=0.4
        )
        
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        # Tabela resumo
        st.markdown("**Resumo por Atividade:**")
        atividades['percentual'] = (atividades['horas'] / atividades['horas'].sum() * 100).round(1)
        atividades.columns = ['Tipo de Atividade', 'Horas', '% do Total']
        
        st.dataframe(
            atividades,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Horas': st.column_config.NumberColumn(format="%.1f"),
                '% do Total': st.column_config.NumberColumn(format="%.1f%%")
            }
        )
    
    st.divider()


# ============================================================
# TABELA DETALHADA DE NÃO REGÊNCIA
# ============================================================

if not df_nr.empty:
    st.markdown("### 📑 Registro Detalhado de Não Regência")
    
    # Preparar DataFrame para exibição
    df_exibicao = df_nr.copy()
    
    # Formatar datas
    if 'data_inicio' in df_exibicao.columns:
        df_exibicao['data_inicio'] = pd.to_datetime(df_exibicao['data_inicio'], errors='coerce')
        df_exibicao['data_inicio'] = df_exibicao['data_inicio'].apply(
            lambda x: formatar_data(x) if pd.notna(x) else '-'
        )
    
    if 'data_fim' in df_exibicao.columns:
        df_exibicao['data_fim'] = pd.to_datetime(df_exibicao['data_fim'], errors='coerce')
        df_exibicao['data_fim'] = df_exibicao['data_fim'].apply(
            lambda x: formatar_data(x) if pd.notna(x) else '-'
        )
    
    # Selecionar colunas para exibir
    colunas_display = []
    
    if 'data_inicio' in df_exibicao.columns and 'data_fim' in df_exibicao.columns:
        colunas_display = ['data_inicio', 'data_fim', 'instrutor_nome_completo', 'tipo_atividade', 'horas']
        nomes_colunas = ['Data Início', 'Data Fim', 'Instrutor', 'Tipo de Atividade', 'Horas']
    else:
        colunas_display = ['instrutor_nome_completo', 'tipo_atividade', 'horas']
        nomes_colunas = ['Instrutor', 'Tipo de Atividade', 'Horas']
    
    # Filtro por instrutor
    lista_instrutores = ['Todos'] + sorted(df_exibicao['instrutor_nome_completo'].unique().tolist())
    instrutor_filtro = st.selectbox("Filtrar por Instrutor:", lista_instrutores)
    
    if instrutor_filtro != 'Todos':
        df_exibicao = df_exibicao[df_exibicao['instrutor_nome_completo'] == instrutor_filtro]
    
    # Exibir tabela
    df_final = df_exibicao[colunas_display].copy()
    df_final.columns = nomes_colunas
    
    st.dataframe(df_final, use_container_width=True, hide_index=True)
    
    # Botão de exportação
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        botao_download_csv(
            df_final,
            f"nao_regencia_{periodo_atual.replace(' ', '_')}.csv",
            label="📥 Exportar para CSV"
        )
    
    with col2:
        st.metric("📊 Total de Registros", len(df_final))


# ============================================================
# LISTA DE INSTRUTORES
# ============================================================

st.divider()
st.markdown("### 👨‍🏫 Cadastro de Instrutores")

df_inst_display = df_instrutores[['nome_completo', 'especialidade', 'carga_horaria_contrato', 'tipo_vinculo', 'ativo']].copy()
df_inst_display.columns = ['Nome', 'Especialidade', 'CH Contrato', 'Vínculo', 'Ativo']

# Filtro por status
filtro_status = st.radio(
    "Filtrar por:",
    ['Todos', 'Apenas Ativos', 'Apenas Inativos'],
    horizontal=True
)

if filtro_status == 'Apenas Ativos':
    df_inst_display = df_inst_display[df_inst_display['Ativo'] == True]
elif filtro_status == 'Apenas Inativos':
    df_inst_display = df_inst_display[df_inst_display['Ativo'] == False]

st.dataframe(
    df_inst_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Ativo': st.column_config.CheckboxColumn('Ativo')
    }
)

col1, col2 = st.columns(2)
with col1:
    botao_download_csv(
        df_inst_display,
        f"instrutores_{periodo_atual.replace(' ', '_')}.csv",
        label="📥 Exportar Lista de Instrutores"
    )