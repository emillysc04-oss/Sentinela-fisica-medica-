import requests

# COLE SUA CHAVE AQUI DENTRO DAS ASPAS
CHAVE = "AIzaSyC5uiHmRvQGf00Qb34qRII2XwuunBRyQ0M"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={CHAVE}"
payload = {"contents": [{"parts": [{"text": "Diga apenas: A chave funcionou!"}]}]}
headers = {'Content-Type': 'application/json'}

print(f"Testando chave: {CHAVE[:5]}...")

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    print("✅ SUCESSO! O Google respondeu:", response.json()['candidates'][0]['content']['parts'][0]['text'])
else:
    print(f"❌ ERRO {response.status_code}: {response.text}")
