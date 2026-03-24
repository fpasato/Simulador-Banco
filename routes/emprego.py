
from flask import Blueprint, render_template, request, session, redirect
from utils.services.emprego.functions import calcula_pontos

emprego_bp = Blueprint("escolher-emprego", __name__, url_prefix="/escolher-emprego")

@emprego_bp.route("/", methods=["GET", "POST"])
def escolher_emprego():
    if request.method == "POST":
        perfil, salario, pontos = calcula_pontos(request)
        
        session["resultado_emprego"] = {
            "perfil": perfil,
            "salario": salario,
            "pontos": pontos
        }    
        return redirect("/login")      
    return render_template("empregos/index.html")   
