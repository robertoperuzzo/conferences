#!/bin/bash

# Post-create script for the development container
echo "Running post-create setup..."

# Only create directories that might not be in Git (due to empty folders)
mkdir -p data/{raw,processed,chunks}
mkdir -p logs

# Create .env file (should not be tracked in Git)
if [ ! -f .env ]; then
    echo "📄 Creating .env file..."
    cat > .env << EOF
# Typesense configuration
TYPESENSE_HOST=typesense
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_API_KEY=xyz

# Application configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Data paths
DATA_RAW_PATH=./data/raw
DATA_PROCESSED_PATH=./data/processed
DATA_CHUNKS_PATH=./data/chunks

# Chunker configuration
CHUNK_SIZE_TOKENS=512
CHUNK_OVERLAP=50
SEMANTIC_THRESHOLD=0.7
EOF
else
    echo "📄 .env file already exists, skipping..."
fi

echo ""
echo "✅ Post-create setup completed successfully!"
echo ""
echo "📁 Directory structure ready"
echo "⚙️  Configuration files ready"
echo "🐍 Python dependencies ready (installed via Dockerfile)"
echo ""
echo "🚀 Development environment is ready!"
