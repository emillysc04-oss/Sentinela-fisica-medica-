import os
from googleapiclient.discovery import build

# --- CONFIGURAÇÕES ---
# Pega as chaves que guardamos no "Cofre" do GitHub
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX_ID = os.getenv("SEARCH_ENGINE_ID")

def buscar_oportunidades():
    """
    Função que usa o Google Oficial para buscar editais.
    """
    print("🤖 SENTINELA INICIADO...")
    
    # 1. Verificação de Segurança
    if not API_KEY or not CX_ID:
        print("❌ ERRO CRÍTICO: Chaves de API não encontradas!")
        print("Verifique se 'GOOGLE_SEARCH_API_KEY' e 'SEARCH_ENGINE_ID' estão nos Secrets.")
        return

    try:
        # 2. Conecta no Motor de Busca
        print("🔌 Conectando ao Google Search...")
        service = build("customsearch", "v1", developerKey=API_KEY)
        
        # 3. Faz a busca (Termo genérico apenas para teste de conexão)
        termo_teste = "edital física médica 2026"
        print(f"🔎 Pesquisando por: '{termo_teste}'")
        
        # dateRestrict='w2' significa "últimas 2 semanas"
        res = service.cse().list(
            q=termo_teste, 
            cx=CX_ID, 
            num=5,
            dateRestrict='w2' 
        ).execute()
        
        items = res.get("items", [])
        
        # 4. Mostra o resultado
        if not items:
            print("Mw Aviso: A busca funcionou, mas não retornou resultados (isso é normal em testes).")
        else:
            print(f"✅ SUCESSO! Encontrei {len(items)} resultados na sua Lista VIP:")
            for item in items:
                print(f"   👉 {item.get('title')}")
                print(f"      🔗 {item.get('link')}")
                print("---")

    except Exception as e:
        print(f"❌ ERRO TÉCNICO: {e}")

# --- PONTO DE PARTIDA ---
if __name__ == "__main__":
    buscar_oportunidades()
