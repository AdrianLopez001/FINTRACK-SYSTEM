import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Carrega as variáveis do ficheiro .env
load_dotenv(override=True)

@st.cache_resource
def inicializar_conexao():
    import os
    import psycopg2
    from dotenv import load_dotenv
    import streamlit as st
    
    load_dotenv(override=True)
    
    try:
        # Pega as variáveis ou usa os padrões locais exatos do seu instalador
        host = os.getenv("DB_HOST") or "127.0.0.1"
        database = os.getenv("DB_NAME") or "fintrack_db"
        user = os.getenv("DB_USER") or "postgres"
        password = os.getenv("DB_PASS") or "postgres"
        port = os.getenv("DB_PORT") or "5432"
        
        conexao = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        return conexao
    except Exception as e:
        st.error(f"Erro crítico ao ligar ao Banco de Dados: {e}")
        return None
    
# Como deve ficar o trecho dentro de config/database.py:
def criar_tabelas_padrao(conexao):
    if not conexao:
        return

    # Limpa qualquer transação pendente/falha da sessão anterior
    try:
        conexao.rollback()
    except Exception:
        pass

    def _exec(cursor, sql):
        try:
            cursor.execute(sql)
            conexao.commit()
        except Exception:
            conexao.rollback()

    cursor = conexao.cursor()

    _exec(cursor, """
        CREATE TABLE IF NOT EXISTS faturamento (
            id SERIAL PRIMARY KEY,
            data_movimentacao DATE,
            descricao TEXT,
            valor NUMERIC,
            tipo TEXT
        );
    """)

    _exec(cursor, """
        ALTER TABLE faturamento ADD CONSTRAINT uq_os_descricao UNIQUE (descricao);
    """)

    _exec(cursor, """
        CREATE TABLE IF NOT EXISTS veiculos (
            id SERIAL PRIMARY KEY,
            placa TEXT UNIQUE NOT NULL,
            cliente_nome TEXT,
            marca TEXT,
            modelo TEXT,
            ano INTEGER,
            motor TEXT,
            data_cadastro DATE DEFAULT CURRENT_DATE
        );
    """)

    # Migração: renomeia tipo_motor → motor se coluna antiga ainda existir
    _exec(cursor, """
        ALTER TABLE veiculos RENAME COLUMN tipo_motor TO motor;
    """)

    # Migração: remove km_atual se existir (coluna do schema antigo)
    _exec(cursor, """
        ALTER TABLE veiculos DROP COLUMN IF EXISTS km_atual;
    """)

    # Garante coluna motor existe (caso tabela antiga não tinha nenhuma das duas)
    _exec(cursor, """
        ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS motor TEXT;
    """)

    _exec(cursor, """
        CREATE TABLE IF NOT EXISTS kit_revisao_catalogo (
            id SERIAL PRIMARY KEY,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano_inicio INTEGER NOT NULL,
            ano_fim INTEGER NOT NULL,
            motor TEXT NOT NULL,
            tipo_item TEXT NOT NULL,
            fabricante TEXT NOT NULL,
            referencia TEXT NOT NULL,
            descricao TEXT
        );
    """)

    cursor.close()

def executar_query(conexao, query, params=None, retorno=False):
    """
    Função utilitária para executar comandos SQL de forma segura.
    Previne ataques de SQL Injection através do uso de parâmetros.
    """
    if conexao is None:
        return None
        
    try:
        with conexao.cursor() as cursor:
            cursor.execute(query, params)
            
            # Se for um SELECT, retorna os resultados
            if retorno:
                return cursor.fetchall()
                
            # Se for INSERT/UPDATE/DELETE, grava as alterações
            conexao.commit()
            return True
    except Exception as e:
        conexao.rollback()  # Cancela a operação em caso de erro para não corromper o banco
        st.error(f"⚠️ Erro ao executar operação SQL: {e}")
        return None