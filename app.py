import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="🤖 AWS Chatbot de Questões", layout="centered")

st.markdown("""
<style>
.chat-bubble {
    background-color: #262730;
    padding: 1rem;
    border-radius: 1rem;
    margin-bottom: 1rem;
    font-size: 0.95rem;
}
.chat-bubble.user {
    background-color: #3B82F6;
    color: white;
    align-self: flex-end;
}
.chat-bubble.bot {
    background-color: #1F2937;
    color: white;
}
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

CERT_MAP = {
    "Developer Associate": "developer",
    "Architect Associate": "saa",
    "Architect Professional": "sap",
    "Cloud Practitioner": "clf",
    "AI Practitioner": "aip"
}

st.title("🤖 Gerador de Questões AWS em estilo Chat")
st.markdown("Escolha a certificação e gere uma nova questão. Responda diretamente no chat!")

cert_friendly = st.selectbox("📘 Certificação:", list(CERT_MAP.keys()))


def carregar_base_por_cert(cert_id):
    caminho = f"base/base_{cert_id}.txt"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def gerar_questao(certificacao):
    cert_id = CERT_MAP.get(certificacao, "clf")
    base = carregar_base_por_cert(cert_id)
    prompt = f"""
    Você é um especialista em criar questões no estilo da certificação AWS {certificacao}.
    Baseie-se nas questões de referência abaixo:
    
    {base}
    
    Crie uma nova questão:
    - Com contexto prático
    - 4 alternativas (A-D)
    - Sem resposta ou explicação
    Formato:
    Pergunta: ...
    Opções:
    A) ...

    B) ...

    C) ...

    D) ...
    """
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        with httpx.Client() as client:
            response = client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro ao gerar questão: {e}"

if st.button("🧠 Gerar nova questão"):
    questao = gerar_questao(cert_friendly)
    st.session_state.chat_history = [("bot", questao)]

for sender, msg in st.session_state.chat_history:
    bubble_class = "user" if sender == "user" else "bot"
    st.markdown(f'<div class="chat-bubble {bubble_class}">{msg}</div>', unsafe_allow_html=True)

if st.session_state.chat_history and st.session_state.chat_history[-1][0] == "bot":
    resposta = st.radio("Escolha sua resposta:", ["A", "B", "C", "D"], key="resposta")
    if st.button("✅ Enviar Resposta"):
        pergunta = st.session_state.chat_history[-1][1]
        st.session_state.chat_history.append(("user", f"Minha resposta: {resposta}"))

        eval_prompt = f"""
        Você é um avaliador de questões da certificação AWS {cert_friendly}.
        
        Questão:
        {pergunta}
        
        Resposta do aluno: {resposta}
        
        1. A resposta está correta ou incorreta?
        2. Qual é a resposta correta?
        3. Explique por que a resposta correta é a mais adequada.
        4. Inclua links oficiais da AWS no final em Markdown.
        """
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": eval_prompt}]
        }
        try:
            with httpx.Client() as client:
                response = client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                resultado = response.json()["choices"][0]["message"]["content"]
                st.session_state.chat_history.append(("bot", resultado))
        except Exception as e:
            st.session_state.chat_history.append(("bot", f"Erro ao avaliar: {e}"))
