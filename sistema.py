import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO (MENU LATERAL PREMIUM ADAPTADO PARA CELULARES)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Terminal Financeiro Pro", layout="wide")

# Bloqueia a tradução automática para evitar travamentos no Safari do iPhone
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

st.title("Terminal de Patrimônio")
st.caption("Acompanhamento de ativos de mercado e controle orçamentário individual")
st.write("---")

# Menu de navegação adaptado para telas de celulares
menu_navegacao = st.sidebar.radio(
    "Navegação do Painel:",
    ["Painel Geral", "Analisador de Ativos", "Controle de Gastos"]
)

# -----------------------------------------------------------------------------
# MOTORES DE BANCO DE DADOS INDIVIDUAIS (SALVA NA MEMÓRIA DE CADA APARELHO)
# -----------------------------------------------------------------------------
if "carteira_celular" not in st.session_state:
    st.session_state["carteira_celular"] = pd.DataFrame(columns=["Ticker", "Quantidade", "Preço Médio (R$)"])

if "gastos_celular" not in st.session_state:
    st.session_state["gastos_celular"] = pd.DataFrame(columns=["Descrição", "Tipo", "Valor (R$)"])

if "historico_celular" not in st.session_state:
    st.session_state["historico_celular"] = pd.DataFrame(columns=["Data", "Patrimônio (R$)"])

# =============================================================================
# SEÇÃO 1: PAINEL GERAL
# =============================================================================
if menu_navegacao == "Painel Geral":
    st.markdown("### Termômetro do Mercado")
    col_ibov, col_dolar = st.columns(2)
    try:
        ibov_pontos = yf.Ticker("^BVSP").history(period="1d")['Close'].iloc[-1]
        col_ibov.metric("Índice Ibovespa", f"{int(ibov_pontos):,} pts".replace(",", "."))
    except:
        col_ibov.metric("Índice Ibovespa", "Mercado Indisponível")
        
    try:
        dolar_reais = yf.Ticker("USDBRL=X").history(period="1d")['Close'].iloc[-1]
        col_dolar.metric("Câmbio USD / BRL", f"R$ {dolar_reais:.2f}")
    except:
        col_dolar.metric("Câmbio USD / BRL", "Indisponível")
        
    st.write("---")
    meta_salva = float(st.number_input("Meta de Patrimônio Alvo (R$):", min_value=0.0, value=5000.0, step=500.0, key="meta_geral"))
    
    with st.expander("Gerenciamento de Ativos (Adicionar / Atualizar)"):
        col_t, col_q, col_p = st.columns(3)
        novo_ticker = col_t.text_input("Código do Ativo (ex: PETR4.SA):", key="tk_painel").upper().strip()
        nova_qtd = col_q.number_input("Quantidade:", min_value=0.0, step=1.0, key="qtd_painel")
        novo_preco = col_p.number_input("Preço Médio Pago (R$):", min_value=0.0, step=0.01, key="prc_painel")
        if st.button("Salvar na Carteira", key="btn_painel") and novo_ticker:
            df_inv = st.session_state["carteira_celular"]
            df_inv = df_inv[df_inv["Ticker"] != novo_ticker]
            nova_linha = pd.DataFrame([{"Ticker": novo_ticker, "Quantidade": nova_qtd, "Preço Médio (R$)": novo_preco}])
            st.session_state["carteira_celular"] = pd.concat([df_inv, nova_linha], ignore_index=True)
            st.success(f"{novo_ticker} atualizado na sua memória local.")
            st.rerun()

    if st.session_state["carteira_celular"].empty:
        st.caption("Sua custódia está vazia neste aparelho. Use o painel acima para incluir ativos.")
    else:
        st.markdown("### Posição de Custódia")
        df_investimentos = st.session_state["carteira_celular"]
        precos_atuais, valores_totais = [], []
        for idx, row in df_investimentos.iterrows():
            p_atual = float(row["Preço Médio (R$)"])
            try:
                hist_ativo = yf.Ticker(row["Ticker"]).history(period="1d")
                if not hist_ativo.empty: p_atual = float(hist_ativo['Close'].iloc[-1])
            except: pass
            precos_atuais.append(p_atual)
            valores_totais.append(p_atual * row["Quantidade"])
            
        df_exibicao = df_investimentos.copy()
        df_exibicao["Preço Atual"] = precos_atuais
        df_exibicao["Total Atual"] = valores_totais
        st.dataframe(df_exibicao.style.format({"Preço Médio (R$)": "R$ {:.2f}", "Preço Atual": "R$ {:.2f}", "Total Atual": "R$ {:.2f}"}), use_container_width=True)
        
        patrimonio_total = df_exibicao["Total Atual"].sum()
        st.write("---")
        st.markdown("### Indicadores de Progresso")
        porcentagem_meta = min(float(patrimonio_total / meta_salva), 1.0) if meta_salva > 0 else 0.0
        st.progress(porcentagem_meta)
        st.metric("Patrimônio Atualizado", f"R$ {patrimonio_total:.2f}", f"{porcentagem_meta*100:.1f}% da meta estabelecida")

    st.write("---")
    st.markdown("### Evolução Patrimonial Histórica")
    col_ev1, col_ev2 = st.columns(2)
    with col_ev1:
        valor_historico = st.number_input("Valor total para registrar no histórico (R$):", min_value=0.0, step=1000.0, key="val_hist")
        data_registro = st.date_input("Data do registro:", datetime.now(), key="data_hist")
        if st.button("Gravar Posição no Histórico", key="btn_hist"):
            data_formatada = data_registro.strftime("%Y-%m-%d")
            df_h = st.session_state["historico_celular"]
            df_h = df_h[df_h["Data"] != data_formatada]
            nova_linha = pd.DataFrame([{"Data": data_formatada, "Patrimônio (R$)": valor_historico}])
            st.session_state["historico_celular"] = pd.concat([df_h, nova_linha], ignore_index=True).sort_values("Data")
            st.success("Histórico local gravado.")
            st.rerun()
    with col_ev2:
        if st.session_state["historico_celular"].empty:
            st.caption("Nenhum dado histórico registrado neste aparelho.")
        else:
            st.metric("Último Registro Salvo", f"R$ {st.session_state['historico_celular']['Patrimônio (R$)'].iloc[-1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.line_chart(st.session_state["historico_celular"].set_index("Data"))

# =============================================================================
# SEÇÃO 2: ANALISADOR DE ATIVOS
# =============================================================================
elif menu_navegacao == "Analisador de Ativos":
    st.markdown("### Análise Avançada de Ativos")
    ticker = st.text_input("Código do Ativo (ex: GARE11.SA):", value="GARE11.SA", key="tk_analisador").upper().strip()
    opcao_selecionada = st.selectbox("Intervalo histórico:", ["1 Mês", "3 Meses", "6 Meses", "1 Ano", "5 Anos"], index=3)
    tradutor_periodo = {"1 Mês": "1mo", "3 Meses": "3mo", "6 Meses": "6mo", "1 Ano": "1y", "5 Anos": "5y"}
    periodo = tradutor_periodo[opcao_selecionada]
    
    if st.button("Executar Análise", key="btn_analisador"):
        ativo = yf.Ticker(ticker)
        historico = ativo.history(period=periodo)
        
        if historico.empty: 
            st.warning("Ativo sem dados para o período selecionado.")
        else:
            info = ativo.info
            nome_empresa = info.get('longName', ticker)
            preco_atual = float(historico['Close'].iloc[-1])
            moeda = info.get('currency', 'BRL')
            st.markdown(f"#### {nome_empresa} ({ticker})")
            st.metric("Preço de Mercado", f"{moeda} {preco_atual:.2f}")
            st.line_chart(historico['Close'])
            
            st.write("---")
            st.markdown("#### Avaliação Estrutural (IA Algorítmica)")
            try:
                p_l = info.get('trailingPE', 0.0)
                p_vp = info.get('priceToBook', 0.0)
                dy = info.get('dividendYield', 0.0) * 100 if info.get('dividendYield') else 0.0
                
                relatorio = f"""
                ### 📋 Análise Fundamentalista Automatizada
                O ativo **{nome_empresa}** está cotado a **{moeda} {preco_atual:.2f}**.
                * **Múltiplo P/L:** {f"{p_l:.2f}" if p_l else "N/A"}
                * **Múltiplo P/VP:** {f"{p_vp:.2f}" if p_vp else "N/A"}
                * **Dividend Yield:** {f"{dy:.2f}%" if dy else "N/A"}
                
                *Mecanismo ativo. Dados atualizados de mercado.*
                """
                st.markdown(relatorio)
            except:
                st.info("Carregando balanço estrutural...")

# =============================================================================
# SEÇÃO 3: CONTROLE DE GASTOS
# =============================================================================
elif menu_navegacao == "Controle de Gastos":
    st.markdown("### Gestão de Fluxo de Caixa")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("#### Registro de Lançamento")
        desc = st.text_input("Descrição:", key="desc_gastos_aba")
        tipo = st.selectbox("Classificação:", ["Receita (Ganho)", "Despesa (Gasto)"], key="tipo_gastos_aba")
        valor = st.number_input("Valor nominal (R$):", min_value=0.0, step=10.0, key="val_gastos_aba")
        
        if st.button("Confirmar Lançamento", key="btn_gastos_aba") and desc and valor > 0:
            df_orc = st.session_state["gastos_celular"]
            nova_linha = pd.DataFrame([{"Descrição": desc, "Tipo": tipo, "Valor (R$)": valor}])
            st.session_state["gastos_celular"] = pd.concat([df_orc, nova_linha], ignore_index=True)
            st.success("Lançamento guardado na sua carteira individual.")
            st.rerun()

    with col_f2:
        st.markdown("#### Demonstrativo Mensal")
        df_orcamento = st.session_state["gastos_celular"]
        if df_orcamento.empty:
            st.caption("Nenhum lançamento registrado neste aparelho.")
        else:
        pass

