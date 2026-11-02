import csv
import re

from django.core.management.base import BaseCommand, CommandError

from biblioteca.models import Exemplar, Obra


def _texto(valor):
    return re.sub(r"\s+", " ", str(valor)).strip() if valor is not None else ""


def _ler_linhas(caminho):
    """Devolve dicionários com as colunas: Nº do Livro, Assunto, Nome do Livro, Autor, Editora, Qtde."""
    if caminho.lower().endswith(".xlsx"):
        import openpyxl

        planilha = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        aba = planilha["Relação de livros"] if "Relação de livros" in planilha.sheetnames else planilha.worksheets[0]
        linhas = list(aba.iter_rows(values_only=True))
        cabecalho = [_texto(c) for c in linhas[0]]
        return [dict(zip(cabecalho, l)) for l in linhas[1:] if any(l)]
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = "Importa o catálogo da biblioteca (.xlsx ou .csv). Pode ser repetido sem duplicar."

    def add_arguments(self, parser):
        parser.add_argument("arquivo")

    def handle(self, *args, **opts):
        try:
            linhas = _ler_linhas(opts["arquivo"])
        except FileNotFoundError:
            raise CommandError(f"Arquivo não encontrado: {opts['arquivo']}")
        obras = exemplares = 0
        for l in linhas:
            numero = int(_texto(l["Nº do Livro"]))
            qtde = int(_texto(l["Qtde"]))
            obra, criada = Obra.objects.update_or_create(
                numero=numero,
                defaults={
                    "titulo": _texto(l["Nome do Livro"]),
                    "autor": _texto(l.get("Autor")),
                    "assunto": _texto(l.get("Assunto")),
                    "editora": _texto(l.get("Editora")),
                },
            )
            obras += criada
            for k in range(1, qtde + 1):
                # A planilha não traz código de tombo; usamos nº do catálogo + sequência.
                _, nova = Exemplar.objects.get_or_create(obra=obra, codigo=f"{numero:03d}-{k}")
                exemplares += nova
        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída: {obras} obras novas, {exemplares} exemplares novos "
            f"({Obra.objects.count()} obras e {Exemplar.objects.count()} exemplares no total)."))
