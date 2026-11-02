from django import forms
from django.db import models

from .models import Emprestimo, Exemplar, Obra


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ["exemplar", "leitor", "data_emprestimo"]
        widgets = {"data_emprestimo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só exemplares sem empréstimo em aberto aparecem na lista.
        livres = [e.pk for e in Exemplar.objects.select_related("obra") if e.disponivel]
        self.fields["exemplar"].queryset = Exemplar.objects.filter(pk__in=livres).select_related("obra")
        self.fields["exemplar"].empty_label = "Selecione um exemplar"
        self.fields["leitor"].empty_label = "Selecione um leitor"


class ObraForm(forms.ModelForm):
    """Cadastro de obra nova, com a quantidade de exemplares a criar."""

    quantidade = forms.IntegerField(label="Quantidade de exemplares", min_value=1, max_value=50, initial=1)

    class Meta:
        model = Obra
        fields = ["isbn", "titulo", "autor", "assunto", "editora", "ano"]
        labels = {"isbn": "ISBN (opcional, permite preencher os dados automaticamente)"}

    def save(self, commit=True):
        obra = super().save(commit=False)
        ultimo = Obra.objects.aggregate(m=models.Max("numero"))["m"] or 0
        obra.numero = ultimo + 1
        obra.save()
        for k in range(1, self.cleaned_data["quantidade"] + 1):
            Exemplar.objects.create(obra=obra, codigo=f"{obra.numero:03d}-{k}")
        return obra
