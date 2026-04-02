"""
Módulo para importação de planilhas Excel para o banco de dados
VERSÃO ROBUSTA - Trata todos os tipos de erros comuns de Excel
"""

import streamlit as st
import pandas as pd
from typing import Tuple, Dict, Optional, List
from datetime import datetime
import io


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
# FUNÇÕES DE CONVERSÃO SEGURA
# ============================================================

def safe_int(value, default: int = 0) -> int:
    """
    Converte valor para inteiro de forma segura
    Trata None, NaN, strings vazias, etc.
    """
    if value is None:
        return default
    
    # Verifica NaN (float)
    if isinstance(value, float):
        if pd.isna(value):
            return default
        return int(value)
    
    # Verifica NaN (pandas)
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    
    # String vazia
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    # Tenta converter diretamente
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """
    Converte valor para float de forma segura
    """
    if value is None:
        return default
    
    if isinstance(value, float):
        if pd.isna(value):
            return default
        return value
    
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    
    if isinstance(value, str):
        value = value.strip().replace(',', '.')
        if not value:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default: str = "") -> str:
    """
    Converte valor para string de forma segura
    Remove 'nan' e valores nulos
    """
    if value is None:
        return default
    
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    
    resultado = str(value).strip()
    
    # Remove strings que representam nulo
    if resultado.lower() in ['nan', 'none', 'null', 'na', 'n/a', '-']:
        return default
    
    return resultado


def safe_date(value, formato: str = '%Y-%m-%d') -> Optional[str]:
    """
    Converte valor para data no formato string para o BD
    """
    if value is None:
        return None
    
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    
    try:
        data = pd.to_datetime(value)
        if pd.isna(data):
            return None
        return data.strftime(formato)
    except:
        return None


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO DE DADOS
# ============================================================

def normalizar_turno(turno_raw) -> str:
    """
    Normaliza o texto do turno vindo do Excel para o padrão do BD
    Aceita: manhã, manha, MANHÃ, Matutino, M, etc.
    """
    valor = safe_str(turno_raw, "").upper()
    
    if not valor:
        return 'Manhã'  # Valor padrão
    
    # Manhã
    if any(x in valor for x in ['MANHÃ', 'MANHA', 'MATUTINO']):
        return 'Manhã'
    if valor == 'M':
        return 'Manhã'
    
    # Tarde
    if any(x in valor for x in ['TARDE', 'VESPERTINO']):
        return 'Tarde'
    if valor == 'T':
        return 'Tarde'
    
    # Noite
    if any(x in valor for x in ['NOITE', 'NOTURNO']):
        return 'Noite'
    if valor == 'N':
        return 'Noite'
    
    # Integral
    if 'INTEGRAL' in valor:
        return 'Integral'
    if valor == 'I':
        return 'Integral'
    
    # EAD
    if any(x in valor for x in ['EAD', 'ONLINE', 'VIRTUAL', 'DISTÂNCIA', 'DISTANCIA']):
        return 'EAD'
    if valor == 'E':
        return 'EAD'
    
    # Fallback
    return 'Manhã'


def normalizar_tipo_ambiente(tipo_raw) -> str:
    """
    Normaliza o tipo de ambiente para o padrão do BD
    """
    valor = safe_str(tipo_raw, "").upper()
    
    if not valor:
        return 'Sala'
    
    if 'LAB' in valor:
        return 'Laboratório'
    if 'OFICINA' in valor:
        return 'Oficina'
    if 'AUDIT' in valor:
        return 'Auditório'
    if 'SALA' in valor:
        return 'Sala'
    
    return 'Outro'


def normalizar_status(status_raw) -> str:
    """
    Normaliza status da disciplina para valores padrão
    """
    valor = safe_str(status_raw, "").upper()
    
    if not valor:
        return 'Não Iniciado'
    
    # Concluído
    if any(x in valor for x in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO', 'COMPLETO', 'TERMINADO']):
        return 'Concluído'
    
    # Em Andamento
    if any(x in valor for x in ['ANDAMENTO', 'CURSO', 'PROGRESSO', 'EXECUTANDO']):
        return 'Em Andamento'
    
    # Cancelado
    if any(x in valor for x in ['CANCELAD', 'ABORT']):
        return 'Cancelado'
    
    # Suspenso
    if any(x in valor for x in ['SUSPENS', 'PAUSAD', 'PARAD']):
        return 'Suspenso'
    
    return 'Não Iniciado'


def normalizar_booleano(valor_raw) -> bool:
    """
    Converte valor para booleano
    """
    valor = safe_str(valor_raw, "").upper()
    
    if not valor:
        return False
    
    return valor in ['SIM', 'S', 'TRUE', '1', 'YES', 'Y', 'VERDADEIRO', 'V']


# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def validar_planilha(arquivo) -> Tuple[bool, str]:
    """
    Valida se a planilha tem todas as abas obrigatórias
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
    """
    try:
        df = pd.read_excel(xls, sheet_name="TURMAS")
    except Exception as e:
        st.error(f"Erro ao ler aba TURMAS: {str(e)}")
        return 0, {}
    
    mapeamento = {}
    turmas = []
    
    for idx, row in df.iterrows():
        # Buscar código da turma
        codigo = safe_str(row.get('ID_TURMA', row.get('CODIGO', row.get('ID', ''))))
        
        # Ignorar linhas sem código
        if not codigo:
            continue
        
        turma = {
            'periodo_id': periodo_id,
            'codigo_turma': codigo,
            'nome_turma': safe_str(row.get('NOME_TURMA', row.get('NOME', row.get('CURSO', '')))),
            'curso': safe_str(row.get('CURSO', '')),
            'turno': normalizar_turno(row.get('TURNO')),
            'vagas_total': safe_int(row.get('VAGAS_TOTAL', row.get('VAGAS', 0))),
            'vagas_ocupadas': safe_int(row.get('VAGAS_OCUPADAS', row.get('ALUNOS', 0)))
        }
        turmas.append(turma)
    
    if turmas:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('turmas').insert(turmas).execute()
            
            if hasattr(response, 'data') and response.data:
                for item in response.data:
                    mapeamento[item['codigo_turma']] = item['id']
        except Exception as e:
            st.error(f"Erro ao inserir turmas: {str(e)}")
            return 0, {}
    
    return len(turmas), mapeamento


def importar_instrutores(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """
    Importa instrutores do Excel para o banco
    """
    try:
        df = pd.read_excel(xls, sheet_name="INSTRUTORES")
    except Exception as e:
        st.error(f"Erro ao ler aba INSTRUTORES: {str(e)}")
        return 0, {}
    
    mapeamento = {}
    instrutores = []
    
    for idx, row in df.iterrows():
        codigo = safe_str(row.get('ID', row.get('ID_INSTRUTOR', row.get('CODIGO', ''))))
        nome = safe_str(row.get('NOME_COMPLETO', row.get('NOME', '')))
        
        # Ignorar linhas sem código ou nome
        if not codigo or not nome:
            continue
        
        instrutor = {
            'periodo_id': periodo_id,
            'codigo_instrutor': codigo,
            'nome_completo': nome,
            'email': safe_str(row.get('EMAIL')) or None,
            'especialidade': safe_str(row.get('ESPECIALIDADE')) or None,
            'carga_horaria_contrato': safe_int(row.get('CARGA_HORARIA', row.get('CH', 40)), 40)
        }
        instrutores.append(instrutor)
    
    if instrutores:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('instrutores').insert(instrutores).execute()
            
            if hasattr(response, 'data') and response.data:
                for item in response.data:
                    mapeamento[item['codigo_instrutor']] = item['id']
        except Exception as e:
            st.error(f"Erro ao inserir instrutores: {str(e)}")
            return 0, {}
    
    return len(instrutores), mapeamento


def importar_ambientes(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """
    Importa ambientes do Excel para o banco
    """
    try:
        df = pd.read_excel(xls, sheet_name="AMBIENTES")
    except Exception as e:
        st.error(f"Erro ao ler aba AMBIENTES: {str(e)}")
        return 0, {}
    
    mapeamento = {}
    ambientes = []
    
    for idx, row in df.iterrows():
        nome = safe_str(row.get('AMBIENTE', row.get('NOME', row.get('NOME_AMBIENTE', ''))))
        
        # Ignorar linhas sem nome
        if not nome:
            continue
        
        ambiente = {
            'periodo_id': periodo_id,
            'codigo_ambiente': nome,
            'nome_ambiente': nome,
            'tipo': normalizar_tipo_ambiente(row.get('TIPO')),
            'capacidade': safe_int(row.get('CAPACIDADE', 0)),
            'virtual': normalizar_booleano(row.get('VIRTUAL', 'NÃO'))
        }
        ambientes.append(ambiente)
    
    if ambientes:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('ambientes').insert(ambientes).execute()
            
            if hasattr(response, 'data') and response.data:
                for item in response.data:
                    mapeamento[item['nome_ambiente']] = item['id']
        except Exception as e:
            st.error(f"Erro ao inserir ambientes: {str(e)}")
            return 0, {}
    
    return len(ambientes), mapeamento


def importar_disciplinas(xls: pd.ExcelFile, periodo_id: str, 
                         mapa_turmas: Dict[str, str],
                         mapa_instrutores: Dict[str, str]) -> int:
    """
    Importa disciplinas do Excel para o banco
    """
    try:
        # Tenta com skiprows primeiro (formato comum)
        try:
            df = pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1)
        except:
            df = pd.read_excel(xls, sheet_name="DISCIPLINAS")
    except Exception as e:
        st.error(f"Erro ao ler aba DISCIPLINAS: {str(e)}")
        return 0
    
    disciplinas = []
    
    for idx, row in df.iterrows():
        codigo_turma = safe_str(row.get('ID_TURMA', row.get('TURMA', '')))
        turma_id = mapa_turmas.get(codigo_turma)
        
        # Pula se não encontrar a turma
        if not turma_id:
            continue
        
        nome_disc = safe_str(row.get('NOME_DISCIPLINA', row.get('DISCIPLINA', row.get('NOME', ''))))
        
        # Pula se não tiver nome
        if not nome_disc:
            continue
        
        # Buscar instrutor (opcional)
        codigo_instrutor = safe_str(row.get('ID_INSTRUTOR', row.get('INSTRUTOR', '')))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        disciplina = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'instrutor_id': instrutor_id,
            'nome_disciplina': nome_disc,
            'carga_horaria': safe_int(row.get('CARGA_HORARIA', row.get('CH', 0))),
            'status': normalizar_status(row.get('STATUS'))
        }
        disciplinas.append(disciplina)
    
    if disciplinas:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('disciplinas').insert(disciplinas).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception as e:
            st.error(f"Erro ao inserir disciplinas: {str(e)}")
            return 0
    
    return 0


def importar_ocupacao(xls: pd.ExcelFile, periodo_id: str,
                      mapa_ambientes: Dict[str, str]) -> int:
    """
    Importa registros de ocupação do Excel para o banco
    """
    try:
        df = pd.read_excel(xls, sheet_name="OCUPAÇÃO")
    except Exception as e:
        st.error(f"Erro ao ler aba OCUPAÇÃO: {str(e)}")
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        nome_ambiente = safe_str(row.get('AMBIENTE', ''))
        ambiente_id = mapa_ambientes.get(nome_ambiente)
        
        # Pula se não encontrar o ambiente
        if not ambiente_id:
            continue
        
        # Processar data
        data = safe_date(row.get('DATA'))
        if not data:
            continue
        
        # Processar percentual (pode vir como 0.75 ou 75)
        percentual = safe_float(row.get('PERCENTUAL_OCUPACAO', row.get('OCUPACAO', 0)))
        
        # Normalizar: se < 1, assume que está em decimal (0.75 = 75%)
        if 0 < percentual <= 1:
            percentual = percentual * 100
        
        # Garantir limite de 0-100
        percentual = max(0, min(100, percentual))
        
        registro = {
            'periodo_id': periodo_id,
            'ambiente_id': ambiente_id,
            'data_ocupacao': data,
            'turno': normalizar_turno(row.get('TURNO')) if row.get('TURNO') else None,
            'percentual_ocupacao': round(percentual, 2)
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('ocupacao').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception as e:
            st.error(f"Erro ao inserir ocupação: {str(e)}")
            return 0
    
    return 0


def importar_nao_regencia(xls: pd.ExcelFile, periodo_id: str,
                          mapa_instrutores: Dict[str, str]) -> int:
    """
    Importa registros de não regência do Excel para o banco
    """
    try:
        df = pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA")
    except Exception as e:
        st.error(f"Erro ao ler aba NÃO_REGÊNCIA: {str(e)}")
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        codigo_instrutor = safe_str(row.get('ID_INSTRUTOR', row.get('INSTRUTOR', '')))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        # Pula se não encontrar o instrutor
        if not instrutor_id:
            continue
        
        tipo = safe_str(row.get('TIPO_ATIVIDADE', row.get('TIPO', row.get('ATIVIDADE', 'Outro'))))
        if not tipo:
            tipo = 'Outro'
        
        horas = safe_float(row.get('HORAS_NAO_REGENCIA', row.get('HORAS', 0)))
        
        # Pula se não tiver horas
        if horas <= 0:
            continue
        
        registro = {
            'periodo_id': periodo_id,
            'instrutor_id': instrutor_id,
            'tipo_atividade': tipo,
            'horas': round(horas, 2),
            'data_inicio': safe_date(row.get('DATA_INICIO', row.get('DATA'))),
            'data_fim': safe_date(row.get('DATA_FIM', row.get('DATA')))
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('nao_regencia').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception as e:
            st.error(f"Erro ao inserir não regência: {str(e)}")
            return 0
    
    return 0


def importar_faltas(xls: pd.ExcelFile, periodo_id: str,
                    mapa_turmas: Dict[str, str]) -> int:
    """
    Importa registros de faltas do Excel para o banco
    """
    try:
        df = pd.read_excel(xls, sheet_name="FALTAS")
    except Exception as e:
        st.error(f"Erro ao ler aba FALTAS: {str(e)}")
        return 0
    
    if df.empty:
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        # Data é obrigatória
        data = safe_date(row.get('DATA_FALTA', row.get('DATA')))
        if not data:
            continue
        
        # Turma (opcional)
        codigo_turma = safe_str(row.get('ID_TURMA', row.get('TURMA', '')))
        turma_id = mapa_turmas.get(codigo_turma)
        
        quantidade = safe_int(row.get('QUANTIDADE', row.get('QTD', 1)), 1)
        
        registro = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'data_falta': data,
            'quantidade_alunos': max(1, quantidade),
            'motivo': safe_str(row.get('MOTIVO')) or None
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('faltas').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception as e:
            st.error(f"Erro ao inserir faltas: {str(e)}")
            return 0
    
    return 0


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
            return False, "Não foi possível detectar o mês automaticamente. Verifique a coluna DATA na aba OCUPAÇÃO.", estatisticas
        
        # 3. Verificar se período já existe
        from src.database import obter_periodo_por_referencia, criar_periodo, limpar_todos_caches
        
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
        
        # 6.1 Turmas (base para disciplinas e faltas)
        qtd, mapa_turmas = importar_turmas(xls, periodo_id)
        estatisticas['turmas'] = qtd
        st.write(f"✅ Turmas importadas: {qtd}")
        
        # 6.2 Instrutores (base para disciplinas e NR)
        qtd, mapa_instrutores = importar_instrutores(xls, periodo_id)
        estatisticas['instrutores'] = qtd
        st.write(f"✅ Instrutores importados: {qtd}")
        
        # 6.3 Ambientes (base para ocupação)
        qtd, mapa_ambientes = importar_ambientes(xls, periodo_id)
        estatisticas['ambientes'] = qtd
        st.write(f"✅ Ambientes importados: {qtd}")
        
        # 6.4 Disciplinas (depende de turmas e instrutores)
        estatisticas['disciplinas'] = importar_disciplinas(
            xls, periodo_id, mapa_turmas, mapa_instrutores
        )
        st.write(f"✅ Disciplinas importadas: {estatisticas['disciplinas']}")
        
        # 6.5 Ocupação (depende de ambientes)
        estatisticas['ocupacao'] = importar_ocupacao(
            xls, periodo_id, mapa_ambientes
        )
        st.write(f"✅ Ocupação importada: {estatisticas['ocupacao']}")
        
        # 6.6 Não Regência (depende de instrutores)
        estatisticas['nao_regencia'] = importar_nao_regencia(
            xls, periodo_id, mapa_instrutores
        )
        st.write(f"✅ Não Regência importada: {estatisticas['nao_regencia']}")
        
        # 6.7 Faltas (depende de turmas)
        estatisticas['faltas'] = importar_faltas(
            xls, periodo_id, mapa_turmas
        )
        st.write(f"✅ Faltas importadas: {estatisticas['faltas']}")
        
        # 7. Limpar caches
        limpar_todos_caches()
        
        return True, f"✅ Período '{mes_ref}' importado com sucesso!", estatisticas
    
    except Exception as e:
        import traceback
        erro_detalhado = traceback.format_exc()
        st.error(f"Erro detalhado: {erro_detalhado}")
        return False, f"Erro durante importação: {str(e)}", estatisticas