import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Gerador de Questões AWS", layout="centered")

st.markdown("## 🚀 Gerador de Questões AWS")
st.markdown("Selecione a certificação desejada, responda a questão e veja seu desempenho ao final.")

if "questoes" not in st.session_state:
    st.session_state.questoes = []
if "respostas" not in st.session_state:
    st.session_state.respostas = []

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
    prompt = f\"\"\"
Você é um gerador de questões no estilo AWS {certificacao}. Baseie-se nas questões abaixo:

{base}

Agora gere uma nova questão original:
- Com cenário
- 4 alternativas (A-D)
- Sem resposta, sem explicação
\"\"\"
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

cert = st.selectbox("📘 Escolha a certificação:", ["developer", "saa", "sap", "clf", "aip"])

if st.button("➕ Gerar nova questão"):
    questao = gerar_questao(cert)
    st.session_state.questoes.append(questao)
    st.session_state.respostas.append("")  # placeholder para resposta

for idx, q in enumerate(st.session_state.questoes):
    st.markdown(f"### Questão {idx + 1}")
    st.text_area("📄 Enunciado e Opções:", value=q, key=f"q_{idx}", height=250, disabled=True)
    st.session_state.respostas[idx] = st.radio(
        "Sua resposta:",
        ["A", "B", "C", "D"],
        key=f"resp_{idx}",
        index=0 if not st.session_state.respostas[idx] else ["A", "B", "C", "D"].index(st.session_state.respostas[idx])
    )

if st.button("✅ Finalizar e Ver Desempenho"):
    st.markdown("---")
    st.markdown("### 🧠 Seu desempenho (avaliação feita via Groq LLM)")
    for idx, q in enumerate(st.session_state.questoes):
        eval_prompt = f\"\"\"
Você é um avaliador de questões AWS.

Pergunta:
{q}

Resposta do usuário: {st.session_state.respostas[idx]}

1. Informe se a resposta está correta ou incorreta.
2. Identifique a alternativa correta.
3. Explique tecnicamente com base nas boas práticas da AWS.
4. Adicione links oficiais no final.
\"\"\"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": eval_prompt}]
        }
        try:
            with httpx.Client() as client:
                response = client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"]
                st.markdown(f"#### Questão {idx + 1}")
                st.markdown(result)
        except Exception as e:
            st.error(f"Erro ao avaliar: {e}")
