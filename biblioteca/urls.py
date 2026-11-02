from django.urls import path

from . import views

urlpatterns = [
    path("", views.obras, name="obras"),
    path("obras/nova/", views.nova_obra, name="nova_obra"),
    path("obras/consultar-isbn/", views.consultar_isbn, name="consultar_isbn"),
    path("emprestimos/novo/", views.novo_emprestimo, name="novo_emprestimo"),
    path("emprestimos/abertos/", views.emprestimos_abertos, name="emprestimos_abertos"),
    path("emprestimos/<int:pk>/devolver/", views.devolver, name="devolver"),
]
