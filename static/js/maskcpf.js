const cpfInput = document.getElementById("cpf");

cpfInput.addEventListener("input", function () {

    let cpf = this.value.replace(/\D/g, "");

    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
    cpf = cpf.replace(/(\d{3})(\d{1,2})$/, "$1-$2");

    this.value = cpf;

});