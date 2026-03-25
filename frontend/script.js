const form = document.getElementById("scrapper-form")
const termo = document.getElementById("termo")
const cidade = document.getElementById("cidade")
const loading = document.getElementById("loading")
const resultado = document.getElementById("resultado") // const resultado = document.getElementById("resultado")

form.addEventListener("submit", function (event) { 
    event.preventDefault() 
    if (termo.value == "" || cidade.value == "") { //verify to not send empty values
        alert("Por favor, preencha todos os campos.");
        return;
    }
   loading.style.display = "block"  // ← mostra o loading

    fetch("http://127.0.0.1:8000/buscar", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        termo: termo.value,
        cidade: cidade.value,
        webhook_url: "https://webhook.site/seu-id-aqui"
    })
})