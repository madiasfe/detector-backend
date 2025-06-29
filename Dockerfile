# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala as bibliotecas Python
# O '--no-cache-dir' é uma boa prática para manter a imagem pequena
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do seu projeto (app, best.pt) para dentro do container
COPY . .

# Expõe a porta 80, que o Azure App Service usará para se comunicar
EXPOSE 80

# Comando para iniciar a aplicação quando o container for executado
# Usamos o 'gunicorn' que é um servidor web Python robusto para produção
CMD ["gunicorn", "--bind", "0.0.0.0:80", "backend_app:app"]
