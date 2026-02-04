import os
import json
import requests
import smtplib
import time
import gspread
from google import genai # Nova biblioteca
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÕES ---
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_APP = os.getenv("SENHA_APP", "").strip()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

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
    
    # Blocos de 8
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
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Erro num bloco: {e}")

    print(f"✅ Busca concluída. {len(resultados_texto)} itens para análise.\n")
    return "\n".join(resultados_texto)

def gerar_html_manual(texto_bruto):
    """PARAQUEDAS: HTML manual se a IA falhar"""
    print("⚠️ Usando formatador manual de emergência...")
    if not texto_bruto: return "<p>Nenhum resultado encontrado.</p>"
    
    linhas = texto_bruto.split("- Título: ")
    html = "<h2>☢️ Sentinela: Relatório (Modo Manual)</h2><p>Links encontrados:</p><ul>"
    
    count = 0
    for item in linhas:
        if "Link: " in item:
            partes = item.split("\n")
            titulo = partes[0].strip()
            link = ""
            snippet = ""
            for p in partes:
                if "Link: " in p: link = p.replace("Link: ", "").strip()
                if "Snippet: " in p: snippet = p.replace("Snippet: ", "").strip()
            
            if link:
                html += f"<li style='margin-bottom:10px;'><a href='{link}'><b>{titulo}</b></a><br><small>{snippet}</small></li>"
                count += 1
    
    html += "</ul>"
    if count == 0: return None
    return html

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Gemini (NOVA BIBLIOTECA) formata e resume"""
    print("🧠 2. ACIONANDO GEMINI (SDK NOVO)...")
    
    if not texto_bruto: return None

    try:
        # --- AQUI ESTÁ A MUDANÇA PARA A NOVA BIBLIOTECA ---
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        Você é um Editor de Conteúdo Científico (Física Médica).
        Organize estes links em um e-mail HTML limpo.
        
        DADOS:
        {texto_bruto}
        
        SAÍDA:
        Apenas código HTML (body). Título <h2>Sentinela: Oportunidades</h2>.
        Use listas <ul>. Destaque prazos.
        """

        # Usando o modelo Flash no novo sistema
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        return response.text.replace("```html", "").replace("```", "")

    except Exception as e:
        print(f"❌ Erro na IA: {e}")
        return gerar_html_manual(texto_bruto)

def obter_lista_emails():
    """Etapa Extra: Pega os e-mails da Planilha"""
    print("📋 Lendo lista de contatos da COLUNA 3...")
    
    lista_final = []
    if EMAIL_REMETENTE: lista_final.append(EMAIL_REMETENTE)

    if not GOOGLE_CREDENTIALS:
        return lista_final

    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open("Sentinela Emails")
        ws = sh.sheet1
        
        emails_raw = ws.col_values(3)
        
        for e in emails_raw:
            email_limpo = e.strip()
            if "@" in email_limpo and "email" not in email_limpo.lower():
                if email_limpo not in lista_final:
                    lista_final.append(email_limpo)
        
        print(f"✅ Destinatários válidos: {len(lista_final)}")
        return lista_final
        
    except Exception as e:
        print(f"❌ Erro na planilha: {e}")
        return lista_final

def enviar_email(corpo_html, destinatario):
    """Etapa 3: Dispara o e-mail"""
    if not destinatario: return

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
    dados = buscar_google_elite()
    relatorio = analisar_com_gemini(dados)
    
    if relatorio:
        lista_vip = obter_lista_emails()
        print(f"\n📧 Iniciando disparos para {len(lista_vip)} pessoas...")
        for email in lista_vip:
            enviar_email(relatorio, email)
        print("🏁 FIM.")
    else:
        print("📭 Nada encontrado.")
