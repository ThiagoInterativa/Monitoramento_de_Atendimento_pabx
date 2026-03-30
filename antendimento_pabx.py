import requests
from bs4 import BeautifulSoup
import streamlit as st
import unicodedata

# ===== CONFIGURAÇÃO =====
fila_id = 2812
email = suporte@interativanet.com.br
senha = smk03657

login_url = "https://pabx.evence.com.br/login"
monitor_url = "https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,53"


# ===== FUNÇÃO PARA REMOVER ACENTOS =====
def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    )


# ===== LOGIN =====
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
        raise Exception("Falha ao fazer login no PABX")


# ===== PEGAR STATUS =====
def pegar_status(session):
    response = session.get(monitor_url)

    if response.status_code != 200:
        return f"Erro ao acessar: {response.status_code}", []

    soup = BeautifulSoup(response.text, "html.parser")
    tabela = soup.find("table")

    if not tabela:
        return "Tabela não encontrada", []

    tbody = tabela.find("tbody")
    linhas = tbody.find_all("tr") if tbody else []

    dados_agentes = []

    for linha in linhas:
        colunas = linha.find_all("td")

        if len(colunas) == 3:
            nome = colunas[0].text.strip()
            status_raw = colunas[2].text.strip().lower()
            status = remover_acentos(status_raw)

            if status != "indisponivel":
                dados_agentes.append((nome, status))

    return None, dados_agentes


# ===== DASHBOARD =====
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
            <th>Agente</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
    """

    for nome, status in agentes:
        cor_bootstrap = cores.get(status, "light")

        badge = f"""
        <span class="badge bg-{cor_bootstrap}" style="padding:10px; font-size:14px;">
        {status}
        </span>
        """

        html += f"""
        <tr>
          <td>{nome}</td>
          <td>{badge}</td>
        </tr>
        """

    html += """
        </tbody>
      </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


# ===== EXECUÇÃO =====
st.set_page_config(layout="wide")

try:
    session = login_pabx()
    erro, agentes = pegar_status(session)

    if erro:
        st.error(erro)
    else:
        gerar_dashboard(agentes)

except Exception as e:
    st.error(str(e))
