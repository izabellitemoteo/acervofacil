// Filtra a tabela de obras enquanto a pessoa digita (sem recarregar a página).
(function () {
  var campo = document.getElementById("filtro");
  var linhas = document.querySelectorAll("#tabela-obras tbody tr");
  var contagem = document.getElementById("contagem");
  if (!campo || !contagem) { return; }
  var temporizador;

  function normalizar(texto) {
    return texto.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  campo.addEventListener("input", function () {
    var termo = normalizar(campo.value);
    var visiveis = 0;
    linhas.forEach(function (linha) {
      var mostra = normalizar(linha.textContent).indexOf(termo) !== -1;
      linha.hidden = !mostra;
      if (mostra) { visiveis++; }
    });
    // Atualiza a contagem só quando a digitação faz uma pausa, para o leitor de tela
    // não anunciar um número a cada tecla.
    clearTimeout(temporizador);
    temporizador = setTimeout(function () {
      contagem.textContent = visiveis + (visiveis === 1 ? " obra exibida." : " obras exibidas.");
    }, 600);
  });
})();
