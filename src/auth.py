"""
Módulo de autenticação e controle de acesso
"""

import streamlit as st
from typing import Optional, Dict


# ============================================================
# CONSTANTES
# ============================================================

NIVEIS_ACESSO = {
    'ADMIN': 3,
    'GESTOR': 2,
    'VISUALIZADOR': 1
}


# ============================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ============================================================

def inicializar_sessao():
    """Inicializa variáveis de sessão para autenticação"""
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
    if 'usuario' not in st.session_state:
        st.session_state['usuario'] = None
    if 'nivel_acesso' not in st.session_state:
        st.session_state['nivel_acesso'] = None


def esta_autenticado() -> bool:
    """Verifica se o usuário está autenticado"""
    inicializar_sessao()
    return st.session_state['autenticado']


def obter_usuario_atual() -> Optional[Dict]:
    """Retorna dados do usuário atual ou None"""
    if esta_autenticado():
        return {
            'nome': st.session_state['usuario'],
            'nivel': st.session_state['nivel_acesso']
        }
    return None


def fazer_login(senha: str) -> bool:
    """
    Realiza login com senha
    
    Args:
        senha: Senha informada pelo usuário
        
    Returns:
        True se login bem sucedido
        
    TODO: Migrar para Supabase Auth posteriormente
    """
    # Por enquanto, usa secrets do Streamlit
    # Depois migrar para Supabase Auth
    senha_admin = st.secrets.get("ADMIN_PASSWORD", "admin123")
    senha_gestor = st.secrets.get("GESTOR_PASSWORD", "gestor123")
    
    if senha == senha_admin:
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = 'Administrador'
        st.session_state['nivel_acesso'] = 'ADMIN'
        return True
    elif senha == senha_gestor:
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = 'Gestor'
        st.session_state['nivel_acesso'] = 'GESTOR'
        return True
    
    return False


def fazer_logout():
    """Realiza logout do usuário"""
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = None
    st.session_state['nivel_acesso'] = None


def tem_permissao(nivel_minimo: str) -> bool:
    """
    Verifica se o usuário tem permissão mínima
    
    Args:
        nivel_minimo: 'ADMIN', 'GESTOR' ou 'VISUALIZADOR'
        
    Returns:
        True se o usuário tem permissão
    """
    if not esta_autenticado():
        return False
    
    nivel_usuario = NIVEIS_ACESSO.get(st.session_state['nivel_acesso'], 0)
    nivel_requerido = NIVEIS_ACESSO.get(nivel_minimo, 0)
    
    return nivel_usuario >= nivel_requerido


def requer_autenticacao(nivel_minimo: str = 'VISUALIZADOR'):
    """
    Decorator/função para proteger páginas
    
    Args:
        nivel_minimo: Nível mínimo de acesso requerido
        
    Uso:
        if requer_autenticacao('ADMIN'):
            # código protegido
    """
    if not esta_autenticado():
        st.warning("🔐 Faça login para acessar esta funcionalidade.")
        return False
    
    if not tem_permissao(nivel_minimo):
        st.error(f"⛔ Acesso negado. Nível mínimo requerido: {nivel_minimo}")
        return False
    
    return True


# ============================================================
# COMPONENTES DE UI
# ============================================================

def renderizar_login_sidebar():
    """Renderiza componente de login na sidebar"""
    inicializar_sessao()
    
    st.sidebar.title("🔐 Acesso")
    
    if not esta_autenticado():
        with st.sidebar.form("form_login", clear_on_submit=True):
            st.markdown("**Faça login para gerenciar dados**")
            senha = st.text_input("Senha:", type="password")
            col1, col2 = st.columns(2)
            
            with col1:
                btn_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_login:
                if fazer_login(senha):
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
    else:
        usuario = obter_usuario_atual()
        st.sidebar.success(f"✅ {usuario['nome']}")
        st.sidebar.caption(f"Nível: {usuario['nivel']}")
        
        if st.sidebar.button("🚪 Sair", use_container_width=True):
            fazer_logout()
            st.rerun()
    
    st.sidebar.divider()