"""
Página: Visão 360º
Visão geral completa do período selecionado
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import (
    obter_periodo_por_referencia,
    listar_disciplinas,
    obter_resumo_hora_aluno
)
from src.auth import inicializar_sessao
from src.utils import formatar_numero, aplicar_estilo_status


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(page_title="Visão 360º", page_icon="🌐", layout="wide")

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

st.title("🌐 Visão 360º - Panorama Completo")
st.markdown(f"**Período:** {periodo_atual}")

st.divider()


# ============================================================
# RESUMO DE HORA-ALUNO
# ============================================================

st.markdown("### 🎯 Execução de Hora-Aluno (HA)")

resumo = obter_resumo_hora_aluno(periodo_id)

meta_ha = resumo.get('meta_hora_aluno', 0)
ha_planejado = resumo.get('ha_planejado', 0)
ha_realizado = resumo.get('ha_realizado', 0)

# Se meta é 0, usa planejado como meta
if meta_ha == 0:
    meta_ha = ha_planejado
    tipo_meta = "Automática (Planilha)"
else:
    tipo_meta = "Manual (Definida pelo Admin)"

progresso = (ha_realizado / meta_ha * 100) if meta_ha > 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric(
    f"📚 Meta HA - {tipo_meta}",
    formatar_numero(meta_ha)
)

col2.metric(
    "✅ Realizado",
    formatar_numero(ha_realizado)
)

col3.metric(
    "🚀 Progresso",
    f"{progresso:.1f}%"
)

st.progress(min(int(progresso), 100))

st.divider()


# ============================================================
# PROGRESSO POR TURMA
# ============================================================

st.markdown("### 🏁 Progresso de Conclusão por Turma")
st.caption("Percentual de disciplinas concluídas por turma")

# Carregar disciplinas com dados da turma
df_disc = listar_disciplinas(periodo_id, com_turma=True)

if df_disc.empty:
    st.info("Nenhuma disciplina cadastrada para este período.")
else:
    # Calcular HA por turma
    df_disc['ha_total'] = df_disc['carga_horaria'] * df_disc['turma_vagas_ocupadas']
    
    # Criar identificador de turma
    if 'turma_nome_turma' in df_disc.columns:
        df_disc['turma_display'] = (
            df_disc['turma_codigo_turma'].astype(str) + " - " + 
            df_disc['turma_nome_turma'].astype(str)
        )
    else:
        df_disc['turma_display'] = "Turma " + df_disc['turma_codigo_turma'].astype(str)
    
    # Agrupar por turma
    resumo_turmas = df_disc.groupby('turma_display').apply(
        lambda x: pd.Series({
            'ha_meta': x['ha_total'].sum(),
            'ha_realizado': x[x['status'] == 'Concluído']['ha_total'].sum()
        })
    ).reset_index()
    
    resumo_turmas['progresso_pct'] = (
        (resumo_turmas['ha_realizado'] / resumo_turmas['ha_meta']) * 100
    ).fillna(0).round(1)
    
    # Ordenar por progresso
    resumo_turmas = resumo_turmas.sort_values('progresso_pct', ascending=True)
    
    # Gráfico de barras horizontais
    fig = px.bar(
        resumo_turmas,
        x='progresso_pct',
        y='turma_display',
        orientation='h',
        text='progresso_pct',
        color='progresso_pct',
        color_continuous_scale='Greens',
        labels={'progresso_pct': 'Conclusão (%)', 'turma_display': ''}
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        xaxis=dict(range=[0, 100]),
        height=max(400, len(resumo_turmas) * 30),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Expander com detalhamento
    with st.expander("🔍 Ver detalhamento de disciplinas por turma"):
        turma_sel = st.selectbox(
            "Selecione uma turma:",
            resumo_turmas['turma_display'].unique()
        )
        
        df_detalhe = df_disc[df_disc['turma_display'] == turma_sel][
            ['nome_disciplina', 'carga_horaria', 'status', 'ha_total']
        ].copy()
        
        df_detalhe.columns = ['Disciplina', 'CH', 'Status', 'Hora-Aluno']
        
        # Aplicar estilo
        try:
            df_styled = aplicar_estilo_status(df_detalhe, 'Status')
            st.dataframe(df_styled, use_container_width=True, hide_index=True)
        except:
            st.dataframe(df_detalhe, use_container_width=True, hide_index=True)

st.divider()


# ============================================================
# STATUS GERAL DAS DISCIPLINAS
# ============================================================

st.markdown("### 📊 Distribuição de Status das Disciplinas")

col1, col2 = st.columns(2)

with col1:
    status_count = df_disc['status'].value_counts().reset_index()
    status_count.columns = ['Status', 'Quantidade']
    
    fig_pizza = px.pie(
        status_count,
        names='Status',
        values='Quantidade',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Teal
    )
    
    st.plotly_chart(fig_pizza, use_container_width=True)

with col2:
    fig_barra = px.bar(
        status_count,
        x='Status',
        y='Quantidade',
        text='Quantidade',
        color='Status'
    )
    fig_barra.update_layout(showlegend=False)
    st.plotly_chart(fig_barra, use_container_width=True)

st.divider()


# ============================================================
# TABELA RESUMO
# ============================================================

st.markdown("### 📋 Resumo Executivo")

col1, col2, col3, col4 = st.columns(4)

col1.metric("📚 Total Disciplinas", len(df_disc))
col2.metric("✅ Concluídas", len(df_disc[df_disc['status'] == 'Concluído']))
col3.metric("🔄 Em Andamento", len(df_disc[df_disc['status'] == 'Em Andamento']))
col4.metric("⏸️ Não Iniciadas", len(df_disc[df_disc['status'] == 'Não Iniciado']))