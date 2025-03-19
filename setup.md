# **Automated Setup and Deployment of LyikServices with Docker**

## **1. System Preparation**

1. **Update and Install Prerequisites**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install docker docker-compose -y
    ```
    
2. **Verify Docker Installation**:
    ```bash
    docker --version
    docker-compose --version
    ```

---

## **2. Clone the Repository**

1. **Clone the LyikServices Repository**:
    ```bash
    git clone https://github.com/lyikadmin/lyik_service.git
    cd lyik_service
    ```

2. **Initialize Git LFS**:
    ```bash
    git lfs install
    git lfs pull
    ```

---

## **3. Create the Required Files**

### **3.1 Create the `Dockerfile`**

Inside the **project root**, create a file named `Dockerfile`:

```dockerfile
# Use the official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Initialize Git LFS
RUN git lfs install

# Copy only the requirements file to leverage Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

### **3.2 Create the `nginx.conf` File**

Inside the project root, create **`nginx.conf`**:

```nginx
server {
    listen 80;
    server_name lyikservices.lyik.com www.lyikservices.lyik.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name lyikservices.lyik.com www.lyikservices.lyik.com;

    ssl_certificate /etc/letsencrypt/live/lyikservices.lyik.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lyikservices.lyik.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305";

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### **3.3 Create the `docker-compose.yml` File**

Inside the **project root**, create **`docker-compose.yml`**:

```yaml
version: '1'

services:
  app:
    build: .
    container_name: lyikservices
    restart: always
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - uploads:/data/uploads

  nginx:
    image: nginx:latest
    container_name: lyik_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - app

  certbot:
    image: certbot/certbot
    container_name: lyik_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: sh -c "certbot certonly --webroot --webroot-path=/var/www/certbot --email you@example.com --agree-tos --no-eff-email --force-renewal -d lyikservices.lyik.com -d www.lyikservices.lyik.com"

volumes:
  uploads:  # Persistent volume for file uploads

```

---

## **4. Start Everything**

Now that all files are created, build and start everything:

```bash
docker-compose up -d --build
```

Verify running containers:
```bash
docker ps
```

Check if FastAPI is running:
```bash
curl -I http://127.0.0.1:8000/docs
```

---

## **5. Set Up Automatic SSL Renewal**

1. Open the crontab:
   ```bash
   sudo crontab -e
   ```
2. Add this line to renew SSL every **Monday at 3 AM**:
   ```
   0 3 * * 1 docker-compose run certbot renew && docker-compose restart nginx
   ```

---

## **6. Updating the Deployment**

When you need to update the app:
```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```