import keyboard
from playwright.sync_api import sync_playwright
import time
import threading

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




def main():
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
                            endereco = "Sem endereço"  # Default text if no address is found # Texto padrão se nenhum endereço for encontrado

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

                print("Fechou!")

        except Exception as e:
            print(f"❌ Erro geral: {e}")

        if stop_flag:
            break


if __name__ == "__main__":
    main()  # Agora sim a função existe e pode ser chamada