from fastapi import FastAPI, BackgroundTasks
import httpx
from pydantic import BaseModel
# ✅ correto
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from scrapper.main import main 
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from scrapper.main import conectar_banco


app = FastAPI() #initialize FastAPI app #inicia FastAPI app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ← aceita qualquer origem # Accept any origin
    allow_methods=["*"],      # ← aceita qualquer método # Accept any method
    allow_headers=["*"],      # ← aceita qualquer header # Accept any header
)




class BuscaRequest(BaseModel): #defining a Pydantic model for the search request #definindo um modelo Pydantic para a requisição de busca
    termo: str
    cidade : str
    webhook_url: str



load_dotenv(Path(__file__).parent / ".env") # Carrega variáveis de ambiente do arquivo .env # Load environment variables from .env file 
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DATABASE = os.getenv("database")

@app.post("/buscar") #using a decorater to define a POST endpoint at "/buscar" #definir um endpoint POST em "/buscar"
def iniciar_busca(request: BuscaRequest, background_tasks: BackgroundTasks): #our function to handle the search request #nossa função para lidar com a requisição de busca
    background_tasks.add_task(rodar_scrapper, request.termo, request.cidade, request.webhook_url) #add the scrapper function to background tasks #adicionar a função do scrapper às tarefas de fundo
    return {"message": "Busca iniciada. Você receberá os resultados em breve."} #return a response indicating the search has started #retornar uma resposta indicando que a busca foi iniciada

def rodar_scrapper(termo: str, cidade: str, webhook_url: str): #function to run the scrapper and send results to the webhook #função para rodar o scrapper e enviar os resultados para o webhook
    main(termo, cidade) #call the main function were the scrapper is working #chamar a função principal onde o scrapper está trabalhando
    httpx.post(webhook_url, json={"status": "completed", "termo": termo, "cidade": cidade}) #send a POST request to the webhook URL with the results #enviar uma requisição POST para a URL do webhook com os resultados


@app.get("/buscas") #our endpoint get to return all searches from database #nosso endpoint GET para retornar todas as buscas do banco de dados

def ver_buscas(): #our fuc(), starting with conn, and cursor, to connect w/ database and return all searches #nossa função(), começando com conn, e cursor, para conectar com o banco de dados e retornar todas as buscas
    conn = None
    cursor = None

    conn = conectar_banco()

    if conn is None:
        return {"erro": "sem conexão"} #if connection fails, return an error message #se a conexão falhar, retornar uma mensagem de erro
    

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empresas_buscas")  #fetch from this table, to get Busca_id and empresa_id, this will be important at future to do a query and display the search results #buscar nesta tabela, para obter Busca_id e empresa_id, isso será importante no futuro para fazer uma consulta e exibir os resultados da busca

        resultado = cursor.fetchall()

        return {"buscas": resultado}

    except Exception as e:
        print(f"❌ Erro: {e}") #if some error occurs during the get on empresas_buscas, print the error and return an error message #se ocorrer algum erro durante a obtenção em empresas_buscas, imprimir o erro e retornar uma mensagem de erro]

        return {"erro": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()