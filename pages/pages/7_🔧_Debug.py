"""
Página de Debug - Identificar erros de importação
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Debug", page_icon="🔧", layout="wide")

st.title("🔧 Debug de Importação")
st.markdown("Use esta página para identificar problemas nos dados da planilha")

st.divider()

arquivo = st.file_uploader("Upload da Planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        xls = pd.ExcelFile(arquivo)
        
        st.success(f"✅ Arquivo carregado! Abas encontradas: {xls.sheet_names}")
        
        aba_selecionada = st.selectbox("Selecione a aba para analisar:", xls.sheet_names)
        
        if aba_selecionada:
            st.divider()
            st.markdown(f"### 📊 Análise da aba: {aba_selecionada}")
            
            # Ler com e sem skiprows
            try:
                df = pd.read_excel(xls, sheet_name=aba_selecionada)
            except:
                df = pd.read_excel(xls, sheet_name=aba_selecionada, skiprows=1)
            
            st.markdown(f"**Linhas:** {len(df)} | **Colunas:** {len(df.columns)}")
            
            # Mostrar colunas e tipos
            st.markdown("#### 📋 Colunas e Tipos de Dados:")
            
            col_info = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nulls = df[col].isna().sum()
                sample = df[col].dropna().head(3).tolist()
                col_info.append({
                    'Coluna': col,
                    'Tipo': dtype,
                    'Nulos': nulls,
                    'Exemplos': str(sample)[:100]
                })
            
            df_info = pd.DataFrame(col_info)
            st.dataframe(df_info, use_container_width=True, hide_index=True)
            
            # Mostrar primeiras linhas
            st.markdown("#### 📄 Primeiras 10 Linhas:")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Identificar problemas
            st.markdown("#### ⚠️ Possíveis Problemas:")
            
            for col in df.columns:
                # Verificar NaN em colunas numéricas
                if df[col].dtype in ['float64', 'int64']:
                    nan_count = df[col].isna().sum()
                    if nan_count > 0:
                        st.warning(f"⚠️ Coluna `{col}`: {nan_count} valores NaN/vazios")
                
                # Verificar strings 'nan'
                if df[col].dtype == 'object':
                    nan_strings = df[col].astype(str).str.lower().isin(['nan', 'none', '']).sum()
                    if nan_strings > 0:
                        st.warning(f"⚠️ Coluna `{col}`: {nan_strings} strings vazias ou 'nan'")
            
            # Teste de conversão
            st.divider()
            st.markdown("#### 🧪 Teste de Conversão para Inteiro:")
            
            colunas_numericas = st.multiselect(
                "Selecione colunas para testar conversão:",
                df.columns.tolist()
            )
            
            if colunas_numericas:
                for col in colunas_numericas:
                    st.markdown(f"**Testando coluna: {col}**")
                    
                    problemas = []
                    for idx, valor in df[col].items():
                        try:
                            # Tenta converter
                            if pd.isna(valor):
                                problemas.append(f"Linha {idx}: NaN")
                            elif isinstance(valor, str) and not valor.strip():
                                problemas.append(f"Linha {idx}: String vazia")
                            else:
                                int(float(valor))  # Testa conversão
                        except Exception as e:
                            problemas.append(f"Linha {idx}: {valor} → {str(e)}")
                    
                    if problemas:
                        st.error(f"❌ {len(problemas)} problemas encontrados:")
                        for p in problemas[:10]:  # Mostra só os 10 primeiros
                            st.text(f"  • {p}")
                        if len(problemas) > 10:
                            st.text(f"  ... e mais {len(problemas) - 10} problemas")
                    else:
                        st.success(f"✅ Nenhum problema de conversão")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        import traceback
        st.code(traceback.format_exc())