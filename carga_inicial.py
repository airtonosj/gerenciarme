import pandas as pd
from db_manager import importar_equipamentos_master

# 1. Coloque o caminho ou o nome exato do seu relatório de 3 meses aqui
caminho_arquivo = r"C:\Users\Edeconsil\Documents\Equipamentos Gerenciarme 21-06-2026.csv"

def realizar_carga_master(): 
    print("[CARGA] Lendo o arquivo...")
    
    try:
        # Tenta ler como CSV primeiro (padrão que vi no seu bot_logic)
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        # Se o CSV vier com apenas 1 coluna, tenta ler com vírgula
        if df.shape[1] == 1:
            df = pd.read_csv(caminho_arquivo, sep=',', encoding='utf-8', on_bad_lines='skip')
    except Exception:
        # Se der erro no CSV, assume que é Excel
        print("[CARGA] Tentando ler como Excel...")
        df = pd.read_excel(caminho_arquivo)

    print(f"[CARGA] Arquivo carregado! Encontradas {len(df)} linhas de dados.")
    
    # Verifica se as colunas necessárias existem
    if 'CR' not in df.columns or 'Equipamento' not in df.columns:
        print("[CARGA] ✗ ERRO: O arquivo não possui as colunas 'CR' e/ou 'Equipamento'.")
        return

    print("[CARGA] Iniciando a importação para a Tabela Master no MySQL...")
    
    # Chama a função que criamos no db_manager.py
    sucesso = importar_equipamentos_master(df)

    if sucesso:
        print("[CARGA] ✓ Carga inicial do Gabarito concluída com sucesso!")
        print("Você já pode abrir o MySQL e rodar 'SELECT * FROM equipamentos_master;' para ver a mágica.")
    else:
        print("[CARGA] ✗ Houve um problema ao enviar os dados para o banco.")

if __name__ == "__main__":
    realizar_carga_master()