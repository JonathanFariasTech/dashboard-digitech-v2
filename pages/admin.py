"""
Página: Administração
Importação de planilhas e gestão do sistema
"""

import streamlit as st
import pandas as pd
from src.database import (
    criar_periodo,
    listar_periodos,
    atualizar_meta_periodo,
    obter_periodo_por_referencia,
    limpar_todos_caches,
    get_db
)
from src.auth import inicializar_sessao, requer_autenticacao
from src.importador import importar_planilha_completa, verificar_periodo_planilha
from src.utils import nome_mes_extenso, formatar_numero


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(page_title="Administração", page_icon="⚙️", layout="wide")

inicializar_sessao()


# ============================================================
# AUTENTICAÇÃO
# ============================================================

if not requer_autenticacao('ADMIN'):
    st.stop()


# ============================================================
# TÍTULO
# ============================================================

st.title("⚙️ Painel Administrativo")
st.markdown("Importação de dados e configurações do sistema")

st.divider()


# ============================================================
# IMPORTAÇÃO DE PLANILHA (COM ATUALIZAÇÃO INTELIGENTE)
# ============================================================

st.markdown("### 📤 Importar / Atualizar Dados")

st.info("""
**💡 Como funciona:**
- Se o período **não existe**: cria um novo período com os dados
- Se o período **já existe**: atualiza os dados (substitui pelos novos)
- O sistema detecta automaticamente o mês baseado na aba OCUPAÇÃO
""")

# Estado para controle do upload
if 'arquivo_pendente' not in st.session_state:
    st.session_state['arquivo_pendente'] = None
if 'mes_detectado' not in st.session_state:
    st.session_state['mes_detectado'] = None
if 'periodo_existe' not in st.session_state:
    st.session_state['periodo_existe'] = False

# Upload do arquivo
arquivo_carregado = st.file_uploader(
    "Selecione a planilha Excel (.xlsx)",
    type=["xlsx"],
    help="A planilha deve conter as abas: TURMAS, OCUPAÇÃO, NÃO_REGÊNCIA, INSTRUTORES, DISCIPLINAS, AMBIENTES, FALTAS, PARÂMETROS",
    key="uploader_principal"
)

if arquivo_carregado:
    # Verificar o arquivo
    with st.spinner("🔍 Analisando planilha..."):
        sucesso, mes_ref, existe = verificar_periodo_planilha(arquivo_carregado)
    
    if not sucesso:
        st.error(f"❌ {mes_ref}")
    else:
        # Mostrar informações detectadas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 12px; text-align: center;">
                <h3 style="color: white; margin: 0;">📅 {nome_mes_extenso(mes_ref)}</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                    Período detectado na planilha
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if existe:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 1.5rem; border-radius: 12px; text-align: center;">
                    <h3 style="color: white; margin: 0;">🔄 ATUALIZAÇÃO</h3>
                    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                        Período já existe - dados serão substituídos
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                            padding: 1.5rem; border-radius: 12px; text-align: center;">
                    <h3 style="color: white; margin: 0;">✨ NOVO PERÍODO</h3>
                    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                        Será criado um novo período
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Botões de ação
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if existe:
                btn_texto = "🔄 Atualizar Dados do Período"
                btn_tipo = "primary"
            else:
                btn_texto = "✨ Criar Novo Período"
                btn_tipo = "primary"
            
            btn_importar = st.button(btn_texto, type=btn_tipo, use_container_width=True)
        
        with col2:
            st.button("❌ Cancelar", use_container_width=True, on_click=lambda: st.cache_data.clear())
        
        # Processar importação
        if btn_importar:
            with st.status("⏳ Processando importação...", expanded=True) as status:
                try:
                    status.write("📥 Importando dados para o banco...")
                    
                    # Forçar atualização se período já existe
                    sucesso, mensagem, estatisticas = importar_planilha_completa(
                        arquivo_carregado, 
                        usuario="admin",
                        forcar_atualizacao=existe  # True se período existe
                    )
                    
                    if sucesso:
                        status.update(
                            label="✅ Importação concluída!",
                            state="complete",
                            expanded=True
                        )
                        
                        # Mostrar modo
                        if estatisticas.get('modo') == 'atualização':
                            st.success(f"🔄 **Dados de {mes_ref} atualizados com sucesso!**")
                        else:
                            st.success(f"✨ **Período {mes_ref} criado com sucesso!**")
                        
                        # Mostrar estatísticas
                        st.markdown("#### 📊 Resumo da Importação")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("📚 Turmas", estatisticas.get('turmas', 0))
                        col2.metric("👨‍🏫 Instrutores", estatisticas.get('instrutores', 0))
                        col3.metric("🏢 Ambientes", estatisticas.get('ambientes', 0))
                        col4.metric("📖 Disciplinas", estatisticas.get('disciplinas', 0))
                        
                        col5, col6, col7, col8 = st.columns(4)
                        col5.metric("📅 Ocupação", estatisticas.get('ocupacao', 0))
                        col6.metric("⏰ Não Regência", estatisticas.get('nao_regencia', 0))
                        col7.metric("⚠️ Faltas", estatisticas.get('faltas', 0))
                        col8.metric("🎯 Modo", "Atualização" if estatisticas.get('modo') == 'atualização' else "Novo")
                        
                        st.balloons()
                        
                    else:
                        status.update(label="❌ Erro", state="error")
                        st.error(mensagem)
                
                except Exception as e:
                    status.update(label="❌ Falha", state="error")
                    st.error(f"Erro: {str(e)}")

st.divider()


# ============================================================
# GESTÃO DE METAS
# ============================================================

st.markdown("### 🎯 Gestão de Metas de Hora-Aluno")

periodos = listar_periodos(apenas_ativos=False)

if periodos.empty or 'mes_referencia' not in periodos.columns:
    st.info("📭 Nenhum período cadastrado. Importe uma planilha primeiro.")
else:
    lista_periodos = periodos['mes_referencia'].tolist()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        periodo_sel = st.selectbox(
            "Selecionar Período:",
            lista_periodos,
            index=0,
            key="periodo_meta"
        )
    
    with col2:
        periodo_info = obter_periodo_por_referencia(periodo_sel)
        
        if periodo_info:
            meta_atual = periodo_info.get('meta_hora_aluno', 0) or 0
            tipo_meta = "Manual" if meta_atual > 0 else "Automática"
            
            st.markdown(f"**Meta atual:** {formatar_numero(meta_atual)} ({tipo_meta})")
            
            nova_meta = st.number_input(
                "Definir Nova Meta (0 = Automático):",
                min_value=0,
                value=int(meta_atual),
                step=500,
                help="Defina 0 para usar cálculo automático baseado nas disciplinas"
            )
            
            if st.button("💾 Salvar Meta", use_container_width=True):
                if nova_meta != meta_atual:
                    sucesso = atualizar_meta_periodo(periodo_info['id'], nova_meta)
                    
                    if sucesso:
                        st.success("✅ Meta atualizada!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar meta.")
                else:
                    st.info("Nenhuma alteração.")

st.divider()


# ============================================================
# EXCLUSÃO DE PERÍODO
# ============================================================

st.markdown("### 🗑️ Remover Período")

if periodos.empty or 'mes_referencia' not in periodos.columns:
    st.info("Não há períodos para remover.")
else:
    st.warning("⚠️ **Atenção:** Esta ação é irreversível! Todos os dados do período serão excluídos permanentemente.")
    
    lista_periodos_remover = periodos['mes_referencia'].tolist()
    
    with st.expander("🗑️ Clique para abrir painel de exclusão", expanded=False):
        periodo_remover = st.selectbox(
            "Selecione o período:",
            ["-- Selecione --"] + lista_periodos_remover,
            key="periodo_remover"
        )
        
        if periodo_remover != "-- Selecione --":
            confirmacao = st.text_input(
                f"Digite **{periodo_remover}** para confirmar:",
                placeholder=periodo_remover
            )
            
            if st.button("🚨 EXCLUIR PERMANENTEMENTE", type="primary", use_container_width=True):
                if confirmacao == periodo_remover:
                    periodo_para_remover = obter_periodo_por_referencia(periodo_remover)
                    
                    if periodo_para_remover:
                        try:
                            db = get_db()
                            
                            # Deletar registros relacionados
                            tabelas = ['disciplinas', 'ocupacao', 'nao_regencia', 'faltas', 
                                       'turmas', 'instrutores', 'ambientes']
                            
                            for tabela in tabelas:
                                try:
                                    db.table(tabela).delete().eq('periodo_id', periodo_para_remover['id']).execute()
                                except:
                                    pass
                            
                            # Deletar período
                            db.table('periodos').delete().eq('id', periodo_para_remover['id']).execute()
                            
                            limpar_todos_caches()
                            st.success(f"✅ Período '{periodo_remover}' removido!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
                    else:
                        st.error("Período não encontrado.")
                else:
                    st.error("❌ Confirmação incorreta.")

st.divider()


# ============================================================
# INFORMAÇÕES DO SISTEMA
# ============================================================

st.markdown("### 📊 Visão Geral dos Dados")

if not periodos.empty:
    # Resumo por período
    st.markdown("#### Períodos Cadastrados")
    
    df_display = periodos[['mes_referencia', 'status', 'meta_hora_aluno', 'data_upload']].copy()
    df_display.columns = ['Período', 'Status', 'Meta HA', 'Data Upload']
    
    # Formatar data
    if 'Data Upload' in df_display.columns:
        df_display['Data Upload'] = pd.to_datetime(df_display['Data Upload'], errors='coerce')
        df_display['Data Upload'] = df_display['Data Upload'].dt.strftime('%d/%m/%Y %H:%M')
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Meta HA': st.column_config.NumberColumn(format="%d"),
            'Status': st.column_config.TextColumn()
        }
    )
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Total de Períodos", len(periodos))
    col2.metric("✅ Ativos", len(periodos[periodos['status'] == 'ATIVO']))
    col3.metric("📦 Arquivados", len(periodos[periodos['status'] == 'ARQUIVADO']))


# ============================================================
# RODAPÉ
# ============================================================

st.divider()
st.caption(f"⚙️ Painel Administrativo • Dashboard Digitech v2.0 • {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")