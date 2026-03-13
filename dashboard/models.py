from django.db import models

class Infracao(models.Model):
    ait = models.CharField(max_length=50, unique=True, db_index=True)
    placa = models.CharField(max_length=20, db_index=True)
    valor_infracao = models.DecimalField(max_digits=12, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2)
    data_infracao = models.DateField(db_index=True)
    data_na = models.DateField(null=True, blank=True)
    data_np = models.DateField(null=True, blank=True)
    codigo = models.CharField(max_length=20, db_index=True)

    def __str__(self):
        return f"{self.ait} - {self.placa}"

class ArquivoImportado(models.Model):
    nome_arquivo = models.CharField(max_length=255, unique=True)
    data_importacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_arquivo} importado em {self.data_importacao.strftime('%d/%m/%Y')}"