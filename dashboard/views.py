
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.db import transaction
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import csv
import io
from datetime import datetime
from .models import Infracao, ArquivoImportado, Enquadramento



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
        # CORRIGIDO: O delimitador para o arquivo de infrações deve ser ponto e vírgula (;).
        leitor_csv = csv.DictReader(io.StringIO(dados_decodificados), delimiter=';')

        # ETAPA DE DIAGNÓSTICO: Verifica se o cabeçalho do arquivo contém as colunas mínimas.
        # Isso ajuda a identificar rapidamente erros de delimitador ou de nome de coluna.
        expected_headers = {'AIT', 'PLACA', 'DTINFRAC', 'CODIGO', 'VALORINFRAC', 'VALORPAGO'} # Adicione aqui todas as colunas essenciais que você espera
        actual_headers = set(leitor_csv.fieldnames or [])

        if not expected_headers.issubset(actual_headers):
            return Response({
                "erro": (
                    "O cabeçalho do arquivo de infrações parece estar incorreto ou o delimitador não é ponto e vírgula (;). "
                    f"Colunas essenciais não encontradas: {list(expected_headers - actual_headers)}. "
                    f"Colunas que foram lidas no arquivo: {list(actual_headers)}. "
                    "Por favor, verifique o arquivo."
                )
            }, status=status.HTTP_400_BAD_REQUEST)

        lote = []
        tamanho_lote = 10000
        # Contadores para diagnóstico
        linhas_processadas = 0
        linhas_com_erro = 0

        def formatar_data(data_str):
            if not data_str or data_str == '00000000' or len(data_str) != 8: return None
            try:
                return datetime.strptime(data_str, '%Y%m%d').date()
            except ValueError:
                return None

        def formatar_valor(valor_str):
            if not valor_str: return Decimal('0.00')
            return Decimal(valor_str) / Decimal('100')

        try:
            with transaction.atomic():
                for linha in leitor_csv:
                    try:
                        if not linha.get('AIT'):
                            continue

                        data_infracao_obj = formatar_data(linha.get('DTINFRAC'))
                        # Normaliza o código da infração para remover o dígito verificador (ex: 5266-1 -> 5266)
                        # Esta lógica deve ser IDÊNTICA à da importação de enquadramentos.
                        codigo_limpo = linha.get('CODIGO', '').strip().split('-')[0]

                        lote.append(
                            Infracao(
                                ait=linha['AIT'].strip(),
                                placa=linha['PLACA'].strip(),
                                valor_infracao=formatar_valor(linha.get('VALORINFRAC', '0')),
                                valor_pago=formatar_valor(linha.get('VALORPAGO', '0')),
                                data_infracao=data_infracao_obj,
                                data_na=formatar_data(linha.get('DATANA')),
                                data_np=formatar_data(linha.get('DATANP')),
                                # Armazena o código diretamente
                                codigo=codigo_limpo
                            )
                        )

                        if len(lote) >= tamanho_lote:
                            Infracao.objects.bulk_create(lote, ignore_conflicts=True)
                            linhas_processadas += len(lote)
                            lote = []
                    
                    except (ValueError, TypeError, InvalidOperation) as e:
                        # Se uma linha específica falhar na conversão de tipo, conta como erro e continua
                        linhas_com_erro += 1
                        continue

                if lote:
                    Infracao.objects.bulk_create(lote, ignore_conflicts=True)
                    linhas_processadas += len(lote)

                ArquivoImportado.objects.create(nome_arquivo=nome_do_arquivo)

            # Constrói a mensagem de resposta detalhada
            msg = (
                f"Sucesso! {linhas_processadas} registros processados do arquivo {nome_do_arquivo}. "
            )
            if linhas_com_erro > 0:
                msg += f" {linhas_com_erro} linhas foram ignoradas devido a erros de formato nos dados."

            return Response({"mensagem": msg}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImportarEnquadramentoView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        arquivo_csv = request.FILES.get('file')
        if not arquivo_csv:
            return Response({"erro": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        def parse_date_br(date_str):
            # Trata tanto campos vazios quanto a data especial '99/99/9999' como nulos.
            if not date_str or date_str.strip() == '99/99/9999': return None
            try:
                # Suporta formatos como 23/12/2019
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except (ValueError, TypeError):
                return None

        def parse_decimal_br(decimal_str):
            if not decimal_str: return None
            try:
                # Suporta formatos como 5000,00
                return Decimal(decimal_str.replace('.', '').replace(',', '.'))
            except (ValueError, InvalidOperation, TypeError):
                return None

        try:
            dados_decodificados = arquivo_csv.read().decode('utf-8-sig')
            # ATENÇÃO: O delimitador foi alterado para TAB para suportar o novo formato.
            leitor_csv = csv.DictReader(io.StringIO(dados_decodificados), delimiter='\t')

            # ETAPA DE DIAGNÓSTICO: Verifica se o cabeçalho do arquivo contém as colunas mínimas.
            # Isso ajuda a identificar rapidamente erros de delimitador ou de nome de coluna.
            expected_headers = {'codigo', 'data_inicio'}
            actual_headers = set(leitor_csv.fieldnames or [])

            if not expected_headers.issubset(actual_headers):
                return Response({
                    "erro": (
                        "O cabeçalho do arquivo parece estar incorreto ou o delimitador não é TAB. "
                        f"Colunas essenciais não encontradas: {list(expected_headers - actual_headers)}. "
                        f"Colunas que foram lidas no arquivo: {list(actual_headers)}. "
                        "Por favor, verifique o arquivo."
                    )
                }, status=status.HTTP_400_BAD_REQUEST)

            enquadramentos_para_criar = []
            enquadramentos_para_atualizar = []
            # A chave do dicionário agora é uma tupla (código, data_início)
            existentes_db = {(e.codigo, e.data_inicio): e for e in Enquadramento.objects.all()}
            registros_no_arquivo = set()

            # Contadores para feedback detalhado
            linhas_lidas = 0
            linhas_ignoradas_dados = 0
            linhas_ignoradas_duplicadas = 0

            for linha in leitor_csv:
                linhas_lidas += 1
                # Normaliza o código para remover o dígito verificador (ex: 5266-1 -> 5266)
                codigo_limpo = linha.get('codigo', '').strip().split('-')[0]
                data_inicio = parse_date_br(linha.get('data_inicio'))

                if not codigo_limpo or not data_inicio:
                    linhas_ignoradas_dados += 1
                    continue
                
                chave_registro = (codigo_limpo, data_inicio)
                if chave_registro in registros_no_arquivo:
                    linhas_ignoradas_duplicadas += 1
                    continue # Pula registros duplicados dentro do mesmo arquivo
                registros_no_arquivo.add(chave_registro)

                # Monta um dicionário com os dados da linha do CSV
                dados_linha = {
                    'portaria': linha.get('portaria', '').strip(),
                    'data_final': parse_date_br(linha.get('data_final')),
                    'descricao': linha.get('descricao', '').strip(),
                    'infrator': linha.get('infrator', '').strip(),
                    'competencia': linha.get('competencia', '').strip(),
                    'valor': parse_decimal_br(linha.get('valor')),
                    'pontos': int(p) if (p := linha.get('pontos', '').strip()).isdigit() else None,
                }

                if chave_registro in existentes_db:
                    obj_existente = existentes_db[chave_registro]
                    # Compara os dados do CSV com os do banco para ver se precisa atualizar
                    if any(getattr(obj_existente, k) != v for k, v in dados_linha.items()):
                        for k, v in dados_linha.items():
                            setattr(obj_existente, k, v)
                        enquadramentos_para_atualizar.append(obj_existente)
                else:
                    enquadramentos_para_criar.append(
                        Enquadramento(codigo=codigo_limpo, data_inicio=data_inicio, **dados_linha)
                    )

            with transaction.atomic():
                if enquadramentos_para_criar:
                    Enquadramento.objects.bulk_create(enquadramentos_para_criar, ignore_conflicts=True)
                if enquadramentos_para_atualizar:
                    campos_para_atualizar = ['portaria', 'data_final', 'descricao', 'infrator', 'competencia', 'valor', 'pontos']
                    Enquadramento.objects.bulk_update(enquadramentos_para_atualizar, campos_para_atualizar)

            # Constrói uma mensagem de resposta mais detalhada
            msg = (
                f"{len(enquadramentos_para_criar)} novos enquadramentos criados e "
                f"{len(enquadramentos_para_atualizar)} atualizados. "
                f"Total de {linhas_lidas} linhas lidas no arquivo."
            )
            detalhes_ignorados = []
            if linhas_ignoradas_dados > 0:
                detalhes_ignorados.append(f"{linhas_ignoradas_dados} por falta de 'código' ou 'data_início' válidos")
            if linhas_ignoradas_duplicadas > 0:
                detalhes_ignorados.append(f"{linhas_ignoradas_duplicadas} por serem duplicadas no arquivo")

            if detalhes_ignorados:
                msg += " Linhas ignoradas: " + " e ".join(detalhes_ignorados) + "."

            return Response({"mensagem": msg}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"erro": f"Erro ao processar o arquivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def pagina_home(request):
    """Renderiza a página inicial (Home) do sistema."""
    return render(request, 'dashboard/home.html')

def pagina_upload(request):
    """Renderiza a interface gráfica para upload do CSV de infrações."""
    return render(request, 'dashboard/upload.html')

def pagina_upload_enquadramento(request):
    """Renderiza a interface gráfica para upload do CSV de enquadramentos."""
    return render(request, 'dashboard/upload_enquadramento.html')

def pagina_dashboard(request):
    """Renderiza a interface gráfica do Dashboard."""
    return render(request, 'dashboard/dashboard.html')


def api_dados_grafico(request):
    """API que retorna os dados filtrados, KPIs financeiros e Funil de Auditoria."""
    queryset = Infracao.objects.all()

    # 1. Filtros de Data
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if data_inicio:
        queryset = queryset.filter(data_infracao__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_infracao__lte=data_fim)

    # 2. Cálculos dos KPIs (Financeiro + Auditoria)
    totais = queryset.aggregate(
        total_infracoes=Count('id'),
        total_arrecadado=Sum('valor_pago'),
        valor_pendente_total=Sum(F('valor_infracao') - F('valor_pago')),
        # KPIs de Auditoria (Funil)
        total_na=Count('id', filter=Q(data_na__isnull=False)),
        total_np=Count('id', filter=Q(data_np__isnull=False))
    )

    # 3. Dados do Gráfico de Evolução
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
            valores_pendentes.append(float(item['pendente_mes'] or 0))

    # 4. Retorno do JSON consolidado
    return JsonResponse({
        'kpis': {
            'total_infracoes': totais['total_infracoes'] or 0,
            'total_arrecadado': float(totais['total_arrecadado'] or 0),
            'valor_pendente_total': float(totais['valor_pendente_total'] or 0),
            'total_na': totais['total_na'] or 0,
            'total_np': totais['total_np'] or 0
        },
        'grafico': {
            'labels': labels,
            'valores_qtd': valores_qtd,
            'valores_pendentes': valores_pendentes
        }
    })



def exportar_csv_pagamentos(request):
    """
    Gera um CSV em tempo real com os pagamentos, % de desconto,
    e dados do enquadramento como descrição e valor original.
    """

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
    writer.writerow(['AIT', 'Placa', 'Data Infracao', 'Codigo', 'Valor Cobrado (R$)', 'Valor Pago (R$)', 'Desconto (%)'])

    for inf in queryset.iterator():
        desconto_pct = 0
        # A base de cálculo do desconto será o valor_infracao, já que não há mais enquadramento direto.
        base_calculo_desconto = inf.valor_infracao
        if base_calculo_desconto > 0:
            # Calcula o desconto em relação ao valor pago.
            desconto_pct = ((base_calculo_desconto - inf.valor_pago) / base_calculo_desconto) * 100

        # Formatação dos valores para o CSV, tratando casos de N/A.
        v_cobrado = f"{inf.valor_infracao:.2f}".replace('.', ',')
        v_pago = f"{inf.valor_pago:.2f}".replace('.', ',')
        pct_formatado = f"{desconto_pct:.2f}".replace('.', ',') if base_calculo_desconto > 0 else 'N/A'

        data_formatada = inf.data_infracao.strftime('%d/%m/%Y') if inf.data_infracao else ''

        writer.writerow([
            inf.ait,
            inf.placa,
            data_formatada,
            inf.codigo, # Usando o campo codigo diretamente
            v_cobrado,
            v_pago,
            pct_formatado
        ])

    return response
