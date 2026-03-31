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

def gerar_dashboard_html(agentes):
    # Mapeamento de status para cores do Bootstrap ou customizadas
    cores = {
        "livre": "success",
        "tocando": "orange-500",
        "ocupado": "danger",
        "em pausa": "warning",
        "offline": "secondary"
    }

    # CSS customizado
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

    # ✅ LOOP CORRETO (apenas um for)
    for nome, status in agentes:
        cor = cores.get(status, "secondary")

        # Ícone
        if status == "livre":
            icone = f'<i class="bi bi-check-circle-fill text-{cor} me-1"></i>'
        elif status == "ocupado":
            icone = f'<i class="bi bi-x-circle-fill text-{cor} me-1"></i>'
        elif status == "em pausa":
            icone = f'<i class="bi bi-pause-circle-fill text-{cor} me-1"></i>'
        elif status == "tocando":
            icone = f'<i class="bi bi-telephone-inbound-fill text-{cor} me-1 blink"></i>'
        else:
            icone = f'<i class="bi bi-circle-fill text-{cor} me-1"></i>'

        # Badge (com animação no tocando)
        if status == "tocando":
            badge = f'<span class="badge bg-{cor} blink text-capitalize d-inline-flex align-items-center justify-content-center" style="width:120px; height:40px; font-size:16px; border-radius:8px;">{status}</span>'
        else:
            badge = f'<span class="badge bg-{cor} text-capitalize d-inline-flex align-items-center justify-content-center" style="width:120px; height:40px; font-size:16px; border-radius:8px;">{status}</span>'

        html += f"<tr><td>{nome}</td><td>{icone} {badge}</td></tr>"

    # ✅ FORA do loop
    html += "</tbody></table></div>"
    return html


