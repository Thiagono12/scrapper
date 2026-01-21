import keyboard
from playwright.sync_api import sync_playwright
import time
import threading
import json 
import os
from dotenv import load_dotenv
import psycopg2




USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")



load_dotenv()  # Carrega variáveis de ambiente do arquivo .env # Load environment variables from .env file 

# Function to insert a single company directly into Supabase
def insert_empresa_supabase(nome, telefone, endereco):
    """Insere uma empresa diretamente no Supabase quando é coletada"""
    conn = None
    cursor = None

    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    database = os.getenv("database")
    

    try:
        connection = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        dbname=database,
        )
        print("Connection successful!")
    
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Current Time:", result)

    except Exception as e:
        print(f"Failed to connect: {e}")



        cursor = connection.cursor()

        # Create table if it doesn't exist
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                telefone TEXT,
                endereco TEXT,
                origem_busca TEXT DEFAULT 'Google Maps',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
    connection.commit()

        # Insert the company
    cursor.execute('''
            INSERT INTO empresas (nome, telefone, endereco, origem_busca)
            VALUES (%s, %s, %s, %s)
        ''', (nome, telefone, endereco, 'Google Maps'))
        
    connection.commit()
    print(f"      ☁️  Salvo no Supabase!")
    return True
        
 

# Function to migrate all data from JSON to Supabase (batch migration)
def migrar_agorar():
    """Migra todos os dados do JSON para o Supabase de uma vez"""
    print("\n🚀 Iniciando migração em lote do Supabase...")
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("host"),
            database=os.getenv("database"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            port=int(os.getenv("port", 5432))
        )

        cursor = conn.cursor()
        print("✅ Conectado no Supabase com sucesso!")
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                telefone TEXT,
                endereco TEXT,
                origem_busca TEXT DEFAULT 'Google Maps',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()

        arquivo_json = "dados_empresas.json"
        if not os.path.exists(arquivo_json):
            print("❌ Arquivo JSON não encontrado. Rode o scraper primeiro.")
            return
        
        with open(arquivo_json, "r", encoding="utf-8") as f:
            dados = json.load(f)

        print(f"🔄 Migrando {len(dados)} registros para o Supabase...")

        novos = 0
        duplicados = 0

        for empresa in dados:
            try:
                cursor.execute('''
                    INSERT INTO empresas (nome, telefone, endereco, origem_busca)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (nome) DO NOTHING;
                ''', (
                    empresa.get("nome"),
                    empresa.get("telefone"),
                    empresa.get("endereco"),
                    'Google Maps'
                ))
                
                if cursor.rowcount > 0:
                    novos += 1
                else:
                    duplicados += 1
                    
            except Exception as e:
                print(f"❌ Erro ao inserir {empresa.get('nome')}: {e}")
                conn.rollback()
                continue
        
        conn.commit()   
        print(f"\n✅ Migração concluída!")
        print(f"   📊 {novos} novos registros adicionados")
        print(f"   ⚠️  {duplicados} registros duplicados ignorados")
                
    except Exception as e:
        print(f"❌ Erro na conexão ou migração: {e}")
        print("Verifique suas credenciais no arquivo .env e a conexão com a internet.")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




stop_flag = False



def monitor_stop_key():
    """Monitora continuamente se a tecla 'q' foi pressionada"""
    global stop_flag
    while True:
        if keyboard.is_pressed('q'):
            stop_flag = True
            print("\n⛔ Parando execução...")
            break
        time.sleep(0.1)


def carregar_dados_existentes():
    arquivo = "dados_empresas.json"

    if not os.path.exists(arquivo): #if file doesn't exist, return an empty list # se o arquivo não existir, retorna uma lista vazia
        return []
    
    try: # If file exists try to load it and read # Se o arquivo existir, tente carregá-lo e ler
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados
    except:
        return [] # If any error occurs, return an empty list # Se ocorrer algum erro, retorna uma lista vazia


def salvar_dados(dados):
    arquivo = "dados_empresas.json"
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4) # Pretty print # Printa bonito
        print(f"✅ Dados salvos em {arquivo}")


def main():

    arquivos_dados = "dados_empresas.json"
    dados_acumulados = carregar_dados_existentes() # Carrega dados existentes ou inicia uma nova lista, based on the fuc above # Load existing data or start a new list, baseado na função acima


    global stop_flag # For using the stop_flag variable inside the function
   

                     
    # Inicia thread para monitorar a tecla 'q'
    monitor_thread = threading.Thread(target=monitor_stop_key, daemon=True)
    monitor_thread.start()

    while not stop_flag:
        try:
            with sync_playwright() as pw:  # Start Playwright # Inicia o Playwright
                browser = pw.chromium.launch(headless=True)  # Launch the browser # Inicializa o navegador # if headless= False, the browser window will be visible # Se headless= False, a janela do navegador será visível
                context = browser.new_context(locale="en-US")  # force the Browser language to English # Força o idioma do navegador para Inglês
                page = context.new_page()

                def route_intercept(route):
                    if route.request.resource_type in ["image", "media", "font"]:
                        route.abort()
                    else:
                        route.continue_()

                    page.route("**/*", route_intercept)

                print("Acessando o google maps..")
                page.goto("https://www.google.com/maps?hl=en")  # Navigate to Google maps #Vai pro google maps 

                print("Pesquisando")
                page.get_by_label("Search Google Maps").fill("Dentist in New York")  # Fill the search box with what comes in the quotes "fill" means to type in the search box # Preenche a caixa de pesquisa com o que vem entre aspas "fill" significa digitar na caixa de pesquisa
                page.keyboard.press("Enter")  # Press Enter to search # Aperta Enter para pesquisar
                print("Aguardando resultados...")

                page.wait_for_selector('div[role="feed"]', timeout=30000)  # Wait for the search results to apear # Espera os resultados da busca aparecerem
                for i in range(5):  # Logic behind scrolling, the i marks the number of scrolls and the range is how many times it will scroll # Lógica por trás do scroll, o i marca o número de scrolls e o range é quantas vezes ele vai rolar
                    if stop_flag:
                        break
                    page.locator('div[role="feed"]').hover()  # Hover over the results feed to ensure the scroll works # Passa o mouse sobre o feed de resultados para garantir que o scroll funcione
                    page.mouse.wheel(0, 3000)  # Scroll + 3000 over Y axis # Rola +3000 no eixo Y
                    time.sleep(2)  # Wait 2 seconds to load new results # Espera 2 segundos para carregar novos resultados
                    print(f" Rolando lista... ({i+1} de 5)")  # Marks the number of scrolls done # Marca o número de scrolls feitos

                time.sleep(5)

                listings = page.locator('a[href*="/maps/place/"]')  # Look for every stuff thats includes /maps/place/ # Olhe para qualquer coisa que inclua /maps/place/
                count = listings.count()  # How many entites were found 

                if count > 0:  # Runs only if something was found # Roda somente se algo foi encontrado
                    print(f"✅ Encontrei {count} empresas! Começando a extração...")
                    ultimo_nome = "" # Inicialize here to keep track of the last company name # Inicialize aqui para acompanhar o nome da última empresa


                    for i in range(count):  # Range count ponts to how many entities were found # Range count aponta para quantas entidades foram encontradas
                        if stop_flag:
                            break
                        try:
                            print(f"\n📍 Processando empresa {i+1}...")  # Log 
                        
                            # --- CORREÇÃO DE CLIQUE (Scroll necessário) ---
                            # Antes de clicar, garantimos que o item está visível
                            #Before clicking, we ensure the item is visible
                            listings.nth(i).scroll_into_view_if_needed()
                            time.sleep(0.5)  
                            # ----------------------------------------------

                            listings.nth(i).click()  # 2. Action (Clica na empresa)
                            
                            # Definição do filtro (Mantido como você fez)
                            cabecalho = page.locator("h1:visible") \
                                            .filter(has_not_text="Results") \
                                            .filter(has_not_text="Sponsored")

                            # --- LÓGICA ANTI-DUPLICATA (Obrigatória para funcionar) ---
                            # No Duplicates Logic
                            start_time = time.time()
                            nome_empresa = ""
                       
                            
                            while True:
                                # Se passar de 5s, desiste
                                if time.time() - start_time > 5:
                                    break
                                
                                # Verifica se carregou
                                if cabecalho.count() > 0:
                                    # Só pra garantir, espera ele estar visível
                                    # (Nota: O wait_for aqui dentro do loop substitui o timeout longo antigo)
                                    texto_tela = cabecalho.first.inner_text()
                                    
                                    # Verifica se é válido e se mudou em relação ao anterior
                                    if texto_tela.strip() != "" and texto_tela != ultimo_nome:
                                        nome_empresa = texto_tela
                                        break 
                                
                                time.sleep(0.1) # Loop rápido
                            
                            # Se falhar o clique ou o nome não mudar, pula essa volta
                            # If Failed click or name didn't change, skip this round 
                            if not nome_empresa or nome_empresa == ultimo_nome:
                                print("   ⚠️ Clique falhou ou repetido. Pulando...")
                                continue
                            # ---------------------------------------------------------

                            # --- EXTRAÇÃO DO ENDEREÇO ---
                            # Adress extraction
                            address_btn = page.locator('button[data-item-id="address"]') # Looks for the button that contains the address # Procura o botão que contém o endereço
                            endereco = "Sem enqqqqdereço"  # Default text if no address is found # Texto padrão se nenhum endereço for encontrado

                            if address_btn.count() > 0:
                                # O endereço completo costuma estar no 'aria-label' # The full address tend to be in aria-label
                                # Ex: "Address: 123 5th Ave, New York..."
                                raw_address = address_btn.get_attribute("aria-label")
                                
                                # CORREÇÃO: O if raw_address precisa estar dentro do if do botão
                                if raw_address:
                                    endereco = raw_address.replace("Address: ", "").strip()  # Clean the text to get just the address # Limpa o texto para obter apenas o endereço
                            
                            # --- EXTRAÇÃO DO TELEFONE ---
                            phone_btn = page.locator('button[data-item-id^="phone:"]')  # Locate the phone button # Localiza o botão de telefone
                            telefone = "Sem telefone" # Correção: Inicializa a variável antes do if para não dar erro

                            if phone_btn.count() > 0:  # If the phone button exists, extract the phone number # Se o botão de telefone existir, extrai o número de telefone
                                raw_text = phone_btn.get_attribute("aria-label")  # Get the aria-label attribute which contains the phone number # Pega o atributo aria-label que contém o número de telefone
                                telefone = raw_text.replace("Phone: ", "").strip()  # Clean the text to get just the number # Limpa o texto para obter apenas o número



                            print(f"   🏢 Nome: {nome_empresa}")
                            print(f"   📞 Tel:  {telefone}")
                            print(f"   📍 End:  {endereco}")


                            # Save the data # Salva os dados 
                            lead_novo = { 
                                "nome": nome_empresa,
                                "telefone": telefone,
                                "endereco": endereco
                            } #our JSON structure # Nossa estrutura JSON

                            dados_acumulados.append(lead_novo)

                            with open(arquivos_dados, "w", encoding="utf-8") as f: # Save the data in a new JSON file # Salva os dados em um novo arquivo JSON
                                json.dump(dados_acumulados, f, ensure_ascii=False, indent=4) # Pretty print # Printa bonito

                            print("   ✅ Dados salvos em JSON!")

                            # Save directly to Supabase
                            insert_empresa_supabase(nome_empresa, telefone, endereco)
                            
                            # Atualiza a memória # Uptade memory
                            ultimo_nome = nome_empresa
                        except Exception as e:
                            print(f"   ❌ Erro nessa empresa: {e}")
                            time.sleep(1)  # Respira um pouco entre uma e outra

                    else:
                        # SENÃO, avisa que deu ruim
                        # ELSE, warns that something went wrong
                        print("⚠️ Não conseguimos fazer a busca. O Google não retornou nada ou o seletor mudou.")

                browser.close()  # Close the browser # Fecha o navegador
                break # Exit the while loop after one complete run # Sai do loop while após uma execução completa

            print("Fechou!")

        except Exception as e:
            print(f"❌ Erro geral: {e}")


        if stop_flag:
            break


if __name__ == "__main__":
    main()  # Agora sim a função existe e pode ser chamada