from flask import Flask
from routes.index import index_bp
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

app.register_blueprint(index_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
