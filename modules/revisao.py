"""
Kit Revisão Básica — catálogo de peças por veículo (placa → modelo → referências)
"""

# Ícone por tipo de item
ICONES = {
    "Filtro de Óleo":         "🛢️",
    "Filtro de Ar do Motor":  "💨",
    "Filtro de Cabine":       "❄️",
    "Filtro de Combustível":  "⛽",
    "Óleo do Motor":          "🔧",
    "Vela de Ignição":        "⚡",
    "Correia Dentada":        "⚙️",
    "Fluido de Freio":        "🔴",
    "Fluido de Arrefecimento":"💧",
    "Pastilha de Freio":      "🛑",
}

FABRICANTES_ORDEM = ["Wega", "Bosch", "Tecfil", "Mann", "Mahle", "NGK", "Denso"]


def buscar_veiculo_por_placa(conexao, placa: str):
    """Retorna (id, placa, cliente_nome, marca, modelo, ano, motor) ou None."""
    cur = conexao.cursor()
    cur.execute("""
        SELECT id, placa, cliente_nome, marca, modelo, ano, motor
        FROM veiculos WHERE UPPER(placa) = %s;
    """, (placa.upper(),))
    row = cur.fetchone()
    cur.close()
    return row


def consultar_placa_api(placa: str) -> dict | None:
    """Consulta dados do veículo pela placa via BrasilAPI. Retorna dict ou None."""
    try:
        import requests
        url = f"https://brasilapi.com.br/api/vehicles/v1/{placa.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "marca":  data.get("MARCA", ""),
                "modelo": data.get("MODELO", ""),
                "ano":    int(data.get("ano", 0)) if data.get("ano") else 0,
                "motor":  data.get("COMBUSTIVEL", ""),
                "cor":    data.get("COR", ""),
                "municipio": data.get("MUNICIPIO", ""),
            }
    except Exception:
        pass
    return None


def buscar_modelos_catalogo(conexao, termo: str) -> list[tuple]:
    """Busca modelos no catálogo por marca ou modelo (busca parcial)."""
    cur = conexao.cursor()
    like = f"%{termo.upper()}%"
    cur.execute("""
        SELECT DISTINCT marca, modelo, motor, ano_inicio, ano_fim
        FROM kit_revisao_catalogo
        WHERE UPPER(marca) LIKE %s OR UPPER(modelo) LIKE %s OR UPPER(motor) LIKE %s
        ORDER BY marca, modelo, ano_inicio;
    """, (like, like, like))
    rows = cur.fetchall()
    cur.close()
    return rows


def buscar_kit(conexao, marca: str, modelo: str, ano: int, motor: str) -> list[dict]:
    """Retorna itens do catálogo agrupados por tipo_item."""
    cur = conexao.cursor()
    cur.execute("""
        SELECT tipo_item, fabricante, referencia, descricao
        FROM kit_revisao_catalogo
        WHERE LOWER(marca)  = LOWER(%s)
          AND LOWER(modelo) = LOWER(%s)
          AND %s BETWEEN ano_inicio AND ano_fim
          AND LOWER(motor)  = LOWER(%s)
        ORDER BY tipo_item, fabricante;
    """, (marca, modelo, ano, motor))
    rows = cur.fetchall()
    cur.close()

    agrupado: dict[str, list] = {}
    for tipo_item, fabricante, referencia, descricao in rows:
        agrupado.setdefault(tipo_item, []).append({
            "fabricante": fabricante,
            "referencia": referencia,
            "descricao":  descricao or "",
        })

    # Ordena fabricantes dentro de cada tipo
    resultado = []
    for tipo_item, pecas in agrupado.items():
        pecas_ordenadas = sorted(
            pecas,
            key=lambda p: FABRICANTES_ORDEM.index(p["fabricante"])
            if p["fabricante"] in FABRICANTES_ORDEM else 99
        )
        resultado.append({"tipo_item": tipo_item, "pecas": pecas_ordenadas})

    return resultado


def listar_modelos_catalogo(conexao) -> list[tuple]:
    """Lista todos os modelos distintos cadastrados no catálogo."""
    cur = conexao.cursor()
    cur.execute("""
        SELECT DISTINCT marca, modelo, ano_inicio, ano_fim, motor
        FROM kit_revisao_catalogo
        ORDER BY marca, modelo, ano_inicio;
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def salvar_item_catalogo(conexao, marca, modelo, ano_inicio, ano_fim, motor,
                         tipo_item, fabricante, referencia, descricao):
    cur = conexao.cursor()
    cur.execute("""
        INSERT INTO kit_revisao_catalogo
            (marca, modelo, ano_inicio, ano_fim, motor, tipo_item, fabricante, referencia, descricao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (marca.upper(), modelo.upper(), ano_inicio, ano_fim, motor.upper(),
          tipo_item, fabricante, referencia.upper(), descricao))
    conexao.commit()
    cur.close()


def cadastrar_veiculo(conexao, placa, cliente_nome, marca, modelo, ano, motor):
    cur = conexao.cursor()
    cur.execute("""
        INSERT INTO veiculos (placa, cliente_nome, marca, modelo, ano, motor)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (placa) DO UPDATE SET
            cliente_nome = EXCLUDED.cliente_nome,
            marca = EXCLUDED.marca,
            modelo = EXCLUDED.modelo,
            ano = EXCLUDED.ano,
            motor = EXCLUDED.motor;
    """, (placa.upper(), cliente_nome.upper() if cliente_nome else None,
          marca.upper(), modelo.upper(), ano, motor.upper()))
    conexao.commit()
    cur.close()
