from django.db import models

class Enquadramento(models.Model):
    """
    Armazena os detalhes de cada tipo de enquadramento de infração,
    incluindo seu período de validade.
    """
    codigo = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Código da infração, sem hífens ou pontos. Ex: 74550"
    )
    portaria = models.CharField(
        max_length=30,
        blank=True,
        help_text="Portaria que instituiu o enquadramento."
    )
    data_inicio = models.DateField(
        db_index=True,
        help_text="Data de início da validade deste enquadramento."
    )
    data_final = models.DateField(
        null=True,
        blank=True,
        help_text="Data final da validade deste enquadramento. Nulo significa 'em vigor'."
    )
    descricao = models.TextField(blank=True)
    infrator = models.CharField(max_length=50, blank=True)
    competencia = models.CharField(max_length=20, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True)

    class Meta:
        # Garante que não haja sobreposição de períodos para o mesmo código
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'data_inicio'], name='unique_codigo_data_inicio')
        ]
        ordering = ['codigo', '-data_inicio']

    def __str__(self):
        return f"{self.codigo} (Início: {self.data_inicio})"

class Infracao(models.Model):
    ait = models.CharField(max_length=50, unique=True, db_index=True)
    placa = models.CharField(max_length=20, db_index=True)
    valor_infracao = models.DecimalField(max_digits=12, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2)
    data_infracao = models.DateField(db_index=True)
    data_na = models.DateField(null=True, blank=True)
    data_np = models.DateField(null=True, blank=True)
    # Retornando ao campo 'codigo' simples, sem relacionamento direto.
    codigo = models.CharField(max_length=20, db_index=True)

    def __str__(self):
        return f"{self.ait} - {self.placa}"

class ArquivoImportado(models.Model):
    nome_arquivo = models.CharField(max_length=255, unique=True)
    data_importacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_arquivo} importado em {self.data_importacao.strftime('%d/%m/%Y')}"