"""
Dashboard Digitech v2.0
Página principal e configuração global
"""

import streamlit as st
import pandas as pd
from src.database import testar_conexao, listar_periodos
from src.auth import renderizar_login_sidebar, inicializar_sessao
from src.utils import nome_mes_extenso


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dashboard Digitech v2.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

# Inicializar sessão de autenticação
inicializar_sessao()

# Variáveis de estado globais
if 'periodo_selecionado' not in st.session_state:
    st.session_state['periodo_selecionado'] = None


# ============================================================
# SIDEBAR: LOGIN E NAVEGAÇÃO
# ============================================================

# Renderizar login/logout
renderizar_login_sidebar()

# Testar conexão com banco
st.sidebar.title("🎯 Seleção de Período")

with st.sidebar:
    status_conexao = testar_conexao()
    
    if not status_conexao:
        st.error("❌ Erro de conexão com o banco de dados!")
        st.info("Verifique as credenciais do Supabase em Settings → Secrets")
        st.stop()
    
    # Listar períodos disponíveis
    df_periodos = listar_periodos(apenas_ativos=True)
    
    if df_periodos.empty:
        st.warning("⚠️ Nenhum período cadastrado ainda.")
        st.info("👉 Vá para a página **Admin** para importar a primeira planilha.")
        lista_periodos = []
    else:
        lista_periodos = df_periodos['mes_referencia'].tolist()
    
    if lista_periodos:
        periodo_sel = st.selectbox(
            "📅 Período de Análise:",
            lista_periodos,
            index=0,
            help="Selecione o mês para visualizar os dados"
        )
        
        # Armazenar na sessão
        if periodo_sel != st.session_state['periodo_selecionado']:
            st.session_state['periodo_selecionado'] = periodo_sel
            # Limpar cache ao trocar período
            st.cache_data.clear()
    else:
        st.session_state['periodo_selecionado'] = None
    
    st.divider()
    
    # Filtros globais (disponíveis para todas as páginas)
    st.markdown("### 🔍 Filtros Globais")
    
    # Filtro de turno
    if 'filtro_turno' not in st.session_state:
        st.session_state['filtro_turno'] = 'Todos'
    
    turno_selecionado = st.selectbox(
        "Turno:",
        ['Todos', 'Manhã', 'Tarde', 'Noite', 'Integral', 'EAD'],
        key='filtro_turno'
    )


# ============================================================
# CONTEÚDO PRINCIPAL
# ============================================================

st.title("📊 Dashboard Digitech v2.0")
st.markdown("### Sistema de Gestão Educacional Integrado")

# Verificar se há período selecionado
if not st.session_state['periodo_selecionado']:
    st.info("👈 **Nenhum período selecionado.** Use a barra lateral para escolher um mês.")
    
    # Mostrar informações do sistema
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🎯 Bem-vindo ao Dashboard Digitech!
        
        Este é um sistema completo de gestão educacional que permite:
        
        - ✅ Acompanhamento de **Turmas** e **Alunos**
        - ✅ Controle de **Instrutores** e **Carga Horária**
        - ✅ Monitoramento de **Ocupação de Ambientes**
        - ✅ Gestão de **Hora-Aluno (HA)**
        - ✅ Análise de **Não Regência**
        - ✅ Registro de **Faltas**
        - ✅ Relatórios e **Exportações**
        - ✅ Histórico e **Tendências**
        """)
    
    with col2:
        st.markdown("""
        #### 🚀 Primeiros Passos
        
        **1. Faça Login**
        - Use a barra lateral para autenticar-se
        - Níveis de acesso: Admin, Gestor, Visualizador
        
        **2. Importe Dados**
        - Acesse a página **⚙️ Admin**
        - Faça upload da planilha Excel mensal
        - O sistema detecta automaticamente o período
        
        **3. Explore os Painéis**
        - **🌐 Visão 360º**: Overview geral
        - **👥 Docentes**: Análise de RH
        - **🏢 Ocupação**: Uso de ambientes
        - **📈 Histórico**: Tendências temporais
        - **📑 Relatórios**: Exportações detalhadas
        """)
    
    st.divider()
    
    st.markdown("#### 📊 Status do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_periodos = len(listar_periodos(apenas_ativos=False))
    periodos_ativos = len(listar_periodos(apenas_ativos=True))
    
    col1.metric("🗓️ Períodos Cadastrados", total_periodos)
    col2.metric("✅ Períodos Ativos", periodos_ativos)
    col3.metric("🔌 Conexão BD", "🟢 Online" if status_conexao else "🔴 Offline")
    col4.metric("📦 Versão", "2.0.0")
    
else:
    # Período selecionado - mostrar resumo rápido
    periodo_atual = st.session_state['periodo_selecionado']
    
    st.success(f"📅 **Período ativo:** {nome_mes_extenso(periodo_atual)}")
    
    # Importar funções necessárias
    from src.database import (
        obter_periodo_por_referencia,
        listar_turmas,
        listar_instrutores,
        listar_ambientes,
        obter_resumo_hora_aluno
    )
    
    # Obter dados do período
    periodo_data = obter_periodo_por_referencia(periodo_atual)
    
    if periodo_data:
        periodo_id = periodo_data['id']
        
        # KPIs Gerais
        st.markdown("### 📈 Indicadores Principais")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Carregar dados
        df_turmas = listar_turmas(periodo_id)
        df_instrutores = listar_instrutores(periodo_id)
        df_ambientes = listar_ambientes(periodo_id, apenas_fisicos=True)
        resumo_ha = obter_resumo_hora_aluno(periodo_id)
        
        # Exibir métricas
        col1.metric(
            "🎓 Turmas Ativas",
            len(df_turmas) if not df_turmas.empty else 0
        )
        
        col2.metric(
            "👨‍🎓 Total de Alunos",
            int(df_turmas['vagas_ocupadas'].sum()) if not df_turmas.empty else 0
        )
        
        col3.metric(
            "👨‍🏫 Instrutores",
            len(df_instrutores) if not df_instrutores.empty else 0
        )
        
        col4.metric(
            "🏫 Ambientes Físicos",
            len(df_ambientes) if not df_ambientes.empty else 0
        )
        
        # Progresso de Hora-Aluno
        ha_planejado = resumo_ha.get('ha_planejado', 0)
        ha_realizado = resumo_ha.get('ha_realizado', 0)
        meta_ha = resumo_ha.get('meta_hora_aluno', ha_planejado)
        
        if meta_ha > 0:
            progresso_ha = (ha_realizado / meta_ha) * 100
        else:
            progresso_ha = 0
        
        col5.metric(
            "🎯 Progresso HA",
            f"{progresso_ha:.1f}%"
        )
        
        # Barra de progresso
        st.markdown("#### 🎯 Meta de Hora-Aluno")
        st.progress(min(int(progresso_ha), 100))
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("📚 Meta HA", f"{meta_ha:,.0f}".replace(',', '.'))
        col_b.metric("✅ Realizado", f"{ha_realizado:,.0f}".replace(',', '.'))
        col_c.metric("📊 Planejado", f"{ha_planejado:,.0f}".replace(',', '.'))
        
        st.divider()
        
        # Distribuição de Turmas por Turno
        if not df_turmas.empty:
            st.markdown("### 📊 Visão Rápida")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🕐 Turmas por Turno")
                turmas_por_turno = df_turmas['turno'].value_counts().reset_index()
                turmas_por_turno.columns = ['Turno', 'Quantidade']
                
                import plotly.express as px
                fig = px.bar(
                    turmas_por_turno,
                    x='Turno',
                    y='Quantidade',
                    color='Turno',
                    text='Quantidade'
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 👥 Alunos por Turno")
                alunos_por_turno = df_turmas.groupby('turno')['vagas_ocupadas'].sum().reset_index()
                alunos_por_turno.columns = ['Turno', 'Alunos']
                
                fig2 = px.pie(
                    alunos_por_turno,
                    names='Turno',
                    values='Alunos',
                    hole=0.4
                )
                fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        
        st.info("""
        👈 **Navegue pelos painéis** no menu lateral para análises detalhadas:
        - **🌐 Visão 360º**: Acompanhamento completo de disciplinas e progresso por turma
        - **👥 Docentes**: Análise de carga horária e não regência
        - **🏢 Ocupação**: Uso e aproveitamento de ambientes
        - **📈 Histórico**: Evolução ao longo dos meses
        - **📑 Relatórios**: Exportação de dados filtrados
        """)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("📊 Dashboard Digitech v2.0")

with col2:
    st.caption("🔒 Powered by Supabase + Streamlit")

with col3:
    if status_conexao:
        st.caption("🟢 Sistema Online")
    else:
        st.caption("🔴 Sistema Offline")