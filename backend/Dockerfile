# Usar a imagem oficial do Python como base
FROM python:3.11-slim

# Definir variáveis de ambiente para desativar o cache de Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos de dependência
# Copiar apenas o requirements.txt para aproveitar o cache do Docker
COPY requirements.txt /app/

# Instalar as dependências do Python
# Usar --no-cache-dir para reduzir o tamanho da imagem
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY . /app

# O comando de execução do contêiner
# Usamos Gunicorn com Uvicorn Worker, que é o padrão de produção para FastAPI
# O servidor Gunicorn/Uvicorn rodará na porta 8000 (padrão do FastAPI)
# O --host 0.0.0.0 é necessário para que o contêiner escute em todas as interfaces de rede
CMD ["gunicorn", "server:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
