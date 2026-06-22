import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '260734Mn.',  # altere se necessário
}

SQL_SETUP = """
CREATE DATABASE IF NOT EXISTS gestao_equipamentos;

USE gestao_equipamentos;

CREATE TABLE IF NOT EXISTS equipamentos_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cr VARCHAR(50) NOT NULL,
    equipamento VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_cr_equip (cr, equipamento)
);

CREATE TABLE IF NOT EXISTS lancamentos_bot_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_referencia DATE NOT NULL,
    cr VARCHAR(50),
    equipamento VARCHAR(255),
    hrs_manu FLOAT DEFAULT 0,
    hrs_trab FLOAT DEFAULT 0,
    hrs_disp FLOAT DEFAULT 0,
    custo_total_trab FLOAT DEFAULT 0,
    custo_total_disp FLOAT DEFAULT 0,
    pct_utilizacao FLOAT DEFAULT 0,
    UNIQUE KEY unique_lancamento (data_referencia, cr, equipamento)
);
"""

def setup():
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor()

        for comando in SQL_SETUP.strip().split(';'):
            comando = comando.strip()
            if comando:
                cursor.execute(comando)

        conexao.commit()
        print("✓ Banco de dados criado com sucesso!")

    except Error as e:
        print(f"✗ Erro: {e}")
    finally:
        cursor.close()
        conexao.close()

if __name__ == "__main__":
    setup()