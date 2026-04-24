from django.urls import path
from .views import (
    ImportarCSVView, pagina_upload, pagina_home, pagina_dashboard,
    api_dados_grafico, exportar_csv_pagamentos, ImportarEnquadramentoView,
    pagina_upload_enquadramento
)

urlpatterns = [
    # Quando acessar "/", cai na Home
    path('', pagina_home, name='pagina_home'),

    # Páginas de Upload
    path('upload/infracoes/', pagina_upload, name='pagina_upload_infracoes'),
    path('upload/enquadramento/', pagina_upload_enquadramento, name='pagina_upload_enquadramento'),

    path('dashboard/', pagina_dashboard, name='pagina_dashboard'),
    path('api/grafico/', api_dados_grafico, name='api_dados_grafico'),

    # Endpoints da API para importação
    path('api/importar/infracoes/', ImportarCSVView.as_view(), name='importar_csv_infracoes'),
    path('api/importar/enquadramento/', ImportarEnquadramentoView.as_view(), name='importar_csv_enquadramento'),
    path('api/exportar/', exportar_csv_pagamentos, name='exportar_csv_pagamentos'),
]