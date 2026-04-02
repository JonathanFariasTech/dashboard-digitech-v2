"""
Página: Ocupação e Ambientes
Análise de uso e aproveitamento dos espaços físicos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import (
    obter_periodo_por_referencia,
    listar_ambientes,
    listar_ocupacao,
    obter_ocupacao_media
)
from src.auth import inicializar_sessao
from src.utils import formatar_numero


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

st.set_page_config(page_title="Ocupação", page_icon="🏢", layout="wide")

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

st.title("🏢 Ocupação de Ambientes e Infraestrutura")
st.markdown(f"**Período:** {periodo_atual}")

st.divider()


# ============================================================
# KPIS DE AMBIENTES
# ============================================================

df_ambientes = listar_ambientes(periodo_id)
df_ocupacao = listar_ocupacao(periodo_id, com_ambiente=True)

if df_ambientes.empty:
    st.warning("Nenhum ambiente cadastrado neste período.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

total_ambientes = len(df_ambientes)
ambientes_fisicos = len(df_ambientes[df_ambientes['virtual'] == False])
ambientes_virtuais = len(df_ambientes[df_ambientes['virtual'] == True])

if not df_ocupacao.empty:
    ocupacao_media_geral = df_ocupacao['percentual_ocupacao'].mean()
else:
    ocupacao_media_geral = 0

col1.metric("🏫 Total de Ambientes", total_ambientes)
col2.metric("🏛️ Físicos", ambientes_fisicos)
col3.metric("💻 Virtuais", ambientes_virtuais)
col4.metric("📊 Ocupação Média", f"{ocupacao_media_geral:.1f}%")

st.divider()


# ============================================================
# SELETOR DE VISUALIZAÇÃO
# ============================================================

if df_ocupacao.empty:
    st.info("Nenhum registro de ocupação disponível para este período.")
    st.stop()

tipo_visualizacao = st.selectbox(
    "📊 Selecione o tipo de análise:",
    [
        "Visão Geral (Média por Ambiente)",
        "Evolução Diária (Linha do Tempo)",
        "Mapa de Calor (Ambiente vs. Data)",
        "Análise por Turno"
    ]
)

st.divider()


# ============================================================
# VISUALIZAÇÃO 1: MÉDIA POR AMBIENTE
# ============================================================

if tipo_visualizacao == "Visão Geral (Média por Ambiente)":
    st.markdown("### 📊 Ocupação Média Acumulada por Ambiente")
    
    # Tentar usar VIEW do banco
    df_media = obter_ocupacao_media(periodo_id)
    
    if df_media.empty:
        # Fallback: calcular manualmente
        df_media = df_ocupacao.groupby('ambiente_nome_ambiente')['percentual_ocupacao'].mean().reset_index()
        df_media.columns = ['nome_ambiente', 'ocupacao_media']
    
    df_media = df_media.sort_values('ocupacao_media', ascending=True)
    
    # Gráfico de barras horizontais
    fig = px.bar(
        df_media,
        x='ocupacao_media',
        y='nome_ambiente',
        orientation='h',
        text='ocupacao_media',
        color='ocupacao_media',
        color_continuous_scale='Blues',
        labels={'ocupacao_media': 'Ocupação Média (%)', 'nome_ambiente': 'Ambiente'}
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        xaxis=dict(range=[0, 100]),
        height=max(400, len(df_media) * 35),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    
    col1.metric("🏆 Maior Ocupação", f"{df_media['ocupacao_media'].max():.1f}%")
    col2.metric("📉 Menor Ocupação", f"{df_media['ocupacao_media'].min():.1f}%")
    col3.metric("📊 Desvio Padrão", f"{df_media['ocupacao_media'].std():.1f}%")


# ============================================================
# VISUALIZAÇÃO 2: EVOLUÇÃO DIÁRIA
# ============================================================

elif tipo_visualizacao == "Evolução Diária (Linha do Tempo)":
    st.markdown("### 📈 Evolução da Ocupação ao Longo do Mês")
    
    if 'data_ocupacao' not in df_ocupacao.columns:
        st.error("Coluna 'data_ocupacao' não encontrada nos dados.")
        st.stop()
    
    # Converter data
    df_ocupacao['data_ocupacao'] = pd.to_datetime(df_ocupacao['data_ocupacao'], errors='coerce')
    df_ocupacao = df_ocupacao.dropna(subset=['data_ocupacao'])
    
    if df_ocupacao.empty:
        st.warning("Nenhuma data válida encontrada.")
        st.stop()
    
    # Agrupar por data
    df_diario = df_ocupacao.groupby('data_ocupacao')['percentual_ocupacao'].mean().reset_index()
    df_diario = df_diario.sort_values('data_ocupacao')
    
    # Gráfico de linha
    fig = px.line(
        df_diario,
        x='data_ocupacao',
        y='percentual_ocupacao',
        markers=True,
        labels={'data_ocupacao': 'Data', 'percentual_ocupacao': 'Ocupação Média (%)'}
    )
    
    fig.update_traces(
        line=dict(color='#1E88E5', width=3),
        marker=dict(size=8)
    )
    
    fig.update_layout(
        yaxis=dict(range=[0, 100]),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise de tendência
    if len(df_diario) > 1:
        primeira_semana = df_diario.head(7)['percentual_ocupacao'].mean()
        ultima_semana = df_diario.tail(7)['percentual_ocupacao'].mean()
        variacao = ultima_semana - primeira_semana
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Primeira Semana", f"{primeira_semana:.1f}%")
        col2.metric("📅 Última Semana", f"{ultima_semana:.1f}%", delta=f"{variacao:+.1f}%")
        col3.metric("📊 Pico de Ocupação", f"{df_diario['percentual_ocupacao'].max():.1f}%")


# ============================================================
# VISUALIZAÇÃO 3: MAPA DE CALOR
# ============================================================

elif tipo_visualizacao == "Mapa de Calor (Ambiente vs. Data)":
    st.markdown("### 🔥 Mapa de Calor - Ocupação Diária por Ambiente")
    st.caption("Cores mais intensas indicam maior ocupação")
    
    if 'data_ocupacao' not in df_ocupacao.columns:
        st.error("Coluna 'data_ocupacao' não encontrada.")
        st.stop()
    
    # Preparar dados
    df_heat = df_ocupacao.copy()
    df_heat['data_ocupacao'] = pd.to_datetime(df_heat['data_ocupacao'], errors='coerce')
    df_heat = df_heat.dropna(subset=['data_ocupacao'])
    
    if df_heat.empty:
        st.warning("Nenhuma data válida para gerar mapa de calor.")
        st.stop()
    
    df_heat['dia_formatado'] = df_heat['data_ocupacao'].dt.strftime('%d/%m')
    
    # Criar pivot table
    pivot = df_heat.pivot_table(
        index='ambiente_nome_ambiente',
        columns='dia_formatado',
        values='percentual_ocupacao',
        aggfunc='mean'
    )
    
    if pivot.empty:
        st.warning("Dados insuficientes para gerar mapa de calor.")
        st.stop()
    
    # Gráfico
    fig = px.imshow(
        pivot,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale='YlOrRd',
        labels=dict(x="Dia do Mês", y="Ambiente", color="Ocupação (%)")
    )
    
    fig.update_layout(
        height=max(400, len(pivot) * 30)
    )
    
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# VISUALIZAÇÃO 4: ANÁLISE POR TURNO
# ============================================================

elif tipo_visualizacao == "Análise por Turno":
    st.markdown("### 🕐 Ocupação por Turno")
    
    if 'turno' not in df_ocupacao.columns or df_ocupacao['turno'].isna().all():
        st.warning("Dados de turno não disponíveis neste período.")
    else:
        df_turnos = df_ocupacao.groupby('turno')['percentual_ocupacao'].agg(['mean', 'count']).reset_index()
        df_turnos.columns = ['Turno', 'Ocupação Média (%)', 'Registros']
        df_turnos = df_turnos.sort_values('Ocupação Média (%)', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(
                df_turnos,
                x='Turno',
                y='Ocupação Média (%)',
                text='Ocupação Média (%)',
                color='Turno',
                title='Ocupação Média por Turno'
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_bar.update_layout(showlegend=False, yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(
                df_turnos,
                names='Turno',
                values='Registros',
                title='Distribuição de Registros por Turno',
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.dataframe(df_turnos, use_container_width=True, hide_index=True)


# ============================================================
# TABELA DE AMBIENTES
# ============================================================

st.divider()
st.markdown("### 🏫 Cadastro de Ambientes")

df_amb_display = df_ambientes[['nome_ambiente', 'tipo', 'capacidade', 'virtual']].copy()
df_amb_display.columns = ['Nome', 'Tipo', 'Capacidade', 'Virtual']

# Filtros
col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    filtro_tipo = st.multiselect(
        "Filtrar por Tipo:",
        df_amb_display['Tipo'].unique(),
        default=df_amb_display['Tipo'].unique()
    )

with col_filtro2:
    filtro_virtual = st.radio(
        "Mostrar:",
        ['Todos', 'Apenas Físicos', 'Apenas Virtuais'],
        horizontal=True
    )

# Aplicar filtros
df_filtrado = df_amb_display[df_amb_display['Tipo'].isin(filtro_tipo)]

if filtro_virtual == 'Apenas Físicos':
    df_filtrado = df_filtrado[df_filtrado['Virtual'] == False]
elif filtro_virtual == 'Apenas Virtuais':
    df_filtrado = df_filtrado[df_filtrado['Virtual'] == True]

st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Virtual': st.column_config.CheckboxColumn('Virtual'),
        'Capacidade': st.column_config.NumberColumn('Capacidade', format="%d")
    }
)