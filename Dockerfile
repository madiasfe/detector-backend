# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do seu projeto (app, best.pt) para dentro do container
COPY . .

# Comando para iniciar a aplicação quando o container for executado
# Usa a forma "shell" que permite a substituição da variável de ambiente $PORT.
# Esta é a correção final para o erro "is not a valid port number".
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 backend_app:app
