from django.contrib import admin

from .models import Emprestimo, Exemplar, Leitor, Obra


class ExemplarInline(admin.TabularInline):
    model = Exemplar
    extra = 1


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ("numero", "titulo", "autor", "assunto", "total_exemplares")
    list_filter = ("assunto",)
    search_fields = ("titulo", "autor", "isbn")
    inlines = [ExemplarInline]


@admin.register(Leitor)
class LeitorAdmin(admin.ModelAdmin):
    list_display = ("nome", "identificacao", "setor")
    search_fields = ("nome", "identificacao")


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ("exemplar", "leitor", "data_emprestimo", "data_prevista", "data_devolucao")
    list_filter = ("data_devolucao",)
