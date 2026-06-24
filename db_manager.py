import mysql.connector
from mysql.connector import Error
import pandas as pd
import warnings
import re

#so pra ignorar mensagem chata de aviso
warnings.filterwarnings('ignore', category=UserWarning)




# Dicionário com as configurações do banco
DB_CONFIG = {
    'host': 'localhost',        # Mantenha localhost se estiver rodando na sua máquina
    'user': 'root',             # Seu usuário do MySQL
    'password': '260734Mn.',    # Coloque sua senha real aqui
    'database': 'gestao_equipamentos'
}

def conectar():
    """Cria e retorna a conexão com o banco de dados."""
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            return conexao
    except Error as e:
        print(f"[DB_MANAGER] Erro ao conectar ao MySQL: {e}")
        return None

def testar_conexao():
    """Função simples para validar se a porta está aberta."""
    conexao = conectar()
    if conexao:
        print("[DB_MANAGER] ✓ Conexão com 'gestao_equipamentos' estabelecida com sucesso!")
        conexao.close()
    else:
        print("[DB_MANAGER] ✗ Falha na conexão.")

if __name__ == "__main__":
    # Rodando este arquivo isoladamente, ele apenas testará a conexão.
    testar_conexao()
def importar_equipamentos_master(df_gabarito):
    """
    Recebe um DataFrame contendo as colunas 'CR' e 'Equipamento'
    e popula a tabela master, ignorando duplicatas automáticas.
    """
    conexao = conectar()
    if not conexao:
        return False
    
    try:
        cursor = conexao.cursor()
        # INSERT IGNORE: Se o par (CR, Equipamento) já existir, o MySQL pula silenciosamente sem travar o código
        sql = """
            INSERT IGNORE INTO equipamentos_master (cr, equipamento) 
            VALUES (%s, %s)
        """
        
        # Prepara os dados do DataFrame para o formato que o MySQL entende (lista de tuplas)
        dados = list(df_gabarito[['CR', 'Equipamento']].itertuples(index=False, name=None))
        
        cursor.executemany(sql, dados) # Executa em lote (muito mais rápido)
        conexao.commit()
        
        print(f"[DB_MANAGER] ✓ Lista Master atualizada/processada. Linhas afetadas: {cursor.rowcount}")
        return True
    except Exception as e:
        print(f"[DB_MANAGER] Erro ao importar Master: {e}")
        return False
    finally:
        cursor.close()
        conexao.close()


import re # Adicione este import lá no topo do arquivo junto com os outros!

def tratar_numero(valor):
    """Limpa e converte strings no formato brasileiro (1.234,56 ou -1,34) para float do Python."""
    if pd.isna(valor) or valor is None or valor == '':
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    v_str = str(valor).strip()
    
    # Se for um traço de nulo na planilha
    if v_str in ('-', '—', ''):
        return 0.0
        
    # Remove pontos de milhar se existirem junto com vírgula (ex: 1.234,56 -> 1234,56)
    if '.' in v_str and ',' in v_str:
        v_str = v_str.replace('.', '')
        
    # Troca a vírgula decimal pelo ponto do Python
    v_str = v_str.replace(',', '.')
    
    # Remove qualquer coisa que não seja número, ponto ou sinal negativo (ex: R$, espaços)
    v_str = re.sub(r"[^0-9.\-]", "", v_str)
    
    try:
        return float(v_str) if v_str else 0.0
    except ValueError:
        return 0.0

def importar_lancamentos_diarios(df_diario, data_referencia):
    """
    Recebe o DataFrame diário do bot e a data de referência.
    Insere os dados tratando para que não haja duplicidade no mesmo dia.
    """
    conexao = conectar()
    if not conexao:
        return False
    
    try:
        cursor = conexao.cursor()
        
        sql = """
            INSERT INTO lancamentos_bot_raw 
            (data_referencia, cr, equipamento, hrs_manu, hrs_trab, hrs_disp, custo_total_trab, custo_total_disp, pct_utilizacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hrs_manu = VALUES(hrs_manu),
                hrs_trab = VALUES(hrs_trab),
                hrs_disp = VALUES(hrs_disp),
                custo_total_trab = VALUES(custo_total_trab),
                custo_total_disp = VALUES(custo_total_disp),
                pct_utilizacao = VALUES(pct_utilizacao);
        """
        
        cols = {
            'CR': '',
            'Equipamento': '',
            'Hrs Manu': 0.0,
            'Hrs Trab': 0.0,
            'Hrs Disp': 0.0,
            '$ Total Trab': 0.0,
            '$ Total Disp': 0.0,
            '% Util': 0.0,
        }
        dados_df = df_diario.reindex(columns=cols.keys(), fill_value=None).fillna(cols)
        dados_df['CR'] = dados_df['CR'].astype(str)
        dados_df['Equipamento'] = dados_df['Equipamento'].astype(str)
        for col in ['Hrs Manu', 'Hrs Trab', 'Hrs Disp', '$ Total Trab', '$ Total Disp', '% Util']:
            dados_df[col] = dados_df[col].map(tratar_numero)
        dados_df['data_referencia'] = data_referencia
        dados = list(dados_df[[
            'data_referencia',
            'CR',
            'Equipamento',
            'Hrs Manu',
            'Hrs Trab',
            'Hrs Disp',
            '$ Total Trab',
            '$ Total Disp',
            '% Util',
        ]].itertuples(index=False, name=None))
            
        cursor.executemany(sql, dados)
        conexao.commit()
        
        print(f"[DB_MANAGER] ✓ Lançamentos do dia {data_referencia} salvos/atualizados. Registros: {len(dados)}")
        return True
    except Exception as e:
        print(f"[DB_MANAGER] Erro ao importar lançamentos diários: {e}")
        return False
    finally:
        cursor.close()
        conexao.close()

def buscar_lancamentos_por_periodo(data_inicio, data_fim):
    """
    Busca e SOMA os dados lançados no banco dentro de um período específico.
    """
    conexao = conectar()
    if not conexao: return pd.DataFrame()
        
    try:
        # Usamos SUM() para consolidar as horas e custos de múltiplos dias, e GROUP BY para agrupar por equipamento
        sql = """
            SELECT 
                cr AS CR,
                equipamento AS Equipamento,
                SUM(hrs_manu) AS `Hrs Manu`,
                SUM(hrs_trab) AS `Hrs Trab`,
                SUM(hrs_disp) AS `Hrs Disp`,
                SUM(custo_total_trab) AS `$ Total Trab`,
                SUM(custo_total_disp) AS `$ Total Disp`,
                AVG(pct_utilizacao) AS `% Util`
            FROM lancamentos_bot_raw
            WHERE data_referencia BETWEEN %s AND %s
            GROUP BY cr, equipamento;
        """
        df_lancados = pd.read_sql(sql, conexao, params=(data_inicio, data_fim))
        return df_lancados
    except Exception as e:
        print(f"[DB_MANAGER] Erro ao buscar lançamentos: {e}")
        return pd.DataFrame()
    finally:
        conexao.close()


def buscar_equipamentos_sem_lancamento(data_inicio, data_fim):
    """
    Identifica quem NÃO teve NENHUM lançamento dentro do período selecionado.
    """
    conexao = conectar()
    if not conexao: return pd.DataFrame()
        
    try:
        # Se não existe registro do equipamento neste intervalo (BETWEEN), ele é classificado como Não Lançado.
        sql = """
            SELECT 
                m.equipamento AS Equipamento,
                m.cr AS CR,
                '—' AS `Hrs Manu`,
                '—' AS `Hrs Trab`,
                '—' AS `Hrs Disp`,
                'Não Lançado' AS Status
            FROM equipamentos_master m 
            LEFT JOIN lancamentos_bot_raw l 
                ON m.cr = l.cr 
                AND m.equipamento = l.equipamento 
                AND l.data_referencia BETWEEN %s AND %s
            WHERE l.id IS NULL
            ORDER BY m.cr, m.equipamento;
        """
        df_pendencias = pd.read_sql(sql, conexao, params=(data_inicio, data_fim))
        return df_pendencias
    except Exception as e:
        print(f"[DB_MANAGER] Erro ao buscar pendências: {e}")
        return pd.DataFrame()
    finally:
        conexao.close()
