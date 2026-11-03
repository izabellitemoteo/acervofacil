import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import servicos
from .forms import EmprestimoForm, ObraForm
from .models import Emprestimo, Obra


@login_required
def obras(request):
    q = request.GET.get("q", "").strip()
    lista = Obra.objects.prefetch_related("exemplares__emprestimos")
    if q:
        lista = lista.filter(
            Q(titulo__icontains=q) | Q(autor__icontains=q) | Q(assunto__icontains=q) | Q(exemplares__codigo__icontains=q)
        ).distinct()
    return render(request, "biblioteca/obras.html", {"obras": lista, "q": q})


@login_required
def novo_emprestimo(request):
    form = EmprestimoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        emp = form.save()
        messages.success(
            request,
            f"Empréstimo registrado: {emp.exemplar.obra.titulo} para {emp.leitor.nome}. "
            f"Devolução prevista em {emp.data_prevista:%d/%m/%Y}.",
        )
        return redirect("emprestimos_abertos")
    return render(request, "biblioteca/novo_emprestimo.html", {"form": form})


@login_required
def emprestimos_abertos(request):
    lista = Emprestimo.objects.filter(data_devolucao__isnull=True).select_related(
        "exemplar__obra", "leitor"
    ).order_by("data_prevista")
    return render(request, "biblioteca/emprestimos_abertos.html", {"emprestimos": lista})


@login_required
@require_POST
def devolver(request, pk):
    emp = get_object_or_404(Emprestimo, pk=pk, data_devolucao__isnull=True)
    emp.devolver()
    messages.success(request, f"Devolução registrada: {emp.exemplar.obra.titulo}.")
    return redirect("emprestimos_abertos")


@login_required
def nova_obra(request):
    form = ObraForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obra = form.save()
        messages.success(
            request,
            f"Obra cadastrada: {obra.titulo} ({obra.total_exemplares} exemplar"
            f"{'es' if obra.total_exemplares > 1 else ''}).",
        )
        return redirect("obras")
    return render(request, "biblioteca/nova_obra.html", {"form": form})


@login_required
def consultar_isbn(request):
    """Devolve em JSON os dados da obra encontrados na API a partir do ISBN."""
    isbn = servicos.normalizar_isbn(request.GET.get("isbn", ""))
    if isbn is None:
        return JsonResponse({"erro": "Informe um ISBN válido, com 10 ou 13 dígitos."}, status=400)
    try:
        dados = servicos.buscar_dados_isbn(isbn)
    except servicos.ErroConsultaAPI:
        return JsonResponse({"erro": "Não foi possível consultar a base bibliográfica agora. Preencha os dados manualmente."}, status=502)
    if dados is None:
        return JsonResponse({"erro": "ISBN não encontrado na base bibliográfica. Preencha os dados manualmente."}, status=404)
    return JsonResponse(dados)


def _seguro(valor):
    """Evita que o Excel interprete texto como fórmula (injeção em planilhas)."""
    texto = "" if valor is None else str(valor)
    return "'" + texto if texto[:1] in ("=", "+", "-", "@") else texto


def _csv(nome_arquivo):
    resposta = HttpResponse(content_type="text/csv; charset=utf-8")
    resposta["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    resposta.write("\ufeff")  # BOM: o Excel abre os acentos corretamente
    return resposta, csv.writer(resposta, delimiter=";")


@login_required
def exportar_acervo(request):
    """Todas as obras e exemplares, com a situação de cada exemplar (para conferência e cópia de segurança)."""
    resposta, escritor = _csv("acervo.csv")
    escritor.writerow(["Nº da obra", "Código do exemplar", "Título", "Autor", "Assunto", "Editora", "Ano", "ISBN", "Situação"])
    for obra in Obra.objects.prefetch_related("exemplares__emprestimos"):
        for ex in obra.exemplares.all():
            escritor.writerow([
                obra.numero or "", ex.codigo, _seguro(obra.titulo), _seguro(obra.autor), _seguro(obra.assunto),
                _seguro(obra.editora), obra.ano or "", _seguro(obra.isbn),
                "Disponível" if ex.disponivel else "Emprestado",
            ])
    return resposta


@login_required
def exportar_emprestimos(request):
    """Todos os empréstimos (abertos e devolvidos)."""
    resposta, escritor = _csv("emprestimos.csv")
    escritor.writerow(["Código do exemplar", "Título", "Leitor", "Identificação", "Emprestado em", "Devolução prevista", "Devolvido em", "Situação"])
    for e in Emprestimo.objects.select_related("exemplar__obra", "leitor").order_by("-data_emprestimo", "-id"):
        escritor.writerow([
            e.exemplar.codigo, _seguro(e.exemplar.obra.titulo), _seguro(e.leitor.nome), _seguro(e.leitor.identificacao),
            f"{e.data_emprestimo:%d/%m/%Y}", f"{e.data_prevista:%d/%m/%Y}",
            f"{e.data_devolucao:%d/%m/%Y}" if e.data_devolucao else "",
            "Em aberto" if e.em_aberto else "Devolvido",
        ])
    return resposta
