from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import tempfile
import pdfplumber
from werkzeug.utils import secure_filename

# ------------------------------
# App setup
# ------------------------------

app = Flask(__name__)
CORS(app)

# ------------------------------
# Gemini configuration
# ------------------------------

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-flash-latest")
else:
    model = None

# ------------------------------
# PDF extraction
# ------------------------------

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Erreur lecture PDF: {e}")
    return text.strip()

# ------------------------------
# Roast generation
# ------------------------------

def generate_roast_from_text(profile_text):
    if not model:
        return "⚠️ Clé API Google manquante. Configure GOOGLE_API_KEY."

    prompt = f"""
Tu es un maître du roast humoristique dans le style des Comedy Central Roasts.

Voici le contenu d'un CV ou d'un profil LinkedIn :

{profile_text}

Ta mission :
Crache un roast cruel mais drôle en français.
3 à 5 phrases maximum.
Agressif, sarcastique, humour noir.
Aucun préambule. Génère uniquement le roast.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        return "Même l'IA a levé les yeux au ciel en lisant ce profil."

# ------------------------------
# Routes API
# ------------------------------

@app.route("/api/roast", methods=["POST"])
def roast():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "PDF requis"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "Aucun fichier sélectionné"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Le fichier doit être un PDF"}), 400

    filename = secure_filename(file.filename)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            file.save(temp_pdf.name)
            pdf_text = extract_text_from_pdf(temp_pdf.name)
        os.unlink(temp_pdf.name)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    if not pdf_text:
        return jsonify({"success": False, "error": "Impossible d'extraire du texte depuis le PDF"}), 400

    roast_text = generate_roast_from_text(pdf_text)

    return jsonify({"success": True, "roast": roast_text})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "gemini_configured": model is not None})

# ✅ Pas besoin de route "/" — le HTML est servi statiquement par Vercel
