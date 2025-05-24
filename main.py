import logging
import requests
from flask import Flask, render_template, request, jsonify

# Set up logging with timestamp (minimal logging for performance)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Translation API URLs
LIBRETRANSLATE_URL = "https://libretranslate.com/translate"
LINGVA_URL = "https://lingva.ml/api/v1"

def translate_text(text, source="auto", target="es"):
    """
    Translate text using LibreTranslate with a fallback to Lingva Translate.
    Optimized for speed with reduced retries and timeouts.
    """
    # Try LibreTranslate first (single attempt)
    try:
        response = requests.post(
            LIBRETRANSLATE_URL,
            json={"q": text, "source": source, "target": target, "format": "text"},
            headers={"Content-Type": "application/json"},
            timeout=5  # Reduced timeout for faster failure
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("translatedText", "Translation failed"), None
        else:
            error_msg = f"LibreTranslate failed: HTTP {response.status_code}"
            logger.warning(error_msg)
    except Exception as e:
        error_msg = f"LibreTranslate error: {str(e)}"
        logger.error(error_msg)

    # Fallback to Lingva Translate
    try:
        lingva_url = f"{LINGVA_URL}/{source}/{target}/{text}"
        response = requests.get(lingva_url, timeout=5)  # Reduced timeout
        if response.status_code == 200:
            result = response.json()
            return result.get("translation", "Translation failed"), None
        else:
            error_msg = f"Lingva translation failed: HTTP {response.status_code}"
            return None, error_msg
    except Exception as e:
        error_msg = f"Lingva translation error: {str(e)}"
        return None, error_msg

@app.route('/')
def homepage():
    return render_template('index.html', page="translate")

@app.route('/translate', methods=['POST'])
def translate():
    text = request.form.get('text')
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'es')

    if not text:
        return jsonify({"error": "Please enter text to translate"}), 400

    translated_text, error = translate_text(text, source_lang, target_lang)
    if error or "error" in translated_text.lower() or "failed" in translated_text.lower():
        logger.error(f"Translation failed: {error or translated_text}")
        return jsonify({"error": error or translated_text}), 500

    logger.info(f"Translation successful: '{text}' from {source_lang} to {target_lang}")
    return jsonify({
        "original_text": text,
        "translated_text": translated_text,
        "source_lang": source_lang,
        "target_lang": target_lang
    })

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=8080)
