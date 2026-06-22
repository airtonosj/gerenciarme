import time
import os
import glob
import pandas as pd
from datetime import datetime, timedelta
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import locale

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

class BotController:
    def __init__(self, start_date, end_date, headless=True, gui_instance=None):
        self.start_date = start_date
        self.end_date = end_date
        self.headless = headless
        self.gui_instance = gui_instance
        self.driver = None
        self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.downloaded_cr_map = {}

    def setup_driver(self):
        print("[BOT LOGIC] Configurando o WebDriver com webdriver-manager...")
        try:
            options = webdriver.ChromeOptions()
            prefs = {"download.prompt_for_download": False, "download.directory_upgrade": True, "safebrowsing.enabled": True, "safebrowsing.disable_download_protection": True}
            options.add_experimental_option("prefs", prefs)
            options.set_capability('acceptInsecureCerts', True)
            if self.headless:
                print("[BOT LOGIC] Modo Headless ATIVADO.")
                options.add_argument("--headless=new")
            else:
                print("[BOT LOGIC] Modo Headless DESATIVADO (Navegador será visível).")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument('--ignore-certificate-errors')
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("[BOT LOGIC] WebDriver configurado com sucesso.")
        except Exception as e:
            print(f"[BOT LOGIC] ERRO CRÍTICO AO CONFIGURAR O DRIVER: {e}")
            raise
            
    def perform_login(self, username, password):
        try:
            self.driver.get("http://v5.gerenciar.me/")
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "input-29"))).send_keys(username)
            self.driver.find_element(By.ID, "input-33").send_keys(password)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Entrar')]"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='v-list-item__title' and contains(text(), 'Projetos')]")))
            print("[BOT LOGIC] Login realizado com sucesso!")
            return True
        except Exception as e:
            print(f"[BOT LOGIC] ERRO DURANTE O LOGIN: {e}")
            return False

    def navigate_to_reports_page(self):
        try:
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='v-list-item__title' and contains(text(), 'Projetos')]")))
            print("[BOT LOGIC] Página principal carregada.")
            wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'v-list-group__header') and .//div[contains(text(), 'Relatórios')]]"))).click()
            time.sleep(0.5)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/relatorios/projeto')]"))).click()
            print("[BOT LOGIC] Navegação para a página de relatórios de projeto concluída.")
            return True
        except Exception as e:
            print(f"[BOT LOGIC] ERRO DURANTE A NAVEGAÇÃO NO MENU: {e}")
            return False

    def select_date_range(self):
        try:
            wait = WebDriverWait(self.driver, 20)
            date_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'v-text-field') and .//*[contains(text(), 'Selecione um range')]]//input")))
            date_input_field.click()
            time.sleep(1)

            def select_a_date(date_str):
                month_map = {
                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
                    'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                }
                target_date = datetime.strptime(date_str, '%d/%m/%Y')
                target_year = target_date.year
                target_month = target_date.month
                target_day = str(target_date.day)

                for _ in range(36): 
                    month_year_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='v-date-picker-header__value']//button")))
                    parts = month_year_element.text.lower().split(' de ')
                    current_month_str = parts[0]
                    current_year = int(parts[1])
                    current_month = month_map[current_month_str]
                    
                    print(f"[BOT LOGIC] Calendário em: {current_month_str.capitalize()} de {current_year}. Alvo: {target_date.strftime('%B de %Y')}")
                    
                    if target_year == current_year and target_month == current_month:
                        print("[BOT LOGIC] Mês e ano corretos encontrados.")
                        break

                    # << CORREÇÃO DEFINITIVA DOS SELETORES DE NAVEGAÇÃO >>
                    if target_year < current_year or (target_year == current_year and target_month < current_month):
                        print("[BOT LOGIC] Voltando um mês...")
                        prev_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Mês anterior']")))
                        self.driver.execute_script("arguments[0].click();", prev_button)
                    else:
                        print("[BOT LOGIC] Avançando um mês...")
                        next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Próximo mês']")))
                        self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(0.4)
                else:
                    raise Exception("Não foi possível encontrar a data alvo no calendário.")
                
                print(f"[BOT LOGIC] Clicando no dia '{target_day}'...")
                day_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'v-date-picker-table')]//tbody//td[not(contains(@class, 'v-date-picker-table--disabled'))]//button[.//div[text()='{target_day}']]")))
                day_button.click()

            select_a_date(self.start_date)
            time.sleep(0.5)
            select_a_date(self.end_date)
            
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[span[contains(text(), 'OK')]]"))).click()
            print("[BOT LOGIC] Período selecionado com sucesso.")
            return True
        except Exception as e:
            print(f"[BOT LOGIC] ERRO DURANTE A SELEÇÃO DE DATAS: {e}")
            return False

    def process_all_projects(self):
        processed_names = set() # Guarda os nomes que já finalizamos
        wait = WebDriverWait(self.driver, 10)
        
        # Localizador do Input (para abrir a lista)
        input_xpath = "//div[contains(@class, 'v-text-field') and .//*[contains(text(), 'Escolha o projeto')]]//input"
        
        while True:
            try:
                # 1. Abre a lista de projetos (se não estiver aberta)
                print("[BOT LOGIC] Abrindo seletor de projetos...")
                project_input = wait.until(EC.element_to_be_clickable((By.XPATH, input_xpath)))
                project_input.click()
                time.sleep(1) # Tempo para a animação do menu abrir

                # 2. Localiza o container da lista para fazer scroll se necessário
                list_container = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'v-menu__content') and contains(@class, 'menuable__content__active')]")))

                # 3. Pega todos os itens VISÍVEIS na lista agora
                visible_items = self.driver.find_elements(By.XPATH, "//div[@role='listbox']//div[contains(@class, 'v-list-item__title')]")
                
                target_element = None
                target_name = ""
                found_new = False

                # 4. Procura o primeiro item que ainda NÃO está no nosso registro de processados
                for item in visible_items:
                    name = item.text.strip()
                    if name and name not in processed_names:
                        target_element = item
                        target_name = name
                        found_new = True
                        break # Paramos de procurar assim que achamos o próximo alvo
                
                # 5. Se não achou nada novo na tela atual, tentamos SCROLLAR para baixo
                if not found_new:
                    print("[BOT LOGIC] Todos os itens visíveis já foram processados. Rolando lista...")
                    last_scroll = self.driver.execute_script("return arguments[0].scrollTop", list_container)
                    self.driver.execute_script("arguments[0].scrollTop += 300;", list_container)
                    time.sleep(1)
                    new_scroll = self.driver.execute_script("return arguments[0].scrollTop", list_container)
                    
                    if last_scroll == new_scroll:
                        print("[BOT LOGIC] Fim da lista alcançado.")
                        break # Sai do loop While True (Fim de tudo)
                    else:
                        continue # Volta para o início do While para ler os novos itens carregados

                # 6. Se achou um alvo novo, CLICA nele
                print(f"\n--- Selecionando: {target_name} ---")
                
                # Scroll suave até o elemento para garantir visibilidade
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_element)
                time.sleep(0.5)
                target_element.click()
                
                # Adiciona à lista de processados IMEDIATAMENTE para não repetir
                processed_names.add(target_name) 

                # 7. A Lógica de Espera e Verificação (solicitada por você)
                print("[BOT LOGIC] Aguardando 5 segundos para carregar dados...")
                time.sleep(8)

                # Verifica se a mensagem "Não há dados" apareceu
                has_data = True
                try:
                    # Procura mensagem de erro visível
                    msgs = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Não há dados disponíveis')]")
                    for msg in msgs:
                        if msg.is_displayed():
                            print(f"[BOT LOGIC] '{target_name}' não possui dados.")
                            has_data = False
                            break
                except Exception:
                    pass
                
                if not has_data:
                    yield f"Sem dados: {target_name}"
                    # O loop 'continue' acontece automaticamente, voltando para abrir a lista novamente
                else:
                    # --- Se tem dados, faz o processo de EXPORTAÇÃO ---
                    print(f"[BOT LOGIC] Dados encontrados para {target_name}. Exportando...")
                    
                    # Clica no botão exportar
                    try:
                        export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//i[contains(@class, 'mdi-checkbox-multiple-blank')]]")))
                        export_btn.click()
                        
                        # Monitora o download
                        files_before = set(os.listdir(self.download_path))
                        wait_start = time.time()
                        downloaded = False
                        
                        while time.time() - wait_start < 45:
                            files_after = set(os.listdir(self.download_path))
                            new_files = files_after - files_before
                            valid_files = [f for f in new_files if f.endswith('.csv') and not f.endswith('.crdownload')]
                            
                            if valid_files:
                                full_path = os.path.join(self.download_path, valid_files[0])
                                self.downloaded_cr_map[full_path] = target_name
                                yield f"Download concluído: {target_name}"
                                downloaded = True
                                break
                            time.sleep(1)
                        
                        if not downloaded:
                            yield f"Timeout no download: {target_name}"

                    except Exception as e:
                        print(f"[BOT LOGIC] Erro ao tentar exportar: {e}")
            
            except Exception as e:
                print(f"[BOT LOGIC] Erro no ciclo: {e}")
                # Tenta recuperar fechando menus (ESC) e continuando
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                continue
            
        return True
    def process_and_merge_reports(self):
        yield "Iniciando tratamento dos arquivos..."
        if not self.downloaded_cr_map:
            yield "Nenhum arquivo para processar."
            return
        all_dfs = []
        for filepath, cr_name in self.downloaded_cr_map.items():
            try:
                print(f"[BOT LOGIC] Processando {filepath} para CR: {cr_name}")
                df = pd.read_csv(filepath, sep=';', encoding='latin-1', on_bad_lines='skip')
                if df.shape[1] == 1:
                    print("[BOT LOGIC] Leitura com ';' falhou, tentando com ','...")
                    df = pd.read_csv(filepath, sep=',', encoding='utf-8', on_bad_lines='skip')
                
                print(f"[BOT LOGIC] Lidas {len(df)} linhas do arquivo {os.path.basename(filepath)}")
                df["CR"] = cr_name
                df["Data(de)"] = self.start_date
                df["Data(para)"] = self.end_date
                all_dfs.append(df)
            except Exception as e:
                print(f"[BOT LOGIC] Erro ao processar o arquivo {filepath}: {e}")
                yield f"Erro ao ler {os.path.basename(filepath)}"
        if not all_dfs:
            yield "Falha ao processar os arquivos."
            return
        
        final_df = pd.concat(all_dfs, ignore_index=True)
        yesterday = datetime.now() - timedelta(1)
        final_filename = f"Equipamentos Gerenciarme {yesterday.strftime('%d-%m-%Y')}.csv"
        final_filepath = os.path.join(self.download_path, final_filename)
        final_df.to_csv(final_filepath, index=False, encoding='utf-8-sig', sep=';')
        yield f"Arquivo final criado: {final_filename}"
        
        if self.gui_instance and messagebox.askyesno(
            "Processo Concluído", 
            f"O relatório final '{final_filename}' foi criado com sucesso.\n\nDeseja excluir os {len(self.downloaded_cr_map)} arquivos individuais?"
        ):
            for f in self.downloaded_cr_map.keys():
                try: os.remove(f)
                except OSError as e: print(f"Erro ao deletar o arquivo {f}: {e}")
            yield "Arquivos individuais excluídos."
        else:
            yield "Arquivos individuais mantidos."

    def run(self):
        try:
            self.setup_driver()
            if not self.perform_login("admin@edeconsil", "changeme"):
                yield "FALHA NO LOGIN"
                return
            yield "Login realizado com sucesso!"
            if not self.navigate_to_reports_page():
                yield "FALHA AO NAVEGAR PARA RELATÓRIOS"
                return
            yield "Navegação para página de relatórios concluída!"
            if not self.select_date_range():
                yield "FALHA AO SELECIONAR DATAS"
                return
            yield "Período selecionado com sucesso!"
            yield from self.process_all_projects()
            yield "PROCESSAMENTO DE CRs CONCLUÍDO!"
            yield from self.process_and_merge_reports()
        except Exception as e:
            print(f"[BOT LOGIC] ERRO GERAL NO MÉTODO 'run': {e}")
            yield f"ERRO GERAL: {e}"
        finally:
            if self.driver:
                self.driver.quit()
            print("[BOT LOGIC] Fim da execução.")