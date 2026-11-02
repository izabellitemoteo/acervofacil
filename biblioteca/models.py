from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

PRAZO_PADRAO_DIAS = 14


class Obra(models.Model):
    """Uma obra do acervo (título). Pode ter vários exemplares."""

    numero = models.PositiveIntegerField("nº no catálogo", null=True, blank=True, unique=True)
    titulo = models.CharField("título", max_length=250)
    autor = models.CharField("autor", max_length=200, blank=True)
    assunto = models.CharField("assunto", max_length=150, blank=True)
    editora = models.CharField("editora", max_length=100, blank=True)
    ano = models.PositiveIntegerField("ano de publicação", null=True, blank=True)
    isbn = models.CharField("ISBN", max_length=20, blank=True)

    class Meta:
        ordering = ["titulo"]

    def __str__(self):
        return f"{self.titulo} ({self.autor})" if self.autor else self.titulo

    @property
    def total_exemplares(self):
        return self.exemplares.count()

    @property
    def exemplares_disponiveis(self):
        return sum(1 for e in self.exemplares.all() if e.disponivel)


class Exemplar(models.Model):
    """Uma cópia física de uma obra, identificada por um código de tombo."""

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name="exemplares")
    codigo = models.CharField("código do exemplar", max_length=30, unique=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name_plural = "exemplares"

    def __str__(self):
        return f"{self.codigo} - {self.obra.titulo}"

    @property
    def disponivel(self):
        return not self.emprestimos.filter(data_devolucao__isnull=True).exists()


class Leitor(models.Model):
    """Servidor do órgão que pode pegar livros emprestados."""

    nome = models.CharField("nome", max_length=150)
    identificacao = models.CharField("matrícula ou identificação", max_length=30, unique=True)
    setor = models.CharField("setor", max_length=100, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "leitores"

    def __str__(self):
        return f"{self.nome} ({self.identificacao})"


class Emprestimo(models.Model):
    exemplar = models.ForeignKey(Exemplar, on_delete=models.PROTECT, related_name="emprestimos")
    leitor = models.ForeignKey(Leitor, on_delete=models.PROTECT, related_name="emprestimos")
    data_emprestimo = models.DateField("data do empréstimo", default=timezone.localdate)
    data_prevista = models.DateField("devolução prevista", blank=True)
    data_devolucao = models.DateField("data da devolução", null=True, blank=True)

    class Meta:
        ordering = ["-data_emprestimo", "-id"]
        verbose_name_plural = "empréstimos"

    def __str__(self):
        return f"{self.exemplar.codigo} -> {self.leitor.nome}"

    def save(self, *args, **kwargs):
        if not self.data_prevista:
            self.data_prevista = self.data_emprestimo + timedelta(days=PRAZO_PADRAO_DIAS)
        super().save(*args, **kwargs)

    def clean(self):
        """Regra central: um exemplar não pode ter dois empréstimos em aberto."""
        if self.data_devolucao is None and self.exemplar_id:
            em_aberto = Emprestimo.objects.filter(
                exemplar_id=self.exemplar_id, data_devolucao__isnull=True
            ).exclude(pk=self.pk)
            if em_aberto.exists():
                raise ValidationError("Este exemplar já está emprestado.")

    @property
    def em_aberto(self):
        return self.data_devolucao is None

    @property
    def atrasado(self):
        return self.em_aberto and self.data_prevista < timezone.localdate()

    def devolver(self):
        self.data_devolucao = timezone.localdate()
        self.save()
