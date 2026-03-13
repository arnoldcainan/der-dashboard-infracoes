from django.urls import path
from .views import ImportarCSVView, pagina_upload, pagina_home, pagina_dashboard, api_dados_grafico,exportar_csv_pagamentos

urlpatterns = [
    # Quando acessar "/", cai na Home
    path('', pagina_home, name='pagina_home'),

    # Quando acessar "/upload/", cai na tela de enviar arquivo
    path('upload/', pagina_upload, name='pagina_upload'),

    path('dashboard/', pagina_dashboard, name='pagina_dashboard'),
    path('api/grafico/', api_dados_grafico, name='api_dados_grafico'),

    # A rota invisível da API que recebe os dados do form
    path('api/importar/', ImportarCSVView.as_view(), name='importar_csv'),
    path('api/exportar/', exportar_csv_pagamentos, name='exportar_csv_pagamentos'),
]