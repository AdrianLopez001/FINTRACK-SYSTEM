import streamlit as st
import streamlit_authenticator as stauth
import sys
import os
from datetime import datetime

# =========================================================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA DO SCRIPT)
# =========================================================================
st.set_page_config(
    page_title="FINTRACK - Gestão Financeira Inteligente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Garante que a VPS localiza a pasta principal e a pasta 'config'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from config.database import inicializar_conexao, executar_query

# =========================================================================
# 2. CONFIGURAÇÃO DO GERENCIAMENTO DE USUÁRIOS
# =========================================================================
# Senhas geradas com bcrypt. Para gerar um novo hash:
#   import streamlit_authenticator as stauth
#   print(stauth.Hasher(['sua_senha']).generate())
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "$2b$12$SUBSTITUA_PELO_HASH_DA_SENHA_ADMIN"
        },
        "gestor": {
            "name": "Gestor AutoTech",
            "password": "$2b$12$SUBSTITUA_PELO_HASH_DA_SENHA_GESTOR"
        }
    }
}

# Inicialização do autenticador
# Inicialização do autenticador com os argumentos nomeados e versão v2
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="fintrack_cookie_v2",
    key="fintrack_key_v2",
    cookie_expiry_days=30
)
# =========================================================================
# 3. RENDERIZAÇÃO DO FORMULÁRIO DE LOGIN
# =========================================================================
authenticator.login()

authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")


# =========================================================================
# FUNÇÃO DO PAINEL: SÓ RODA SE O USUÁRIO ESTIVER AUTENTICADO
# =========================================================================
def executar_painel():
    # Tenta conectar ao banco de dados usando o arquivo .env
    conexao = inicializar_conexao()
    
    # Força a criação das tabelas caso o banco esteja limpo
    if conexao:
        from config.database import criar_tabelas_padrao
        criar_tabelas_padrao(conexao)
    
    # Barra Lateral de Navegação
    st.sidebar.title("📊 FINTRACK")
    st.sidebar.write(f"Olá, **{name}**")
    
    # Adiciona botão de logout na barra lateral
    authenticator.logout("Sair do Sistema", "sidebar")
    st.sidebar.markdown("---")

# =========================================================================
    # MENU DE NAVEGAÇÃO: FILTRADO POR PERFIL DE USUÁRIO (Linha 74)
    # =========================================================================
    usuario_atual = st.session_state.get("username")

    if usuario_atual == "admin":
        menu = [
            "Dashboard",
            "Importar Relatórios (PDF)",
            "Configurar Metas",
            "Cadastrar Padrão de PDF",
            "Painel Geral SaaS (Admin)",
            "CRM WhatsApp",
            "Kit Revisão Básica",
            "Sair"
        ]
    else:
        menu = [
            "Dashboard",
            "Kit Revisão Básica",
            "Sair"
        ]
        
    # ESTA DEVE SER A ÚNICA ATRIBUIÇÃO DO RADIO:
    escolha = st.sidebar.radio("Navegação", menu)
    st.sidebar.markdown("---")

    # 🛑 ATENÇÃO: Se as linhas abaixo ainda existirem no seu código, APAGUE-AS:
    # menu = [
    #     "Dashboard", 
    #     "Importar Relatórios (PDF)", 
    #     ...
    # ]

    
    # Exibe o status real da conexão no rodapé da barra lateral
    if conexao:
        st.sidebar.success("⚡ Conectado ao PostgreSQL")
    else:
        st.sidebar.error("🔴 Modo Offline - Verifique o .env")

    # ==================== TELA: DASHBOARD ====================
   # ==================== TELA: DASHBOARD ====================
    if escolha == "Dashboard":
        st.title("📈 Painel de Controle Financeiro de Alta Performance")
        st.subheader("Indicadores de Faturamento e Metas Semanais")
        
        # Inicialização das variáveis padrões
        faturamento_mes = 0.0
        faturamento_dia = 0.0
        os_fechadas = 0
        ticket_medio = 0.0
        
        # Valores por semana
        faturamento_sem1 = 0.0
        faturamento_sem2 = 0.0
        faturamento_sem3 = 0.0
        faturamento_sem4 = 0.0
        
        # Metas
        meta_do_mes = 0.0
        meta_diaria_alvo = 0.0
        
        mes_atual = datetime.today().strftime('%Y-%m')
        
        if conexao:
            try:
                cursor = conexao.cursor()
                
                # 1. Total do Mês, Hoje e Número de OS Fechadas
                cursor.execute("""
                    SELECT SUM(valor), COUNT(id) FROM faturamento 
                    WHERE tipo = 'Receita' 
                    AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s;
                """, (mes_atual,))
                res_mes = cursor.fetchone()
                if res_mes and res_mes[0] is not None:
                    faturamento_mes = float(res_mes[0])
                    os_fechadas = int(res_mes[1])
                
                # Ticket Médio por Serviço (Faturamento do Mês / Qtd de OS)
                if os_fechadas > 0:
                    ticket_medio = faturamento_mes / os_fechadas
                
                # Faturamento do dia atual (Hoje)
                cursor.execute("""
                    SELECT SUM(valor) FROM faturamento 
                    WHERE tipo = 'Receita' AND data_movimentacao = CURRENT_DATE;
                """)
                res_dia = cursor.fetchone()
                if res_dia and res_dia[0] is not None:
                    faturamento_dia = float(res_dia[0])
                
                # 2. SEPARAÇÃO DAS 4 SEMANAS (Baseado nas semanas do mês corrente no Postgres)
                # Semana 1 (Dias 1 a 7)
                cursor.execute("""
                    SELECT SUM(valor) FROM faturamento WHERE tipo = 'Receita' 
                    AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s AND EXTRACT(DAY FROM data_movimentacao) BETWEEN 1 AND 7;
                """, (mes_atual,))
                faturamento_sem1 = float(cursor.fetchone()[0] or 0.0)

                # Semana 2 (Dias 8 a 14)
                cursor.execute("""
                    SELECT SUM(valor) FROM faturamento WHERE tipo = 'Receita' 
                    AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s AND EXTRACT(DAY FROM data_movimentacao) BETWEEN 8 AND 14;
                """, (mes_atual,))
                faturamento_sem2 = float(cursor.fetchone()[0] or 0.0)

                # Semana 3 (Dias 15 a 21)
                cursor.execute("""
                    SELECT SUM(valor) FROM faturamento WHERE tipo = 'Receita' 
                    AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s AND EXTRACT(DAY FROM data_movimentacao) BETWEEN 15 AND 21;
                """, (mes_atual,))
                faturamento_sem3 = float(cursor.fetchone()[0] or 0.0)

                # Semana 4 (Dias 22 até o fim do mês)
                cursor.execute("""
                    SELECT SUM(valor) FROM faturamento WHERE tipo = 'Receita' 
                    AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s AND EXTRACT(DAY FROM data_movimentacao) >= 22;
                """, (mes_atual,))
                faturamento_sem4 = float(cursor.fetchone()[0] or 0.0)

                # 3. Busca de Metas (Meta Mensal e calcula a Meta Diária estimada para os gráficos)
                cursor.execute("SELECT valor_meta FROM metas WHERE mes_ano = %s;", (mes_atual,))
                res_meta = cursor.fetchone()
                if res_meta and res_meta[0] is not None:
                    meta_do_mes = float(res_meta[0])
                    # Meta diária dividida por 22 dias úteis padrão de operação
                    meta_diaria_alvo = meta_do_mes / 22.0
                    
                # 4. Dados para o gráfico de faturamento diário do mês corrente
                cursor.execute("""
                    SELECT EXTRACT(DAY FROM data_movimentacao) as dia, SUM(valor) as total
                    FROM faturamento 
                    WHERE tipo = 'Receita' AND TO_CHAR(data_movimentacao, 'YYYY-MM') = %s
                    GROUP BY dia ORDER BY dia;
                """, (mes_atual,))
                dados_grafico = cursor.fetchall()
                
                cursor.close()
            except Exception as e:
                st.error(f"Erro no banco de dados: {e}")
        
        # Função para formatação de moeda
        def formatar_reais(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

      # --- SEÇÃO SUPERIOR: TICKET MÉDIO E MÉTRICAS ---
        st.markdown("### 📊 Indicadores Gerais e Semanais")
        
        col_topo1, col_topo2, col_topo3, col_topo4 = st.columns(4)
        col_topo1.metric("Valor Total Finalizado", formatar_reais(faturamento_mes))
        col_topo2.metric("Ticket Médio / Serviço", formatar_reais(ticket_medio))
        col_topo3.metric("OS Fechadas (Mês)", f"{os_fechadas} Finalizadas", "Performance")
        col_topo4.metric("Meta Diária Alvo", formatar_reais(meta_diaria_alvo), "Base: 22 dias úteis")
        
        st.markdown("---")

        # --- SEÇÃO INTERMEDIÁRIA: VALORES DAS 4 SEMANAS ---
        st.markdown("#### 📅 Acompanhamento por Semana")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Semana 1 (Dias 01-07)", formatar_reais(faturamento_sem1))
        col_s2.metric("Semana 2 (Dias 08-14)", formatar_reais(faturamento_sem2))
        col_s3.metric("Semana 3 (Dias 15-21)", formatar_reais(faturamento_sem3))
        col_s4.metric("Semana 4 (Dias 22+)", formatar_reais(faturamento_sem4))

        st.markdown("---")

       # --- SEÇÃO INFERIOR: GRÁFICO DE COLUNAS COM LINHA DE META HORIZONTAL ---
        st.markdown("### 📉 Desempenho Diário vs Meta")
        
        import pandas as pd
        import plotly.graph_objects as go
        
        # 1. Criamos um DataFrame base com todos os dias possíveis do mês (1 a 31)
        # Isso garante que a linha da meta cruze o gráfico inteiro mesmo que o mês esteja no começo
        df_base = pd.DataFrame({'Dia': list(range(1, 32))})
        
        # 2. Se houver dados vindos do banco, jogamos no DataFrame
        if dados_grafico:
            df_banco = pd.DataFrame(dados_grafico, columns=['Dia', 'Faturamento'])
            df_banco['Dia'] = df_banco['Dia'].astype(int)
            # Une os dados reais com a base de dias vazios
            df_final = pd.merge(df_base, df_banco, on='Dia', how='left').fillna(0)
        else:
            df_final = df_base.copy()
            df_final['Faturamento'] = 0.0

        # 3. Montagem visual do gráfico misto
        fig = go.Figure()
        
        # Adiciona as Colunas de Faturamento Real
        fig.add_trace(go.Bar(
            x=df_final['Dia'],
            y=df_final['Faturamento'],
            name='Faturamento do Dia',
            marker_color='#1f77b4'
        ))
        
        # Adiciona a Linha Pontilhada de Meta de ponta a ponta (Dias 1 ao 31)
        fig.add_trace(go.Scatter(
            x=df_final['Dia'],
            y=[meta_diaria_alvo] * len(df_final),
            mode='lines',
            name='Meta Diária Alvo',
            line=dict(color='red', width=2, dash='dot')
        ))
        
        # Configurações de escala e eixos
        fig.update_layout(
            xaxis_title="Dias do Mês",
            yaxis_title="Valor em R$",
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                range=[0.5, 31.5]
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=420
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.info("Nenhuma movimentação registrada para gerar o gráfico de colunas neste mês ainda.")

   
    # ==================== TELA: IMPORTAR RELATÓRIOS ====================
    elif escolha == "Importar Relatórios (PDF)":
        st.title("📁 Upload de Movimentações Diárias")
        st.write("Arraste os relatórios diários para atualizar o banco de dados.")
        
        from modules.leitor_pdf import extrair_texto_pdf
        
        with st.form("formulario_pdf", clear_on_submit=True):
            arquivos_enviados = st.file_uploader(
                "Selecione os arquivos PDF", 
                type=["pdf"], 
                accept_multiple_files=True
            )
            botao_enviar = st.form_submit_button("Processar e Salvar no Banco")
        
        if botao_enviar and arquivos_enviados:
            sucesso_total = True
            total_movimentacoes = 0
            
            for arquivo in arquivos_enviados:
                st.write(f"📄 Processando: **{arquivo.name}**")
                dados = extrair_texto_pdf(arquivo)
                
                if dados and isinstance(dados, list):
                    total_movimentacoes += len(dados)
                    st.dataframe(dados)
                    
                    if conexao:
                        try:
                            cursor = conexao.cursor()
                            for item in dados:
                                # Ajusta o formato da data DD/MM/YY para YYYY-MM-DD aceito pelo Postgres
                                part = item["data"].split("/")
                                if len(part[2]) == 2:
                                    part[2] = "20" + part[2]
                                data_formatada = f"{part[2]}-{part[1]}-{part[0]}"
                                
                                cursor.execute(
                                    """
                                    INSERT INTO faturamento (data_movimentacao, descricao, valor, tipo)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (descricao) DO UPDATE
                                        SET data_movimentacao = EXCLUDED.data_movimentacao,
                                            valor = EXCLUDED.valor,
                                            tipo = EXCLUDED.tipo
                                    """,
                                    (data_formatada, item["descricao"], item["valor"], item["tipo"])
                                )
                            conexao.commit()
                            cursor.close()
                        except Exception as e:
                            st.error(f"Erro ao salvar o arquivo {arquivo.name}: {e}")
                            sucesso_total = False
                else:
                    st.warning(f"⚠️ Nenhum padrão financeiro identificado em: {arquivo.name}")
    # ==================== TELA: CONFIGURAR METAS ====================
    elif escolha == "Configurar Metas":
        st.title("🎯 Definição de Metas da Empresa")
        st.write("Insira a meta de faturamento para o mês vigente.")
        
        mes_atual = datetime.today().strftime('%Y-%m')
        
        nova_meta = st.number_input(
            f"Defina a meta de faturamento para o mês ({mes_atual}):", 
            min_value=0.0, 
            value=60000.0, 
            step=1000.0
        )
        
        if st.button("Gravar Meta no Banco"):
            if conexao:
                try:
                    cursor = conexao.cursor()
                    cursor.execute(
                        """
                        INSERT INTO metas (mes_ano, valor_meta) 
                        VALUES (%s, %s)
                        ON CONFLICT (mes_ano) 
                        DO UPDATE SET valor_meta = EXCLUDED.valor_meta;
                        """,
                        (mes_atual, nova_meta)
                    )
                    conexao.commit()
                    cursor.close()
                    st.success(f"🎯 Meta de R$ {nova_meta:,.2f} gravada com sucesso para o período {mes_atual}!")
                except Exception as e:
                    st.error(f"Erro ao salvar a meta no banco de dados: {e}")

    # ==================== TELA: CADASTRAR PADRÃO PDF ====================
    elif escolha == "Cadastrar Padrão de PDF":
        st.title("🧠 Mapeamento de Padrões de Texto (PDF)")
        st.write("Cadastre palavras-chave contidas nos arquivos para categorização automática entre Receitas e Despesas.")
        
        novo_termo = st.text_input("Palavra-chave identificadora (Ex: Nome de Fornecedor ou Cliente):")
        tipo_associado = st.selectbox("Classificação Padrão:", ["Receita", "Despesa"])
        
        if st.button("Salvar Regra de Processamento"):
            if novo_termo.strip() == "":
                st.warning("Insira um termo válido para salvar a regra.")
            elif conexao:
                try:
                    cursor = conexao.cursor()
                    cursor.execute(
                        """
                        INSERT INTO padroes_pdf (termo_chave, tipo_movimentacao) 
                        VALUES (%s, %s)
                        ON CONFLICT (termo_chave) 
                        DO UPDATE SET tipo_movimentacao = EXCLUDED.tipo_movimentacao;
                        """,
                        (novo_termo.upper().strip(), tipo_associado)
                    )
                    conexao.commit()
                    cursor.close()
                    st.success(f"✔️ Regra para '{novo_termo.upper()}' salva como '{tipo_associado}'!")
                except Exception as e:
                    st.error(f"Erro ao registrar padrão no banco: {e}")
        
    # ==================== TELA: CRM WHATSAPP ====================
    elif escolha == "CRM WhatsApp":
        st.title("📱 CRM — Disparo de WhatsApp")
        st.markdown("""
O módulo CRM roda como um serviço separado (Java/Spring Boot) na porta **8080**.

Clique no botão abaixo para abrir o painel de envio de WhatsApp em uma nova aba.
""")
        VPS_IP = "2.24.87.18"
        st.link_button("🚀 Abrir CRM WhatsApp", f"http://{VPS_IP}:8080/crm", use_container_width=True)

        st.markdown("---")
        st.subheader("Status do serviço CRM")
        import subprocess, shutil
        col_a, col_b = st.columns(2)
        col_a.info("🔗 Endereço: `http://2.24.87.18:8080/crm`")
        col_b.info("🖥️ Tecnologia: Java 17 + Spring Boot")

        st.markdown("""
**Para subir o serviço na VPS (primeira vez):**
```bash
# 1. Instalar Java 17
sudo apt update && sudo apt install -y openjdk-17-jdk maven

# 2. Compilar o projeto
cd /var/www/fintrack/Fintrack2/crm-java
mvn package -DskipTests

# 3. Rodar como serviço permanente
sudo systemctl start fintrack-crm
sudo systemctl enable fintrack-crm
```
""")

    # ==================== TELA: PAINEL SAAS ADMIN ====================
    elif escolha == "Painel Geral SaaS (Admin)":
        st.title("👑 Gestão Geral de Clientes (SaaS)")
        st.success("Você está no modo Administrador Geral. Aqui você gerencia seus clientes.")

        st.markdown("---")
        st.subheader("🗑️ Gerenciamento de Dados")

        col_info, col_btn = st.columns([2, 1])

        if conexao:
            try:
                cur = conexao.cursor()
                cur.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM faturamento WHERE tipo = 'Receita';")
                qtd, total = cur.fetchone()
                cur.close()
                col_info.info(f"**{int(qtd)} registros** no banco totalizando **R$ {float(total):,.2f}**".replace(",","X").replace(".",",").replace("X","."))
            except Exception:
                col_info.warning("Não foi possível contar os registros.")

        confirmar = st.checkbox("⚠️ Confirmo que quero apagar TODOS os registros de faturamento")
        if st.button("🗑️ Limpar Todos os Dados de Faturamento", type="primary", disabled=not confirmar):
            if conexao:
                try:
                    cur = conexao.cursor()
                    cur.execute("DELETE FROM faturamento;")
                    conexao.commit()
                    cur.close()
                    st.success("✅ Todos os registros foram removidos. Importe um novo relatório PDF.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar dados: {e}")
        
    # ==================== TELA: KIT REVISÃO BÁSICA ====================
    elif escolha == "Kit Revisão Básica":
        from modules.revisao import (buscar_veiculo_por_placa, buscar_kit,
                                     cadastrar_veiculo, salvar_item_catalogo,
                                     listar_modelos_catalogo, buscar_modelos_catalogo, ICONES)

        st.title("🔧 Kit Revisão Básica")

        def _mostrar_kit(kit, marca, modelo, ano, motor):
            if not kit:
                st.warning(f"Nenhuma peça no catálogo para **{marca} {modelo} {ano} {motor}**. "
                           "Acesse **Gerenciar Catálogo** para adicionar.")
                return
            st.markdown(f"**Kit Revisão — {marca} {modelo} {ano} · {motor}**")
            import pandas as pd
            linhas = []
            for grupo in kit:
                icone = ICONES.get(grupo["tipo_item"], "🔧")
                for peca in grupo["pecas"]:
                    linhas.append({
                        "Item": f"{icone} {grupo['tipo_item']}",
                        "Fabricante": peca["fabricante"],
                        "Referência": peca["referencia"],
                        "Descrição": peca["descricao"],
                    })
            st.table(pd.DataFrame(linhas))

        aba_consulta, aba_catalogo = st.tabs(["🔍 Consultar", "📦 Gerenciar Catálogo"])

        # ══════════════════════════════════════════════
        # ABA 1 — CONSULTA
        # ══════════════════════════════════════════════
        with aba_consulta:
            # Carrega todos os veículos cadastrados
            todos_veiculos = []
            if conexao:
                try:
                    cur = conexao.cursor()
                    cur.execute("""
                        SELECT id, placa, cliente_nome, marca, modelo, ano, motor
                        FROM veiculos ORDER BY marca, modelo, placa;
                    """)
                    todos_veiculos = cur.fetchall()
                    cur.close()
                except Exception as e:
                    conexao.rollback()
                    st.error(f"Erro ao carregar veículos: {e}")

            busca_input = st.text_input("Buscar por modelo ou cliente",
                                        placeholder="Ex: HILUX  ou  PEUGEOT  ou  JOÃO",
                                        key="busca_revisao").strip().upper()

            # Filtra veículos cadastrados
            filtrados = []
            for row in todos_veiculos:
                vid, placa, cli_nome, marca, modelo, ano, motor = row
                if not busca_input or any(busca_input in str(v or "").upper()
                                          for v in [placa, cli_nome, marca, modelo, motor]):
                    filtrados.append(row)

            if filtrados:
                st.caption(f"{len(filtrados)} veículo(s) cadastrado(s).")
                for row in filtrados:
                    vid, placa, cli_nome, marca, modelo, ano, motor = row
                    label = f"🚗 {marca} {modelo} {ano} · {motor}"
                    if cli_nome:
                        label += f"  ·  {cli_nome}"
                    col_btn, col_del = st.columns([10, 1])
                    if col_btn.button(label, key=f"vsel_{vid}", use_container_width=True):
                        st.session_state["veiculo_id_sel"] = vid
                        st.rerun()
                    if usuario_atual == "admin" and col_del.button("🗑️", key=f"vdel_{vid}"):
                        try:
                            cur = conexao.cursor()
                            cur.execute("DELETE FROM veiculos WHERE id = %s;", (vid,))
                            conexao.commit()
                            cur.close()
                            if st.session_state.get("veiculo_id_sel") == vid:
                                del st.session_state["veiculo_id_sel"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

            elif busca_input:
                # Busca no catálogo por modelo (sem veículo cadastrado)
                modelos_cat = []
                try:
                    modelos_cat = buscar_modelos_catalogo(conexao, busca_input)
                except Exception as e:
                    conexao.rollback()

                if modelos_cat:
                    st.info("Veículo não cadastrado. Modelos encontrados no catálogo:")
                    for marca_c, modelo_c, motor_c, ano_ini, ano_fim in modelos_cat:
                        lb = f"📦 {marca_c} {modelo_c} · {motor_c} · {ano_ini}–{ano_fim}"
                        if st.button(lb, key=f"catsel_{marca_c}_{modelo_c}_{motor_c}_{ano_ini}"):
                            st.session_state["kit_cat"] = (marca_c, modelo_c, motor_c, ano_ini)
                            st.rerun()
                else:
                    if usuario_atual == "admin":
                        st.info(f"**{busca_input}** não cadastrado. Preencha para registrar:")
                        with st.form("form_cad_veiculo"):
                            c1, c2 = st.columns(2)
                            placa_f  = c1.text_input("Placa", value=busca_input if len(busca_input) <= 8 and " " not in busca_input else "")
                            cli      = c2.text_input("Nome do Cliente")
                            c3, c4 = st.columns(2)
                            marca_f  = c3.text_input("Marca")
                            modelo_f = c4.text_input("Modelo")
                            c5, c6 = st.columns(2)
                            ano_f    = c5.number_input("Ano", min_value=1990, max_value=2035, value=2022, step=1)
                            motor_f  = c6.text_input("Motor (ex: 2.8 DIESEL)")
                            if st.form_submit_button("💾 Cadastrar Veículo"):
                                if placa_f and marca_f and modelo_f and motor_f:
                                    try:
                                        cadastrar_veiculo(conexao, placa_f, cli, marca_f, modelo_f, int(ano_f), motor_f)
                                        st.success("Veículo cadastrado!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {e}")
                                else:
                                    st.warning("Preencha Placa, Marca, Modelo e Motor.")
                    else:
                        st.warning("Não encontrado. Solicite ao administrador o cadastro.")

            # Exibe kit do veículo selecionado (clicado na lista)
            if "veiculo_id_sel" in st.session_state:
                vid_sel = st.session_state["veiculo_id_sel"]
                row_sel = next((r for r in todos_veiculos if r[0] == vid_sel), None)
                if row_sel:
                    vid, placa, cli_nome, marca, modelo, ano, motor = row_sel
                    st.markdown("---")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Placa", placa)
                    c2.metric("Veículo", f"{marca} {modelo}")
                    c3.metric("Ano / Motor", f"{ano} · {motor}")
                    c4.metric("Cliente", cli_nome or "—")

                    kit = buscar_kit(conexao, marca, modelo, ano, motor) if conexao else []
                    _mostrar_kit(kit, marca, modelo, ano, motor)

                    if usuario_atual == "admin":
                        with st.expander("✏️ Editar dados do veículo"):
                            with st.form("form_edit_veiculo"):
                                ec1, ec2 = st.columns(2)
                                novo_cli   = ec1.text_input("Cliente", value=cli_nome or "")
                                novo_motor = ec2.text_input("Motor", value=motor or "")
                                ec3, ec4, ec5 = st.columns(3)
                                nova_marca  = ec3.text_input("Marca", value=marca or "")
                                novo_modelo = ec4.text_input("Modelo", value=modelo or "")
                                novo_ano    = ec5.number_input("Ano", min_value=1990, max_value=2035,
                                                               value=int(ano) if ano else 2022, step=1)
                                if st.form_submit_button("Salvar alterações"):
                                    try:
                                        cadastrar_veiculo(conexao, placa, novo_cli, nova_marca,
                                                          novo_modelo, int(novo_ano), novo_motor)
                                        st.success("Dados atualizados!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {e}")

            # Exibe kit de modelo do catálogo selecionado (sem veículo cadastrado)
            if "kit_cat" in st.session_state and "veiculo_id_sel" not in st.session_state:
                marca_c, modelo_c, motor_c, ano_c = st.session_state["kit_cat"]
                st.markdown("---")
                kit_c = buscar_kit(conexao, marca_c, modelo_c, ano_c, motor_c) if conexao else []
                _mostrar_kit(kit_c, marca_c, modelo_c, ano_c, motor_c)

        # ══════════════════════════════════════════════
        # ABA 2 — GERENCIAR CATÁLOGO (admin)
        # ══════════════════════════════════════════════
        with aba_catalogo:
            if usuario_atual != "admin":
                st.info("Apenas o administrador pode gerenciar o catálogo de peças.")
            else:
                st.subheader("Adicionar peça ao catálogo")

                TIPOS_ITEM = [
                    "Filtro de Óleo", "Filtro de Ar do Motor", "Filtro de Cabine",
                    "Filtro de Combustível", "Óleo do Motor", "Vela de Ignição",
                    "Correia Dentada", "Fluido de Freio", "Fluido de Arrefecimento",
                    "Pastilha de Freio",
                ]
                FABRICANTES = ["Wega", "Bosch", "Tecfil", "Mann", "Mahle", "NGK", "Denso", "Outro"]

                with st.form("form_catalogo"):
                    cc1, cc2, cc3 = st.columns(3)
                    cat_marca  = cc1.text_input("Marca (ex: TOYOTA)")
                    cat_modelo = cc2.text_input("Modelo (ex: RAV4)")
                    cat_motor  = cc3.text_input("Motor (ex: 2.0 FLEX)")

                    cd1, cd2 = st.columns(2)
                    cat_ano_ini = cd1.number_input("Ano início", min_value=1990, max_value=2035, value=2019, step=1)
                    cat_ano_fim = cd2.number_input("Ano fim",   min_value=1990, max_value=2035, value=2024, step=1)

                    ce1, ce2 = st.columns(2)
                    cat_tipo       = ce1.selectbox("Tipo de Item", TIPOS_ITEM)
                    cat_fabricante = ce2.selectbox("Fabricante", FABRICANTES)

                    cf1, cf2 = st.columns(2)
                    cat_referencia = cf1.text_input("Referência (ex: ML-100)")
                    cat_descricao  = cf2.text_input("Descrição (ex: Para 4 litros de óleo)")

                    if st.form_submit_button("➕ Adicionar ao catálogo"):
                        if cat_marca and cat_modelo and cat_motor and cat_referencia:
                            try:
                                salvar_item_catalogo(
                                    conexao, cat_marca, cat_modelo,
                                    int(cat_ano_ini), int(cat_ano_fim), cat_motor,
                                    cat_tipo, cat_fabricante, cat_referencia, cat_descricao
                                )
                                st.success(f"✅ {cat_tipo} — {cat_fabricante} {cat_referencia} adicionado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                        else:
                            st.warning("Preencha Marca, Modelo, Motor e Referência.")

                # Lista do catálogo com editar / excluir
                st.markdown("---")
                st.subheader("Catálogo atual")
                if conexao:
                    try:
                        cur = conexao.cursor()
                        cur.execute("""
                            SELECT id, marca, modelo, ano_inicio, ano_fim, motor,
                                   tipo_item, fabricante, referencia, descricao
                            FROM kit_revisao_catalogo
                            ORDER BY marca, modelo, ano_inicio, tipo_item, fabricante;
                        """)
                        rows = cur.fetchall()
                        cur.close()

                        if not rows:
                            st.info("Catálogo vazio. Adicione as primeiras peças acima.")
                        else:
                            # Cabeçalho
                            h = st.columns([2,2,1,1,2,2,2,1,1])
                            for col, label in zip(h, ["Marca","Modelo","Ini","Fim","Motor","Tipo","Fabricante","Ref.",""]):
                                col.markdown(f"**{label}**")
                            st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

                            for row in rows:
                                rid, rmarca, rmodelo, rani, ranf, rmotor, rtipo, rfab, rref, rdesc = row
                                c = st.columns([2,2,1,1,2,2,2,1,1])
                                c[0].write(rmarca)
                                c[1].write(rmodelo)
                                c[2].write(str(rani))
                                c[3].write(str(ranf))
                                c[4].write(rmotor)
                                c[5].write(rtipo)
                                c[6].write(rfab)
                                c[7].write(rref)
                                if c[8].button("✏️", key=f"edit_{rid}"):
                                    st.session_state[f"editando_{rid}"] = True
                                    st.rerun()

                                # Formulário de edição inline
                                if st.session_state.get(f"editando_{rid}"):
                                    with st.form(f"form_edit_{rid}"):
                                        st.markdown(f"**Editando:** {rmarca} {rmodelo} — {rfab} {rref}")
                                        ec1, ec2, ec3 = st.columns(3)
                                        n_marca  = ec1.text_input("Marca", value=rmarca, key=f"nm_{rid}")
                                        n_modelo = ec2.text_input("Modelo", value=rmodelo, key=f"nmo_{rid}")
                                        n_motor  = ec3.text_input("Motor", value=rmotor, key=f"nmt_{rid}")
                                        ed1, ed2 = st.columns(2)
                                        n_ani = ed1.number_input("Ano início", value=int(rani), min_value=1990, max_value=2035, step=1, key=f"nai_{rid}")
                                        n_anf = ed2.number_input("Ano fim",    value=int(ranf), min_value=1990, max_value=2035, step=1, key=f"naf_{rid}")
                                        ee1, ee2 = st.columns(2)
                                        n_tipo = ee1.selectbox("Tipo", TIPOS_ITEM, index=TIPOS_ITEM.index(rtipo) if rtipo in TIPOS_ITEM else 0, key=f"nti_{rid}")
                                        n_fab  = ee2.selectbox("Fabricante", FABRICANTES, index=FABRICANTES.index(rfab) if rfab in FABRICANTES else 0, key=f"nfa_{rid}")
                                        ef1, ef2 = st.columns(2)
                                        n_ref  = ef1.text_input("Referência", value=rref, key=f"nre_{rid}")
                                        n_desc = ef2.text_input("Descrição",  value=rdesc or "", key=f"nde_{rid}")
                                        col_salvar, col_excluir, col_cancelar = st.columns(3)
                                        salvar_edit   = col_salvar.form_submit_button("💾 Salvar")
                                        excluir_item  = col_excluir.form_submit_button("🗑️ Excluir")
                                        cancelar_edit = col_cancelar.form_submit_button("Cancelar")

                                    if salvar_edit:
                                        try:
                                            cur2 = conexao.cursor()
                                            cur2.execute("""
                                                UPDATE kit_revisao_catalogo SET
                                                    marca=%s, modelo=%s, ano_inicio=%s, ano_fim=%s, motor=%s,
                                                    tipo_item=%s, fabricante=%s, referencia=%s, descricao=%s
                                                WHERE id=%s;
                                            """, (n_marca.upper(), n_modelo.upper(), n_ani, n_anf, n_motor.upper(),
                                                  n_tipo, n_fab, n_ref.upper(), n_desc, rid))
                                            conexao.commit()
                                            cur2.close()
                                            del st.session_state[f"editando_{rid}"]
                                            st.success("Atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {e}")
                                    elif excluir_item:
                                        try:
                                            cur2 = conexao.cursor()
                                            cur2.execute("DELETE FROM kit_revisao_catalogo WHERE id=%s;", (rid,))
                                            conexao.commit()
                                            cur2.close()
                                            del st.session_state[f"editando_{rid}"]
                                            st.success("Item excluído.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {e}")
                                    elif cancelar_edit:
                                        del st.session_state[f"editando_{rid}"]
                                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    # ==================== TELA: SAIR ====================
    elif escolha == "Sair":
        st.title("👋 Até logo!")
        st.write("Você saiu do sistema com segurança.")


# =========================================================================
# 4. CONTROLE DE ACESSO DEFINITIVO (TOTALMENTE ALINHADO)
# =========================================================================
if authentication_status:
    executar_painel()

elif authentication_status is False:
    st.error("Usuário ou senha inválidos. Tente novamente.")

elif authentication_status is None:
    st.info("Por favor, informe suas credenciais para acessar o painel financeiro.")