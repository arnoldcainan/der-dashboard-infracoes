from rest_framework import serializers
from .models import Infracao

class InfracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infracao
        fields = '__all__'