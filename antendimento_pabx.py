import streamlit as st
import streamlit.components.v1 as components
import time
import requests
from bs4 import BeautifulSoup
import unicodedata

# Injeta CSS customizado
st.markdown("""
<style>
/* Badge cores customizadas */
.badge {
    color: white !important;
    padding: 0.25em 0.5em;
    border-radius: 0.25rem;
    font-weight: bold;
}

/* Cores estilo Tailwind */
.bg-purple-700 { background-color: #6f42c1 !important; }
.bg-yellow-500 { background-color: #eab308 !important; }
.bg-green-500  { background-color: #22c55e !important; }
.bg-red-500    { background-color: #ef4444 !important; }
.bg-indigo-500 { background-color: #6366f1 !important; }
.bg-blue-500   { background-color: #3b82f6 !important; }
.bg-gray-500   { background-color: #6b7280 !important; }
.bg-cyan-400   { background-color: #22d3ee !important; }

/* Preto puro */
.bg-black { 
    background-color: #000000 !important; 
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

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
                elif any(x in td_text for x in ["tocando", "Tocando", "ringing", "chamando"]):
                    status_final = "tocando"
                elif any(x in td_text for x in ["ocupado", "falando", "chamada", "tocar", "ringi", "busy"]):
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
    # Mapeamento de status para cores do Bootstrap ou customizadas
    cores = {
        "livre": "success",
        "tocando": "orange-500",  #  tocando
        "ocupado": "danger",
        "em pausa": "warning",  # classe customizada 
        "offline": "secondary"     # exemplo de status extra
    }

    # CSS customizado para cores que não existem no Bootstrap
    css_custom = """
<style>
.bg-purple-700 { background-color: #6f42c1 !important; color: white !important; }
.text-purple-700 { color: #6f42c1 !important; }

/* ORANGE */
.bg-orange-500 { background-color: #fd7e14 !important; color: white !important; }
.text-orange-500 { color: #fd7e14 !important; }

/* ANIMAÇÃO PISCANDO */
@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0.3; }
  100% { opacity: 1; }
}

.blink {
  animation: blink 1s infinite;
}
</style>
"""
    
    html = f"""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    {css_custom}
    <div class="container-fluid">
      <h1 class="text-center mb-4">Monitoramento de Atendimento</h1>
      <table class="table table-striped table-hover table-bordered align-middle">
        <thead class="table-primary">
          <tr><th>Agente <i class="bi bi-person-circle"></i></th>
              <th style="width:170px;">Status <i class="bi bi-info-circle"></i></th></tr>
        </thead>
        <tbody>
    """

    for nome, status in agentes:
        cor = cores.get(status, "secondary")

        # Escolhe o ícone e a cor do ícone
        if status == "livre": icone = f'<i class="bi bi-check-circle-fill text-{cor} me-1"></i>'
        elif status == "ocupado": icone = f'<i class="bi bi-x-circle-fill text-{cor} me-1"></i>'
        elif status == "em pausa": icone = f'<i class="bi bi-pause-circle-fill text-{cor} me-1"></i>'
        else: icone = f'<i class="bi bi-circle-fill text-{cor} me-1"></i>'

        badge = f'<span class="badge bg-{cor} text-capitalize d-inline-flex align-items-center justify-content-center" style="width:120px; height:40px; font-size:16px; border-radius:8px;">{status}</span>'
        html += f"<tr><td>{nome}</td><td>{icone} {badge}</td></tr>"

    html += "</tbody></table></div>"
    return html
    

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
