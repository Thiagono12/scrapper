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
    global stop_flag
    
    # Inicia thread para monitorar a tecla 'q'
    monitor_thread = threading.Thread(target=monitor_stop_key, daemon=True)
    monitor_thread.start()

    while not stop_flag:
        try:
            with sync_playwright() as pw:  # Start Playwright # Inicia o Playwright
                browser = pw.chromium.launch(headless=False)  # Launch the browser # Inicializa o navegador # if headless= False, the browser window will be visible # Se headless= False, a janela do navegador será visível
                context = browser.new_context(locale="en-US")  # force the Browser language to English # Força o idioma do navegador para Inglês
                page = context.new_page()

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

                    for i in range(count):  # Range count ponts to how many entities were found # Range count aponta para quantas entidades foram encontradas
                        if stop_flag:
                            break
                        try:
                            print(f"\n📍 Processando empresa {i+1}...")  # Log 
                            listings.nth(i).click()  # 2. Action (Clica na empresa)
                            page.wait_for_selector('h1', timeout=5000)  # Wait for the details to load # Espera os detalhes carregarem

                            cabecalho = page.locator("h1:visible") \
                                        .filter(has_not_text="Results") \
                                        .filter(has_not_text="Sponsored")

                            # Só pra garantir, espera ele estar visível
                            cabecalho.first.wait_for(state="visible", timeout=5000)

                            nome_empresa = cabecalho.first.inner_text()

                            address_btn = page.locator('button[data-item-id="address"]') # Looks for the button that contains the address # Procura o botão que contém o endereço
                            endereco = "Sem endereço"  # Default text if no address is found # Texto padrão se nenhum endereço for encontrado

                            phone_btn = page.locator('button[data-item-id^="phone:"]')  # Locate the phone button # Localiza o botão de telefone
                            endereco = ""  # Default text for adress before we process the data # Texto padrão para endreco anntes de processar os dados

                            if address_btn.count() > 0:
                                    # O endereço completo costuma estar no 'aria-label' # The full address tend to be in aria-label
                                    # Ex: "Address: 123 5th Ave, New York..."
                                raw_address = address_btn.get_attribute("aria-label")
                            if raw_address:
                                endereco = raw_address.replace("Address: ", "").strip()  # Clean the text to get just the address # Limpa o texto para obter apenas o endereço

                            if phone_btn.count() > 0:  # If the phone button exists, extract the phone number # Se o botão de telefone existir, extrai o número de telefone
                                raw_text = phone_btn.get_attribute("aria-label")  # Get the aria-label attribute which contains the phone number # Pega o atributo aria-label que contém o número de telefone
                                telefone = raw_text.replace("Phone: ", "").strip()  # Clean the text to get just the number # Limpa o texto para obter apenas o número

                            print(f"   🏢 Nome: {nome_empresa}")
                            print(f"   📞 Tel:  {telefone}")
                            print(f"   📍 End:  {endereco}")

                        except Exception as e:
                            print(f"   ❌ Erro nessa empresa: {e}")

                        time.sleep(1)  # Respira um pouco entre uma e outra

                else:
                    # SENÃO, avisa que deu ruim
                    print("⚠️ Não conseguimos fazer a busca. O Google não retornou nada ou o seletor mudou.")

                browser.close()  # Close the browser # Fecha o navegador

                print("Fechou!")

        except Exception as e:
            print(f"❌ Erro geral: {e}")

        if stop_flag:
            break


if __name__ == "__main__":
    main()  # Agora sim a função existe e pode ser chamadaqqqqq