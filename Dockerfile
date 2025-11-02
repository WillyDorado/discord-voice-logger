# Usa Python 3.11 (compatible con audioop)
FROM python:3.11-slim

# Crea carpeta de trabajo
WORKDIR /app

# Copia archivos
COPY . .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Ejecuta el bot
CMD ["python", "Botdiscord.py"]
