# Acervo Fácil

**Sistema publicado:** https://acervofacil.pythonanywhere.com

Aplicação web (Django) para controlar os empréstimos da biblioteca do MPCSP.
Projeto Integrador II – Univesp.

## Como rodar no seu computador

1. Instale o Python 3.10 ou mais novo (python.org). No Windows, marque "Add Python to PATH".
2. Abra o terminal dentro desta pasta e crie o ambiente virtual:
   - Windows: `python -m venv .venv` e depois `.venv\Scripts\activate`
   - Linux/macOS: `python3 -m venv .venv` e depois `source .venv/bin/activate`
3. Instale o Django: `pip install -r requirements.txt`
4. Crie o banco de dados: `python manage.py migrate`
5. Crie o seu usuário de acesso: `python manage.py createsuperuser`
6. Importe o catálogo real: `python manage.py importar_acervo caminho/da/planilha.xlsx` (ou, só para testar, `python manage.py popular_exemplo`)
7. Inicie: `python manage.py runserver` e abra http://127.0.0.1:8000/
8. Rodar os testes automáticos: `python manage.py test`

## Onde está cada coisa

- `biblioteca/models.py` – tabelas: Obra, Exemplar, Leitor, Emprestimo e a regra "um exemplar não pode ter dois empréstimos abertos".
- `biblioteca/views.py` – o que acontece em cada tela (acervo, novo empréstimo, empréstimos em aberto, devolução).
- `biblioteca/forms.py` – formulário de empréstimo (só mostra exemplares disponíveis).
- `biblioteca/templates/` e `templates/` – o HTML das telas.
- `biblioteca/static/biblioteca/filtro.js` – filtro de obras enquanto se digita (JavaScript).
- `biblioteca/servicos.py` – consulta à API Open Library (preenche título, autor, editora e ano a partir do ISBN).
- `biblioteca/static/biblioteca/isbn.js` – botão "Buscar dados pelo ISBN" da tela Nova obra.
- `biblioteca/tests.py` – testes automáticos (21).
- Painel de cadastros: http://127.0.0.1:8000/admin/ (obras, exemplares, leitores).

## Cadastro de obra com a API

Menu **Nova obra**: digite o ISBN (com ou sem hifens) e clique em "Buscar dados pelo ISBN". Título, autor, editora, ano e assunto são preenchidos para conferência; se a API estiver fora do ar ou o ISBN não existir, a tela avisa e o cadastro continua manual. Exemplo para teste: 9788535902778. Requer internet.

## Publicar no PythonAnywhere (nuvem)

1. Crie uma conta gratuita em pythonanywhere.com (o nome de usuário define o endereço: `SEUUSUARIO.pythonanywhere.com`).
2. Em **Consoles > Bash**, envie o projeto (`git clone` do seu repositório no GitHub ou **Files > Upload** do .zip, depois `unzip`).
3. No console:
   - `cd acervofacil`
   - `python3 -m venv ~/venv && source ~/venv/bin/activate`
   - `pip install -r requirements.txt`
   - `python manage.py migrate`
   - `python manage.py createsuperuser`
   - `python manage.py importar_acervo caminho/da/planilha.xlsx`
   - `python manage.py collectstatic`
4. Em **Web > Add a new web app > Manual configuration** (mesma versão do Python do venv). Preencha:
   - Source code e Working directory: a pasta `acervofacil`.
   - Virtualenv: `/home/SEUUSUARIO/venv`.
   - Static files: URL `/static/` apontando para `/home/SEUUSUARIO/acervofacil/staticfiles`.
5. Edite o arquivo WSGI da aba Web, apagando o conteúdo de exemplo e deixando:

```python
import os, sys
sys.path.insert(0, "/home/SEUUSUARIO/acervofacil")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DEBUG"] = "0"
os.environ["DJANGO_SECRET_KEY"] = "COLE-AQUI-UMA-CHAVE-LONGA-E-ALEATORIA"
os.environ["DJANGO_ALLOWED_HOSTS"] = "SEUUSUARIO.pythonanywhere.com"
os.environ["DJANGO_CSRF_ORIGINS"] = "https://SEUUSUARIO.pythonanywhere.com"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

6. Clique em **Reload** e abra o endereço. Na conta gratuita, o acesso à internet é limitado a uma lista de sites permitidos; teste a tela Nova obra para confirmar que a consulta à Open Library funciona.

Para gerar uma chave: `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
