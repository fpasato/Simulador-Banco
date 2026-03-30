from flask import Blueprint, render_template, request, session, redirect
from utils.services.banco.emprestimo import simularEmprestimo
from utils.validators import check_session


emprestimos_bp = Blueprint("emprestimos", __name__, url_prefix="/emprestimos")


@emprestimos_bp.route("/")
def emprestimos():
    if not check_session():
        return redirect("/login")
    
    if request.method == "POST":
        valor = request.form.get("valor", type=float)
        parcelas = request.form.get("parcelas", type=int)
    else:
        valor = request.args.get("valor", type=float)
        parcelas = request.args.get("parcelas", type=int)
        
    resultado = None
    if valor and parcelas:
        resultado = simularEmprestimo(valor, parcelas)
    
    if valor and parcelas:
        return render_template("emprestimos/index.html", resultado=resultado)
    
    return render_template("emprestimos/index.html")
