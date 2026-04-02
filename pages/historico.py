"""
Página: Evolução Histórica
Análise de tendências e comparativos entre períodos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database import compilar_historico, listar_periodos
from src.auth import inicializar_sessao


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(page_title="Histórico", page_icon="📈", layout="wide")

inicializar_sessao()


# ============================================================
# TÍTULO
# ============================================================

st.title("📈 Evolução Histórica e Tendências")
st.markdown("Comparativo de indicadores ao longo dos períodos cadastrados")

st.divider()


# ============================================================
# CARREGAR DADOS
# ============================================================

df_periodos = listar_periodos(apenas_ativos=False)

if df_periodos.empty or len(df_periodos) < 2:
    st.warning("⚠️ É necessário ter pelo menos 2 períodos cadastrados para visualizar tendências.")
    st.info("👉 Importe mais períodos na página **Admin** para habilitar análises históricas.")
    st.stop()

# Compilar dados históricos usando a VIEW
df_historico = compilar_historico()

if df_historico.empty:
    st.error("Erro ao compilar dados históricos.")
    st.stop()


# ============================================================
# MÉTRICAS RESUMO
# ============================================================

st.markdown("### 📊 Visão Geral do Histórico")

col1, col2, col3, col4 = st.columns(4)

total_periodos = len(df_historico)
periodo_mais_recente = df_historico.iloc[0]['mes_referencia'] if not df_historico.empty else "N/A"

col1.metric("📅 Períodos Cadastrados", total_periodos)
col2.metric("🆕 Mais Recente", periodo_mais_recente)

if 'total_alunos' in df_historico.columns:
    total_alunos_historico = df_historico['total_alunos'].sum()
    col3.metric("👨‍🎓 Total de Alunos (Histórico)", f"{total_alunos_historico:,.0f}".replace(',', '.'))

if 'ha_realizado' in df_historico.columns:
    total_ha_historico = df_historico['ha_realizado'].sum()
    col4.metric("✅ Total HA Realizado", f"{total_ha_historico:,.0f}".replace(',', '.'))

st.divider()


# ============================================================
# GRÁFICOS DE TENDÊNCIA
# ============================================================

st.markdown("### 📊 Evolução de Indicadores-Chave")

# Criar abas para diferentes métricas
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Hora-Aluno",
    "👥 Alunos e Turmas",
    "📚 Disciplinas",
    "🏢 Ocupação"
])


# ============================================================
# TAB 1: HORA-ALUNO
# ============================================================

with tab1:
    if 'ha_planejado' in df_historico.columns and 'ha_realizado' in df_historico.columns:
        st.markdown("#### Evolução de Hora-Aluno")
        
        # Calcular percentual de execução
        df_historico['percentual_execucao'] = (
            (df_historico['ha_realizado'] / df_historico['ha_planejado']) * 100
        ).fillna(0)
        
        # Gráfico de linha dupla
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_historico['mes_referencia'],
            y=df_historico['ha_planejado'],
            mode='lines+markers',
            name='HA Planejado',
            line=dict(color='#FFA726', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_historico['mes_referencia'],
            y=df_historico['ha_realizado'],
            mode='lines+markers',
            name='HA Realizado',
            line=dict(color='#66BB6A', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Planejado vs. Realizado',
            xaxis_title='Período',
            yaxis_title='Hora-Aluno',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de percentual de execução
        fig_perc = px.bar(
            df_historico,
            x='mes_referencia',
            y='percentual_execucao',
            text='percentual_execucao',
            title='Percentual de Execução da Meta HA',
            color='percentual_execucao',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig_perc.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_perc.update_layout(
            yaxis=dict(range=[0, 110]),
            showlegend=False
        )
        
        st.plotly_chart(fig_perc, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Média de Execução", f"{df_historico['percentual_execucao'].mean():.1f}%")
        col2.metric("🏆 Melhor Período", f"{df_historico['percentual_execucao'].max():.1f}%")
        col3.metric("📉 Pior Período", f"{df_historico['percentual_execucao'].min():.1f}%")
    
    else:
        st.info("Dados de Hora-Aluno não disponíveis no histórico.")


# ============================================================
# TAB 2: ALUNOS E TURMAS
# ============================================================

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        if 'total_alunos' in df_historico.columns:
            st.markdown("#### Total de Alunos por Período")
            
            fig_alunos = px.bar(
                df_historico,
                x='mes_referencia',
                y='total_alunos',
                text='total_alunos',
                color='total_alunos',
                color_continuous_scale='Blues'
            )
            
            fig_alunos.update_traces(textposition='outside')
            fig_alunos.update_layout(showlegend=False)
            
            st.plotly_chart(fig_alunos, use_container_width=True)
    
    with col2:
        if 'total_turmas' in df_historico.columns:
            st.markdown("#### Total de Turmas por Período")
            
            fig_turmas = px.line(
                df_historico,
                x='mes_referencia',
                y='total_turmas',
                markers=True,
                line_shape='spline'
            )
            
            fig_turmas.update_traces(
                line=dict(color='#E91E63', width=3),
                marker=dict(size=10)
            )
            
            st.plotly_chart(fig_turmas, use_container_width=True)
    
    # Relação Alunos/Turma
    if 'total_alunos' in df_historico.columns and 'total_turmas' in df_historico.columns:
        df_historico['media_alunos_turma'] = (
            df_historico['total_alunos'] / df_historico['total_turmas']
        ).fillna(0)
        
        st.markdown("#### Média de Alunos por Turma")
        
        fig_media = px.area(
            df_historico,
            x='mes_referencia',
            y='media_alunos_turma',
            line_shape='spline'
        )
        
        fig_media.update_traces(
            line=dict(color='#9C27B0'),
            fillcolor='rgba(156, 39, 176, 0.3)'
        )
        
        st.plotly_chart(fig_media, use_container_width=True)


# ============================================================
# TAB 3: DISCIPLINAS
# ============================================================

with tab3:
    st.markdown("#### Status de Disciplinas ao Longo do Tempo")
    
    # Este gráfico requer dados mais detalhados
    # Por enquanto, mostrar mensagem
    st.info("""
    📊 **Análise de Disciplinas por Período**
    
    Para visualizar a evolução de disciplinas (Concluídas, Em Andamento, etc.), 
    seria necessário adicionar campos específicos na VIEW `vw_hora_aluno_resumo`.
    
    **Sugestão de implementação futura:**
    - Adicionar contadores de disciplinas por status na VIEW
    - Criar gráfico de área empilhada mostrando evolução dos status
    """)


# ============================================================
# TAB 4: OCUPAÇÃO
# ============================================================

with tab4:
    st.markdown("#### Evolução da Ocupação Média de Ambientes")
    
    # Buscar dados de ocupação de cada período
    from src.database import obter_ocupacao_media, obter_periodo_por_referencia
    
    ocupacao_historica = []
    
    for _, row in df_periodos.iterrows():
        mes_ref = row['mes_referencia']
        periodo_id = row['id']
        
        df_oc = obter_ocupacao_media(periodo_id)
        
        if not df_oc.empty:
            media_periodo = df_oc['ocupacao_media'].mean()
            ocupacao_historica.append({
                'mes_referencia': mes_ref,
                'ocupacao_media': media_periodo
            })
    
    if ocupacao_historica:
        df_oc_hist = pd.DataFrame(ocupacao_historica)
        
        fig_oc = px.line(
            df_oc_hist,
            x='mes_referencia',
            y='ocupacao_media',
            markers=True,
            line_shape='spline',
            title='Ocupação Média Geral dos Ambientes'
        )
        
        fig_oc.update_traces(
            line=dict(color='#00BCD4', width=3),
            marker=dict(size=10)
        )
        
        fig_oc.update_layout(
            yaxis=dict(range=[0, 100], title='Ocupação (%)'),
            xaxis_title='Período'
        )
        
        st.plotly_chart(fig_oc, use_container_width=True)
        
        # Adicionar linha de meta (exemplo: 70%)
        fig_oc.add_hline(
            y=70,
            line_dash="dash",
            line_color="red",
            annotation_text="Meta: 70%"
        )
        
        st.plotly_chart(fig_oc, use_container_width=True)
    else:
        st.warning("Dados de ocupação insuficientes para análise histórica.")


# ============================================================
# TABELA CONSOLIDADA
# ============================================================

st.divider()
st.markdown("### 📋 Tabela Consolidada - Todos os Períodos")

# Preparar DataFrame para exibição
df_display = df_historico.copy()

# Selecionar e renomear colunas
colunas_exibir = {
    'mes_referencia': 'Período',
}

if 'total_turmas' in df_display.columns:
    colunas_exibir['total_turmas'] = 'Turmas'

if 'total_alunos' in df_display.columns:
    colunas_exibir['total_alunos'] = 'Alunos'

if 'ha_planejado' in df_display.columns:
    colunas_exibir['ha_planejado'] = 'HA Planejado'

if 'ha_realizado' in df_display.columns:
    colunas_exibir['ha_realizado'] = 'HA Realizado'

if 'percentual_execucao' in df_display.columns:
    colunas_exibir['percentual_execucao'] = 'Execução (%)'

df_final = df_display[list(colunas_exibir.keys())].copy()
df_final.columns = list(colunas_exibir.values())

st.dataframe(
    df_final,
    use_container_width=True,
    hide_index=True
)

# Botão de exportação
from src.utils import botao_download_csv

botao_download_csv(
    df_final,
    "historico_consolidado.csv",
    label="📥 Exportar Histórico Consolidado"
)