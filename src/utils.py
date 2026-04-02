"""
Funções utilitárias gerais
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Optional


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar_numero(valor: float, decimais: int = 0) -> str:
    """Formata número com separador de milhares brasileiro"""
    if pd.isna(valor):
        return "0"
    return f"{valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor: float, decimais: int = 1) -> str:
    """Formata percentual com símbolo"""
    if pd.isna(valor):
        return "0%"
    return f"{valor:.{decimais}f}%"


def formatar_data(data, formato: str = "%d/%m/%Y") -> str:
    """Formata data para exibição"""
    if pd.isna(data):
        return "-"
    if isinstance(data, str):
        try:
            data = pd.to_datetime(data)
        except:
            return data
    return data.strftime(formato)


# ============================================================
# CORES E ESTILOS
# ============================================================

def cor_por_percentual(valor: float) -> str:
    """Retorna cor baseada em percentual (0-100)"""
    if valor >= 80:
        return "#28a745"  # Verde
    elif valor >= 50:
        return "#ffc107"  # Amarelo
    else:
        return "#dc3545"  # Vermelho


def estilo_status(status: str) -> str:
    """Retorna estilo CSS para célula baseado no status"""
    status_upper = str(status).upper()
    
    if status_upper in ['CONCLUÍDO', 'CONCLUIDO', 'FINALIZADO']:
        return "background-color: #d4edda; color: #155724;"
    elif status_upper in ['EM ANDAMENTO', 'ANDAMENTO']:
        return "background-color: #fff3cd; color: #856404;"
    elif status_upper in ['CANCELADO', 'SUSPENSO']:
        return "background-color: #f8d7da; color: #721c24;"
    else:
        return "background-color: #e2e3e5; color: #383d41;"


def aplicar_estilo_status(df: pd.DataFrame, coluna: str = 'status') -> pd.DataFrame:
    """Aplica estilo condicional a DataFrame baseado em status"""
    
    def pintar(val):
        return estilo_status(val)
    
    if coluna in df.columns:
        return df.style.map(pintar, subset=[coluna])
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
    resultado = extrair_mes_ano(mes_referencia)
    if resultado:
        mes, ano = resultado
        return f"{MESES_PT[mes]} de {ano}"
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

def calcular_variacao(atual: float, anterior: float) -> tuple:
    """
    Calcula variação percentual entre dois valores
    
    Returns:
        Tupla (percentual, texto_formatado)
    """
    if anterior == 0:
        return (0, "N/A")
    
    variacao = ((atual - anterior) / anterior) * 100
    sinal = "+" if variacao > 0 else ""
    texto = f"{sinal}{variacao:.1f}%"
    
    return (variacao, texto)


def delta_cor(valor: float, inverter: bool = False) -> str:
    """
    Retorna indicador de delta para st.metric
    
    Args:
        valor: Valor da variação
        inverter: Se True, negativo é bom (ex: faltas)
    """
    if inverter:
        return "inverse" if valor > 0 else "normal"
    return "normal" if valor > 0 else "inverse"