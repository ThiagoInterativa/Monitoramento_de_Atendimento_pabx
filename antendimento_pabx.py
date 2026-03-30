import streamlit as st
import streamlit.components.v1 as components
import time
import requests
from bs4 import BeautifulSoup
import unicodedata

# Configuração da página
st.set_page_config(layout="wide")

# URL de login e monitoramento (Mantido original)
login_url = "https://pabx.evence.com.br/login"
monitor_url = "https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,53"

# --- Credenciais ---
fila_id = 2812
email = "suporte@interativanet.com.br"
senha = "smk03657"


def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    )

def login_pabx():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = session.get(login_url)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_token = soup.find("input", {"name": "_token"})["value"]
        payload = {"login": email, "senha": senha, "_token": csrf_token}
        response = session.post(login_url, data=payload)
        return session if response.url != login_url else None
    except:
        return None

def pegar_status(session):
    try:
        response = session.get(monitor_url)
        if response.status_code != 200:
            return f"Erro {response.status_code}", []

        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table")
        if not tabela: return "Tabela não encontrada", []

        tbody = tabela.find("tbody")
        linhas = tbody.find_all("tr") if tbody else []
        dados_agentes = []

        for linha in linhas:
            colunas = linha.find_all("td")
            if len(colunas) >= 2:
                # Limpeza do nome do agente
                nome_bruto = colunas[0].get_text(strip=True).split("Última chamada")[0].strip()
                
                # Captura o texto do status das colunas possíveis (2 ou 3)
                # O strip=True é vital aqui para ignorar células que parecem vazias mas têm espaços
                status_raw_1 = colunas[1].get_text(strip=True).lower()
                status_raw_2 = colunas[2].get_text(strip=True).lower() if len(colunas) >= 3 else ""
                
                # Unifica os textos encontrados para busca
                td_text = remover_acentos(status_raw_1 + " " + status_raw_2)

                # --- LÓGICA DE FILTRAGEM ULTRA-RESTRITA ---
                status_final = None 

                # Só entra no dashboard se houver uma palavra-chave de atividade real
                if "pausa" in td_text:
                    status_final = "em pausa"
                elif any(x in td_text for x in ["ocupado", "falando", "chamada", "toca", "ringing", "busy"]):
                    status_final = "ocupado"
                elif any(x in td_text for x in ["livre", "disponivel", "dispo", "ready", "online"]):
                    # SEGUNDA VALIDAÇÃO: Se o texto for "indisponivel", anula o "livre"
                    if "indisponivel" not in td_text and "offline" not in td_text:
                        status_final = "livre"

                # FUNCIONALIDADE: SÓ ADICIONA SE FOR UM STATUS ATIVO (Livre, Ocupado ou Pausa)
                # Se status_final for None, Matheus, Ramon e Thiago não aparecerão.
                if status_final and len(nome_bruto) > 2:
                    dados_agentes.append((nome_bruto, status_final))

        return None, dados_agentes
    except Exception as e:
        return f"Erro: {str(e)}", []

def gerar_dashboard_html(agentes):
    cores = {
        "livre": "success",
        "ocupado": "danger",
        "em pausa": "purple-700"  # classe customizada
    }
    
    html = """
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <div class="container-fluid">
      <h1 class="text-center mb-4">Monitoramento de Atendimento</h1>
      <table class="table table-striped table-hover table-bordered align-middle">
        <thead class="table-primary">
          <tr><th>Agente <i class="bi bi-person-circle"></i></th><th style="width:170px;">Status <i class="bi bi-info-circle"></i></th></tr>
        </thead>
        <tbody>
    """
    for nome, status in agentes:
        cor = cores.get(status, "secondary")
        icone = ""
        if status == "livre": icone = '<i class="bi bi-check-circle-fill text-success me-1"></i>'
        elif status == "ocupado": icone = '<i class="bi bi-x-circle-fill text-danger me-1"></i>'
        elif status == "em pausa": icone = '<i class="bi bi-pause-circle-fill text-warning me-1"></i>'
        
        badge = f'<span class="badge bg-{cor} text-capitalize d-inline-flex align-items-center justify-content-center" style="width:120px; height:40px; font-size:16px; border-radius:8px;">{status}</span>'
        html += f"<tr><td>{nome}</td><td>{icone} {badge}</td></tr>"

    return html + "</tbody></table></div>"

# LOOP PRINCIPAL
placeholder = st.empty()

if 'session_pabx' not in st.session_state:
    st.session_state.session_pabx = login_pabx()

if st.session_state.session_pabx:
    while True:
        erro, agentes = pegar_status(st.session_state.session_pabx)
        with placeholder.container():
            if erro:
                st.error(erro)
                st.session_state.session_pabx = login_pabx()
            elif agentes:
                components.html(gerar_dashboard_html(agentes), height=800, scrolling=True)
            else:
                st.warning("Todos os técnicos estão indisponíveis no momento.")
        time.sleep(40)
else:
    st.error("Falha no login.")
