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
# FUNÇÕES AUXILIARES
# ============================================================

def safe_number(value, default=0):
    """
    Converte valor para número de forma segura
    Trata None, NaN, strings, etc.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return default
        return value
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_number(value, decimals=0):
    """
    Formata número com separador de milhares brasileiro
    Trata valores None/NaN de forma segura
    """
    num = safe_number(value, 0)
    if decimals == 0:
        return f"{int(num):,}".replace(',', '.')
    else:
        return f"{num:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


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
    try:
        status_conexao = testar_conexao()
    except Exception as e:
        status_conexao = False
        st.error(f"❌ Erro de conexão: {str(e)}")
    
    if not status_conexao:
        st.error("❌ Erro de conexão com o banco de dados!")
        st.info("Verifique as credenciais do Supabase em Settings → Secrets")
        st.stop()
    
    # Listar períodos disponíveis
    try:
        df_periodos = listar_periodos(apenas_ativos=True)
    except Exception as e:
        st.error(f"Erro ao listar períodos: {str(e)}")
        df_periodos = pd.DataFrame()
    
    if df_periodos.empty or 'mes_referencia' not in df_periodos.columns:
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
    st.info("👈 **Nenhum período selecionado.** Use a barra lateral para escolher um mês ou importe dados na página Admin.")
    
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
    
    try:
        total_periodos = len(listar_periodos(apenas_ativos=False))
        periodos_ativos = len(listar_periodos(apenas_ativos=True))
    except Exception:
        total_periodos = 0
        periodos_ativos = 0
    
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
    try:
        periodo_data = obter_periodo_por_referencia(periodo_atual)
    except Exception as e:
        st.error(f"Erro ao carregar período: {str(e)}")
        periodo_data = None
    
    if periodo_data:
        periodo_id = periodo_data['id']
        
        # KPIs Gerais
        st.markdown("### 📈 Indicadores Principais")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Carregar dados com tratamento de erro
        try:
            df_turmas = listar_turmas(periodo_id)
        except Exception:
            df_turmas = pd.DataFrame()
        
        try:
            df_instrutores = listar_instrutores(periodo_id)
        except Exception:
            df_instrutores = pd.DataFrame()
        
        try:
            df_ambientes = listar_ambientes(periodo_id, apenas_fisicos=True)
        except Exception:
            df_ambientes = pd.DataFrame()
        
        try:
            resumo_ha = obter_resumo_hora_aluno(periodo_id)
        except Exception:
            resumo_ha = {}
        
        # Exibir métricas com tratamento de valores nulos
        col1.metric(
            "🎓 Turmas Ativas",
            len(df_turmas) if not df_turmas.empty else 0
        )
        
        # ✅ CORREÇÃO: Tratamento seguro para soma de vagas
        if not df_turmas.empty and 'vagas_ocupadas' in df_turmas.columns:
            total_alunos = int(safe_number(df_turmas['vagas_ocupadas'].sum(), 0))
        else:
            total_alunos = 0
        
        col2.metric("👨‍🎓 Total de Alunos", total_alunos)
        
        col3.metric(
            "👨‍🏫 Instrutores",
            len(df_instrutores) if not df_instrutores.empty else 0
        )
        
        col4.metric(
            "🏫 Ambientes Físicos",
            len(df_ambientes) if not df_ambientes.empty else 0
        )
        
        # ✅ CORREÇÃO: Tratamento seguro para valores do resumo
        ha_planejado = safe_number(resumo_ha.get('ha_planejado'), 0)
        ha_realizado = safe_number(resumo_ha.get('ha_realizado'), 0)
        meta_ha = safe_number(resumo_ha.get('meta_hora_aluno'), 0)
        
        # Se meta é 0, usa planejado como meta
        if meta_ha == 0:
            meta_ha = ha_planejado
        
        # Calcular progresso de forma segura
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
        
        # ✅ CORREÇÃO: Usando format_number seguro
        col_a.metric("📚 Meta HA", format_number(meta_ha))
        col_b.metric("✅ Realizado", format_number(ha_realizado))
        col_c.metric("📊 Planejado", format_number(ha_planejado))
        
        st.divider()
        
        # Distribuição de Turmas por Turno
        if not df_turmas.empty and 'turno' in df_turmas.columns:
            st.markdown("### 📊 Visão Rápida")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🕐 Turmas por Turno")
                turmas_por_turno = df_turmas['turno'].value_counts().reset_index()
                turmas_por_turno.columns = ['Turno', 'Quantidade']
                
                if not turmas_por_turno.empty:
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
                else:
                    st.info("Sem dados de turno disponíveis")
            
            with col2:
                st.markdown("#### 👥 Alunos por Turno")
                
                if 'vagas_ocupadas' in df_turmas.columns:
                    alunos_por_turno = df_turmas.groupby('turno')['vagas_ocupadas'].sum().reset_index()
                    alunos_por_turno.columns = ['Turno', 'Alunos']
                    
                    if not alunos_por_turno.empty and alunos_por_turno['Alunos'].sum() > 0:
                        import plotly.express as px
                        fig2 = px.pie(
                            alunos_por_turno,
                            names='Turno',
                            values='Alunos',
                            hole=0.4
                        )
                        fig2.update_layout(height=300)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Sem dados de alunos por turno")
                else:
                    st.info("Coluna 'vagas_ocupadas' não encontrada")
        
        st.divider()
        
        st.info("""
        👈 **Navegue pelos painéis** no menu lateral para análises detalhadas:
        - **🌐 Visão 360º**: Acompanhamento completo de disciplinas e progresso por turma
        - **👥 Docentes**: Análise de carga horária e não regência
        - **🏢 Ocupação**: Uso e aproveitamento de ambientes
        - **📈 Histórico**: Evolução ao longo dos meses
        - **📑 Relatórios**: Exportação de dados filtrados
        """)
    
    else:
        st.error("❌ Erro ao carregar dados do período selecionado.")
        st.info("Tente selecionar outro período ou verifique se os dados foram importados corretamente.")


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