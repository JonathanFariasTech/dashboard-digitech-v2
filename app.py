"""
Dashboard Digitech v2.0
Página principal com sidebar elegante
"""

import streamlit as st
import pandas as pd
from src.database import testar_conexao, listar_periodos
from src.auth import renderizar_login_sidebar, inicializar_sessao, esta_autenticado, obter_usuario_atual
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
# CSS CUSTOMIZADO PARA SIDEBAR
# ============================================================

st.markdown("""
<style>
    /* ===== SIDEBAR GERAL ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* ===== LOGO/HEADER ===== */
    .sidebar-logo {
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    .sidebar-logo h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sidebar-logo p {
        font-size: 0.75rem;
        opacity: 0.7;
        margin: 0.3rem 0 0 0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* ===== SEÇÕES ===== */
    .sidebar-section {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .sidebar-section-title {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        opacity: 0.6;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    
    /* ===== STATUS BADGES ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-online {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e !important;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* ===== USER INFO ===== */
    .user-info {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.8rem;
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .user-details h4 {
        margin: 0;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .user-details p {
        margin: 0;
        font-size: 0.7rem;
        opacity: 0.7;
    }
    
    /* ===== PERÍODO CARD ===== */
    .periodo-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(139, 92, 246, 0.3);
        text-align: center;
    }
    
    .periodo-card h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .periodo-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.75rem;
        opacity: 0.8;
    }
    
    /* ===== INFO CARDS ===== */
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    .info-row:last-child {
        border-bottom: none;
    }
    
    .info-label {
        font-size: 0.8rem;
        opacity: 0.7;
    }
    
    .info-value {
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* ===== FOOTER ===== */
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        padding: 1rem;
        font-size: 0.7rem;
        opacity: 0.5;
        text-align: center;
        width: inherit;
        background: linear-gradient(0deg, #0f3460 0%, transparent 100%);
    }
    
    /* ===== SELECTBOX CUSTOMIZADO ===== */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: rgba(255,255,255,0.4) !important;
    }
    
    /* ===== BOTÕES ===== */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* ===== DIVIDERS ===== */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
        margin: 1rem 0 !important;
    }
    
    /* ===== EXPANDER ===== */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 8px !important;
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def safe_number(value, default=0):
    """Converte valor para número de forma segura"""
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
    """Formata número com separador de milhares brasileiro"""
    num = safe_number(value, 0)
    if decimals == 0:
        return f"{int(num):,}".replace(',', '.')
    else:
        return f"{num:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


# ============================================================
# INICIALIZAÇÃO
# ============================================================

inicializar_sessao()

if 'periodo_selecionado' not in st.session_state:
    st.session_state['periodo_selecionado'] = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    
    # ===== LOGO/HEADER =====
    st.markdown("""
    <div class="sidebar-logo">
        <h1>📊 Digitech</h1>
        <p>Dashboard Educacional</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== STATUS DA CONEXÃO =====
    try:
        status_conexao = testar_conexao()
    except Exception:
        status_conexao = False
    
    if status_conexao:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span class="status-badge status-online">
                🟢 Sistema Online
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span class="status-badge status-offline">
                🔴 Sistema Offline
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.error("Verifique a conexão com o banco de dados")
        st.stop()
    
    st.divider()
    
    # ===== SEÇÃO: AUTENTICAÇÃO =====
    if not esta_autenticado():
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-section-title">🔐 Acesso ao Sistema</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            senha = st.text_input("Senha:", type="password", placeholder="Digite sua senha")
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("🚀 Entrar", use_container_width=True)
            
            if submitted and senha:
                from src.auth import fazer_login
                if fazer_login(senha):
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
    else:
        # ===== USUÁRIO LOGADO =====
        usuario = obter_usuario_atual()
        nome_usuario = usuario.get('nome', 'Usuário') if usuario else 'Usuário'
        nivel_usuario = usuario.get('nivel', 'VISUALIZADOR') if usuario else 'VISUALIZADOR'
        
        # Emoji baseado no nível
        emoji_nivel = "👑" if nivel_usuario == "ADMIN" else ("⭐" if nivel_usuario == "GESTOR" else "👤")
        
        st.markdown(f"""
        <div class="user-info">
            <div class="user-avatar">{emoji_nivel}</div>
            <div class="user-details">
                <h4>{nome_usuario}</h4>
                <p>{nivel_usuario}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sair", use_container_width=True):
            from src.auth import fazer_logout
            fazer_logout()
            st.rerun()
    
    st.divider()
    
    # ===== SEÇÃO: PERÍODO =====
    st.markdown("""
    <div class="sidebar-section-title">📅 Período de Análise</div>
    """, unsafe_allow_html=True)
    
    try:
        df_periodos = listar_periodos(apenas_ativos=True)
    except Exception:
        df_periodos = pd.DataFrame()
    
    if df_periodos.empty or 'mes_referencia' not in df_periodos.columns:
        st.warning("⚠️ Nenhum período disponível")
        st.info("Importe dados na página Admin")
        lista_periodos = []
    else:
        lista_periodos = df_periodos['mes_referencia'].tolist()
    
    if lista_periodos:
        periodo_sel = st.selectbox(
            "Selecione o período:",
            lista_periodos,
            index=0,
            label_visibility="collapsed"
        )
        
        if periodo_sel != st.session_state.get('periodo_selecionado'):
            st.session_state['periodo_selecionado'] = periodo_sel
            st.cache_data.clear()
        
        # Card do período selecionado
        st.markdown(f"""
        <div class="periodo-card">
            <h3>📆 {nome_mes_extenso(periodo_sel)}</h3>
            <p>Período ativo para análise</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.session_state['periodo_selecionado'] = None
    
    st.divider()
    
    # ===== SEÇÃO: FILTROS =====
    st.markdown("""
    <div class="sidebar-section-title">🔍 Filtros Globais</div>
    """, unsafe_allow_html=True)
    
    turno_selecionado = st.selectbox(
        "Turno:",
        ['Todos', 'Manhã', 'Tarde', 'Noite', 'Integral', 'EAD'],
        key='filtro_turno',
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # ===== SEÇÃO: NAVEGAÇÃO RÁPIDA =====
    st.markdown("""
    <div class="sidebar-section-title">🧭 Navegação Rápida</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/1_🌐_Visao_360.py", label="🌐 Visão 360", use_container_width=True)
        st.page_link("pages/3_🏢_Ocupacao.py", label="🏢 Ocupação", use_container_width=True)
        st.page_link("pages/5_📑_Relatorios.py", label="📑 Relatórios", use_container_width=True)
    with col2:
        st.page_link("pages/2_👥_Docentes.py", label="👥 Docentes", use_container_width=True)
        st.page_link("pages/4_📈_Historico.py", label="📈 Histórico", use_container_width=True)
        if esta_autenticado():
            st.page_link("pages/6_⚙️_Admin.py", label="⚙️ Admin", use_container_width=True)
    
    st.divider()
    
    # ===== SEÇÃO: INFORMAÇÕES DO SISTEMA =====
    with st.expander("ℹ️ Sobre o Sistema", expanded=False):
        st.markdown("""
        <div class="info-row">
            <span class="info-label">Versão</span>
            <span class="info-value">2.0.0</span>
        </div>
        <div class="info-row">
            <span class="info-label">Framework</span>
            <span class="info-value">Streamlit</span>
        </div>
        <div class="info-row">
            <span class="info-label">Banco de Dados</span>
            <span class="info-value">Supabase</span>
        </div>
        <div class="info-row">
            <span class="info-label">Hospedagem</span>
            <span class="info-value">Cloud</span>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== FOOTER =====
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; opacity: 0.5; font-size: 0.7rem;">
        <p>© 2024 Digitech</p>
        <p>Todos os direitos reservados</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# CONTEÚDO PRINCIPAL
# ============================================================

st.title("📊 Dashboard Digitech v2.0")
st.markdown("### Sistema de Gestão Educacional Integrado")

if not st.session_state['periodo_selecionado']:
    # ===== TELA INICIAL SEM PERÍODO =====
    st.info("👈 **Selecione um período** na barra lateral para começar, ou importe dados na página Admin.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Funcionalidades
        
        - ✅ **Turmas e Alunos** - Acompanhamento completo
        - ✅ **Instrutores** - Gestão de carga horária
        - ✅ **Ambientes** - Monitoramento de ocupação
        - ✅ **Hora-Aluno** - Metas e execução
        - ✅ **Não Regência** - Controle de atividades
        - ✅ **Faltas** - Registro e análise
        - ✅ **Relatórios** - Exportação de dados
        - ✅ **Histórico** - Tendências temporais
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Primeiros Passos
        
        **1. Autentique-se**
        > Use a senha de administrador para ter acesso completo
        
        **2. Importe Dados**
        > Acesse ⚙️ Admin e faça upload da planilha
        
        **3. Explore**
        > Navegue pelos painéis e visualize os indicadores
        """)
    
    st.divider()
    
    # Status do sistema
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        total_periodos = len(listar_periodos(apenas_ativos=False))
        periodos_ativos = len(listar_periodos(apenas_ativos=True))
    except Exception:
        total_periodos = 0
        periodos_ativos = 0
    
    col1.metric("📅 Períodos", total_periodos)
    col2.metric("✅ Ativos", periodos_ativos)
    col3.metric("🔌 Status", "Online" if status_conexao else "Offline")
    col4.metric("📦 Versão", "2.0.0")

else:
    # ===== DASHBOARD COM PERÍODO SELECIONADO =====
    periodo_atual = st.session_state['periodo_selecionado']
    
    st.success(f"📅 **{nome_mes_extenso(periodo_atual)}**")
    
    from src.database import (
        obter_periodo_por_referencia,
        listar_turmas,
        listar_instrutores,
        listar_ambientes,
        obter_resumo_hora_aluno
    )
    
    try:
        periodo_data = obter_periodo_por_referencia(periodo_atual)
    except Exception:
        periodo_data = None
    
    if periodo_data:
        periodo_id = periodo_data['id']
        
        # ===== KPIs =====
        st.markdown("### 📈 Indicadores Principais")
        
        try:
            df_turmas = listar_turmas(periodo_id)
            df_instrutores = listar_instrutores(periodo_id)
            df_ambientes = listar_ambientes(periodo_id, apenas_fisicos=True)
            resumo_ha = obter_resumo_hora_aluno(periodo_id)
        except Exception:
            df_turmas = pd.DataFrame()
            df_instrutores = pd.DataFrame()
            df_ambientes = pd.DataFrame()
            resumo_ha = {}
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric(
            "🎓 Turmas",
            len(df_turmas) if not df_turmas.empty else 0
        )
        
        total_alunos = 0
        if not df_turmas.empty and 'vagas_ocupadas' in df_turmas.columns:
            total_alunos = int(safe_number(df_turmas['vagas_ocupadas'].sum(), 0))
        col2.metric("👨‍🎓 Alunos", format_number(total_alunos))
        
        col3.metric(
            "👨‍🏫 Instrutores",
            len(df_instrutores) if not df_instrutores.empty else 0
        )
        
        col4.metric(
            "🏫 Ambientes",
            len(df_ambientes) if not df_ambientes.empty else 0
        )
        
        # Progresso HA
        ha_planejado = safe_number(resumo_ha.get('ha_planejado'), 0)
        ha_realizado = safe_number(resumo_ha.get('ha_realizado'), 0)
        meta_ha = safe_number(resumo_ha.get('meta_hora_aluno'), 0)
        
        if meta_ha == 0:
            meta_ha = ha_planejado
        
        progresso_ha = (ha_realizado / meta_ha * 100) if meta_ha > 0 else 0
        
        col5.metric("🎯 Progresso HA", f"{progresso_ha:.1f}%")
        
        # ===== BARRA DE PROGRESSO =====
        st.markdown("#### 🎯 Meta de Hora-Aluno")
        st.progress(min(int(progresso_ha), 100))
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("📚 Meta", format_number(meta_ha))
        col_b.metric("✅ Realizado", format_number(ha_realizado))
        col_c.metric("📊 Planejado", format_number(ha_planejado))
        
        st.divider()
        
        # ===== GRÁFICOS RÁPIDOS =====
        if not df_turmas.empty and 'turno' in df_turmas.columns:
            st.markdown("### 📊 Distribuição")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🕐 Turmas por Turno")
                turmas_turno = df_turmas['turno'].value_counts().reset_index()
                turmas_turno.columns = ['Turno', 'Quantidade']
                
                if not turmas_turno.empty:
                    import plotly.express as px
                    fig = px.bar(
                        turmas_turno,
                        x='Turno',
                        y='Quantidade',
                        color='Turno',
                        text='Quantidade',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig.update_layout(
                        showlegend=False, 
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 👥 Alunos por Turno")
                
                if 'vagas_ocupadas' in df_turmas.columns:
                    alunos_turno = df_turmas.groupby('turno')['vagas_ocupadas'].sum().reset_index()
                    alunos_turno.columns = ['Turno', 'Alunos']
                    
                    if not alunos_turno.empty and alunos_turno['Alunos'].sum() > 0:
                        import plotly.express as px
                        fig2 = px.pie(
                            alunos_turno,
                            names='Turno',
                            values='Alunos',
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig2.update_layout(
                            height=300,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        
        # ===== NAVEGAÇÃO =====
        st.markdown("### 🧭 Explorar Dados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 12px; text-align: center;">
                <h3 style="color: white; margin: 0;">🌐 Visão 360º</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                    Acompanhamento completo de disciplinas e turmas
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/1_🌐_Visao_360.py", label="Acessar →", use_container_width=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 1.5rem; border-radius: 12px; text-align: center;">
                <h3 style="color: white; margin: 0;">👥 Docentes</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                    Análise de carga horária e não regência
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/2_👥_Docentes.py", label="Acessar →", use_container_width=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 1.5rem; border-radius: 12px; text-align: center;">
                <h3 style="color: white; margin: 0;">🏢 Ocupação</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                    Uso e aproveitamento de ambientes
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/3_🏢_Ocupacao.py", label="Acessar →", use_container_width=True)
    
    else:
        st.error("❌ Erro ao carregar dados do período.")


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)
col1.caption("📊 Dashboard Digitech v2.0")
col2.caption("🔒 Supabase + Streamlit")
col3.caption("🟢 Online" if status_conexao else "🔴 Offline")