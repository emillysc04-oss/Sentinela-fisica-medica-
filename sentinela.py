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

# --- CONFIGURAÇÕES ---
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS") # O JSON do robô

# Lista de Sites (Os 42 Guerreiros)
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
    """Etapa 1: Busca os links brutos na internet"""
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
        payload = json.dumps({"q": query_final, "tbs": "qdr:m", "gl": "br"})
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            dados = response.json()
            items = dados.get("organic", [])
            for item in items:
                linha = f"- Título: {item.get('title')}\n  Link: {item.get('link')}\n  Data/Trecho: {item.get('snippet')}\n"
                resultados_texto.append(linha)
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Erro num bloco: {e}")

    print(f"✅ Busca concluída. {len(resultados_texto)} links coletados.\n")
    return "\n".join(resultados_texto)

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Gemini filtra e formata"""
    print("🧠 2. ACIONANDO INTELIGÊNCIA ARTIFICIAL...")
    if not texto_bruto: return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    Você é um Sentinela de Física Médica. Analise estes resultados de busca:
    {texto_bruto}

    MISSÃO:
    1. Ignore notícias velhas ou irrelevantes.
    2. Selecione APENAS oportunidades reais (editais, bolsas, grants, vagas).
    3. Crie um HTML para e-mail. Use <h2> para títulos e listas <ul>.
    4. Se não tiver nada útil, responda apenas "NADA".
    
    Comece direto com o HTML (<h2>Relatório...</h2>).
    """

    try:
        res = model.generate_content(prompt)
        texto = res.text.replace("```html", "").replace("```", "")
        if "NADA" in texto: return None
        return texto
    except:
        return None

def obter_lista_emails():
    """Etapa Extra: Pega os e-mails da Planilha"""
    print("📋 Lendo lista de contatos da Planilha Google...")
    
    if not GOOGLE_CREDENTIALS:
        print("⚠️ Sem credenciais da planilha. Usando apenas e-mail do remetente.")
        return [EMAIL_REMETENTE]

    try:
        # Conecta na planilha usando o JSON do cofre
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        gc = gspread.service_account_from_dict(creds_dict)
        
        # Abre a planilha pelo nome exato
        sh = gc.open("Sentinela Emails")
        ws = sh.sheet1
        
        # Pega a primeira coluna (assumindo que os emails estão na coluna A)
        emails = ws.col_values(1)
        
        # Limpa cabeçalhos e linhas vazias
        lista_limpa = [e.strip() for e in emails if "@" in e and "email" not in e.lower()]
        
        print(f"✅ Lista carregada! {len(lista_limpa)} destinatários encontrados.")
        return lista_limpa
        
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")
        print("   (Verifique se o nome da planilha é 'Sentinela Emails' e se o robô foi convidado)")
        return [EMAIL_REMETENTE]

def enviar_email(corpo_html, destinatario):
    """Etapa 3: Dispara o e-mail"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = f"☢️ Sentinela Física Médica - {datetime.now().strftime('%d/%m')}"
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
    
    # 2. Analisa
    relatorio = analisar_com_gemini(dados)
    
    if relatorio:
        # 3. Pega lista de e-mails
        lista_vip = obter_lista_emails()
        
        # 4. Envia para todos
        print(f"\n📧 Iniciando disparos para {len(lista_vip)} pessoas...")
        for email in lista_vip:
            enviar_email(relatorio, email)
        print("🏁 FIM DO CICLO.")
    else:
        print("📭 Nenhuma oportunidade relevante hoje. E-mails não enviados.")
