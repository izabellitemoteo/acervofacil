// Preenche o formulário de obra com os dados devolvidos pela API (via servidor) a partir do ISBN.
(function () {
  var botao = document.getElementById("buscar-isbn");
  var campoIsbn = document.getElementById("id_isbn");
  var aviso = document.getElementById("resultado-isbn");
  if (!botao || !campoIsbn || !aviso) { return; }

  var campos = ["titulo", "autor", "assunto", "editora", "ano"];

  botao.addEventListener("click", function () {
    aviso.textContent = "Consultando…";
    fetch(botao.dataset.url + "?isbn=" + encodeURIComponent(campoIsbn.value), { credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, dados: d }; }); })
      .then(function (res) {
        if (!res.ok) { aviso.textContent = res.dados.erro; return; }
        campos.forEach(function (nome) {
          var el = document.getElementById("id_" + nome);
          if (el && res.dados[nome]) { el.value = res.dados[nome]; }
        });
        aviso.textContent = "Dados preenchidos. Confira e corrija, se necessário, antes de cadastrar.";
        document.getElementById("id_titulo").focus();
      })
      .catch(function () { aviso.textContent = "Não foi possível consultar agora. Preencha os dados manualmente."; });
  });
})();
