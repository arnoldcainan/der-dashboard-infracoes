import fitz  # PyMuPDF
import csv

caminho_pdf = "2008_a_2015.pdf" 
padrao_nome_csv = "planilha_saida_parte_{}.csv" 

limite_linhas_por_arquivo = 900000 

print(f"A iniciar extração dividida do ficheiro: {caminho_pdf}")

try:
    pdf = fitz.open(caminho_pdf)
    total_paginas = len(pdf)
    print(f"Total de páginas: {total_paginas}\n")

    contador_arquivos = 1
    linhas_no_arquivo_atual = 0
    linhas_totais = 0
    
    arquivo_csv = open(padrao_nome_csv.format(contador_arquivos), mode='w', newline='', encoding='utf-8-sig')
    escritor_csv = csv.writer(arquivo_csv, delimiter=';')
    cabecalho = ['AIT', 'PLACA', 'VALORINFRAC', 'VALORPAGO', 'DTINFRAC', 'DATANA', 'DATANP', 'CODIGO']
    escritor_csv.writerow(cabecalho)

    for num_pagina in range(total_paginas):
        pagina = pdf.load_page(num_pagina)
        texto = pagina.get_text()
        
        if not texto:
            continue
            
        linhas = texto.split('\n')
        
        for linha in linhas:
            linha_limpa = linha.strip()
            
            # Regras de limpeza
            if not linha_limpa or '---' in linha_limpa or 'VALORINFRAC' in linha_limpa or 'PLACA' in linha_limpa:
                continue
                
            partes = linha_limpa.split()
            
            # Verifica se é uma linha válida (8 ou 9 partes)
            if len(partes) == 8 or len(partes) >= 9:
                
                # Controle de quebra de arquivo
                if linhas_no_arquivo_atual >= limite_linhas_por_arquivo:
                    arquivo_csv.close()
                    contador_arquivos += 1
                    print(f"\nLimite atingido! A criar novo ficheiro: Parte {contador_arquivos}...")
                    
                    arquivo_csv = open(padrao_nome_csv.format(contador_arquivos), mode='w', newline='', encoding='utf-8-sig')
                    escritor_csv = csv.writer(arquivo_csv, delimiter=';')
                    escritor_csv.writerow(cabecalho)
                    linhas_no_arquivo_atual = 0

                # LÓGICA FLEXÍVEL: Dependendo do tamanho das partes, ele sabe onde está a placa
                if len(partes) == 8:
                    # AIT sem espaço (ex: 1D2717102)
                    ait = partes[0]
                    placa = partes[1]
                    valorinfrac = partes[2]
                    valorpago = partes[3]
                    dtinfrac = partes[4]
                    datana = partes[5]
                    datanp = partes[6]
                    codigo = partes[7]
                
                else: # Se tem 9 ou mais partes
                    # AIT com espaço (ex: 1S 3147131)
                    ait = f"{partes[0]} {partes[1]}"
                    placa = partes[2]
                    valorinfrac = partes[3]
                    valorpago = partes[4]
                    dtinfrac = partes[5]
                    datana = partes[6]
                    datanp = partes[7]
                    codigo = partes[8]
                
                # Escreve a linha
                escritor_csv.writerow([ait, placa, valorinfrac, valorpago, dtinfrac, datana, datanp, codigo])
                linhas_totais += 1
                linhas_no_arquivo_atual += 1
        
        if (num_pagina + 1) % 100 == 0 or (num_pagina + 1) == total_paginas:
            print(f"Página {num_pagina + 1} de {total_paginas} processada... (Total guardado: {linhas_totais})")

    arquivo_csv.close()
    print(f"\nSucesso absoluto! {linhas_totais} registos extraídos e divididos em {contador_arquivos} ficheiros.")

except FileNotFoundError:
    print(f"\nERRO: O ficheiro '{caminho_pdf}' não foi encontrado.")
except Exception as e:
    print(f"\nERRO FATAL: {e}")