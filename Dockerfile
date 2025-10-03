FROM python:3.11-slim

# Instalar dependencias básicas y herramientas de compilación
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    libsrtp2-1 \
    libsrtp2-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias del sistema para OpenCV y streaming
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    ffmpeg \
    python3-opencv \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch CUDA wheels before general requirements to ensure GPU support
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# Install all dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for RTSP to WebRTC streaming
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-socketio \
    websockets \
    loguru \
    pydantic-settings \
    opencv-python-headless \
    numpy \
    aiortc \
    aiofiles \
    python-multipart

# Copiar código fuente
COPY src/ ./src/
COPY static/ ./static/
COPY .env ./
COPY run.py ./

# Crear directorios necesarios
RUN mkdir -p logs output videos streams

# Configurar permisos para directorios
RUN chmod -R 777 /app/logs /app/output /app/videos /app/streams

# Exponer puerto para la API
EXPOSE 8990

# Variables de entorno
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8990

# Comando por defecto
CMD ["python", "run.py"]