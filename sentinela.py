import os
import json
import requests
import smtplib
import time
import gspread
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÕES ---
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Trouxemos de volta!
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# Lista de Sites (42 Fontes)
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
    
    # Blocos de 8 para não engasgar
    tamanho_bloco = 8
    blocos = [SITES_ALVO[i:i + tamanho_bloco] for i in range(0, len(SITES_ALVO), tamanho_bloco)]

    for bloco in blocos:
        filtro_sites = " OR ".join(bloco)
        query_final = f"{query_base} ({filtro_sites})"
        
        # Pede 10 resultados por bloco (qdr:m = último mês)
        payload = json.dumps({"q": query_final, "tbs": "qdr:m", "gl": "br"})
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            dados = response.json()
            items = dados.get("organic", [])
            
            for item in items:
                # Prepara o texto para o Gemini ler
                linha = f"- Título: {item.get('title')}\n  Link: {item.get('link')}\n  Snippet: {item.get('snippet')}\n  Data Google: {item.get('date', 'N/A')}\n"
                resultados_texto.append(linha)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Erro num bloco: {e}")

    print(f"✅ Busca concluída. {len(resultados_texto)} itens para análise.\n")
    return "\n".join(resultados_texto)

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Gemini formata e resume (menos rigoroso)"""
    print("🧠 2. ACIONANDO GEMINI (Modo Editor)...")
    
    if not texto_bruto: return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # PROMPT AJUSTADO: Foco em formatação, não em exclusão.
    prompt = f"""
    Você é um Editor de Conteúdo Científico (Física Médica).
    Abaixo estão resultados de busca vindos de fontes confiáveis.
    
    SUA MISSÃO:
    1. Organize esses links em um e-mail HTML bonito e legível.
    2. NÃO FILTRE RIGOROSAMENTE. A menos que seja um link quebrado ou totalmente nada a ver (ex: política de cookies), MANTENHA O LINK.
    3. Resuma o "Snippet" para explicar do que se trata em 1 linha.
    4. Se houver menção de DATAS ou PRAZOS no texto, destaque em NEGRITO.
    5. Agrupe, se possível (ex: Nacional vs Internacional).
    
    FORMATO DE SAÍDA:
    Apenas o código HTML (body). Use cores sóbrias (azul escuro para links).
    Comece com <h2>☢️ Sentinela: Novas Oportunidades</h2>.
    
    DADOS PARA PROCESSAR:
    {texto_bruto}
    """

    try:
        res = model.generate_content(prompt)
        # Limpa marcadores de código se o Gemini colocar
        return res.text.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"❌ Erro na IA: {e}")
        return None

def obter_lista_emails():
    """Etapa Extra: Pega os e-mails da Planilha"""
    print("📋 Lendo lista de contatos...")
    if not GOOGLE_CREDENTIALS:
        return [EMAIL_REMETENTE]

    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open("Sentinela Emails")
        ws = sh.sheet1
        emails = ws.col_values(1)
        return [e.strip() for e in emails if "@" in e and "email" not in e.lower()]
    except Exception as e:
        print(f"❌ Erro na planilha: {e}")
        return [EMAIL_REMETENTE]

def enviar_email(corpo_html, destinatario):
    """Etapa 3: Dispara o e-mail"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = f"Sentinela Física Médica - {datetime.now().strftime('%d/%m')}"
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        server.quit()
        print(f"   📤 Enviado para: {destinatario}")
    except Exception as e:
        print(f"   ❌ Falha ao enviar para {destinatario}: {e}")

if __name__ == "__main__":
    # 1. Busca
    dados = buscar_google_elite()
    
    # 2. Analisa (com IA suave)
    relatorio = analisar_com_gemini(dados)
    
    if relatorio:
        # 3. Pega lista
        lista_vip = obter_lista_emails()
        
        # 4. Envia
        print(f"\n📧 Enviando para {len(lista_vip)} pessoas...")
        for email in lista_vip:
            enviar_email(relatorio, email)
        print("🏁 FIM.")
    else:
        print("📭 Nada encontrado ou erro na IA.")
