import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Gerador de Questões AWS", layout="centered")

st.markdown("## 🚀 Gerador de Questões AWS")
st.markdown("Responda cada questão, veja o feedback e finalize para ver seu desempenho geral.")

if "questoes" not in st.session_state:
    st.session_state.questoes = []
if "respostas" not in st.session_state:
    st.session_state.respostas = []
if "avaliacoes" not in st.session_state:
    st.session_state.avaliacoes = []
if "certificacao" not in st.session_state:
    st.session_state.certificacao = "developer"

CERT_MAP = {
    "Developer Associate": "developer",
    "Architect Associate": "saa",
    "Architect Professional": "sap",
    "Cloud Practitioner": "clf",
    "AI Practitioner": "aip"
}

def carregar_base_por_cert(cert_id):
    caminho = f"base/base_{cert_id}.txt"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Sem base para essa certificação."

def gerar_questao(certificacao_friendly):
    cert_id = CERT_MAP.get(certificacao_friendly, "clf")
    base = carregar_base_por_cert(cert_id)
    prompt = f"""
    Você é um especialista em criar questões no estilo da prova oficial AWS {certificacao_friendly}.
    Com base nas questões abaixo (que representam o estilo e conteúdo esperados), crie uma nova questão.
    
    Base de inspiração:
    {base}
    
    Regras:
    - Utilize um cenário realista com linguagem técnica
    - Siga o estilo de múltipla escolha
    - Crie 4 alternativas (A, B, C, D)
    - Não inclua a resposta correta
    - Não adicione explicações, comentários ou links
    - Seja direto e preciso como uma questão de prova
    
    Formato:
    Pergunta:
    [enunciado da questão]
    
    Opções:
    A) ...
    B) ...
    C) ...
    D) ...
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
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
        return f"Erro: {str(e)}"

def avaliar_questao(certificacao_friendly, pergunta, resposta_usuario):
    prompt = f"""
    Você é um avaliador experiente de questões de certificações AWS, como a {certificacao_friendly}.
    Com base na questão abaixo e na resposta fornecida, realize uma análise técnica objetiva.
    
    Questão:
    {pergunta}
    
    Resposta do usuário: {resposta_usuario}
    
    Sua tarefa:
    1. Informe se a resposta está correta ou incorreta.
    2. Aponte qual é a alternativa correta.
    3. Explique tecnicamente por que essa alternativa é a correta, com base nas boas práticas da AWS.
    4. Diga por que as outras alternativas estão incorretas.
    5. Inclua links oficiais da AWS relevantes no final, em Markdown.
    
    Mantenha o estilo formal e direto como esperado em provas oficiais e materiais técnicos.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        with httpx.Client() as client:
            response = client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro ao avaliar: {e}"

st.session_state.certificacao = st.selectbox("📘 Escolha a certificação:", list(CERT_MAP.keys()))

if st.button("➕ Gerar nova questão"):
    questao = gerar_questao(st.session_state.certificacao)
    st.session_state.questoes.append(questao)
    st.session_state.respostas.append(None)
    st.session_state.avaliacoes.append("")

for idx, q in enumerate(st.session_state.questoes):
    st.markdown(f"### Questão {idx + 1}")
    st.text_area("📄 Enunciado e Opções:", value=q, key=f"q_{idx}", height=250, disabled=True)

    resposta = st.radio(
        f"Sua resposta (Q{idx+1}):",
        ["A", "B", "C", "D"],
        index=0 if not st.session_state.respostas[idx] else ["A", "B", "C", "D"].index(st.session_state.respostas[idx]),
        key=f"resp_{idx}"
    )
    if st.button(f"✅ Avaliar Resposta {idx + 1}"):
        st.session_state.respostas[idx] = resposta
        resultado = avaliar_questao(st.session_state.certificacao, q, resposta)
        st.session_state.avaliacoes[idx] = resultado

    if st.session_state.avaliacoes[idx]:
        st.markdown("**🔍 Avaliação:**")
        st.markdown(st.session_state.avaliacoes[idx])

if st.button("📊 Finalizar e Ver Desempenho Geral"):
    st.markdown("---")
    acertos = sum("✔️ Correta" in av or "✅ Correta" in av for av in st.session_state.avaliacoes if av)
    total = len([a for a in st.session_state.avaliacoes if a])
    st.markdown(f"### 🎯 Resultado Final: {acertos}/{total} acertos")
