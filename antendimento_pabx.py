import requests
from bs4 import BeautifulSoup
import streamlit as st
import time
import unicodedata

# ===== CONFIGURAÇÃO =====
fila_id = 2812
email = "suporte@interativanet.com.br"
senha = "smk03657"

# URL de login do PABX
login_url = "https://pabx.evence.com.br/login"
monitor_url = "https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,53"

# Função para remover acentos
def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    )

# ===== FUNÇÃO PARA LOGIN =====
def login_pabx():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

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
        raise Exception("Falha ao fazer login no PABX. Verifique email e senha.")

# ===== FUNÇÃO PARA PEGAR STATUS DOS AGENTES =====
def pegar_status(session):
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
            # Pega o nome do agente, removendo "Última chamada" se existir
            nome = colunas[0].get_text(strip=True).split("Última chamada")[0].strip()

            # Captura o status real (o texto do span ou outro elemento)
            span_status = colunas[1].find("span")
            if span_status and span_status.get_text(strip=True):
                status_text = span_status.get_text(strip=True).lower()
            else:
                # Se não tiver span, tenta pegar o texto bruto do td
                status_text = colunas[1].get_text(strip=True).lower()

            # Normaliza acentos
            status = remover_acentos(status_text)

            # Se status não reconhecido, marca como indisponivel
            if status not in ["livre", "ocupado", "em pausa"]:
                status = "indisponivel"

            dados_agentes.append((nome, status))

    return None, dados_agentes

# ===== FUNÇÃO PARA GERAR DASHBOARD =====
def gerar_dashboard(agentes):
    cores = {
        "livre": "success",
        "ocupado": "danger",
        "em pausa": "warning",
        "indisponivel": "secondary"
    }

    html = """
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">

    <div class="container my-4">
      <h1 class="text-center mb-4">Monitoramento de Atendimento</h1>
      <table class="table table-striped table-hover table-bordered align-middle">
        <thead class="table-primary">
          <tr>
            <th>Agente <i class="bi bi-person-circle"></i></th>
            <th style="width:170px;">Status <i class="bi bi-info-circle"></i></th>
          </tr>
        </thead>
        <tbody>
    """

    for nome, status in agentes:
        cor_bootstrap = cores.get(status, "light")

        badge = f"""
        <span class="badge bg-{cor_bootstrap} text-capitalize d-inline-flex align-items-center justify-content-center"
        style="width:120px; height:40px; font-size:16px; border-radius:8px;">
        {status}
        </span>
        """

        icone_status = ""
        if status == "livre":
            icone_status = '<i class="bi bi-check-circle-fill text-success me-1"></i>'
        elif status == "ocupado":
            icone_status = '<i class="bi bi-x-circle-fill text-danger me-1"></i>'
        elif status == "em pausa":
            icone_status = '<i class="bi bi-pause-circle-fill text-warning me-1"></i>'
        elif status == "indisponivel":
            icone_status = '<i class="bi bi-dash-circle-fill text-secondary me-1"></i>'

        html += f"""
        <tr>
          <td>{nome}</td>
          <td>{icone_status} {badge}</td>
        </tr>
        """

    html += """
        </tbody>
      </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

# ===== LOOP PRINCIPAL =====
try:
    session = login_pabx()
    while True:
        erro, agentes = pegar_status(session)
        if erro:
            st.error(erro)
        else:
            gerar_dashboard(agentes)
        time.sleep(40)
except Exception as e:
    st.error(f"{str(e)}")
