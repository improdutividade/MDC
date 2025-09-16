import streamlit as st
import pandas as pd
import os
import json
import zipfile
import io
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ======================
# Configurações iniciais
# ======================

st.set_page_config(page_title="Servidor Pokémon", layout="wide")

FILES_DIR = "files"
DATA_DIR = "data"
NEWS_FILE = os.path.join(DATA_DIR, "news.json")
SUGGESTIONS_FILE = os.path.join(DATA_DIR, "suggestions.json")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# ======================
# Funções auxiliares
# ======================

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_email(subject, body):
    """Tenta enviar email se secrets de SMTP estiverem configurados"""
    try:
        smtp_server = st.secrets["smtp_server"]
        smtp_port = st.secrets["smtp_port"]
        smtp_user = st.secrets["smtp_user"]
        smtp_pass = st.secrets["smtp_pass"]
        to_email = st.secrets["to_email"]

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
    except Exception as e:
        st.warning(f"Não foi possível enviar o e-mail: {e}")


def make_zip_bytes(folder_path):
    """Compacta uma pasta inteira em memória e retorna bytes do zip"""
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                zf.write(full_path, rel_path)
    mem_zip.seek(0)
    return mem_zip


# ======================
# Carregar dados
# ======================

news = load_json(NEWS_FILE, [])
suggestions = load_json(SUGGESTIONS_FILE, [])
whatsapp_link = st.secrets.get("whatsapp_link", "")


# ======================
# Layout principal
# ======================

st.title("🌟 Servidor Pokémon 🌟")

# Link do WhatsApp
if whatsapp_link:
    st.markdown(f"👉 [Grupo do WhatsApp]({whatsapp_link})")


# ======================
# Menu lateral
# ======================

menu = st.sidebar.radio(
    "Navegação",
    ["Notícias", "Regras", "Downloads", "Sugestões", "Scoreboard", "Admin"]
)

# ----------------------
# Notícias
# ----------------------
if menu == "Notícias":
    st.header("📰 Notícias")
    if news:
        for item in reversed(news):
            st.subheader(item["title"])
            st.write(item["content"])
            st.caption(f"Publicado em {item['date']}")
    else:
        st.info("Nenhuma notícia publicada ainda.")

# ----------------------
# Regras
# ----------------------
elif menu == "Regras":
    st.header("📖 Livro de Regras")
    rules_path = os.path.join(FILES_DIR, "rules.pdf")
    if os.path.exists(rules_path):
        with open(rules_path, "rb") as f:
            st.download_button("📥 Baixar Regras", f, file_name="regras.pdf")
    else:
        st.warning("O livro de regras ainda não foi enviado.")

# ----------------------
# Downloads
# ----------------------
elif menu == "Downloads":
    st.header("📦 Downloads")

    # Mods
    mods_path = os.path.join(FILES_DIR, "mods")
    if os.path.exists(mods_path) and os.listdir(mods_path):
        mem_zip = make_zip_bytes(mods_path)
        st.download_button("📥 Baixar Mods", mem_zip, file_name="mods.zip")
    else:
        st.warning("Nenhum mod disponível.")

    # Resourcepacks
    rp_path = os.path.join(FILES_DIR, "resourcepacks")
    if os.path.exists(rp_path) and os.listdir(rp_path):
        mem_zip = make_zip_bytes(rp_path)
        st.download_button("📥 Baixar Resourcepacks", mem_zip, file_name="resourcepacks.zip")
    else:
        st.warning("Nenhum resourcepack disponível.")

# ----------------------
# Sugestões
# ----------------------
elif menu == "Sugestões":
    st.header("💡 Sugestões")
    with st.form("suggestion_form"):
        text = st.text_area("Digite sua sugestão")
        submit = st.form_submit_button("Enviar")
        if submit and text.strip():
            new_suggestion = {
                "text": text.strip(),
                "date": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            suggestions.append(new_suggestion)
            save_json(SUGGESTIONS_FILE, suggestions)
            send_email("Nova sugestão recebida", text.strip())
            st.success("Sugestão enviada com sucesso!")

# ----------------------
# Scoreboard
# ----------------------
elif menu == "Scoreboard":
    st.header("🏆 Scoreboard")
    csv_path = os.path.join(DATA_DIR, "scoreboard.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df)
        metric = st.selectbox("Filtrar por", ["economy", "wins", "gym_wins"])
        top_n = st.slider("Top N", 5, 50, 10)
        top_players = df.sort_values(metric, ascending=False).head(top_n)
        st.subheader(f"Top {top_n} por {metric}")
        st.table(top_players)
    else:
        st.info("Nenhum scoreboard disponível.")

# ----------------------
# Admin
# ----------------------
elif menu == "Admin":
    st.header("🔐 Área Administrativa")
    password = st.text_input("Senha:", type="password")
    correct_password = st.secrets.get("admin_password", "trocar_senha")

    if password == correct_password:
        st.success("Acesso liberado!")

        # Adicionar notícia
        st.subheader("Adicionar notícia")
        with st.form("news_form"):
            title = st.text_input("Título")
            content = st.text_area("Conteúdo")
            submit_news = st.form_submit_button("Publicar")
            if submit_news and title and content:
                news.append({
                    "title": title,
                    "content": content,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                save_json(NEWS_FILE, news)
                st.success("Notícia publicada!")

        # Upload regras
        st.subheader("Enviar livro de regras (PDF)")
        rules_file = st.file_uploader("Upload PDF", type=["pdf"])
        if rules_file:
            with open(os.path.join(FILES_DIR, "rules.pdf"), "wb") as f:
                f.write(rules_file.read())
            st.success("Regras enviadas com sucesso!")

        # Upload mods
        st.subheader("Enviar pasta mods (ZIP)")
        mods_file = st.file_uploader("Upload Mods.zip", type=["zip"])
        if mods_file:
            mods_path = os.path.join(FILES_DIR, "mods")
            os.makedirs(mods_path, exist_ok=True)
            with zipfile.ZipFile(mods_file, "r") as zip_ref:
                zip_ref.extractall(mods_path)
            st.success("Mods atualizados com sucesso!")

        # Upload resourcepacks
        st.subheader("Enviar pasta resourcepacks (ZIP)")
        rp_file = st.file_uploader("Upload Resourcepacks.zip", type=["zip"])
        if rp_file:
            rp_path = os.path.join(FILES_DIR, "resourcepacks")
            os.makedirs(rp_path, exist_ok=True)
            with zipfile.ZipFile(rp_file, "r") as zip_ref:
                zip_ref.extractall(rp_path)
            st.success("Resourcepacks atualizados com sucesso!")

        # Link WhatsApp
        st.subheader("Definir link do WhatsApp")
        new_link = st.text_input("Novo link do WhatsApp", value=whatsapp_link)
        if st.button("Salvar link"):
            st.session_state["whatsapp_link"] = new_link
            st.success("Link atualizado! (adicione no secrets para persistir)")

        # Upload scoreboard
        st.subheader("Enviar scoreboard (CSV)")
        csv_file = st.file_uploader("Upload CSV", type=["csv"])
        if csv_file:
            with open(os.path.join(DATA_DIR, "scoreboard.csv"), "wb") as f:
                f.write(csv_file.read())
            st.success("Scoreboard atualizado!")

        # Visualizar sugestões
        st.subheader("Sugestões recebidas")
        if suggestions:
            for s in reversed(suggestions):
                st.write(f"- {s['text']} ({s['date']})")
        else:
            st.info("Nenhuma sugestão recebida.")
    else:
        if password:
            st.error("Senha incorreta!")
