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
        /* Fundo Geral: Usa a cor padrão do cliente de e-mail (geralmente branco ou adapta ao tema) */
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
            border-bottom: 2px solid #e0e0e0; 
            padding-bottom: 5px; 
            text-transform: uppercase;
        }
        
        ul { list-style-type: none; padding: 0; margin: 0; }
        
        /* CARTÕES MINIMALISTAS (Sem fundo escuro) */
        li { 
            margin-bottom: 20px; 
            background-color: transparent; /* FUNDO TRANSPARENTE */
            padding: 15px; 
            border: 1px solid #e0e0e0; /* Borda cinza fininha para delimitar */
            border-left: 5px solid #009688; /* A Borda Verde que você gostou */
            border-radius: 4px;
        }
        
        /* Texto dentro do cartão (Escuro para leitura) */
        strong { color: #004d40; font-size: 16px; display: block; margin-bottom: 6px; }
        .resumo { color: #555555; font-size: 14px; display: block; margin-bottom: 12px; line-height: 1.4; }
        
        /* Prazo (Destaque Clean) */
        .prazo { 
            color: #d84315; /* Laranja escuro */
            font-size: 12px; 
            font-weight: bold; 
            text-transform: uppercase; 
            background-color: #fbe9e7; /* Fundo pêssego bem clarinho */
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        /* Botão Acessar */
        a { 
            background-color: #009688;
            color: #ffffff !important;
            text-decoration: none; 
            font-weight: bold; 
            font-size: 12px; 
            float: right; 
            padding: 5px 12px;
            border-radius: 4px;
            margin-top: -5px;
        }
        a:hover { background-color: #00796b; }
        
        /* RODAPÉ */
        .footer { padding: 30px; text-align: center; font-size: 11px; color: #888; margin-top: 40px; border-top: 1px solid #eee; }
    """

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
            <div class="header-content">
                <img src="{LOGO_URL}" alt="HCPA" class="logo">
                <h1 class="title">Sistema Sentinela</h1>
                <div class="subtitle">Serviço de Física Médica e Radioproteção</div>
            </div>
            <div class="header-bar"></div>
            
            <div class="content">
                {conteudo_ia}
            </div>
            
            <div class="footer">
                Hospital de Clínicas de Porto Alegre<br>
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
                html_items += f"<li><a href='{link}'>ACESSAR</a><strong>{titulo}</strong><span class='resumo'>Link direto identificado.</span></li>"
    
    return aplicar_template_profissional(f"<h3>Resultados (Modo Manual)</h3><ul>{html_items}</ul>")

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Inteligência Artificial (Modelo 2.5 Flash)"""
    print("🧠 2. ACIONANDO GEMINI 2.5 FLASH...")
    
    if not texto_bruto: return None

    modelo = "gemini-2.5-flash"
    
    prompt = f"""
    Você é um Assistente do HCPA.
    Analise os dados e encontre oportunidades de Física Médica.
    
    PARA CADA ITEM, ENCONTRE O PRAZO (OBRIGATÓRIO).
    Procure por: "inscrições até", "vencimento", "deadline", "data".
    
    FORMATO HTML (LIMPO):
    Não use <html> ou <body>. Apenas o conteúdo.
    Agrupe por temas (ex: <h3>Editais</h3>).
    
    Use esta estrutura para CADA item:
    <li>
        <a href="LINK_AQUI">ACESSAR ➜</a>
        <strong>TÍTULO_DA_OPORTUNIDADE</strong>
        <span class="resumo">Resumo: (1 linha explicando o objetivo).</span>
        <br>
        <span class="prazo">📅 Prazo: DD/MM/AAAA (ou "Fluxo Contínuo")</span>
    </li>
    
    Se não houver data explícita, use: <span class="prazo">⚠️ Verificar Edital</span>
    
    DADOS:
    {texto_bruto}
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
