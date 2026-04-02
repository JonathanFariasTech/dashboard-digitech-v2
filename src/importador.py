"""
Módulo para importação de planilhas Excel para o banco de dados
"""

import streamlit as st
import pandas as pd
from typing import Tuple, Dict, Optional
from datetime import datetime
import io

from src.database import (
    criar_periodo, obter_periodo_por_referencia,
    inserir_turmas_batch, inserir_instrutores_batch,
    inserir_ambientes_batch, inserir_disciplinas_batch,
    inserir_ocupacao_batch, inserir_nao_regencia_batch,
    inserir_faltas_batch, limpar_todos_caches, get_db
)


# ============================================================
# CONSTANTES
# ============================================================

ABAS_OBRIGATORIAS = [
    "TURMAS", "OCUPAÇÃO", "NÃO_REGÊNCIA", "INSTRUTORES",
    "DISCIPLINAS", "AMBIENTES", "FALTAS", "PARÂMETROS"
]

MESES_PT = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}


# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def validar_planilha(arquivo) -> Tuple[bool, str]:
    """
    Valida se a planilha tem todas as abas obrigatórias
    
    Args:
        arquivo: Arquivo Excel carregado
        
    Returns:
        Tupla (sucesso, mensagem)
    """
    try:
        xls = pd.ExcelFile(arquivo)
        abas_arquivo = xls.sheet_names
        abas_faltantes = [aba for aba in ABAS_OBRIGATORIAS if aba not in abas_arquivo]
        
        if abas_faltantes:
            return False, f"Faltam as abas: {', '.join(abas_faltantes)}"
        
        return True, "Planilha validada com sucesso!"
    
    except Exception as e:
        return False, f"Erro ao ler arquivo: {str(e)}"


def extrair_mes_automatico(arquivo) -> Optional[str]:
    """
    Extrai o mês de referência automaticamente da planilha
    
    Args:
        arquivo: Arquivo Excel carregado
        
    Returns:
        String no formato "03 - Mar 2025" ou None
    """
    try:
        arquivo.seek(0)
        df_temp = pd.read_excel(arquivo, sheet_name="OCUPAÇÃO", usecols=["DATA"])
        datas = pd.to_datetime(df_temp["DATA"], errors="coerce").dropna()
        
        if not datas.empty:
            data_predominante = datas.mode()[0]
            mes_num = data_predominante.month
            ano = data_predominante.year
            return f"{mes_num:02d} - {MESES_PT[mes_num]} {ano}"
    
    except Exception:
        pass
    
    return None


# ============================================================
# FUNÇÕES DE IMPORTAÇÃO
# ============================================================

def importar_turmas(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """
    Importa turmas do Excel para o banco
    
    Args:
        xls: ExcelFile aberto
        periodo_id: UUID do período
        
    Returns:
        Tupla (quantidade importada, mapeamento codigo_original -> UUID)
    """
    df = pd.read_excel(xls, sheet_name="TURMAS")
    
    mapeamento = {}
    turmas = []
    
    for _, row in df.iterrows():
        codigo = str(row.get('ID_TURMA', row.get('CODIGO', '')))
        
        turma = {
            'periodo_id': periodo_id,
            'codigo_turma': codigo,
            'nome_turma': str(row.get('NOME_TURMA', row.get('NOME', ''))),
            'curso': str(row.get('CURSO', '')),
            'turno': str(row.get('TURNO', '')),
            'vagas_total': int(row.get('VAGAS_TOTAL', row.get('VAGAS', 0)) or 0),
            'vagas_ocupadas': int(row.get('VAGAS_OCUPADAS', 0) or 0)
        }
        turmas.append(turma)
    
    if turmas:
        db = get_db()
        response = db.table('turmas').insert(turmas).execute()
        
        # Criar mapeamento de códigos para UUIDs
        for item in response.data:
            mapeamento[item['codigo_turma']] = item['id']
    
    return len(turmas), mapeamento


def importar_instrutores(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """
    Importa instrutores do Excel para o banco
    
    Returns:
        Tupla (quantidade importada, mapeamento codigo_original -> UUID)
    """
    df = pd.read_excel(xls, sheet_name="INSTRUTORES")
    
    mapeamento = {}
    instrutores = []
    
    for _, row in df.iterrows():
        codigo = str(row.get('ID', row.get('ID_INSTRUTOR', row.get('CODIGO', ''))))
        
        instrutor = {
            'periodo_id': periodo_id,
            'codigo_instrutor': codigo,
            'nome_completo': str(row.get('NOME_COMPLETO', row.get('NOME', ''))),
            'email': str(row.get('EMAIL', '')) if pd.notna(row.get('EMAIL')) else None,
            'especialidade': str(row.get('ESPECIALIDADE', '')) if pd.notna(row.get('ESPECIALIDADE')) else None,
            'carga_horaria_contrato': int(row.get('CARGA_HORARIA', 40) or 40)
        }
        instrutores.append(instrutor)
    
    if instrutores:
        db = get_db()
        response = db.table('instrutores').insert(instrutores).execute()
        
        for item in response.data:
            mapeamento[item['codigo_instrutor']] = item['id']
    
    return len(instrutores), mapeamento


def importar_ambientes(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """
    Importa ambientes do Excel para o banco
    
    Returns:
        Tupla (quantidade importada, mapeamento nome -> UUID)
    """
    df = pd.read_excel(xls, sheet_name="AMBIENTES")
    
    mapeamento = {}
    ambientes = []
    
    for _, row in df.iterrows():
        nome = str(row.get('AMBIENTE', row.get('NOME', row.get('NOME_AMBIENTE', ''))))
        
        # Detectar se é virtual
        virtual_raw = row.get('VIRTUAL', 'NÃO')
        virtual = str(virtual_raw).upper() in ['SIM', 'S', 'TRUE', '1', 'VIRTUAL']
        
        ambiente = {
            'periodo_id': periodo_id,
            'codigo_ambiente': nome,  # Usa nome como código
            'nome_ambiente': nome,
            'tipo': str(row.get('TIPO', 'Sala')),
            'capacidade': int(row.get('CAPACIDADE', 0) or 0),
            'virtual': virtual
        }
        ambientes.append(ambiente)
    
    if ambientes:
        db = get_db()
        response = db.table('ambientes').insert(ambientes).execute()
        
        for item in response.data:
            mapeamento[item['nome_ambiente']] = item['id']
    
    return len(ambientes), mapeamento


def importar_disciplinas(xls: pd.ExcelFile, periodo_id: str, 
                         mapa_turmas: Dict[str, str],
                         mapa_instrutores: Dict[str, str]) -> int:
    """
    Importa disciplinas do Excel para o banco
    
    Args:
        xls: ExcelFile aberto
        periodo_id: UUID do período
        mapa_turmas: Mapeamento código_turma -> UUID
        mapa_instrutores: Mapeamento código_instrutor -> UUID
        
    Returns:
        Quantidade de disciplinas importadas
    """
    try:
        df = pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1)
    except:
        df = pd.read_excel(xls, sheet_name="DISCIPLINAS")
    
    disciplinas = []
    
    for _, row in df.iterrows():
        codigo_turma = str(row.get('ID_TURMA', ''))
        turma_id = mapa_turmas.get(codigo_turma)
        
        if not turma_id:
            continue  # Pula se não encontrar a turma
        
        # Buscar instrutor se houver
        codigo_instrutor = str(row.get('ID_INSTRUTOR', row.get('INSTRUTOR', '')))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        # Normalizar status
        status_raw = str(row.get('STATUS', 'Não Iniciado'))
        status = normalizar_status(status_raw)
        
        disciplina = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'instrutor_id': instrutor_id,
            'nome_disciplina': str(row.get('NOME_DISCIPLINA', row.get('DISCIPLINA', ''))),
            'carga_horaria': int(row.get('CARGA_HORARIA', 0) or 0),
            'status': status
        }
        disciplinas.append(disciplina)
    
    return inserir_disciplinas_batch(disciplinas)


def importar_ocupacao(xls: pd.ExcelFile, periodo_id: str,
                      mapa_ambientes: Dict[str, str]) -> int:
    """
    Importa registros de ocupação do Excel para o banco
    """
    df = pd.read_excel(xls, sheet_name="OCUPAÇÃO")
    
    registros = []
    
    for _, row in df.iterrows():
        nome_ambiente = str(row.get('AMBIENTE', ''))
        ambiente_id = mapa_ambientes.get(nome_ambiente)
        
        if not ambiente_id:
            continue
        
        # Tratar data
        data_raw = row.get('DATA')
        if pd.isna(data_raw):
            continue
        
        try:
            data = pd.to_datetime(data_raw).strftime('%Y-%m-%d')
        except:
            continue
        
        # Tratar percentual
        percentual = row.get('PERCENTUAL_OCUPACAO', 0)
        if pd.isna(percentual):
            percentual = 0
        percentual = float(percentual) * 100 if float(percentual) <= 1 else float(percentual)
        
        registro = {
            'periodo_id': periodo_id,
            'ambiente_id': ambiente_id,
            'data_ocupacao': data,
            'turno': str(row.get('TURNO', '')) if pd.notna(row.get('TURNO')) else None,
            'percentual_ocupacao': min(percentual, 100)  # Garantir máximo de 100%
        }
        registros.append(registro)
    
    return inserir_ocupacao_batch(registros)


def importar_nao_regencia(xls: pd.ExcelFile, periodo_id: str,
                          mapa_instrutores: Dict[str, str]) -> int:
    """
    Importa registros de não regência do Excel para o banco
    """
    df = pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA")
    
    registros = []
    
    for _, row in df.iterrows():
        codigo_instrutor = str(row.get('ID_INSTRUTOR', ''))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        if not instrutor_id:
            continue
        
        # Tratar datas
        data_inicio = row.get('DATA_INICIO', row.get('DATA'))
        data_fim = row.get('DATA_FIM', data_inicio)
        
        try:
            data_inicio = pd.to_datetime(data_inicio).strftime('%Y-%m-%d') if pd.notna(data_inicio) else None
            data_fim = pd.to_datetime(data_fim).strftime('%Y-%m-%d') if pd.notna(data_fim) else None
        except:
            data_inicio = None
            data_fim = None
        
        registro = {
            'periodo_id': periodo_id,
            'instrutor_id': instrutor_id,
            'tipo_atividade': str(row.get('TIPO_ATIVIDADE', row.get('TIPO', 'Outro'))),
            'horas': float(row.get('HORAS_NAO_REGENCIA', row.get('HORAS', 0)) or 0),
            'data_inicio': data_inicio,
            'data_fim': data_fim
        }
        registros.append(registro)
    
    return inserir_nao_regencia_batch(registros)


def importar_faltas(xls: pd.ExcelFile, periodo_id: str,
                    mapa_turmas: Dict[str, str]) -> int:
    """
    Importa registros de faltas do Excel para o banco
    """
    df = pd.read_excel(xls, sheet_name="FALTAS")
    
    if df.empty:
        return 0
    
    registros = []
    
    for _, row in df.iterrows():
        # Buscar turma se houver
        codigo_turma = str(row.get('ID_TURMA', ''))
        turma_id = mapa_turmas.get(codigo_turma)
        
        # Tratar data
        data_raw = row.get('DATA_FALTA', row.get('DATA'))
        if pd.isna(data_raw):
            continue
        
        try:
            data = pd.to_datetime(data_raw).strftime('%Y-%m-%d')
        except:
            continue
        
        registro = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'data_falta': data,
            'quantidade_alunos': int(row.get('QUANTIDADE', 1) or 1),
            'motivo': str(row.get('MOTIVO', '')) if pd.notna(row.get('MOTIVO')) else None
        }
        registros.append(registro)
    
    return inserir_faltas_batch(registros)


# ============================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# ============================================================

def importar_planilha_completa(arquivo, usuario: str = "admin") -> Tuple[bool, str, Dict]:
    """
    Importa uma planilha completa para o banco de dados
    
    Args:
        arquivo: Arquivo Excel carregado
        usuario: Nome do usuário que está importando
        
    Returns:
        Tupla (sucesso, mensagem, estatísticas)
    """
    estatisticas = {
        'turmas': 0,
        'instrutores': 0,
        'ambientes': 0,
        'disciplinas': 0,
        'ocupacao': 0,
        'nao_regencia': 0,
        'faltas': 0
    }
    
    try:
        # 1. Validar planilha
        arquivo.seek(0)
        valido, msg = validar_planilha(arquivo)
        if not valido:
            return False, msg, estatisticas
        
        # 2. Extrair mês de referência
        arquivo.seek(0)
        mes_ref = extrair_mes_automatico(arquivo)
        if not mes_ref:
            return False, "Não foi possível detectar o mês automaticamente.", estatisticas
        
        # 3. Verificar se período já existe
        periodo_existente = obter_periodo_por_referencia(mes_ref)
        if periodo_existente:
            return False, f"O período '{mes_ref}' já existe. Delete-o primeiro se quiser reimportar.", estatisticas
        
        # 4. Criar período
        periodo = criar_periodo(mes_ref, usuario)
        if not periodo:
            return False, "Erro ao criar período no banco de dados.", estatisticas
        
        periodo_id = periodo['id']
        
        # 5. Abrir Excel
        arquivo.seek(0)
        xls = pd.ExcelFile(arquivo)
        
        # 6. Importar dados em ordem de dependência
        
        # 6.1 Turmas (base para disciplinas)
        qtd, mapa_turmas = importar_turmas(xls, periodo_id)
        estatisticas['turmas'] = qtd
        
        # 6.2 Instrutores (base para disciplinas e NR)
        qtd, mapa_instrutores = importar_instrutores(xls, periodo_id)
        estatisticas['instrutores'] = qtd
        
        # 6.3 Ambientes (base para ocupação)
        qtd, mapa_ambientes = importar_ambientes(xls, periodo_id)
        estatisticas['ambientes'] = qtd
        
        # 6.4 Disciplinas (depende de turmas e instrutores)
        estatisticas['disciplinas'] = importar_disciplinas(
            xls, periodo_id, mapa_turmas, mapa_instrutores
        )
        
        # 6.5 Ocupação (depende de ambientes)
        estatisticas['ocupacao'] = importar_ocupacao(
            xls, periodo_id, mapa_ambientes
        )
        
        # 6.6 Não Regência (depende de instrutores)
        estatisticas['nao_regencia'] = importar_nao_regencia(
            xls, periodo_id, mapa_instrutores
        )
        
        # 6.7 Faltas (depende de turmas)
        estatisticas['faltas'] = importar_faltas(
            xls, periodo_id, mapa_turmas
        )
        
        # 7. Limpar caches
        limpar_todos_caches()
        
        return True, f"✅ Período '{mes_ref}' importado com sucesso!", estatisticas
    
    except Exception as e:
        return False, f"Erro durante importação: {str(e)}", estatisticas


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_status(status: str) -> str:
    """Normaliza status da disciplina para valores padrão"""
    status_upper = status.strip().upper()
    
    if status_upper in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO', 'COMPLETO']:
        return 'Concluído'
    elif status_upper in ['EM ANDAMENTO', 'ANDAMENTO', 'EM CURSO']:
        return 'Em Andamento'
    elif status_upper in ['CANCELADO', 'CANCELADA']:
        return 'Cancelado'
    elif status_upper in ['SUSPENSO', 'SUSPENSA']:
        return 'Suspenso'
    else:
        return 'Não Iniciado'