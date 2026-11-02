from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
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
        lista = lista.filter(Q(titulo__icontains=q) | Q(autor__icontains=q) | Q(assunto__icontains=q))
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
