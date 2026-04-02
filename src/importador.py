"""
Módulo para importação de planilhas Excel para o banco de dados
VERSÃO LIMPA - Sem mensagens de debug
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional, List


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
# FUNÇÕES DE LIMPEZA E CONVERSÃO
# ============================================================

def limpar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa todo o DataFrame substituindo NaN por valores padrão"""
    df = df.copy()
    
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str)
            df[col] = df[col].replace(['nan', 'NaN', 'NAN', 'None', 'none', 'NONE', 'null', 'NULL'], '')
            df[col] = df[col].str.strip()
        elif df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            df[col] = df[col].fillna(0)
    
    return df


def valor_inteiro(valor, padrao: int = 0) -> int:
    """Converte qualquer valor para inteiro de forma segura"""
    if valor is None:
        return padrao
    
    if isinstance(valor, int):
        return valor
    
    if isinstance(valor, float):
        if np.isnan(valor) or pd.isna(valor):
            return padrao
        return int(valor)
    
    if isinstance(valor, (np.integer, np.floating)):
        if pd.isna(valor):
            return padrao
        return int(valor)
    
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor or valor.lower() in ['nan', 'none', 'null', '', '-']:
            return padrao
        try:
            return int(float(valor))
        except:
            return padrao
    
    try:
        if pd.isna(valor):
            return padrao
        return int(float(valor))
    except:
        return padrao


def valor_float(valor, padrao: float = 0.0) -> float:
    """Converte qualquer valor para float de forma segura"""
    if valor is None:
        return padrao
    
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and (np.isnan(valor) or pd.isna(valor)):
            return padrao
        return float(valor)
    
    if isinstance(valor, (np.integer, np.floating)):
        if pd.isna(valor):
            return padrao
        return float(valor)
    
    if isinstance(valor, str):
        valor = valor.strip().replace(',', '.')
        if not valor or valor.lower() in ['nan', 'none', 'null', '', '-']:
            return padrao
        try:
            return float(valor)
        except:
            return padrao
    
    try:
        if pd.isna(valor):
            return padrao
        return float(valor)
    except:
        return padrao


def valor_texto(valor, padrao: str = "") -> str:
    """Converte qualquer valor para texto de forma segura"""
    if valor is None:
        return padrao
    
    try:
        if pd.isna(valor):
            return padrao
    except:
        pass
    
    texto = str(valor).strip()
    
    if texto.lower() in ['nan', 'none', 'null', 'na', 'n/a', '-']:
        return padrao
    
    return texto


def valor_data(valor, formato: str = '%Y-%m-%d') -> Optional[str]:
    """Converte qualquer valor para data no formato string"""
    if valor is None:
        return None
    
    try:
        if pd.isna(valor):
            return None
    except:
        pass
    
    try:
        data = pd.to_datetime(valor, errors='coerce')
        if pd.isna(data):
            return None
        return data.strftime(formato)
    except:
        return None


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def normalizar_turno(turno_raw) -> str:
    """Normaliza turno para valores aceitos pelo BD"""
    valor = valor_texto(turno_raw, "").upper()
    
    if not valor:
        return 'Manhã'
    
    if any(x in valor for x in ['MANHÃ', 'MANHA', 'MATUTINO']) or valor == 'M':
        return 'Manhã'
    if any(x in valor for x in ['TARDE', 'VESPERTINO']) or valor == 'T':
        return 'Tarde'
    if any(x in valor for x in ['NOITE', 'NOTURNO']) or valor == 'N':
        return 'Noite'
    if 'INTEGRAL' in valor or valor == 'I':
        return 'Integral'
    if any(x in valor for x in ['EAD', 'ONLINE', 'VIRTUAL', 'DISTÂNCIA', 'DISTANCIA']) or valor == 'E':
        return 'EAD'
    
    return 'Manhã'


def normalizar_tipo_ambiente(tipo_raw) -> str:
    """Normaliza tipo de ambiente"""
    valor = valor_texto(tipo_raw, "").upper()
    
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
    """Normaliza status da disciplina"""
    valor = valor_texto(status_raw, "").upper()
    
    if not valor:
        return 'Não Iniciado'
    
    if any(x in valor for x in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO', 'COMPLETO']):
        return 'Concluído'
    if any(x in valor for x in ['ANDAMENTO', 'CURSO', 'PROGRESSO']):
        return 'Em Andamento'
    if 'CANCELAD' in valor:
        return 'Cancelado'
    if 'SUSPENS' in valor:
        return 'Suspenso'
    
    return 'Não Iniciado'


def normalizar_booleano(valor_raw) -> bool:
    """Converte para booleano"""
    valor = valor_texto(valor_raw, "").upper()
    return valor in ['SIM', 'S', 'TRUE', '1', 'YES', 'Y', 'VERDADEIRO', 'V']


# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def validar_planilha(arquivo) -> Tuple[bool, str]:
    """Valida se a planilha tem todas as abas obrigatórias"""
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
    """Extrai o mês de referência automaticamente da planilha"""
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
    """Importa turmas do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="TURMAS")
        df = limpar_dataframe(df)
    except Exception as e:
        return 0, {}
    
    mapeamento = {}
    turmas = []
    
    for idx, row in df.iterrows():
        codigo = valor_texto(row.get('ID_TURMA', row.get('CODIGO', row.get('ID', ''))))
        
        if not codigo:
            continue
        
        turma = {
            'periodo_id': periodo_id,
            'codigo_turma': codigo,
            'nome_turma': valor_texto(row.get('NOME_TURMA', row.get('NOME', row.get('CURSO', '')))),
            'curso': valor_texto(row.get('CURSO', '')),
            'turno': normalizar_turno(row.get('TURNO')),
            'vagas_total': valor_inteiro(row.get('VAGAS_TOTAL', row.get('VAGAS', 0))),
            'vagas_ocupadas': valor_inteiro(row.get('VAGAS_OCUPADAS', row.get('ALUNOS', 0)))
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
        except Exception:
            return 0, {}
    
    return len(turmas), mapeamento


def importar_instrutores(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """Importa instrutores do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="INSTRUTORES")
        df = limpar_dataframe(df)
    except Exception:
        return 0, {}
    
    mapeamento = {}
    instrutores = []
    
    for idx, row in df.iterrows():
        codigo = valor_texto(row.get('ID', row.get('ID_INSTRUTOR', row.get('CODIGO', ''))))
        nome = valor_texto(row.get('NOME_COMPLETO', row.get('NOME', '')))
        
        if not codigo or not nome:
            continue
        
        instrutor = {
            'periodo_id': periodo_id,
            'codigo_instrutor': codigo,
            'nome_completo': nome,
            'email': valor_texto(row.get('EMAIL')) or None,
            'especialidade': valor_texto(row.get('ESPECIALIDADE')) or None,
            'carga_horaria_contrato': valor_inteiro(row.get('CARGA_HORARIA', row.get('CH', 40)), 40)
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
        except Exception:
            return 0, {}
    
    return len(instrutores), mapeamento


def importar_ambientes(xls: pd.ExcelFile, periodo_id: str) -> Tuple[int, Dict[str, str]]:
    """Importa ambientes do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="AMBIENTES")
        df = limpar_dataframe(df)
    except Exception:
        return 0, {}
    
    mapeamento = {}
    ambientes = []
    
    for idx, row in df.iterrows():
        nome = valor_texto(row.get('AMBIENTE', row.get('NOME', row.get('NOME_AMBIENTE', ''))))
        
        if not nome:
            continue
        
        ambiente = {
            'periodo_id': periodo_id,
            'codigo_ambiente': nome,
            'nome_ambiente': nome,
            'tipo': normalizar_tipo_ambiente(row.get('TIPO')),
            'capacidade': valor_inteiro(row.get('CAPACIDADE', 0)),
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
        except Exception:
            return 0, {}
    
    return len(ambientes), mapeamento


def importar_disciplinas(xls: pd.ExcelFile, periodo_id: str, 
                         mapa_turmas: Dict[str, str],
                         mapa_instrutores: Dict[str, str]) -> int:
    """Importa disciplinas do Excel para o banco"""
    try:
        try:
            df = pd.read_excel(xls, sheet_name="DISCIPLINAS", skiprows=1)
        except:
            df = pd.read_excel(xls, sheet_name="DISCIPLINAS")
        df = limpar_dataframe(df)
    except Exception:
        return 0
    
    disciplinas = []
    
    for idx, row in df.iterrows():
        codigo_turma = valor_texto(row.get('ID_TURMA', row.get('TURMA', '')))
        turma_id = mapa_turmas.get(codigo_turma)
        
        if not turma_id:
            continue
        
        nome_disc = valor_texto(row.get('NOME_DISCIPLINA', row.get('DISCIPLINA', row.get('NOME', ''))))
        
        if not nome_disc:
            continue
        
        codigo_instrutor = valor_texto(row.get('ID_INSTRUTOR', row.get('INSTRUTOR', '')))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        disciplina = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'instrutor_id': instrutor_id,
            'nome_disciplina': nome_disc,
            'carga_horaria': valor_inteiro(row.get('CARGA_HORARIA', row.get('CH', 0))),
            'status': normalizar_status(row.get('STATUS'))
        }
        disciplinas.append(disciplina)
    
    if disciplinas:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('disciplinas').insert(disciplinas).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception:
            return 0
    
    return 0


def importar_ocupacao(xls: pd.ExcelFile, periodo_id: str,
                      mapa_ambientes: Dict[str, str]) -> int:
    """Importa registros de ocupação do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="OCUPAÇÃO")
        df = limpar_dataframe(df)
    except Exception:
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        nome_ambiente = valor_texto(row.get('AMBIENTE', ''))
        ambiente_id = mapa_ambientes.get(nome_ambiente)
        
        if not ambiente_id:
            continue
        
        data = valor_data(row.get('DATA'))
        if not data:
            continue
        
        percentual = valor_float(row.get('PERCENTUAL_OCUPACAO', row.get('OCUPACAO', 0)))
        if 0 < percentual <= 1:
            percentual = percentual * 100
        percentual = max(0, min(100, percentual))
        
        registro = {
            'periodo_id': periodo_id,
            'ambiente_id': ambiente_id,
            'data_ocupacao': data,
            'turno': normalizar_turno(row.get('TURNO')) if valor_texto(row.get('TURNO')) else None,
            'percentual_ocupacao': round(percentual, 2)
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('ocupacao').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception:
            return 0
    
    return 0


def importar_nao_regencia(xls: pd.ExcelFile, periodo_id: str,
                          mapa_instrutores: Dict[str, str]) -> int:
    """Importa registros de não regência do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="NÃO_REGÊNCIA")
        df = limpar_dataframe(df)
    except Exception:
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        codigo_instrutor = valor_texto(row.get('ID_INSTRUTOR', row.get('INSTRUTOR', '')))
        instrutor_id = mapa_instrutores.get(codigo_instrutor)
        
        if not instrutor_id:
            continue
        
        tipo = valor_texto(row.get('TIPO_ATIVIDADE', row.get('TIPO', row.get('ATIVIDADE', 'Outro'))))
        if not tipo:
            tipo = 'Outro'
        
        horas = valor_float(row.get('HORAS_NAO_REGENCIA', row.get('HORAS', 0)))
        
        if horas <= 0:
            continue
        
        registro = {
            'periodo_id': periodo_id,
            'instrutor_id': instrutor_id,
            'tipo_atividade': tipo,
            'horas': round(horas, 2),
            'data_inicio': valor_data(row.get('DATA_INICIO', row.get('DATA'))),
            'data_fim': valor_data(row.get('DATA_FIM', row.get('DATA')))
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('nao_regencia').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception:
            return 0
    
    return 0


def importar_faltas(xls: pd.ExcelFile, periodo_id: str,
                    mapa_turmas: Dict[str, str]) -> int:
    """Importa registros de faltas do Excel para o banco"""
    try:
        df = pd.read_excel(xls, sheet_name="FALTAS")
        df = limpar_dataframe(df)
    except Exception:
        return 0
    
    if df.empty:
        return 0
    
    registros = []
    
    for idx, row in df.iterrows():
        data = valor_data(row.get('DATA_FALTA', row.get('DATA')))
        if not data:
            continue
        
        codigo_turma = valor_texto(row.get('ID_TURMA', row.get('TURMA', '')))
        turma_id = mapa_turmas.get(codigo_turma)
        
        quantidade = valor_inteiro(row.get('QUANTIDADE', row.get('QTD', 1)), 1)
        
        registro = {
            'periodo_id': periodo_id,
            'turma_id': turma_id,
            'data_falta': data,
            'quantidade_alunos': max(1, quantidade),
            'motivo': valor_texto(row.get('MOTIVO')) or None
        }
        registros.append(registro)
    
    if registros:
        try:
            from src.database import get_db
            db = get_db()
            response = db.table('faltas').insert(registros).execute()
            return len(response.data) if hasattr(response, 'data') and response.data else 0
        except Exception:
            return 0
    
    return 0


# ============================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# ============================================================

def importar_planilha_completa(arquivo, usuario: str = "admin") -> Tuple[bool, str, Dict]:
    """Importa uma planilha completa para o banco de dados"""
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
        from src.database import obter_periodo_por_referencia, criar_periodo, limpar_todos_caches
        
        periodo_existente = obter_periodo_por_referencia(mes_ref)
        if periodo_existente:
            return False, f"O período '{mes_ref}' já existe. Delete-o primeiro.", estatisticas
        
        # 4. Criar período
        periodo = criar_periodo(mes_ref, usuario)
        if not periodo:
            return False, "Erro ao criar período no banco de dados.", estatisticas
        
        periodo_id = periodo['id']
        
        # 5. Abrir Excel
        arquivo.seek(0)
        xls = pd.ExcelFile(arquivo)
        
        # 6. Importar dados (ordem de dependência)
        qtd, mapa_turmas = importar_turmas(xls, periodo_id)
        estatisticas['turmas'] = qtd
        
        qtd, mapa_instrutores = importar_instrutores(xls, periodo_id)
        estatisticas['instrutores'] = qtd
        
        qtd, mapa_ambientes = importar_ambientes(xls, periodo_id)
        estatisticas['ambientes'] = qtd
        
        estatisticas['disciplinas'] = importar_disciplinas(xls, periodo_id, mapa_turmas, mapa_instrutores)
        
        estatisticas['ocupacao'] = importar_ocupacao(xls, periodo_id, mapa_ambientes)
        
        estatisticas['nao_regencia'] = importar_nao_regencia(xls, periodo_id, mapa_instrutores)
        
        estatisticas['faltas'] = importar_faltas(xls, periodo_id, mapa_turmas)
        
        # 7. Limpar caches
        limpar_todos_caches()
        
        return True, f"✅ Período '{mes_ref}' importado com sucesso!", estatisticas
    
    except Exception as e:
        return False, f"Erro durante importação: {str(e)}", estatisticas