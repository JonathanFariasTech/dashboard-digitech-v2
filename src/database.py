"""
Módulo de conexão e operações com Supabase
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================
# CONEXÃO COM SUPABASE
# ============================================================

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Cria e retorna cliente Supabase (singleton com cache)
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_db() -> Client:
    """Alias para obter cliente do banco"""
    return get_supabase_client()


# ============================================================
# OPERAÇÕES COM PERÍODOS
# ============================================================

@st.cache_data(ttl=300)
def listar_periodos(apenas_ativos: bool = True) -> pd.DataFrame:
    """
    Lista todos os períodos cadastrados
    
    Args:
        apenas_ativos: Se True, retorna apenas períodos com status ATIVO
        
    Returns:
        DataFrame com os períodos
    """
    db = get_db()
    query = db.table('periodos').select('*').order('mes_referencia', desc=True)
    
    if apenas_ativos:
        query = query.eq('status', 'ATIVO')
    
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def obter_periodo_por_referencia(mes_referencia: str) -> Optional[Dict]:
    """
    Busca um período pelo mês de referência
    
    Args:
        mes_referencia: Ex: "03 - Mar 2025"
        
    Returns:
        Dicionário com dados do período ou None
    """
    db = get_db()
    response = db.table('periodos')\
        .select('*')\
        .eq('mes_referencia', mes_referencia)\
        .maybe_single()\
        .execute()
    return response.data


def criar_periodo(mes_referencia: str, usuario: str = "admin", 
                  meta_ha: int = 0) -> Dict:
    """
    Cria um novo período
    
    Args:
        mes_referencia: Ex: "03 - Mar 2025"
        usuario: Nome do usuário que está criando
        meta_ha: Meta de hora-aluno (0 = automático)
        
    Returns:
        Dicionário com o período criado
    """
    db = get_db()
    response = db.table('periodos').insert({
        'mes_referencia': mes_referencia,
        'usuario_upload': usuario,
        'meta_hora_aluno': meta_ha,
        'status': 'ATIVO'
    }).execute()
    
    # Limpa cache após inserção
    listar_periodos.clear()
    
    return response.data[0] if response.data else None


def atualizar_meta_periodo(periodo_id: str, nova_meta: int) -> bool:
    """
    Atualiza a meta de hora-aluno de um período
    
    Args:
        periodo_id: UUID do período
        nova_meta: Nova meta de hora-aluno
        
    Returns:
        True se sucesso, False caso contrário
    """
    db = get_db()
    try:
        db.table('periodos')\
            .update({'meta_hora_aluno': nova_meta})\
            .eq('id', periodo_id)\
            .execute()
        listar_periodos.clear()
        return True
    except Exception:
        return False


# ============================================================
# OPERAÇÕES COM TURMAS
# ============================================================

@st.cache_data(ttl=300)
def listar_turmas(periodo_id: str, turno: Optional[str] = None) -> pd.DataFrame:
    """
    Lista turmas de um período
    
    Args:
        periodo_id: UUID do período
        turno: Filtro opcional de turno
        
    Returns:
        DataFrame com as turmas
    """
    db = get_db()
    query = db.table('turmas')\
        .select('*')\
        .eq('periodo_id', periodo_id)
    
    if turno and turno != "Todos":
        query = query.eq('turno', turno)
    
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def inserir_turmas_batch(turmas: List[Dict]) -> int:
    """
    Insere múltiplas turmas de uma vez
    
    Args:
        turmas: Lista de dicionários com dados das turmas
        
    Returns:
        Quantidade de turmas inseridas
    """
    if not turmas:
        return 0
        
    db = get_db()
    response = db.table('turmas').insert(turmas).execute()
    listar_turmas.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM DISCIPLINAS
# ============================================================

@st.cache_data(ttl=300)
def listar_disciplinas(periodo_id: str, 
                       com_turma: bool = True) -> pd.DataFrame:
    """
    Lista disciplinas de um período
    
    Args:
        periodo_id: UUID do período
        com_turma: Se True, inclui dados da turma (JOIN)
        
    Returns:
        DataFrame com as disciplinas
    """
    db = get_db()
    
    if com_turma:
        # Query com JOIN
        select_fields = '*, turmas(codigo_turma, nome_turma, turno, vagas_ocupadas)'
    else:
        select_fields = '*'
    
    response = db.table('disciplinas')\
        .select(select_fields)\
        .eq('periodo_id', periodo_id)\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    
    # Expande dados da turma se houver JOIN
    if com_turma and 'turmas' in df.columns:
        turmas_df = pd.json_normalize(df['turmas'])
        turmas_df.columns = [f'turma_{col}' for col in turmas_df.columns]
        df = pd.concat([df.drop('turmas', axis=1), turmas_df], axis=1)
    
    return df


def inserir_disciplinas_batch(disciplinas: List[Dict]) -> int:
    """Insere múltiplas disciplinas de uma vez"""
    if not disciplinas:
        return 0
        
    db = get_db()
    response = db.table('disciplinas').insert(disciplinas).execute()
    listar_disciplinas.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM INSTRUTORES
# ============================================================

@st.cache_data(ttl=300)
def listar_instrutores(periodo_id: str) -> pd.DataFrame:
    """Lista instrutores de um período"""
    db = get_db()
    response = db.table('instrutores')\
        .select('*')\
        .eq('periodo_id', periodo_id)\
        .order('nome_completo')\
        .execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def inserir_instrutores_batch(instrutores: List[Dict]) -> int:
    """Insere múltiplos instrutores de uma vez"""
    if not instrutores:
        return 0
        
    db = get_db()
    response = db.table('instrutores').insert(instrutores).execute()
    listar_instrutores.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM AMBIENTES
# ============================================================

@st.cache_data(ttl=300)
def listar_ambientes(periodo_id: str, 
                     apenas_fisicos: bool = False) -> pd.DataFrame:
    """
    Lista ambientes de um período
    
    Args:
        periodo_id: UUID do período
        apenas_fisicos: Se True, exclui ambientes virtuais
        
    Returns:
        DataFrame com os ambientes
    """
    db = get_db()
    query = db.table('ambientes')\
        .select('*')\
        .eq('periodo_id', periodo_id)
    
    if apenas_fisicos:
        query = query.eq('virtual', False)
    
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def inserir_ambientes_batch(ambientes: List[Dict]) -> int:
    """Insere múltiplos ambientes de uma vez"""
    if not ambientes:
        return 0
        
    db = get_db()
    response = db.table('ambientes').insert(ambientes).execute()
    listar_ambientes.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM OCUPAÇÃO
# ============================================================

@st.cache_data(ttl=300)
def listar_ocupacao(periodo_id: str, 
                    com_ambiente: bool = True) -> pd.DataFrame:
    """
    Lista registros de ocupação de um período
    
    Args:
        periodo_id: UUID do período
        com_ambiente: Se True, inclui dados do ambiente (JOIN)
        
    Returns:
        DataFrame com os registros de ocupação
    """
    db = get_db()
    
    if com_ambiente:
        select_fields = '*, ambientes(nome_ambiente, tipo)'
    else:
        select_fields = '*'
    
    response = db.table('ocupacao')\
        .select(select_fields)\
        .eq('periodo_id', periodo_id)\
        .order('data_ocupacao')\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    
    if com_ambiente and 'ambientes' in df.columns:
        amb_df = pd.json_normalize(df['ambientes'])
        amb_df.columns = [f'ambiente_{col}' for col in amb_df.columns]
        df = pd.concat([df.drop('ambientes', axis=1), amb_df], axis=1)
    
    return df


def inserir_ocupacao_batch(registros: List[Dict]) -> int:
    """Insere múltiplos registros de ocupação de uma vez"""
    if not registros:
        return 0
        
    db = get_db()
    response = db.table('ocupacao').insert(registros).execute()
    listar_ocupacao.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM NÃO REGÊNCIA
# ============================================================

@st.cache_data(ttl=300)
def listar_nao_regencia(periodo_id: str, 
                        com_instrutor: bool = True) -> pd.DataFrame:
    """
    Lista registros de não regência de um período
    
    Args:
        periodo_id: UUID do período
        com_instrutor: Se True, inclui dados do instrutor (JOIN)
        
    Returns:
        DataFrame com os registros
    """
    db = get_db()
    
    if com_instrutor:
        select_fields = '*, instrutores(nome_completo)'
    else:
        select_fields = '*'
    
    response = db.table('nao_regencia')\
        .select(select_fields)\
        .eq('periodo_id', periodo_id)\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    
    if com_instrutor and 'instrutores' in df.columns:
        inst_df = pd.json_normalize(df['instrutores'])
        inst_df.columns = [f'instrutor_{col}' for col in inst_df.columns]
        df = pd.concat([df.drop('instrutores', axis=1), inst_df], axis=1)
    
    return df


def inserir_nao_regencia_batch(registros: List[Dict]) -> int:
    """Insere múltiplos registros de não regência"""
    if not registros:
        return 0
        
    db = get_db()
    response = db.table('nao_regencia').insert(registros).execute()
    listar_nao_regencia.clear()
    return len(response.data) if response.data else 0


# ============================================================
# OPERAÇÕES COM FALTAS
# ============================================================

@st.cache_data(ttl=300)
def listar_faltas(periodo_id: str) -> pd.DataFrame:
    """Lista registros de faltas de um período"""
    db = get_db()
    response = db.table('faltas')\
        .select('*, turmas(nome_turma)')\
        .eq('periodo_id', periodo_id)\
        .order('data_falta', desc=True)\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    
    if 'turmas' in df.columns:
        turma_df = pd.json_normalize(df['turmas'])
        turma_df.columns = [f'turma_{col}' for col in turma_df.columns]
        df = pd.concat([df.drop('turmas', axis=1), turma_df], axis=1)
    
    return df


def inserir_faltas_batch(faltas: List[Dict]) -> int:
    """Insere múltiplos registros de faltas"""
    if not faltas:
        return 0
        
    db = get_db()
    response = db.table('faltas').insert(faltas).execute()
    listar_faltas.clear()
    return len(response.data) if response.data else 0


# ============================================================
# VIEWS E AGREGAÇÕES
# ============================================================

@st.cache_data(ttl=300)
def obter_resumo_hora_aluno(periodo_id: str) -> Dict:
    """
    Obtém resumo de hora-aluno de um período usando a VIEW
    
    Args:
        periodo_id: UUID do período
        
    Returns:
        Dicionário com métricas de HA
    """
    db = get_db()
    response = db.table('vw_hora_aluno_resumo')\
        .select('*')\
        .eq('periodo_id', periodo_id)\
        .maybe_single()\
        .execute()
    
    return response.data if response.data else {
        'total_turmas': 0,
        'total_alunos': 0,
        'ha_planejado': 0,
        'ha_realizado': 0,
        'meta_hora_aluno': 0
    }


@st.cache_data(ttl=300)
def obter_ocupacao_media(periodo_id: str) -> pd.DataFrame:
    """Obtém ocupação média por ambiente usando a VIEW"""
    db = get_db()
    
    # Primeiro, busca o mes_referencia do periodo
    periodo = db.table('periodos')\
        .select('mes_referencia')\
        .eq('id', periodo_id)\
        .single()\
        .execute()
    
    if not periodo.data:
        return pd.DataFrame()
    
    response = db.table('vw_ocupacao_media')\
        .select('*')\
        .eq('mes_referencia', periodo.data['mes_referencia'])\
        .execute()
    
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


@st.cache_data(ttl=300)
def obter_ranking_nao_regencia(periodo_id: str) -> pd.DataFrame:
    """Obtém ranking de não regência usando a VIEW"""
    db = get_db()
    
    periodo = db.table('periodos')\
        .select('mes_referencia')\
        .eq('id', periodo_id)\
        .single()\
        .execute()
    
    if not periodo.data:
        return pd.DataFrame()
    
    response = db.table('vw_ranking_nao_regencia')\
        .select('*')\
        .eq('mes_referencia', periodo.data['mes_referencia'])\
        .execute()
    
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


# ============================================================
# HISTÓRICO (COMPILAÇÃO DE MÚLTIPLOS PERÍODOS)
# ============================================================

@st.cache_data(ttl=600)
def compilar_historico() -> pd.DataFrame:
    """
    Compila dados históricos de todos os períodos ativos
    
    Returns:
        DataFrame com métricas por período
    """
    db = get_db()
    response = db.table('vw_hora_aluno_resumo')\
        .select('*')\
        .order('mes_referencia')\
        .execute()
    
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


# ============================================================
# AUDITORIA
# ============================================================

@st.cache_data(ttl=60)
def listar_auditoria(limite: int = 100, 
                     tabela: Optional[str] = None) -> pd.DataFrame:
    """
    Lista registros de auditoria
    
    Args:
        limite: Quantidade máxima de registros
        tabela: Filtro opcional por nome da tabela
        
    Returns:
        DataFrame com os logs
    """
    db = get_db()
    query = db.table('auditoria')\
        .select('*')\
        .order('created_at', desc=True)\
        .limit(limite)
    
    if tabela:
        query = query.eq('tabela', tabela)
    
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_todos_caches():
    """Limpa todos os caches de dados"""
    listar_periodos.clear()
    listar_turmas.clear()
    listar_disciplinas.clear()
    listar_instrutores.clear()
    listar_ambientes.clear()
    listar_ocupacao.clear()
    listar_nao_regencia.clear()
    listar_faltas.clear()
    obter_resumo_hora_aluno.clear()
    obter_ocupacao_media.clear()
    obter_ranking_nao_regencia.clear()
    compilar_historico.clear()
    listar_auditoria.clear()


def testar_conexao() -> bool:
    """Testa se a conexão com o Supabase está funcionando"""
    try:
        db = get_db()
        db.table('parametros').select('chave').limit(1).execute()
        return True
    except Exception:
        return False