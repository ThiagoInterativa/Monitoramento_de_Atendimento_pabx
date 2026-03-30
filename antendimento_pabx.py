import streamlit as st
import streamlit.components.v1 as components
import time
import requests
from bs4 import BeautifulSoup
import unicodedata

# Configuração da página
st.set_page_config(layout="wide", page_title="Monitoramento Helpdesk")

# URL de login do PABX
login_url = "https://pabx.evence.com.br/login"
monitor_url = "https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,53"

# --- Insira suas credenciais aqui ou use st.secrets ---
fila_id = 2812
email = "suporte@interativanet.com.br"
senha = "smk03657"

# Função para remover acentos
def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    )

# ===== FUNÇÃO PARA LOGIN =====
def login_pabx():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        r = session.get(login_url)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_input = soup.find("input", {"name": "_token"})
        csrf_token = csrf_input["value"] if csrf_input else ""

        payload = {
            "login": email,
            "senha": senha,
            "_token": csrf_token
        }

        response = session.post(login_url, data=payload)
        if response.url != login_url:
            return session
        else:
            return None
    except:
        return None

# ===== FUNÇÃO PARA PEGAR STATUS DOS AGENTES =====
def pegar_status(session):
    try:
        response = session.get(monitor_url)
        if response.status_code != 200:
            return f"Erro ao acessar {response.status_code}", []

        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table")

        if not tabela:
            return "Tabela não encontrada ou sem dados", []

        tbody = tabela.find("tbody")
        linhas = tbody.find_all("tr") if tbody else []

        dados_agentes = []

        for linha in linhas:
            colunas = linha.find_all("td")
            if len(colunas) >= 2:
                nome = colunas[0].get_text(strip=True).split("Última chamada")[0].strip()
                td_text = colunas[1].get_text(strip=True).lower()
                td_text = remover_acentos(td_text)

                # Define o status baseado no texto da coluna
                if "livre" in td_text:
                    status = "livre"
                elif "ocupado" in td_text:
                    status = "ocupado"
                elif "pausa" in td_text:
                    status = "em pausa"
                else:
                    status = "indisponivel"

                # REGRA DE NEGÓCIO: Só adiciona se NÃO for indisponível
                if status != "indisponivel":
                    dados_agentes.append((nome, status))

        return None, dados_agentes
    except Exception as e:
        return f"Erro na requisição: {str(e)}", []

# ===== FUNÇÃO PARA GERAR DASHBOARD HTML =====
def gerar_dashboard_html(agentes):
    # Corrigido: Mapeamento da cor 'livre' e 'em pausa'
    cores = {
        "livre": "success",
        "ocupado": "danger",
        "em pausa": "warning",
        "indisponivel": "secondary"
    }

    html = """
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background-color: white; font-family: sans-serif; }
        .table { margin-top: 20px; }
        .badge { width: 130px; height: 35px; font-size: 14px; border-radius: 6px; }
    </style>

    <div class="container-fluid">
      <h2 class="text-center my-3">Monitoramento de Atendimento</h2>
      <table class="table table-striped table-hover table-bordered align-middle">
        <thead class="table-dark">
          <tr>
            <th>Agente <i class="bi bi-person-circle"></i></th>
            <th style="width:200px;">Status <i class="bi bi-info-circle"></i></th>
          </tr>
        </thead>
        <tbody>
    """

    for nome, status in agentes:
        cor_bootstrap = cores.get(status, "light")
        
        icone_status = ""
        if status == "livre":
            icone_status = '<i class="bi bi-check-circle-fill text-success me-2"></i>'
        elif status == "ocupado":
            icone_status = '<i class="bi bi-x-circle-fill text-danger me-2"></i>'
        elif status == "em pausa":
            icone_status = '<i class="bi bi-pause-circle-fill text-warning me-2"></i>'

        html += f"""
        <tr>
          <td style="font-weight: 500;">{nome}</td>
          <td>
            <div class="d-flex align-items-center">
                {icone_status}
                <span class="badge bg-{cor_bootstrap} d-inline-flex align-items-center justify-content-center text-capitalize">
                    {status}
                </span>
            </div>
          </td>
        </tr>
        """

    html += "</tbody></table></div>"
    return html

# ===== INTERFACE E LOOP =====
placeholder = st.empty()

# Inicializa a sessão se não existir
if 'session_pabx' not in st.session_state or st.session_state.session_pabx is None:
    st.session_state.session_pabx = login_pabx()

if st.session_state.session_pabx is None:
    st.error("Não foi possível conectar ao PABX. Verifique as credenciais.")
else:
    while True:
        erro, agentes = pegar_status(st.session_state.session_pabx)
        
        with placeholder.container():
            if erro:
                st.error(f"Tentando reconectar... ({erro})")
                st.session_state.session_pabx = login_pabx()
            elif agentes:
                html_final = gerar_dashboard_html(agentes)
                components.html(html_final, height=600, scrolling=True)
            else:
                st.info("Todos os técnicos estão indisponíveis no momento.")
        
        time.sleep(30) # Atualiza a cada 30 segundos
