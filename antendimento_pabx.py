import streamlit as st
import streamlit.components.v1 as components
import time
import requests
from bs4 import BeautifulSoup
import unicodedata

# Configuração da página (Opcional, mas ajuda no layout)
st.set_page_config(layout="wide")

# URL de login do PABX
login_url = "https://pabx.evence.com.br/login"
monitor_url = "https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,53"

# ===== CONFIGURAÇÃO =====
fila_id = 2812
email = "suporte@interativanet.com.br"
senha = "smk03657

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

                if "livre" in td_text:
                    status = "livre"
                elif "ocupado" in td_text:
                    status = "ocupado"
                elif "pausa" in td_text:
                    status = "em pausa"
                else:
                    status = "indisponivel"

                dados_agentes.append((nome, status))

        return None, dados_agentes
    except Exception as e:
        return f"Erro na requisição: {str(e)}", []

# ===== FUNÇÃO PARA GERAR DASHBOARD (Retorna a string completa) =====
def gerar_dashboard_html(agentes):
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
    </style>

    <div class="container-fluid">
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
    return html

# ===== LOOP PRINCIPAL =====
placeholder = st.empty()

try:
    if 'session_pabx' not in st.session_state:
        st.session_state.session_pabx = login_pabx()

    while True:
        # CORREÇÃO: Removido o ".session_state" duplicado que causava erro
        erro, agentes = pegar_status(st.session_state.session_pabx)
        
        with placeholder.container():
            if erro:
                st.error(erro)
                # Tenta logar novamente se a sessão expirar
                if "401" in erro or "acessar" in erro:
                    st.session_state.session_pabx = login_pabx()
            elif agentes:
                html_final = gerar_dashboard_html(agentes)
                components.html(html_final, height=800, scrolling=True)
            else:
                st.warning("Nenhum dado de agente encontrado.")
        
        time.sleep(40)

except Exception as e:
    st.error(f"Erro crítico: {str(e)}")
