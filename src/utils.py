"""
Funções utilitárias gerais
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Optional


# ============================================================
# TRATAMENTO SEGURO DE VALORES
# ============================================================

def safe_number(value, default=0):
    """
    Converte valor para número de forma segura
    Trata None, NaN, strings, etc.
    """
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


def safe_int(value, default=0):
    """Converte valor para inteiro de forma segura"""
    return int(safe_number(value, default))


def safe_string(value, default=""):
    """Converte valor para string de forma segura"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value)


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar_numero(valor, decimais: int = 0) -> str:
    """Formata número com separador de milhares brasileiro"""
    num = safe_number(valor, 0)
    if decimais == 0:
        return f"{int(num):,}".replace(',', '.')
    else:
        return f"{num:,.{decimais}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_percentual(valor, decimais: int = 1) -> str:
    """Formata percentual com símbolo"""
    num = safe_number(valor, 0)
    return f"{num:.{decimais}f}%"


def formatar_data(data, formato: str = "%d/%m/%Y") -> str:
    """Formata data para exibição"""
    if data is None or (isinstance(data, float) and pd.isna(data)):
        return "-"
    if isinstance(data, str):
        try:
            data = pd.to_datetime(data)
        except:
            return data
    try:
        return data.strftime(formato)
    except:
        return str(data)


# ============================================================
# CORES E ESTILOS
# ============================================================

def cor_por_percentual(valor: float) -> str:
    """Retorna cor baseada em percentual (0-100)"""
    num = safe_number(valor, 0)
    if num >= 80:
        return "#28a745"  # Verde
    elif num >= 50:
        return "#ffc107"  # Amarelo
    else:
        return "#dc3545"  # Vermelho


def estilo_status(status: str) -> str:
    """Retorna estilo CSS para célula baseado no status"""
    status_str = safe_string(status, "").upper()
    
    if status_str in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO']:
        return "background-color: #d4edda; color: #155724;"
    elif status_str in ['EM ANDAMENTO', 'ANDAMENTO']:
        return "background-color: #fff3cd; color: #856404;"
    elif status_str in ['CANCELADO', 'SUSPENSO']:
        return "background-color: #f8d7da; color: #721c24;"
    else:
        return "background-color: #e2e3e5; color: #383d41;"


def aplicar_estilo_status(df: pd.DataFrame, coluna: str = 'status'):
    """Aplica estilo condicional a DataFrame baseado em status"""
    
    def pintar(val):
        return estilo_status(val)
    
    if coluna in df.columns:
        try:
            return df.style.map(pintar, subset=[coluna])
        except AttributeError:
            # Versão antiga do pandas
            return df.style.applymap(pintar, subset=[coluna])
    return df


# ============================================================
# MESES E DATAS
# ============================================================

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

MESES_PT_ABREV = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}


def extrair_mes_ano(mes_referencia: str) -> Optional[tuple]:
    """
    Extrai mês e ano de uma string de referência
    
    Args:
        mes_referencia: Ex: "03 - Mar 2025"
        
    Returns:
        Tupla (mes, ano) ou None
    """
    if not mes_referencia:
        return None
    try:
        partes = mes_referencia.split()
        mes = int(partes[0])
        ano = int(partes[-1])
        return (mes, ano)
    except:
        return None


def nome_mes_extenso(mes_referencia: str) -> str:
    """
    Converte referência curta para nome extenso
    
    Args:
        mes_referencia: Ex: "03 - Mar 2025"
        
    Returns:
        Ex: "Março de 2025"
    """
    if not mes_referencia:
        return "Período não definido"
    
    resultado = extrair_mes_ano(mes_referencia)
    if resultado:
        mes, ano = resultado
        return f"{MESES_PT.get(mes, 'Mês')} de {ano}"
    return mes_referencia


# ============================================================
# EXPORTAÇÃO
# ============================================================

def df_para_csv(df: pd.DataFrame) -> bytes:
    """Converte DataFrame para CSV em bytes (para download)"""
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def df_para_excel(df: pd.DataFrame) -> bytes:
    """Converte DataFrame para Excel em bytes (para download)"""
    import io
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()


def botao_download_csv(df: pd.DataFrame, nome_arquivo: str, 
                       label: str = "📥 Baixar CSV"):
    """Renderiza botão de download de CSV"""
    if df.empty:
        st.info("Não há dados para exportar")
        return
    
    csv = df_para_csv(df)
    st.download_button(
        label=label,
        data=csv,
        file_name=nome_arquivo,
        mime="text/csv",
        use_container_width=True
    )


# ============================================================
# MÉTRICAS
# ============================================================

def calcular_variacao(atual, anterior) -> tuple:
    """
    Calcula variação percentual entre dois valores
    
    Returns:
        Tupla (percentual, texto_formatado)
    """
    atual_num = safe_number(atual, 0)
    anterior_num = safe_number(anterior, 0)
    
    if anterior_num == 0:
        return (0, "N/A")
    
    variacao = ((atual_num - anterior_num) / anterior_num) * 100
    sinal = "+" if variacao > 0 else ""
    texto = f"{sinal}{variacao:.1f}%"
    
    return (variacao, texto)


def delta_cor(valor, inverter: bool = False) -> str:
    """
    Retorna indicador de delta para st.metric
    
    Args:
        valor: Valor da variação
        inverter: Se True, negativo é bom (ex: faltas)
    """
    num = safe_number(valor, 0)
    if inverter:
        return "inverse" if num > 0 else "normal"
    return "normal" if num > 0 else "inverse"