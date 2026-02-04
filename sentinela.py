import requests
import json

# COLE SUA CHAVE AQUI DENTRO
CHAVE = "COLE_SUA_CHAVE_AQUI"

print(f"🔍 Consultando 'cardápio' de modelos para a chave: {CHAVE[:5]}...\n")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={CHAVE}"

try:
    response = requests.get(url)
    
    if response.status_code == 200:
        dados = response.json()
        modelos = dados.get('models', [])
        
        if not modelos:
            print("❌ LISTA VAZIA! A API está ativada, mas nenhum modelo foi liberado para essa conta.")
            print("👉 Solução: Você precisa ativar o 'Google AI Studio' ou aceitar os termos de uso na conta.")
        else:
            print("✅ SUCESSO! Modelos disponíveis para você:")
            print("="*40)
            encontrou_algum = False
            for m in modelos:
                # Filtra só os que geram texto (ignora os de apenas visão/embedding)
                if "generateContent" in m.get('supportedGenerationMethods', []):
                    print(f"🟢 {m['name']}")
                    encontrou_algum = True
            
            if not encontrou_algum:
                print("⚠️ AVISO: Existem modelos, mas nenhum serve para gerar texto (chat).")
            print("="*40)

    else:
        print(f"❌ ERRO AO LISTAR ({response.status_code}):")
        print(response.text)

except Exception as e:
    print(f"❌ ERRO DE CONEXÃO: {e}")
