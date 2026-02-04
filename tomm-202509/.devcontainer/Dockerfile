# Use Microsoft's VS Code Dev Container Python 3.13 image
FROM mcr.microsoft.com/vscode/devcontainers/python:3.13

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    sudo \
    vim \
    wget \
    zip \
    unzip \
    poppler-utils \
    tesseract-ocr \
    libglib2.0-0 \
    libmagic1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set the working directory
WORKDIR /workspace

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command
CMD ["/bin/bash"]
