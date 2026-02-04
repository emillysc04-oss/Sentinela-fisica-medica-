import os
import json
import requests
import smtplib
import time
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÕES ---
# ✅ MODO SEGURO
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_APP = os.getenv("SENHA_APP", "").strip()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# 🖼️ SEU LOGO DO GITHUB
LOGO_URL = "https://raw.githubusercontent.com/emillysc04-oss/Sentinela-3.0/main/Logo3.png"

# Lista de Sites
SITES_ALVO = [
    "site:gov.br", "site:edu.br", "site:org.br", "site:b.br",
    "site:fapergs.rs.gov.br", "site:hcpa.edu.br", "site:ufrgs.br", "site:ufcspa.edu.br",
    "site:afimrs.com.br", "site:sgr.org.br", "site:amrigs.org.br",
    "site:fapesc.sc.gov.br", "site:fara.pr.gov.br", "site:fapesp.br",
    "site:iaea.org", "site:who.int", "site:nih.gov", "site:europa.eu", "site:nsf.gov",
    "site:aapm.org", "site:estro.org", "site:astro.org", "site:rsna.org",
    "site:iomp.org", "site:efomp.org", "site:snmmi.org",
    "site:edu", "site:ac.uk", "site:arxiv.org",
    "site:ieee.org", "site:nature.com", "site:science.org", "site:sciencedirect.com",
    "site:iop.org", "site:frontiersin.org", "site:mdpi.com", "site:wiley.com",
    "site:springer.com", "site:thelancet.com",
    "site:einstein.br", "site:hospitalsiriolibanes.org.br", "site:moinhosdevento.org.br"
]

def buscar_google_elite():
    """Etapa 1: Busca os links brutos"""
    print("🚀 1. INICIANDO VARREDURA (SERPER)...")
    
    query_base = '(edital OR chamada OR "call for papers" OR bolsa OR grant) ("física médica" OR radioterapia OR "medical physics")'
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    resultados_texto = []
    tamanho_bloco = 8
    blocos = [SITES_ALVO[i:i + tamanho_bloco] for i in range(0, len(SITES_ALVO), tamanho_bloco)]

    for bloco in blocos:
        filtro_sites = " OR ".join(bloco)
        query_final = f"{query_base} ({filtro_sites})"
        payload = json.dumps({"q": query_final, "tbs": "qdr:m", "gl": "br"})
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            dados = response.json()
            items = dados.get("organic", [])
            for item in items:
                linha = f"- Título: {item.get('title')}\n  Link: {item.get('link')}\n  Snippet: {item.get('snippet')}\n  Data: {item.get('date', 'N/A')}\n"
                resultados_texto.append(linha)
            time.sleep(1.0)
        except Exception as e:
            print(f"❌ Erro num bloco: {e}")

    print(f"✅ Busca concluída. {len(resultados_texto)} itens para análise.\n")
    return "\n".join(resultados_texto)

def aplicar_template_profissional(conteudo_ia):
    """Envelopa o texto: Clean & Minimalist (Sem fundos escuros)"""
    
    if not conteudo_ia:
        conteudo_ia = "<p style='text-align:center; color:#777;'>Nenhuma oportunidade relevante encontrada hoje.</p>"

    estilos_css = """
        /* Fundo Geral: Usa a cor padrão do cliente de e-mail */
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        
        /* CONTAINER: Totalmente invisível */
        .container { 
            max-width: 600px; 
            margin: 0 auto; 
            padding: 10px;
        }
        
        /* CABEÇALHO */
        .header-content { text-align: center; margin-bottom: 30px; }
        .logo { max-width: 180px; margin-bottom: 10px; }
        .title { color: #009688; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
        .subtitle { color: #555; font-size: 13px; margin-top: 5px; letter-spacing: 1px; text-transform: uppercase; }
        
        /* Barra de destaque fina */
        .header-bar { height: 3px; background: linear-gradient(90deg, #004d40 0%, #009688 50%, #80cbc4 100%); width: 100%; border-radius: 4px; margin-bottom: 30px;}
        
        /* Títulos de Seção */
        h3 { 
            color: #00796b; 
            margin-top: 40px; 
            font-size: 18px;
