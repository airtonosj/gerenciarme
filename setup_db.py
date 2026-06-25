import os

import mysql.connector
from mysql.connector import Error

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


DB_NAME = os.getenv("MYSQL_DATABASE", "gestao_equipamentos")
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "260734Mn."),
}

SQL_SETUP = """
CREATE DATABASE IF NOT EXISTS {db_name};

USE {db_name};

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
    conexao = None
    cursor = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor()

        for comando in SQL_SETUP.format(db_name=DB_NAME).strip().split(";"):
            comando = comando.strip()
            if comando:
                cursor.execute(comando)

        conexao.commit()
        print("Banco de dados criado com sucesso!")
        return True

    except Error as e:
        print(f"Erro ao conectar/configurar o MySQL: {e}")
        print("Verifique MYSQL_USER e MYSQL_PASSWORD no arquivo .env ou no MySQL.")
        return False
    finally:
        if cursor:
            cursor.close()
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    setup()
