from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# --- Arquivo onde o recorde será salvo ---
RECORD_FILE = "world_record.json"

# --- Função para carregar recorde do arquivo ---
def load_record():
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "r") as f:
            return json.load(f)
    else:
        # Recorde inicial
        return {"nick": "", "email": "", "pontuacao": 0}

# --- Função para salvar recorde no arquivo ---
def save_record(record):
    with open(RECORD_FILE, "w") as f:
        json.dump(record, f)

# --- Recorde atual ---
recorde_mundial = load_record()

@app.route("/recorde", methods=["GET"])
def get_record():
    return jsonify(recorde_mundial)

@app.route("/recorde", methods=["POST"])
def update_record():
    global recorde_mundial
    data = request.json
    nick = data.get("nick", "")
    email = data.get("email", "")
    pontuacao = data.get("pontuacao", 0)

    # Atualiza apenas se a pontuação for maior que a atual
    if pontuacao > recorde_mundial.get("pontuacao", 0):
        recorde_mundial = {"nick": nick, "email": email, "pontuacao": pontuacao}
        save_record(recorde_mundial)  # Salva no arquivo

    return jsonify({"recorde": recorde_mundial})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


