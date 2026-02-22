#!/bin/bash

# Clearpath RAG Chatbot - AWS Deployment Script
# This script is intended to be run on a fresh Amazon Linux 2023 or Ubuntu EC2 instance.

set -e

echo "🚀 Starting Clearpath RAG Chatbot Deployment..."

# 1. Update system and install Docker
echo "📦 Installing Docker and dependencies..."
sudo yum update -y || sudo apt-get update -y
sudo yum install -y docker || sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 2. Install Docker Compose
echo "🛠️ Installing Docker Compose..."
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# 3. Request environment variables from user if .env doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Configuring environment variables..."
    read -p "Enter Groq API Key (required): " groq_key
    
    cat <<EOF > .env
CLEARPATH_GROQ_API_KEY=$groq_key
CLEARPATH_ALLOWED_ORIGINS=http://localhost,http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
CLEARPATH_LOG_LEVEL=INFO
CLEARPATH_FAISS_INDEX_PATH=backend/data/faiss_index
CLEARPATH_PDF_DIR=backend/data/pdfs/clearpath_docs
CLEARPATH_LOG_FILE_PATH=backend/data/logs/queries.jsonl
VITE_API_BASE_URL=
EOF
    echo "✅ .env file created."
fi

# 4. Build and start production containers
echo "🏗️ Building and starting containers..."
docker compose -f docker-compose.prod.yml up --build -d

echo "----------------------------------------------------"
echo "🎉 Deployment Successful!"
echo "Your chatbot is now running."
echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "----------------------------------------------------"
