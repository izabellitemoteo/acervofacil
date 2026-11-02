from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Emprestimo, Exemplar, Leitor, Obra


class BaseTeste(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Livro de Teste", autor="Autor")
        self.ex1 = Exemplar.objects.create(obra=self.obra, codigo="T-1")
        self.ex2 = Exemplar.objects.create(obra=self.obra, codigo="T-2")
        self.leitor = Leitor.objects.create(nome="Maria", identificacao="1")


class EmprestimoModelTest(BaseTeste):
    def test_exemplar_novo_esta_disponivel(self):
        self.assertTrue(self.ex1.disponivel)

    def test_emprestimo_define_prazo_de_14_dias(self):
        e = Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        self.assertEqual(e.data_prevista, e.data_emprestimo + timedelta(days=14))

    def test_exemplar_emprestado_fica_indisponivel(self):
        Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        self.assertFalse(self.ex1.disponivel)
        self.assertEqual(self.obra.exemplares_disponiveis, 1)

    def test_nao_permite_dois_emprestimos_do_mesmo_exemplar(self):
        Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        segundo = Emprestimo(exemplar=self.ex1, leitor=self.leitor)
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_devolucao_libera_o_exemplar(self):
        e = Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        e.devolver()
        self.assertTrue(self.ex1.disponivel)
        self.assertIsNotNone(e.data_devolucao)

    def test_atraso(self):
        antigo = timezone.localdate() - timedelta(days=30)
        e = Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor, data_emprestimo=antigo)
        self.assertTrue(e.atrasado)


class ViewsTest(BaseTeste):
    def setUp(self):
        super().setUp()
        User.objects.create_user("bib", password="senha-forte-123")

    def test_acervo_exige_login(self):
        r = self.client.get(reverse("obras"))
        self.assertEqual(r.status_code, 302)

    def test_acervo_lista_obras(self):
        self.client.login(username="bib", password="senha-forte-123")
        r = self.client.get(reverse("obras"))
        self.assertContains(r, "Livro de Teste")

    def test_busca_por_titulo(self):
        Obra.objects.create(titulo="Outro Assunto", autor="Fulano")
        self.client.login(username="bib", password="senha-forte-123")
        r = self.client.get(reverse("obras"), {"q": "Outro"})
        self.assertContains(r, "Outro Assunto")
        self.assertNotContains(r, "Livro de Teste")

    def test_registrar_emprestimo_pela_tela(self):
        self.client.login(username="bib", password="senha-forte-123")
        r = self.client.post(reverse("novo_emprestimo"), {
            "exemplar": self.ex1.pk, "leitor": self.leitor.pk,
            "data_emprestimo": timezone.localdate().isoformat()})
        self.assertRedirects(r, reverse("emprestimos_abertos"))
        self.assertFalse(Exemplar.objects.get(pk=self.ex1.pk).disponivel)

    def test_exemplar_emprestado_nao_aparece_no_formulario(self):
        Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        self.client.login(username="bib", password="senha-forte-123")
        r = self.client.get(reverse("novo_emprestimo"))
        self.assertNotContains(r, "T-1 - Livro")
        self.assertContains(r, "T-2 - Livro")

    def test_devolver_pela_tela(self):
        e = Emprestimo.objects.create(exemplar=self.ex1, leitor=self.leitor)
        self.client.login(username="bib", password="senha-forte-123")
        self.client.post(reverse("devolver", args=[e.pk]))
        e.refresh_from_db()
        self.assertIsNotNone(e.data_devolucao)


class ImportacaoTest(TestCase):
    def test_importa_csv_sem_duplicar(self):
        import os
        import tempfile

        from django.core.management import call_command

        conteudo = ("Nº do Livro,Assunto,Nome do Livro,Autor,Editora,Qtde\n"
                    "1,Direito,Livro A,Autor A,Ed A,2\n"
                    "2,Legislação,Livro B,,,1\n")
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(conteudo)
        try:
            call_command("importar_acervo", f.name, verbosity=0)
            call_command("importar_acervo", f.name, verbosity=0)
        finally:
            os.unlink(f.name)
        self.assertEqual(Obra.objects.count(), 2)
        self.assertEqual(Exemplar.objects.count(), 3)


# ---- Integração com a API de dados bibliográficos (Open Library) ----
import io
import json as _json
from unittest import mock

from . import servicos

RESPOSTA_API = {
    "ISBN:9788535902778": {
        "title": "Dom Casmurro",
        "authors": [{"name": "Machado de Assis"}],
        "publishers": [{"name": "Companhia das Letras"}],
        "publish_date": "March 2003",
        "subjects": [{"name": "Romance brasileiro"}],
    }
}


def _resposta_falsa(corpo):
    r = io.BytesIO(_json.dumps(corpo).encode("utf-8"))
    r.__enter__ = lambda s=r: s
    r.__exit__ = lambda *a: False
    return r


class ApiBibliograficaTest(TestCase):
    def setUp(self):
        User.objects.create_user("bibliotecario", password="senha-forte-123")
        self.client.login(username="bibliotecario", password="senha-forte-123")

    def test_normaliza_isbn_com_hifens(self):
        self.assertEqual(servicos.normalizar_isbn("978-85-359-0277-8"), "9788535902778")
        self.assertIsNone(servicos.normalizar_isbn("123"))

    @mock.patch("biblioteca.servicos.urlopen")
    def test_busca_extrai_titulo_autor_editora_ano(self, urlopen):
        urlopen.return_value = _resposta_falsa(RESPOSTA_API)
        d = servicos.buscar_dados_isbn("9788535902778")
        self.assertEqual(d["titulo"], "Dom Casmurro")
        self.assertEqual(d["autor"], "Machado de Assis")
        self.assertEqual(d["editora"], "Companhia das Letras")
        self.assertEqual(d["ano"], 2003)

    @mock.patch("biblioteca.servicos.urlopen")
    def test_isbn_nao_encontrado_devolve_none(self, urlopen):
        urlopen.return_value = _resposta_falsa({})
        self.assertIsNone(servicos.buscar_dados_isbn("9788535902778"))

    @mock.patch("biblioteca.servicos.urlopen", side_effect=servicos.URLError("sem rede"))
    def test_falha_de_rede_vira_erro_tratado(self, _):
        with self.assertRaises(servicos.ErroConsultaAPI):
            servicos.buscar_dados_isbn("9788535902778")

    @mock.patch("biblioteca.servicos.urlopen", side_effect=servicos.URLError("sem rede"))
    def test_endpoint_informa_falha_sem_quebrar(self, _):
        r = self.client.get(reverse("consultar_isbn"), {"isbn": "9788535902778"})
        self.assertEqual(r.status_code, 502)

    def test_endpoint_rejeita_isbn_invalido(self):
        r = self.client.get(reverse("consultar_isbn"), {"isbn": "abc"})
        self.assertEqual(r.status_code, 400)

    def test_endpoint_exige_login(self):
        self.client.logout()
        r = self.client.get(reverse("consultar_isbn"), {"isbn": "9788535902778"})
        self.assertEqual(r.status_code, 302)

    def test_cadastro_de_obra_cria_exemplares_com_codigo(self):
        r = self.client.post(reverse("nova_obra"), {"titulo": "Livro Novo", "autor": "A", "quantidade": 2})
        self.assertEqual(r.status_code, 302)
        obra = Obra.objects.get(titulo="Livro Novo")
        self.assertEqual(obra.total_exemplares, 2)
        self.assertTrue(obra.exemplares.filter(codigo=f"{obra.numero:03d}-1").exists())
