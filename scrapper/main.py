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


        try:
            page.get_by_label("Search Google Maps").fill("Pizza in New York")
            page.keyboard.press("Enter")
            print("✅ Sucesso! O site obedeceu.")
        except:
            print("❌ Erro: O site ainda está em português")

        
        time.sleep(5)
        
        browser.close()
        print("Fechou!")

if __name__ == "__main__":
    main()  # Agora sim a função existe e pode ser chamada