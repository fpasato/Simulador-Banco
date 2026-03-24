from flask import Blueprint, request, render_template
from utils.services.register.functions import register_account

register_bp = Blueprint("register", __name__, url_prefix="/register")

@register_bp.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        result = register_account(request.form)
        if result["success"]:
            return render_template("empregos/index.html", popup_message=result["message"], popup_type="success")
        else:
            return render_template(
                "register/index.html",
                popup_message=result["message"],
                popup_type="error"
            )
    return render_template("register/index.html")