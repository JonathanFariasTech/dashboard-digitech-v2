# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO E LIMPEZA DE DADOS
# ============================================================

def normalizar_turno(turno_raw) -> str:
    """Normaliza o texto do turno vindo do Excel para o padrão do BD"""
    if pd.isna(turno_raw) or not str(turno_raw).strip():
        return 'Manhã'  # Valor padrão seguro se estiver vazio
        
    t = str(turno_raw).strip().upper()
    
    if t in ['MANHÃ', 'MANHA', 'MATUTINO', 'M']:
        return 'Manhã'
    elif t in ['TARDE', 'VESPERTINO', 'T']:
        return 'Tarde'
    elif t in ['NOITE', 'NOTURNO', 'N']:
        return 'Noite'
    elif t in ['INTEGRAL', 'I']:
        return 'Integral'
    elif t in ['EAD', 'ONLINE', 'VIRTUAL', 'E']:
        return 'EAD'
        
    return 'Manhã'  # Fallback (valor padrão)


def normalizar_tipo_ambiente(tipo_raw) -> str:
    """Normaliza o tipo de ambiente para o padrão do BD"""
    if pd.isna(tipo_raw) or not str(tipo_raw).strip():
        return 'Sala'
        
    t = str(tipo_raw).strip().upper()
    
    if 'LAB' in t: return 'Laboratório'
    if 'SALA' in t: return 'Sala'
    if 'OFICINA' in t: return 'Oficina'
    if 'AUDIT' in t: return 'Auditório'
    
    return 'Outro'


def normalizar_status(status_raw) -> str:
    """Normaliza status da disciplina para valores padrão"""
    if pd.isna(status_raw) or not str(status_raw).strip():
        return 'Não Iniciado'
        
    s = str(status_raw).strip().upper()
    
    if s in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO', 'COMPLETO']:
        return 'Concluído'
    elif s in ['EM ANDAMENTO', 'ANDAMENTO', 'EM CURSO']:
        return 'Em Andamento'
    elif s in ['CANCELADO', 'CANCELADA']:
        return 'Cancelado'
    elif s in ['SUSPENSO', 'SUSPENSA']:
        return 'Suspenso'
    else:
        return 'Não Iniciado'


# ============================================================
# FUNÇÕES DE IMPORTAÇÃO (CORRIGIDAS)
# ============================================================

def importar_turmas(xls: pd.ExcelFile, periodo_id: str):
    """Importa turmas do Excel para o banco"""
    df = pd.read_excel(xls, sheet_name="TURMAS")
    
    mapeamento = {}
    turmas = []
    
    for _, row in df.iterrows():
        codigo = str(row.get('ID_TURMA', row.get('CODIGO', '')))
        
        # Ignorar linhas completamente vazias
        if not codigo or codigo.lower() == 'nan':
            continue
            
        # ✅ Usando a nova função de normalização
        turno_limpo = normalizar_turno(row.get('TURNO'))
        
        turma = {
            'periodo_id': periodo_id,
            'codigo_turma': codigo,
            'nome_turma': str(row.get('NOME_TURMA', row.get('NOME', ''))),
            'curso': str(row.get('CURSO', '')),
            'turno': turno_limpo,
            'vagas_total': int(row.get('VAGAS_TOTAL', row.get('VAGAS', 0)) or 0),
            'vagas_ocupadas': int(row.get('VAGAS_OCUPADAS', 0) or 0)
        }
        turmas.append(turma)
    
    if turmas:
        from src.database import get_db
        db = get_db()
        response = db.table('turmas').insert(turmas).execute()
        
        # Criar mapeamento de códigos para UUIDs
        if hasattr(response, 'data') and response.data:
            for item in response.data:
                mapeamento[item['codigo_turma']] = item['id']
    
    return len(turmas), mapeamento


def importar_ambientes(xls: pd.ExcelFile, periodo_id: str):
    """Importa ambientes do Excel para o banco"""
    df = pd.read_excel(xls, sheet_name="AMBIENTES")
    
    mapeamento = {}
    ambientes = []
    
    for _, row in df.iterrows():
        nome = str(row.get('AMBIENTE', row.get('NOME', row.get('NOME_AMBIENTE', ''))))
        
        if not nome or nome.lower() == 'nan':
            continue
        
        # Detectar se é virtual
        virtual_raw = row.get('VIRTUAL', 'NÃO')
        virtual = str(virtual_raw).upper() in ['SIM', 'S', 'TRUE', '1', 'VIRTUAL']
        
        # ✅ Usando a nova função de normalização
        tipo_limpo = normalizar_tipo_ambiente(row.get('TIPO'))
        
        ambiente = {
            'periodo_id': periodo_id,
            'codigo_ambiente': nome,
            'nome_ambiente': nome,
            'tipo': tipo_limpo,
            'capacidade': int(row.get('CAPACIDADE', 0) or 0),
            'virtual': virtual
        }
        ambientes.append(ambiente)
    
    if ambientes:
        from src.database import get_db
        db = get_db()
        response = db.table('ambientes').insert(ambientes).execute()
        
        if hasattr(response, 'data') and response.data:
            for item in response.data:
                mapeamento[item['nome_ambiente']] = item['id']
    
    return len(ambientes), mapeamento