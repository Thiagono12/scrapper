from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as pw: # Start Playwright # Inicia o Playwright
        
        browser = pw.chromium.launch(headless=False) # Launch the browser # Inicializa o navegador # if headless= False, the browser window will be visible # Se headless= False, a janela do navegador será visível
        page = browser.new_page() #Open a new page in the browser # Abre uma nova página no navegador


        context = browser.new_context(locale ="en-US") # force the Browser language to English # Força o idioma do navegador para Inglês
        page = context.new_page()

        print("Acessando o google maps..")
        page.goto("https://www.google.com/maps?hl=en") # Navigate to Google maps #Vai pro google maps 

        print("Pesquisando")
        page.get_by_label("Search Google Maps").fill("Dentist in New York") # Fill the search box with what comes in the quotes "fill" means to type in the search box # Preenche a caixa de pesquisa com o que vem entre aspas "fill" significa digitar na caixa de pesquisa
        page.keyboard.press("Enter") # Press Enter to search # Aperta Enter para pesquisar
        print("Aguardando resultados...")


        page.wait_for_selector('div[role="feed"]', timeout=30000) # Wait for the search results to apear # Espera os resultados da busca aparecerem
        for i in range(5): # Logic behind scrolling, the i marks the number of scrolls and the range is how many times it will scroll # Lógica por trás do scroll, o i marca o número de scrolls e o range é quantas vezes ele vai rolar
            page.locator('div[role="feed"]').hover() # Hover over the results feed to ensure the scroll works # Passa o mouse sobre o feed de resultados para garantir que o scroll funcione
            page.mouse.wheel(0, 3000) # Scroll + 3000 over Y axis # Rola +3000 no eixo Y
            time.sleep(2) # Wait 2 seconds to load new results # Espera 2 segundos para carregar novos resultados
            print(f" Rolando lista... ({i+1} de 5)") # Marks the number of scrolls done # Marca o número de scrolls feitos

        
        time.sleep(5)
        

        listings = page.locator('a[href*="/maps/place/"]')
        
        # Conta quantos achou
        count = listings.count()
        print(f"✅ Encontrei {count} empresas na lista!")
        
        # Vamos imprimir o link da primeira só pra confirmar
        if count > 0:
            first_link = listings.nth(0).get_attribute("href")
            print(f"🔗 Exemplo de link capturado: {first_link[:50]}...") # Mostra só o começo

        browser.close() # Close the browser # Fecha o navegador
        
        print("Fechou!")

if __name__ == "__main__":
    main()  # Agora sim a função existe e pode ser chamada
    #arrumando essa bosta 2