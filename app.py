import os
import logging

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import requests

load_dotenv()

APP_NAME = "Mercado Pago Transparent Checkout"
MP_PUBLIC_KEY = os.environ.get("MP_PUBLIC_KEY", "")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mp_checkout")


def missing_credentials():
    """Return information about missing Mercado Pago credentials."""
    missing = []
    if not MP_PUBLIC_KEY:
        missing.append("MP_PUBLIC_KEY")
    if not MP_ACCESS_TOKEN:
        missing.append("MP_ACCESS_TOKEN")
    return missing


@app.route("/")
def checkout():
    missing = missing_credentials()
    return render_template(
        "checkout.html",
        title=APP_NAME,
        public_key=MP_PUBLIC_KEY,
        missing_credentials=missing
    )


@app.route("/api/payments", methods=["POST"])
def create_payment():
    if not MP_ACCESS_TOKEN:
        return (
            jsonify(
                {
                    "error": "Configuração incompleta",
                    "message": "Defina a variável MP_ACCESS_TOKEN antes de prosseguir."
                }
            ),
            500,
        )

    payload = request.get_json(force=True, silent=True) or {}
    logger.info("Payload recebido do frontend: %s", payload)

    payment_payload = {
        "token": payload.get("token"),
        "description": payload.get("description", "Pagamento via checkout transparente"),
        "transaction_amount": payload.get("transaction_amount"),
        "installments": payload.get("installments", 1),
        "payment_method_id": payload.get("payment_method_id"),
        "issuer_id": payload.get("issuer_id"),
        "payer": {
            "email": payload.get("payer_email"),
        },
    }

    # Remove keys that are None (MP API rejects them)
    sanitized_payload = {k: v for k, v in payment_payload.items() if v is not None}

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=headers,
            json=sanitized_payload,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as err:
        logger.exception("Erro ao comunicar com a API do Mercado Pago")
        return jsonify({"error": "request_error", "details": str(err)}), 502

    return jsonify(response.json()), response.status_code


@app.route("/api/config", methods=["GET"])
def config():
    """Expose non-sensitive configuration to the client (public key only)."""
    return jsonify(
        {
            "public_key": MP_PUBLIC_KEY,
            "missing_credentials": missing_credentials(),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
