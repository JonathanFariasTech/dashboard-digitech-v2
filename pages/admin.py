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
from src.importador import importar_planilha_completa
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

st.sidebar.success("✅ Login Admin Confirmado")

st.sidebar.divider()

if st.sidebar.button("🚪 Sair", use_container_width=True):
    from src.auth import fazer_logout
    fazer_logout()
    st.rerun()


# ============================================================
# TÍTULO
# ============================================================

st.title("⚙️ Painel Administrativo")
st.markdown("""
## Importação de Dados e Configurações do Sistema

Utilize esta área para:
- 📥 **Adicionar novos períodos** via upload de planilha
- 🎯 **Definir metas** de Hora-Aluno manualmente  
- 🗑️ **Remover períodos** do banco de dados
""")

st.divider()


# ============================================================
# IMPORTAÇÃO DE NOVO PERÍODO
# ============================================================

st.markdown("### 📤 Adicionar Novo Período")
st.caption("Faça upload da planilha mensal (.xlsx) com todas as abas obrigatórias")

with st.expander("ℹ️ Requisitos da Planilha", expanded=False):
    st.markdown("""
    **Abas Obrigatórias:**
    - ✅ TURMAS
    - ✅ OCUPAÇÃO  
    - ✅ NÃO_REGÊNCIA
    - ✅ INSTRUTORES
    - ✅ DISCIPLINAS
    - ✅ AMBIENTES
    - ✅ FALTAS
    - ✅ PARÂMETROS
    
    **Colunas Mínimas Necessárias:**
    - TURMAS: ID_TURMA, NOME_TURMA, TURNO, VAGAS_OCUPADAS
    - OCUPAÇÃO: DATA, AMBIENTE, PERCENTUAL_OCUPACAO
    - DISCIPLINAS: ID_TURMA, NOME_DISCIPLINA, CARGA_HORARIA, STATUS
    """)

# Upload do arquivo
arquivo_carregado = st.file_uploader(
    "Upload de Planilha Excel (.xlsx)",
    type=["xlsx"],
    help="Selecione o arquivo mensal para importar"
)

if arquivo_carregado:
    with st.spinner("🔍 Validando planilha..."):
        try:
            # Testar leitura rápida para verificação
            xls = pd.ExcelFile(arquivo_carregado)
            abas = xls.sheet_names
            
            st.success(f"✅ Planilha válida! Abas encontradas: {len(abas)}")
            for aba in abas:
                st.markdown(f"• **{aba}**: OK")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            st.stop()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        btn_importar = st.button("🚀 Importar para o Banco de Dados", use_container_width=True)
    
    with col2:
        btn_cancelar = st.button("❌ Cancelar", use_container_width=True)
    
    if btn_importar:
        with st.status("⏳ Importando dados...", expanded=True) as status:
            try:
                status.write("📥 Processando arquivo...")
                
                sucesso, mensagem, estatisticas = importar_planilha_completa(
                    arquivo_carregado, 
                    usuario="admin"
                )
                
                if sucesso:
                    status.update(
                        label="✅ Importação concluída!",
                        state="complete",
                        expanded=False
                    )
                    
                    st.success(mensagem)
                    
                    # Mostrar estatísticas
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    col_stats1.metric("📚 Turmas", estatisticas.get('turmas', 0))
                    col_stats2.metric("👨‍🏫 Instrutores", estatisticas.get('instrutores', 0))
                    col_stats3.metric("📖 Disciplinas", estatisticas.get('disciplinas', 0))
                    
                    col_stats4, col_stats5, col_stats6 = st.columns(3)
                    col_stats4.metric("🏢 Ocupações", estatisticas.get('ocupacao', 0))
                    col_stats5.metric("⏰ Não Regência", estatisticas.get('nao_regencia', 0))
                    col_stats6.metric("⚠️ Faltas", estatisticas.get('faltas', 0))
                    
                    st.info("✨ Limpeza de cache automática realizada.")
                    
                else:
                    status.update(label="❌ Erro na importação", state="error")
                    st.error(mensagem)
                    
                    if estatisticas:
                        st.info("Parciais antes do erro:")
                        st.json(estatisticas)
                
            except Exception as e:
                status.update(label="❌ Falha crítica", state="error")
                st.error(f"Erro inesperado: {str(e)}")
                
                import traceback
                st.code(traceback.format_exc(), language="text")


# ============================================================
# GESTÃO DE METAS
# ============================================================

st.divider()
st.markdown("### 🎯 Gestão de Metas de Hora-Aluno")

# Carregar períodos com tratamento de erro
periodos = listar_periodos(apenas_ativos=False)

# ✅ CORREÇÃO: Verificar se DataFrame está vazio ou não tem colunas
if periodos.empty or 'mes_referencia' not in periodos.columns:
    st.info("📭 Nenhum período cadastrado ainda. Importe uma planilha primeiro usando o formulário acima.")
else:
    # ✅ CORREÇÃO: Agora só acessa se tiver dados
    lista_periodos = periodos['mes_referencia'].tolist()
    
    periodo_sel = st.selectbox(
        "Selecionar Período:",
        lista_periodos,
        index=0
    )
    
    periodo_info = obter_periodo_por_referencia(periodo_sel)
    
    if periodo_info:
        meta_atual = periodo_info.get('meta_hora_aluno', 0)
        tipo_meta = "Manual" if meta_atual > 0 else "Automática"
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Meta Atual**")
            st.metric(label=f"Tipo: {tipo_meta}", value=formatar_numero(meta_atual))
        
        with col2:
            nova_meta = st.number_input(
                "Definir Nova Meta (0 = Automático):",
                min_value=0,
                value=int(meta_atual),
                step=500,
                help="Defina 0 para usar cálculo automático baseado nas disciplinas"
            )
            
            if st.button("💾 Salvar Meta", use_container_width=True):
                if nova_meta != meta_atual:
                    # Atualizar no banco
                    sucesso = atualizar_meta_periodo(
                        periodo_info['id'],
                        nova_meta
                    )
                    
                    if sucesso:
                        st.success("Meta atualizada com sucesso! ✨")
                        limpar_todos_caches()
                        st.rerun()
                    else:
                        st.error("Erro ao salvar meta.")
                else:
                    st.info("Nenhuma alteração detectada.")


# ============================================================
# EXCLUSÃO DE PERÍODO
# ============================================================

st.divider()
st.markdown("### 🗑️ Remover Período")

# ✅ CORREÇÃO: Verificar novamente se há períodos
if periodos.empty or 'mes_referencia' not in periodos.columns:
    st.info("Não há períodos para remover.")
else:
    st.warning("⚠️ Esta ação é irreversível! Todos os dados do período serão excluídos permanentemente.")
    
    lista_periodos_remover = periodos['mes_referencia'].tolist()
    
    with st.form("form_remover_periodo", clear_on_submit=True):
        periodo_remover = st.selectbox(
            "Selecione o período para excluir:",
            ["-- Selecione --"] + lista_periodos_remover
        )
        
        confirmacao = st.text_input(
            "Digite o código do período para confirmar:",
            placeholder="Ex: 03 - Mar 2025"
        )
        
        btn_remover = st.form_submit_button("🚨 EXCLUIR DEFINITIVAMENTE", type="primary", use_container_width=True)
        
        if btn_remover:
            if periodo_remover == "-- Selecione --":
                st.warning("Por favor, selecione um período.")
            elif confirmacao != periodo_remover:
                st.error("❌ Código de confirmação incorreto.")
            else:
                periodo_para_remover = obter_periodo_por_referencia(confirmacao)
                
                if periodo_para_remover:
                    try:
                        db = get_db()
                        
                        # Deletar registros relacionados primeiro (CASCADE deveria fazer isso, mas por segurança)
                        tabelas_relacionadas = [
                            'disciplinas', 'turmas', 'instrutores', 'ambientes',
                            'ocupacao', 'nao_regencia', 'faltas'
                        ]
                        
                        for tabela in tabelas_relacionadas:
                            try:
                                db.table(tabela)\
                                    .delete()\
                                    .eq('periodo_id', periodo_para_remover['id'])\
                                    .execute()
                            except Exception:
                                pass  # Ignora se tabela não existir
                        
                        # Agora deletar o próprio período
                        response = db.table('periodos')\
                            .delete()\
                            .eq('id', periodo_para_remover['id'])\
                            .execute()
                        
                        limpar_todos_caches()
                        st.success(f"✅ Período '{confirmacao}' removido com sucesso!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao remover período: {str(e)}")
                else:
                    st.error("Período não encontrado.")


# ============================================================
# AUDITORIA DO SISTEMA
# ============================================================

st.divider()
st.markdown("### 🔍 Logs de Auditoria")
st.caption("Registro de alterações realizadas no sistema")

from src.database import listar_auditoria

limite_logs = st.slider("Limite de registros:", 50, 500, 100, step=50)

# Lista de tabelas para filtro
tabelas_disponiveis = ['turmas', 'disciplinas', 'instrutores', 'ambientes', 'nao_regencia', 'faltas', 'periodos']
filtro_tabela = st.multiselect("Filtrar por tabela:", tabelas_disponiveis)

df_logs = listar_auditoria(limite=limite_logs)

# ✅ CORREÇÃO: Verificar se há logs e se a coluna existe
if df_logs.empty:
    st.info("📭 Nenhum registro de auditoria encontrado.")
else:
    # Aplicar filtro se selecionado
    if filtro_tabela and 'tabela' in df_logs.columns:
        df_logs = df_logs[df_logs['tabela'].isin(filtro_tabela)]
    
    if df_logs.empty:
        st.info("Nenhum registro encontrado com os filtros aplicados.")
    else:
        # Preparar para exibição
        df_display = df_logs.head(200).copy()
        
        # Formatamento de data
        if 'created_at' in df_display.columns:
            df_display['created_at'] = pd.to_datetime(df_display['created_at'], errors='coerce')
            df_display['timestamp'] = df_display['created_at'].dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Selecionar colunas existentes
        cols_desejadas = ['timestamp', 'tabela', 'operacao', 'usuario']
        cols_existentes = [col for col in cols_desejadas if col in df_display.columns]
        
        if cols_existentes:
            df_final = df_display[cols_existentes].copy()
            
            # Renomear colunas
            rename_map = {
                'timestamp': 'Data/Hora',
                'tabela': 'Tabela',
                'operacao': 'Operação',
                'usuario': 'Usuário'
            }
            df_final = df_final.rename(columns={k: v for k, v in rename_map.items() if k in df_final.columns})
            
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📊 Mostrando {len(df_final)} de {len(df_logs)} registros")
        else:
            st.warning("Estrutura de logs diferente do esperado.")
            st.dataframe(df_display.head(20))

st.divider()
st.caption(f"Dashboard Digitech v2.0 • Painel Administrativo • {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")