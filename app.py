import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def carregar_base_por_cert(cert):
    arquivos = {
        "developer": "base_developer.txt",
        "saa": "base_saa.txt",
        "sap": "base_sap.txt",
        "clf": "base_clf.txt",
        "aip": "base_aip.txt"
    }
    caminho = arquivos.get(cert.lower(), "base_clf.txt")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Sem base para essa certificação."

def gerar_questao(certificacao):
    base = carregar_base_por_cert(certificacao)
    prompt = f"""
Você é um gerador de questões no estilo AWS {certificacao}. Baseie-se nas questões abaixo:

{base}

Agora gere uma nova questão original:
- Com cenário
- 4 alternativas (A-D)
- Sem resposta, sem explicação
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

st.title("Gerador de Questões AWS")
cert = st.selectbox("Escolha a certificação:", ["developer", "saa", "sap", "clf", "aip"])

if st.button("Gerar questão"):
    questao = gerar_questao(cert)
    st.text_area("Questão gerada", questao, height=300)
