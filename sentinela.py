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
# ✅ MODO SEGURO: Puxa a chave dos Secrets do GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_APP = os.getenv("SENHA_APP", "").strip()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# Link do Logo
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3063/3063176.png"

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
    """Envelopa o texto da IA no design bonito (Dark Mode)"""
    
    if not conteudo_ia:
        conteudo_ia = "<p style='text-align:center; color:#777;'>Nenhuma oportunidade relevante encontrada hoje.</p>"

    # --- CORREÇÃO: CSS em variável separada para não dar erro de sintaxe ---
    estilos_css = """
        body { margin: 0; padding: 0; background-color: #121212; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; background-color: #1e1e1e; color: #e0e0e0; }
        .header-bar { height: 5px; background-color: #009688; width: 100%; }
        .header-content { padding: 30px 20px; text-align: center; border-bottom: 1px solid #333; }
        .logo { max-width: 120px; margin-bottom: 15px; }
        .title { color: #4db6ac; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px; }
        .subtitle { color: #888; font-size: 14px; margin-top: 5px; }
        .content { padding: 30px 20px; line-height: 1.6; }
        h3 { color: #80cbc4; border-bottom: 1px solid #333; padding-bottom: 8px; margin-top: 25px; font-size: 18px; }
        ul { padding-left: 20px; margin-bottom: 20px; }
        li { margin-bottom: 15px; color: #ccc; }
        strong { color: #fff; }
        a { color: #4fc3f7; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #333; background-color: #181818; }
    """

    # Agora montamos o HTML injetando o CSS e as variáveis
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        {estilos_css}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header-bar"></div>
            
            <div class="header-content">
                <img src="{LOGO_URL}" alt="Logo Física Médica" class="logo">
                <h1 class="title">Sistema Sentinela</h1>
                <div class="subtitle">Monitoramento de Editais e Pesquisa</div>
            </div>
            
            <div class="content">
                {conteudo_ia}
            </div>
            
            <div class="footer">
                Hospital de Clínicas de Porto Alegre<br>
                Serviço de Física Médica e Radioproteção<br>
                Gerado automaticamente via Inteligência Artificial
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def gerar_html_manual(texto_bruto):
    """Backup manual"""
    print("⚠️ Usando formatador manual...")
    linhas = texto_bruto.split("- Título: ")
    html_items = ""
    for item in linhas:
        if "Link: " in item:
            partes = item.split("\n")
            titulo = partes[0].strip()
            link = ""
            for p in partes:
                if "Link: " in p: link = p.replace("Link: ", "").strip()
            if link:
                html_items += f"<li><strong><a href='{link}'>{titulo}</a></strong></li>"
    
    return aplicar_template_profissional(f"<h3>Resultados (Modo Manual)</h3><ul>{html_items}</ul>")

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Inteligência Artificial (Modelo 2.5 Flash)"""
    print("🧠 2. ACIONANDO GEMINI 2.5 FLASH...")
    
    if not texto_bruto: return None

    # Modelo descoberto via teste
    modelo = "gemini-2.5-flash"
    
    prompt = f"""
    Você é um sistema extrator de dados para Física Médica.
    Analise a lista abaixo e extraia as oportunidades.
    
    IMPORTANTE SOBRE A FORMATAÇÃO:
    1. Retorne APENAS o código HTML das categorias e itens.
    2. NÃO inclua tags <html>, <head>, <body>.
    3. NÃO inclua saudações como "Prezado colega" ou "Atenciosamente".
    4. NÃO coloque título principal (já tenho no template).
    
    ESTRUTURA DESEJADA:
    - Use <h3> para o nome da categoria (ex: <h3>Chamamentos e Bolsas</h3>).
    - Use <ul> para a lista de itens.
    - Em cada <li>, coloque o título em negrito (<strong>) e link no final.
    
    DADOS: {texto_bruto}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("   ✅ SUCESSO! A IA gerou o conteúdo.")
            resultado = response.json()
            texto_cru_ia = resultado['candidates'][0]['content']['parts'][0]['text']
            
            # Limpa marcadores
            texto_limpo = texto_cru_ia.replace("```html", "").replace("```", "")
            
            # Aplica o layout
            return aplicar_template_profissional(texto_limpo)
        else:
            print(f"   ❌ Erro na API ({response.status_code}): {response.text}")
            return gerar_html_manual(texto_bruto)

    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
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
