from fastapi import FastAPI, BackgroundTasks
import httpx
from pydantic import BaseModel
# ❌ atual
from main import main

# ✅ correto
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from main import main


app = FastAPI() #initialize FastAPI app #inicia FastAPI app


class BuscaRequest(BaseModel): #defining a Pydantic model for the search request #definindo um modelo Pydantic para a requisição de busca
    termo: str
    cidade : str
    webhook_url: str
    


@app.post("/buscar") #using a decorater to define a POST endpoint at "/buscar" #definir um endpoint POST em "/buscar"
def iniciar_busca(request: BuscaRequest, background_tasks: BackgroundTasks): #our function to handle the search request #nossa função para lidar com a requisição de busca
    background_tasks.add_task(rodar_scrapper, request.termo, request.cidade, request.webhook_url) #add the scrapper function to background tasks #adicionar a função do scrapper às tarefas de fundo
    return {"message": "Busca iniciada. Você receberá os resultados em breve."} #return a response indicating the search has started #retornar uma resposta indicando que a busca foi iniciada

def rodar_scrapper(termo: str, cidade: str, webhook_url: str): #function to run the scrapper and send results to the webhook #função para rodar o scrapper e enviar os resultados para o webhook
    main(termo, cidade) #call the main function were the scrapper is working #chamar a função principal onde o scrapper está trabalhando
    httpx.post(webhook_url, json={"status": "completed", "termo": termo, "cidade": cidade}) #send a POST request to the webhook URL with the results #enviar uma requisição POST para a URL do webhook com os resultados
