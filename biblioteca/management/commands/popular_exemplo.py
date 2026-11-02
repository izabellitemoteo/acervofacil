from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from biblioteca.models import Emprestimo, Exemplar, Leitor, Obra


class Command(BaseCommand):
    help = "Cria dados FICTÍCIOS de exemplo para demonstrar o sistema."

    def handle(self, *args, **options):
        if Obra.objects.exists():
            self.stdout.write("Já existem obras cadastradas; nada foi feito.")
            return
        dados = [
            ("Direito Administrativo Brasileiro", "Autor Exemplo A", 2019, 2),
            ("Controle Externo da Administração Pública", "Autor Exemplo B", 2021, 1),
            ("Lei de Responsabilidade Fiscal Comentada", "Autor Exemplo C", 2018, 2),
            ("Manual de Contabilidade Pública", "Autor Exemplo D", 2020, 1),
            ("Licitações e Contratos Administrativos", "Autor Exemplo E", 2022, 3),
        ]
        n = 1
        for titulo, autor, ano, qtd in dados:
            obra = Obra.objects.create(titulo=titulo, autor=autor, ano=ano)
            for _ in range(qtd):
                Exemplar.objects.create(obra=obra, codigo=f"EX-{n:03d}")
                n += 1
        ana = Leitor.objects.create(nome="Leitora Exemplo 1", identificacao="1001", setor="Gabinete")
        beto = Leitor.objects.create(nome="Leitor Exemplo 2", identificacao="1002", setor="Secretaria")
        hoje = timezone.localdate()
        Emprestimo.objects.create(exemplar=Exemplar.objects.get(codigo="EX-001"), leitor=ana,
                                  data_emprestimo=hoje - timedelta(days=5))
        Emprestimo.objects.create(exemplar=Exemplar.objects.get(codigo="EX-003"), leitor=beto,
                                  data_emprestimo=hoje - timedelta(days=20))
        self.stdout.write(self.style.SUCCESS("Dados de exemplo criados (fictícios)."))
