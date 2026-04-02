"""
Página de diagnóstico de conexão
Execute: streamlit run diagnostico.py
"""

import streamlit as st
import os

st.set_page_config(page_title="Diagnóstico", page_icon="🔧", layout="wide")

st.title("🔧 Diagnóstico de Conexão - Dashboard Digitech")

st.divider()

# ============================================================
# 1. VERIFICAR SECRETS
# ============================================================

st.markdown("### 1️⃣ Verificação de Secrets")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Arquivo .streamlit/secrets.toml existe?**")
    secrets_file = os.path.exists(".streamlit/secrets.toml")
    if secrets_file:
        st.success("✅ Arquivo encontrado")
    else:
        st.error("❌ Arquivo NÃO encontrado")
        st.info("Crie o arquivo `.streamlit/secrets.toml` na raiz do projeto")

with col2:
    st.markdown("**st.secrets está disponível?**")
    if hasattr(st, 'secrets'):
        st.success("✅ st.secrets disponível")
        
        # Listar chaves (sem valores)
        try:
            chaves = list(st.secrets.keys())
            st.info(f"Chaves encontradas: {', '.join(chaves)}")
        except:
            st.warning("Não foi possível listar as chaves")
    else:
        st.error("❌ st.secrets NÃO disponível")

st.divider()

# ============================================================
# 2. VERIFICAR VARIÁVEIS ESPECÍFICAS
# ============================================================

st.markdown("### 2️⃣ Verificação de Variáveis do Supabase")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**SUPABASE_URL**")
    if "SUPABASE_URL" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        st.success(f"✅ Configurado: `{url[:30]}...`")
        
        if url.startswith("https://"):
            st.success("✅ Formato correto (https://)")
        else:
            st.error("❌ Deve começar com https://")
    else:
        st.error("❌ NÃO configurado")
        st.code("""
# Adicione ao .streamlit/secrets.toml:
SUPABASE_URL = "https://seu-projeto.supabase.co"
        """)

with col2:
    st.markdown("**SUPABASE_KEY**")
    if "SUPABASE_KEY" in st.secrets:
        key = st.secrets["SUPABASE_KEY"]
        st.success(f"✅ Configurado ({len(key)} caracteres)")
        
        if len(key) > 100:
            st.success("✅ Tamanho adequado")
        else:
            st.warning("⚠️ Chave parece curta demais")
    else:
        st.error("❌ NÃO configurado")
        st.code("""
# Adicione ao .streamlit/secrets.toml:
SUPABASE_KEY = "sua-chave-anon-public-aqui"
        """)

st.divider()

# ============================================================
# 3. TESTE DE CONEXÃO
# ============================================================

st.markdown("### 3️⃣ Teste de Conexão com Banco")

if st.button("🔌 Testar Conexão Agora", type="primary", use_container_width=True):
    
    if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
        st.error("❌ Configure SUPABASE_URL e SUPABASE_KEY primeiro!")
    else:
        with st.spinner("Conectando..."):
            try:
                from supabase import create_client
                
                url = st.secrets["SUPABASE_URL"]
                key = st.secrets["SUPABASE_KEY"]
                
                st.info(f"Tentando conectar em: {url}")
                
                client = create_client(url, key)
                
                st.success("✅ Cliente Supabase criado!")
                
                # Testar query simples
                st.info("Testando query na tabela 'parametros'...")
                response = client.table('parametros').select('*').limit(1).execute()
                
                st.success("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
                
                if hasattr(response, 'data'):
                    st.json(response.data)
                
            except Exception as e:
                st.error(f"❌ Erro na conexão: {str(e)}")
                
                st.markdown("**Possíveis causas:**")
                st.markdown("- URL ou Key incorretos")
                st.markdown("- Tabelas não foram criadas no Supabase")
                st.markdown("- Row Level Security (RLS) muito restritivo")
                st.markdown("- Firewall bloqueando a conexão")
                
                with st.expander("🔍 Detalhes técnicos do erro"):
                    import traceback
                    st.code(traceback.format_exc())

st.divider()

# ============================================================
# 4. INSTRUÇÕES
# ============================================================

st.markdown("### 4️⃣ Como Obter as Credenciais do Supabase")

tab1, tab2, tab3 = st.tabs(["📝 Passo a Passo", "🔑 Localizar Credenciais", "📋 Template"])

with tab1:
    st.markdown("""
    **1. Acesse o Supabase:**
    - Vá para https://supabase.com
    - Faça login ou crie uma conta
    
    **2. Crie um Projeto:**
    - Clique em "New Project"
    - Nome: `digitech-dashboard`
    - Database Password: escolha uma senha forte
    - Region: South America (ou mais próxima)
    - Clique em "Create new project"
    - Aguarde ~2 minutos
    
    **3. Execute o SQL:**
    - No menu lateral, clique em "SQL Editor"
    - Cole o script SQL completo das tabelas
    - Clique em "Run"
    
    **4. Obtenha as Credenciais:**
    - Vá em Settings → API
    - Copie "Project URL" e "anon public key"
    """)

with tab2:
    st.markdown("""
    **Localização das Credenciais no Supabase:**
    
    1. **Painel do projeto** → **Settings** (ícone de engrenagem)
    2. **API** (menu lateral esquerdo)
    3. Copie:
       - **URL**: `https://xxxxx.supabase.co`
       - **anon key** (public): `eyJhbGci...` (grande string)
    
    ⚠️ **NÃO use a `service_role` key em produção!**
    """)
    
    st.image("https://supabase.com/docs/img/api/api-url-and-key.png")

with tab3:
    st.markdown("**Template do arquivo `.streamlit/secrets.toml`:**")
    
    st.code("""
# .streamlit/secrets.toml
# Crie este arquivo na raiz do projeto

SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4eHh4eHh4eHh4eHh4IiwiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNjg..."

# Senhas do sistema (opcional)
ADMIN_PASSWORD = "admin123"
GESTOR_PASSWORD = "gestor123"
    """, language="toml")

st.divider()

st.caption("💡 Após configurar, execute `streamlit run app.py` para iniciar o dashboard principal")