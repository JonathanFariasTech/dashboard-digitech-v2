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
from src.utils import formatar_numero, aplicar_estilo_status, safe_number


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

st.set_page_config(page_title="Visão 360º", page_icon="🌐", layout="wide")

inicializar_sessao()


# ============================================================
# VERIFICAÇÕES
# ============================================================

periodo_atual = st.session_state.get('periodo_selecionado')

if not periodo_atual:
    st.warning("⚠️ Nenhum período selecionado. Volte à página inicial.")
    st.stop()

try:
    periodo_data = obter_periodo_por_referencia(periodo_atual)
except Exception as e:
    st.error(f"Erro ao carregar período: {str(e)}")
    periodo_data = None

if not periodo_data:
    st.error("Erro ao carregar dados do período.")
    st.stop()

periodo_id = periodo_data.get('id')

if not periodo_id:
    st.error("ID do período não encontrado.")
    st.stop()


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

try:
    resumo = obter_resumo_hora_aluno(periodo_id)
except Exception as e:
    st.warning(f"Erro ao obter resumo: {str(e)}")
    resumo = {}

# ✅ CORREÇÃO: Usar safe_number para tratar valores None
meta_ha = safe_number(resumo.get('meta_hora_aluno'), 0)
ha_planejado = safe_number(resumo.get('ha_planejado'), 0)
ha_realizado = safe_number(resumo.get('ha_realizado'), 0)

# Se meta é 0, usa planejado como meta
if meta_ha == 0:
    meta_ha = ha_planejado
    tipo_meta = "Automática (Planilha)"
else:
    tipo_meta = "Manual (Definida pelo Admin)"

# ✅ CORREÇÃO: Agora meta_ha é garantidamente um número
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
try:
    df_disc = listar_disciplinas(periodo_id, com_turma=True)
except Exception as e:
    st.error(f"Erro ao listar disciplinas: {str(e)}")
    df_disc = pd.DataFrame()

if df_disc.empty:
    st.info("📭 Nenhuma disciplina cadastrada para este período.")
else:
    # ✅ CORREÇÃO: Verificar se colunas existem antes de usar
    carga_horaria_col = 'carga_horaria' if 'carga_horaria' in df_disc.columns else None
    vagas_col = 'turma_vagas_ocupadas' if 'turma_vagas_ocupadas' in df_disc.columns else None
    
    if carga_horaria_col and vagas_col:
        # Calcular HA por turma (com tratamento de valores nulos)
        df_disc['ha_total'] = df_disc.apply(
            lambda row: safe_number(row.get(carga_horaria_col), 0) * safe_number(row.get(vagas_col), 0),
            axis=1
        )
    else:
        df_disc['ha_total'] = 0
        st.warning("Colunas de carga horária ou vagas não encontradas.")
    
    # Criar identificador de turma
    if 'turma_nome_turma' in df_disc.columns and 'turma_codigo_turma' in df_disc.columns:
        df_disc['turma_display'] = (
            df_disc['turma_codigo_turma'].astype(str) + " - " + 
            df_disc['turma_nome_turma'].fillna('').astype(str)
        )
    elif 'turma_codigo_turma' in df_disc.columns:
        df_disc['turma_display'] = "Turma " + df_disc['turma_codigo_turma'].astype(str)
    else:
        df_disc['turma_display'] = "Turma " + df_disc.index.astype(str)
    
    # Verificar se coluna status existe
    if 'status' not in df_disc.columns:
        st.warning("Coluna 'status' não encontrada nas disciplinas.")
        df_disc['status'] = 'Não Definido'
    
    # Agrupar por turma
    try:
        resumo_turmas = df_disc.groupby('turma_display').apply(
            lambda x: pd.Series({
                'ha_meta': safe_number(x['ha_total'].sum(), 0),
                'ha_realizado': safe_number(
                    x[x['status'].str.upper().isin(['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO'])]['ha_total'].sum(), 
                    0
                )
            })
        ).reset_index()
        
        # ✅ CORREÇÃO: Cálculo seguro do progresso
        resumo_turmas['progresso_pct'] = resumo_turmas.apply(
            lambda row: (row['ha_realizado'] / row['ha_meta'] * 100) if row['ha_meta'] > 0 else 0,
            axis=1
        ).fillna(0).round(1)
        
        # Ordenar por progresso
        resumo_turmas = resumo_turmas.sort_values('progresso_pct', ascending=True)
        
        if not resumo_turmas.empty:
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
                xaxis=dict(range=[0, 110]),
                height=max(400, len(resumo_turmas) * 30),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Expander com detalhamento
            with st.expander("🔍 Ver detalhamento de disciplinas por turma"):
                turmas_lista = resumo_turmas['turma_display'].unique().tolist()
                
                if turmas_lista:
                    turma_sel = st.selectbox(
                        "Selecione uma turma:",
                        turmas_lista
                    )
                    
                    # Filtrar disciplinas da turma selecionada
                    df_detalhe = df_disc[df_disc['turma_display'] == turma_sel].copy()
                    
                    # Selecionar colunas disponíveis
                    colunas_exibir = []
                    if 'nome_disciplina' in df_detalhe.columns:
                        colunas_exibir.append('nome_disciplina')
                    if 'carga_horaria' in df_detalhe.columns:
                        colunas_exibir.append('carga_horaria')
                    if 'status' in df_detalhe.columns:
                        colunas_exibir.append('status')
                    if 'ha_total' in df_detalhe.columns:
                        colunas_exibir.append('ha_total')
                    
                    if colunas_exibir:
                        df_detalhe_exibir = df_detalhe[colunas_exibir].copy()
                        
                        # Renomear colunas
                        rename_map = {
                            'nome_disciplina': 'Disciplina',
                            'carga_horaria': 'CH',
                            'status': 'Status',
                            'ha_total': 'Hora-Aluno'
                        }
                        df_detalhe_exibir = df_detalhe_exibir.rename(
                            columns={k: v for k, v in rename_map.items() if k in df_detalhe_exibir.columns}
                        )
                        
                        # Aplicar estilo se coluna Status existir
                        if 'Status' in df_detalhe_exibir.columns:
                            try:
                                df_styled = aplicar_estilo_status(df_detalhe_exibir, 'Status')
                                st.dataframe(df_styled, use_container_width=True, hide_index=True)
                            except Exception:
                                st.dataframe(df_detalhe_exibir, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_detalhe_exibir, use_container_width=True, hide_index=True)
                    else:
                        st.info("Sem dados detalhados disponíveis.")
                else:
                    st.info("Nenhuma turma disponível para detalhamento.")
        else:
            st.info("Não foi possível calcular o progresso das turmas.")
    
    except Exception as e:
        st.error(f"Erro ao processar dados das turmas: {str(e)}")
        st.info("Verifique se a planilha foi importada corretamente.")

st.divider()


# ============================================================
# STATUS GERAL DAS DISCIPLINAS
# ============================================================

st.markdown("### 📊 Distribuição de Status das Disciplinas")

if not df_disc.empty and 'status' in df_disc.columns:
    col1, col2 = st.columns(2)
    
    with col1:
        # Contar status (tratando valores nulos)
        df_disc['status_clean'] = df_disc['status'].fillna('Não Definido').astype(str)
        status_count = df_disc['status_clean'].value_counts().reset_index()
        status_count.columns = ['Status', 'Quantidade']
        
        if not status_count.empty:
            fig_pizza = px.pie(
                status_count,
                names='Status',
                values='Quantidade',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Teal
            )
            
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem dados de status para exibir.")
    
    with col2:
        if not status_count.empty:
            fig_barra = px.bar(
                status_count,
                x='Status',
                y='Quantidade',
                text='Quantidade',
                color='Status'
            )
            fig_barra.update_layout(showlegend=False)
            st.plotly_chart(fig_barra, use_container_width=True)
        else:
            st.info("Sem dados de status para exibir.")

else:
    st.info("Sem dados de disciplinas para exibir distribuição de status.")

st.divider()


# ============================================================
# TABELA RESUMO
# ============================================================

st.markdown("### 📋 Resumo Executivo")

if not df_disc.empty and 'status' in df_disc.columns:
    # Contar por status (tratando valores nulos)
    df_disc['status_upper'] = df_disc['status'].fillna('').astype(str).str.upper()
    
    total_disc = len(df_disc)
    concluidas = len(df_disc[df_disc['status_upper'].isin(['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO'])])
    em_andamento = len(df_disc[df_disc['status_upper'].isin(['EM ANDAMENTO', 'ANDAMENTO'])])
    nao_iniciadas = len(df_disc[df_disc['status_upper'].isin(['NÃO INICIADO', 'NAO INICIADO', 'NÃO INICIADA'])])
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("📚 Total Disciplinas", total_disc)
    col2.metric("✅ Concluídas", concluidas)
    col3.metric("🔄 Em Andamento", em_andamento)
    col4.metric("⏸️ Não Iniciadas", nao_iniciadas)

else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📚 Total Disciplinas", 0)
    col2.metric("✅ Concluídas", 0)
    col3.metric("🔄 Em Andamento", 0)
    col4.metric("⏸️ Não Iniciadas", 0)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()
st.caption(f"📊 Visão 360º • {periodo_atual} • Dashboard Digitech v2.0")