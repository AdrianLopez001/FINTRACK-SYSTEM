import os
import sys
import re
import pdfplumber

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config')))

def extrair_texto_pdf(arquivo_pdf):
    """
    Extrai OS do relatório "Listagem de Ordens de Serviço".
    - Usa o número da OS como chave única para evitar duplicatas
    - Usa a "Data do Faturamento" (última data da linha) como data_movimentacao
    - Captura o R$ Total da OS (último valor monetário da linha)
    """
    movimentacoes = []

    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_da_pagina = pagina.extract_text()
                if not texto_da_pagina:
                    continue

                linhas = texto_da_pagina.split("\n")

                for linha in linhas:
                    linha_limpa = linha.strip()

                    # Detecta início de linha OS: Contador + Número OS + Data OS
                    match_estrutura = re.search(r'^(\d+)\s+(\d+)\s+(\d{2}/\d{2}/\d{2,4})', linha_limpa)

                    if not match_estrutura:
                        continue

                    num_os = match_estrutura.group(2)

                    # Captura TODAS as datas da linha (DD/MM/AA ou DD/MM/AAAA)
                    todas_datas = re.findall(r'\d{2}/\d{2}/\d{2,4}', linha_limpa)

                    # Estrutura da linha: Data OS | ... | Finalizada em | ... | Data Faturamento
                    # O relatório filtra por "Data de Finalização" = segunda data (índice 1)
                    # Usar índice 1 garante que OS abertas em maio mas finalizadas em junho
                    # apareçam corretamente no mês de junho
                    if len(todas_datas) >= 2:
                        data_mov = todas_datas[1]   # "Finalizada em"
                    elif todas_datas:
                        data_mov = todas_datas[0]
                    else:
                        data_mov = match_estrutura.group(3)

                    # Captura todos os valores monetários da linha (ex: 1.809,20)
                    valores_moeda = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', linha_limpa)

                    if not valores_moeda:
                        continue

                    # R$ Total da OS = último valor monetário da linha
                    valor_total_str = valores_moeda[-1]
                    valor_float = float(valor_total_str.replace(".", "").replace(",", "."))

                    # Descrição com número da OS como chave única para ON CONFLICT
                    descricao = f"OS {num_os}"

                    movimentacoes.append({
                        "data": data_mov,
                        "descricao": descricao,
                        "valor": valor_float,
                        "tipo": "Receita"
                    })

    except Exception as e:
        print(f"Erro no processamento do PDF: {e}")

    return movimentacoes
