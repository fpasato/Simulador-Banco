from flask import Flask, redirect, session

from routes.home import home_bp
from routes.login import login_bp  
from routes.register import register_bp
from routes.transfer import transfer_bp
from routes.versaldo import versaldo_bp
from routes.emprestimos import emprestimos_bp
from routes.pix import pix_bp
from routes.cards import cards_bp
from routes.investimento import investimento_bp
from routes.emprego import emprego_bp
from routes.faturas import faturas_bp  
from routes.extrato import extrato_bp

from werkzeug.middleware.proxy_fix import ProxyFix
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = "segredo_super_secreto"

# Registra todos os blueprints
app.register_blueprint(home_bp)
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(transfer_bp)
app.register_blueprint(versaldo_bp)
app.register_blueprint(emprestimos_bp)
app.register_blueprint(pix_bp)
app.register_blueprint(cards_bp)
app.register_blueprint(investimento_bp)
app.register_blueprint(emprego_bp)
app.register_blueprint(faturas_bp)
app.register_blueprint(extrato_bp)


@app.route("/")
def index():
    return redirect("/login")

        
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)