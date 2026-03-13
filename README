# 🚦 DER Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-092E20.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg)
![Chart.js](https://img.shields.io/badge/Chart.js-4.0+-FF6384.svg)

> Plataforma em Django para processamento de arquivos CSV massivos (2M+ linhas) e visualização de KPIs financeiros de infrações de trânsito via Chart.js.

## 📖 Sobre o Projeto
O **DER Analytics Dashboard** é uma solução de software construída para lidar com o gargalo de processamento de grandes volumes de dados rodoviários. O sistema é capaz de ingerir relatórios massivos sem estourar a memória RAM e transformar dados brutos em inteligência acionável.

A plataforma não apenas exibe o volume de infrações, mas realiza cálculos na camada do banco de dados para revelar o **Déficit de Arrecadação** (dinheiro de multas não pagas), permitindo filtros dinâmicos por período através de uma interface moderna e responsiva baseada na identidade visual do DER-SP.

## ✨ Principais Funcionalidades

- **🚀 Ingestão Otimizada (Chunking):** Leitura de CSVs gigantes e inserção no banco de dados em lotes via `bulk_create`, garantindo baixo consumo de memória (RAM).
- **🛡️ Trava de Segurança Antiduplicidade:** Bloqueio inteligente no backend que impede o reprocessamento de arquivos já importados.
- **📊 Dashboard Financeiro Interativo:** Gráfico de duplo eixo cruzando Volume de Infrações (Qtd) vs. Déficit Financeiro (R$).
- **⚡ Consultas de Alta Performance:** Uso de indexação (`db_index=True`) e agregações nativas do banco (`Sum`, `Count`, `F`) para retornar KPIs em milissegundos, mesmo com milhões de linhas.

## 🛠️ Stack Tecnológica
- **Backend:** Python, Django, Django REST Framework
- **Banco de Dados:** SQLite (Pronto para migração para PostgreSQL)
- **Frontend:** HTML5, CSS3, Vanilla JS, Bootstrap 5
- **Visualização de Dados:** Chart.js

---

## ⚙️ Como rodar o projeto localmente

### Pré-requisitos
Certifique-se de ter o [Python 3.10+](https://www.python.org/) e o [Git](https://git-scm.com/) instalados em sua máquina.

### Passo a passo

1. **Clone o repositório:**
```bash
git clone [https://github.com/SEU_USUARIO/der-dashboard-infracoes.git](https://github.com/SEU_USUARIO/der-dashboard-infracoes.git)
cd der-dashboard-infracoes