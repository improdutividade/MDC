# Arquivos do repositório — Site Pokémon (Streamlit)

Este documento contém **todos os arquivos necessários** prontos para você colar no repositório GitHub e fazer o deploy no Streamlit Cloud.

> **Instruções:** copie cada bloco (entre as linhas `--- arquivo: <nome>` e a próxima seção) para os arquivos correspondentes no repositório.

\--- arquivo: `streamlit_pokemon_server_site.py`

```python
"""
Streamlit site for Pokémon server
Coloque este arquivo na raiz do repositório.
"""

import streamlit as st
from pathlib import Path
import json
import io
import zipfile
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage
import pandas as pd

# -------------------- Config --------------------
DATA_DIR = Path("data")
FILES_DIR = Path("files")
DATA_DIR.mkdir(exist_ok=True)
FILES_DIR.mkdir(exist_ok=True)

NEWS_FILE = DATA_DIR / "news.json"
SUGGESTIONS_FILE = DATA_DIR / "suggestions.json"
SCOREBOARD_FILE = DATA_DIR / "scoreboard.csv"
WHATSAPP_FILE = DATA_DIR / "whatsapp.json"

if not NEWS_FILE.exists():
    NEWS_FILE.write_text(json.dumps([]), encoding='utf-8')
if not SUGGESTIONS_FILE.exists():
    SUGGESTIONS_FILE.write_text(json.dumps([]), encoding='utf-8')
if not WHATSAPP_FILE.exists():
    WHATSAPP_FILE.write_text(json.dumps({"link": "https://chat.whatsapp.com/EXEMPLO"}), encoding='utf-8')

# Admin password and SMTP are pulled from st.secrets
ADMIN_PASSWORD = st.secrets.get("admin_password", "trocar_senha")
SMTP_SERVER = st.secrets.get("smtp_server")
SMTP_PORT = int(st.secrets.get("smtp_port", 587) or 587)
SMTP_USER = st.secrets.get("smtp_user")
SMTP_PASS = st.secrets.get("smtp_pass")
TO_EMAIL = st.secrets.get("to_email", "minezindoscrias2025@gmail.com")

# -------------------- Helpers --------------------

def load_news():
    try:
        return json.loads(NEWS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def save_news(news_list):
    NEWS_FILE.write_text(json.dumps(news_list, ensure_ascii=False, indent=2), encoding='utf-8')


def append_suggestion(sugg):
    try:
        data = json.loads(SUGGESTIONS_FILE.read_text(encoding='utf-8'))
    except Exception:
        data = []
    data.append(sugg)
    SUGGESTIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def send_email(subject, body, to=TO_EMAIL):
    if not (SMTP_SERVER and SMTP_USER and SMTP_PASS):
        return False, "SMTP não configurado"
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True, "E-mail enviado"
    except Exception as e:
        return False, str(e)


def zip_folder_bytes(folder_path: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full = Path(root) / file
                zf.write(full, arcname=str(full.relative_to(folder_path)))
    buffer.seek(0)
    return buffer.read()


def read_file_bytes(file_path: Path) -> bytes:
    return file_path.read_bytes()

# -------------------- UI --------------------

st.set_page_config(page_title="Servidor Pokémon", layout="wide")
st.title("Servidor Pokémon — Site Oficial")

page = st.sidebar.selectbox("Navegar", ["Home", "Notícias", "Downloads", "Sugestões", "Scoreboard", "Admin"])

# WhatsApp
try:
    whatsapp_data = json.loads(WHATSAPP_FILE.read_text(encoding='utf-8'))
    whatsapp_link = whatsapp_data.get("link", "")
except Exception:
    whatsapp_link = ""

st.markdown(f"**Grupo WhatsApp:** [{whatsapp_link}]({whatsapp_link})")

if page == "Home":
    st.header("Bem-vindo")
    st.write("Site oficial do servidor. Use o menu para navegar.")

elif page == "Notícias":
    st.header("Notícias")
    news = load_news()
    if news:
        for item in sorted(news, key=lambda x: x.get('date', ''), reverse=True):
            st.subheader(item.get("title"))
            st.write(item.get("content"))
            st.caption(f"Publicado em {item.get('date')}")
            st.markdown("---")
    else:
        st.info("Nenhuma notícia disponível.")

elif page == "Downloads":
    st.header("Downloads")
    # Rules
    st.subheader("Livro de Regras")
    rules_path = FILES_DIR / "rules.pdf"
    if rules_path.exists():
        st.download_button("Baixar livro de regras", data=read_file_bytes(rules_path), file_name="regras.pdf", mime="application/pdf")
    else:
        st.warning("rules.pdf não encontrado em files/")

    # Mods
    st.subheader("Mods")
    mods_path = FILES_DIR / "mods"
    if mods_path.exists() and any(mods_path.iterdir()):
        st.download_button("Baixar mods (zip)", data=zip_folder_bytes(mods_path), file_name="mods.zip", mime="application/zip")
    else:
        st.warning("Pasta files/mods vazia ou ausente.")

    # Resourcepacks
    st.subheader("Resourcepacks")
    rp_path = FILES_DIR / "resourcepacks"
    if rp_path.exists() and any(rp_path.iterdir()):
        st.download_button("Baixar resourcepacks (zip)", data=zip_folder_bytes(rp_path), file_name="resourcepacks.zip", mime="application/zip")
    else:
        st.warning("Pasta files/resourcepacks vazia ou ausente.")

elif page == "Sugestões":
    st.header("Enviar sugestão")
    name = st.text_input("Seu nome (opcional)")
    content = st.text_area("Sugestão")
    anon = st.checkbox("Enviar anonimamente", value=False)
    if st.button("Enviar"):
        if not content.strip():
            st.error("Digite algo antes de enviar.")
        else:
            suggestion = {
                "name": "Anonimo" if anon else (name or "Sem nome"),
                "content": content,
                "date": datetime.utcnow().isoformat()
            }
            append_suggestion(suggestion)
            sent, msg = send_email(f"Sugestão - {suggestion['name']}", f"Sugestão: {suggestion['content']}\n\nEnviado em: {suggestion['date']}")
            if sent:
                st.success("Sugestão salva e e-mail enviado.")
            else:
                st.warning(f"Sugestão salva, mas e-mail não enviado: {msg}")

elif page == "Scoreboard":
    st.header("Scoreboard")
    if SCOREBOARD_FILE.exists():
        try:
            df = pd.read_csv(SCOREBOARD_FILE)
        except Exception:
            df = pd.read_csv(SCOREBOARD_FILE, sep=';')
        st.subheader("Tabela")
        st.dataframe(df)
        metric = st.selectbox("Ordenar por", [col for col in ["economy","wins","gym_wins"] if col in df.columns])
        topn = st.number_input("Top N", min_value=1, max_value=500, value=10)
        asc = st.checkbox("Ascendente", value=False)
        df_sorted = df.sort_values(by=metric, ascending=asc)
        st.table(df_sorted.head(topn))
    else:
        st.info("Nenhum scoreboard carregado. Faça upload na aba Admin.")
        st.markdown("**Formato esperado:** player_id,player_name,economy,wins,gym_wins")

elif page == "Admin":
    st.header("Admin")
    pwd = st.text_input("Senha admin", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Digite a senha correta.")
        st.stop()
    st.success("Acesso permitido")

    # Notícias
    st.subheader("Adicionar notícia")
    with st.form("news_form"):
        ntitle = st.text_input("Título")
        ncontent = st.text_area("Conteúdo")
        addn = st.form_submit_button("Adicionar")
    if addn:
        news = load_news()
        news.append({"title": ntitle, "content": ncontent, "date": datetime.utcnow().isoformat()})
        save_news(news)
        st.success("Notícia adicionada")

    # Upload rules
    st.subheader("Upload de arquivos de download")
    up_rules = st.file_uploader("Enviar rules.pdf", type=["pdf"])    
    if up_rules is not None:
        (FILES_DIR / "rules.pdf").write_bytes(up_rules.read())
        st.success("rules.pdf salvo")

    up_mods = st.file_uploader("Enviar mods (zip)", type=["zip"])    
    if up_mods is not None:
        z = zipfile.ZipFile(io.BytesIO(up_mods.read()))
        mods_dir = FILES_DIR / "mods"
        if mods_dir.exists():
            for f in mods_dir.glob("**/*"):
                if f.is_file():
                    f.unlink()
        else:
            mods_dir.mkdir(parents=True, exist_ok=True)
        z.extractall(mods_dir)
        st.success("Mods enviados e extraídos")

    up_rp = st.file_uploader("Enviar resourcepacks (zip)", type=["zip"])    
    if up_rp is not None:
        z = zipfile.ZipFile(io.BytesIO(up_rp.read()))
        rp_dir = FILES_DIR / "resourcepacks"
        if rp_dir.exists():
            for f in rp_dir.glob("**/*"):
                if f.is_file():
                    f.unlink()
        else:
            rp_dir.mkdir(parents=True, exist_ok=True)
        z.extractall(rp_dir)
        st.success("Resourcepacks enviados e extraídos")

    # Whatsapp link
    st.subheader("WhatsApp")
    wa = st.text_input("Link do WhatsApp", value=whatsapp_link)
    if st.button("Salvar WhatsApp"):
        WHATSAPP_FILE.write_text(json.dumps({"link": wa}), encoding='utf-8')
        st.success("Link salvo")

    # Scoreboard CSV
    st.subheader("Upload scoreboard.csv")
    up_csv = st.file_uploader("Enviar scoreboard.csv", type=["csv"])    
    if up_csv is not None:
        SCOREBOARD_FILE.write_bytes(up_csv.read())
        st.success("Scoreboard salvo")

    # Ver sugestões
    st.subheader("Sugestões")
    try:
        suggestions = json.loads(SUGGESTIONS_FILE.read_text(encoding='utf-8'))
    except Exception:
        suggestions = []
    for s in suggestions[::-1]:
        st.write(f"**{s.get('name')}** — {s.get('date')}")
        st.write(s.get('content'))
        st.markdown("---")

    # Test send
    st.subheader("Enviar e-mail de teste")
    ts = st.text_input("Assunto", value="Teste")
    tb = st.text_area("Corpo", value="Teste de envio")
    if st.button("Enviar teste"):
        ok, m = send_email(ts, tb)
        if ok:
            st.success("E-mail enviado")
        else:
            st.error(f"Erro: {m}")

st.markdown("---")
st.caption("Aplicativo Streamlit — ajuste st.secrets antes do deploy.")
```

\--- arquivo: `requirements.txt`

```
streamlit>=1.20.0
pandas
```

\--- arquivo: `.gitignore`

```
__pycache__/
data/
files/
.env
*.pyc
.DS_Store
```

\--- arquivo: `.streamlit/secrets.toml (EXEMPLO)`

```
# Não faça commit deste arquivo com dados reais!
admin_password = "SUA_SENHA_FORTE"

# SMTP (opcional) — use app password se for Gmail
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "seu@email.com"
smtp_pass = "SUA_SENHA_OU_APP_PASSWORD"
to_email = "minezindoscrias2025@gmail.com"
```

\--- arquivo: `README.md`

```markdown
# Site do Servidor Pokémon (Streamlit)

Site simples para gerenciar notícias, downloads, sugestões e scoreboard do servidor.

## Estrutura
- `streamlit_pokemon_server_site.py` — arquivo principal (app Streamlit)
- `requirements.txt` — dependências
- `files/` — arquivos públicos: `rules.pdf`, `mods/`, `resourcepacks/` (o admin também pode enviar via UI)
- `data/` — criado automaticamente para armazenar `news.json`, `suggestions.json`, `scoreboard.csv` e `whatsapp.json`

## Deploy no Streamlit Cloud
1. Crie repositório no GitHub e envie os arquivos.
2. Em [share.streamlit.io](https://share.streamlit.io) conecte a conta GitHub e faça deploy apontando para `streamlit_pokemon_server_site.py`.
3. Configure Secrets (Settings → Secrets) com as chaves do arquivo `.streamlit/secrets.toml` (não suba esse arquivo com valores reais ao GitHub).

## Configuração importante
- Alterar `admin_password` em `st.secrets` para evitar acesso público às funções de admin.
- Se quiser que sugestões enviem e-mail, configure SMTP nas `secrets`.

## Formato do scoreboard
CSV com colunas:
```

player\_id,player\_name,economy,wins,gym\_wins

```

## Observações
- Downloads são servidos com `st.download_button`, que inicia o download direto (sem redirecionamento).
- O app salva dados em arquivos locais no diretório `data/`. No Streamlit Cloud esses arquivos persistem entre execuções do mesmo deploy (para o app hospedado), mas não são um substituto para um banco de dados caso precise de alta confiabilidade.

---

```

\--- arquivo: `EXTRA_NOTAS.md`

```markdown
Dicas e próximos passos:
- Se desejar autenticação sólida, trocar a proteção por OAuth (Discord, Google) em vez de senha simples.
- Se quiser hospedar arquivos grandes (mods/resourcepacks), recomendo usar um serviço de storage (Git LFS, S3, Google Drive) e disponibilizar links no app em vez de manter arquivos pesados no repo.
- Para integrações automáticas com o servidor do jogo (ex.: atualizar scoreboard a partir do banco do servidor), considere criar uma rota API (FastAPI) que seja alimentada pelo servidor de jogo e ler essa API no Streamlit.
```
