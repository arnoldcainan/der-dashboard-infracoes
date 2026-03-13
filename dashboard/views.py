
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.db import transaction
import csv
import io
from datetime import datetime
from .models import Infracao, ArquivoImportado

class ImportarCSVView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        arquivo_csv = request.FILES.get('file')

        if not arquivo_csv:
            return Response({"erro": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        nome_do_arquivo = arquivo_csv.name

        # TRAVA DE SEGURANÇA: Verifica se o arquivo já existe no banco
        if ArquivoImportado.objects.filter(nome_arquivo=nome_do_arquivo).exists():
            return Response(
                {"erro": f"O arquivo '{nome_do_arquivo}' já foi importado anteriormente!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        dados_decodificados = arquivo_csv.read().decode('utf-8-sig')
        leitor_csv = csv.DictReader(io.StringIO(dados_decodificados), delimiter=';')

        lote = []
        tamanho_lote = 10000
        linhas_processadas = 0

        def formatar_data(data_str):
            if not data_str or data_str == '00000000' or len(data_str) != 8: return None
            try:
                return datetime.strptime(data_str, '%Y%m%d').date()
            except ValueError:
                return None

        def formatar_valor(valor_str):
            if not valor_str: return 0.00
            return float(valor_str) / 100

        try:
            with transaction.atomic():
                for linha in leitor_csv:
                    if not linha.get('AIT'):
                        continue

                    lote.append(
                        Infracao(
                            ait=linha['AIT'].strip(),
                            placa=linha['PLACA'].strip(),
                            valor_infracao=formatar_valor(linha.get('VALORINFRAC', '0')),
                            valor_pago=formatar_valor(linha.get('VALORPAGO', '0')),
                            data_infracao=formatar_data(linha.get('DTINFRAC')),
                            data_na=formatar_data(linha.get('DATANA')),
                            data_np=formatar_data(linha.get('DATANP')),
                            codigo=linha['CODIGO'].strip()
                        )
                    )

                    if len(lote) >= tamanho_lote:
                        Infracao.objects.bulk_create(lote, ignore_conflicts=True)
                        linhas_processadas += len(lote)
                        lote = []

                if lote:
                    Infracao.objects.bulk_create(lote, ignore_conflicts=True)
                    linhas_processadas += len(lote)

                ArquivoImportado.objects.create(nome_arquivo=nome_do_arquivo)

            return Response(
                {"mensagem": f"Sucesso! {linhas_processadas} registros importados do arquivo {nome_do_arquivo}."},
                status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def pagina_home(request):
    """Renderiza a página inicial (Home) do sistema."""
    return render(request, 'dashboard/home.html')

def pagina_upload(request):
    """Renderiza a interface gráfica para upload do CSV."""
    return render(request, 'dashboard/upload.html')


def pagina_dashboard(request):
    """Renderiza a interface gráfica do Dashboard."""
    return render(request, 'dashboard/dashboard.html')


def api_dados_grafico(request):
    """API que retorna os dados formatados para o Chart.js"""
    dados = (
        Infracao.objects
        .annotate(mes=TruncMonth('data_infracao'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    labels = []
    valores = []

    for item in dados:
        if item['mes']:
            labels.append(item['mes'].strftime('%m/%Y'))
            valores.append(item['total'])

    return JsonResponse({'labels': labels, 'valores': valores})

def api_dados_grafico(request):
    """API que retorna os dados filtrados e os KPIs financeiros."""
    queryset = Infracao.objects.all()
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if data_inicio:
        queryset = queryset.filter(data_infracao__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_infracao__lte=data_fim)

    totais = queryset.aggregate(
        total_infracoes=Count('id'),
        total_arrecadado=Sum('valor_pago'),
        valor_pendente_total=Sum(F('valor_infracao') - F('valor_pago'))
    )

    dados_mensais = (
        queryset
        .annotate(mes=TruncMonth('data_infracao'))
        .values('mes')
        .annotate(
            total_qtd=Count('id'),
            pendente_mes=Sum(F('valor_infracao') - F('valor_pago'))
        )
        .order_by('mes')
    )

    labels = []
    valores_qtd = []
    valores_pendentes = []

    for item in dados_mensais:
        if item['mes']:
            labels.append(item['mes'].strftime('%m/%Y'))
            valores_qtd.append(item['total_qtd'])
            # Converte Decimal para float para não quebrar o JSON
            valores_pendentes.append(float(item['pendente_mes'] or 0))

    return JsonResponse({
        'kpis': {
            'total_infracoes': totais['total_infracoes'] or 0,
            'total_arrecadado': float(totais['total_arrecadado'] or 0),
            'valor_pendente_total': float(totais['valor_pendente_total'] or 0)
        },
        'grafico': {
            'labels': labels,
            'valores_qtd': valores_qtd,
            'valores_pendentes': valores_pendentes
        }
    })



def exportar_csv_pagamentos(request):
    """Gera um CSV em tempo real com os pagamentos e % de desconto"""

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    queryset = Infracao.objects.filter(valor_pago__gt=0)

    if data_inicio:
        queryset = queryset.filter(data_infracao__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_infracao__lte=data_fim)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_descontos_der.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(
        ['AIT', 'Placa', 'Data Infracao', 'Codigo', 'Valor Infracao (R$)', 'Valor Pago (R$)', 'Desconto (%)'])

    for inf in queryset.iterator():
        desconto_pct = 0
        if inf.valor_infracao > 0:
            desconto_pct = ((inf.valor_infracao - inf.valor_pago) / inf.valor_infracao) * 100

        v_infracao = f"{inf.valor_infracao:.2f}".replace('.', ',')
        v_pago = f"{inf.valor_pago:.2f}".replace('.', ',')
        pct_formatado = f"{desconto_pct:.2f}".replace('.', ',')

        data_formatada = inf.data_infracao.strftime('%d/%m/%Y') if inf.data_infracao else ''

        writer.writerow([
            inf.ait,
            inf.placa,
            data_formatada,
            inf.codigo,
            v_infracao,
            v_pago,
            pct_formatado
        ])

    return response
