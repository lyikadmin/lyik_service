
## **1. System Preparation**

1. **Update and Install Prerequisites**:
    
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3.10 python3.10-venv python3-pip git git-lfs nginx ffmpeg screen -y
    ```
    
2. **Verify Installations**:
    
    ```bash
    python3.10 --version
    git --version
    git lfs --version
    nginx -v
    ffmpeg -version
    ```
    

---

## **2. Clone the Repository and Pull LFS Files**

1. **Clone Your Repository**:
    
    ```bash
    git clone https://github.com/lyikadmin/lyik_service.git
    cd lyik_service
    ```
    
2. **Initialise Git LFS and Pull Files**:
    
    ```bash
    git lfs install
    git lfs pull
    ```
    

---

## **3. Setup Virtual Environment**

1. **Create and Activate Virtual Environment**:
    
    ```bash
    python3.10 -m venv .venv
    source .venv/bin/activate
    ```
    
2. **Install Dependencies**:
    
    ```bash
    pip install -r requirements.txt
    ```
    

---

## **4. Prepare FastAPI Server**

1. **Start the FastAPI Server**:
    
    ```bash
    python app.py
    ```
    
---

## **5. Configure Nginx for Reverse Proxy**

1. **Create Nginx Configuration**:
    
    ```bash
    sudo nano /etc/nginx/sites-available/your_app
    ```
    
    **Add the Updated Configuration**:
    
    ```nginx
    server {
        listen 80;
        server_name 52.162.99.187;
    
        client_max_body_size 50M;
    
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```
    
2. **Enable Configuration and Test**:
    
    ```bash
    sudo ln -s /etc/nginx/sites-available/your_app /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t
    ```
    
3. **Restart Nginx**:
    
    ```bash
    sudo systemctl restart nginx
    ```

---

## **6. Start Application Using Screen**

1. **Install and Start a Screen Session**:
    
    ```bash
    sudo apt install screen -y
    screen -S myapp
    ```
    
2. **Run the FastAPI Server**:
    
    ```bash
    uvicorn app:app --host 127.0.0.1 --port 8000
    ```
    
3. **Detach from the Session**: Press `Ctrl+A`, then `D`.
    
4. **Reattach to the Session Later**:
    
    ```bash
    screen -r myapp
    ```
    

---

## **7. Final Testing**

1. **Access the API**:
    
    Open a browser and navigate to:
    
    ```
    http://52.162.99.187/docs
    ```
    
2. **Verify Endpoints**:
    
     `POST /process`
    

---

## **8. Maintenance and Updates**

1. **Check Logs**:
    
    ```bash
    tail -f /var/log/nginx/error.log
    ```
    
2. **Pull Updates**:
    
    ```bash
    git pull origin main
    pip install -r requirements.txt
    sudo systemctl restart nginx
    ```
    

---

## **8. Maintenance and Updates**

1. SSH into the server
    
    ```bash
    ssh -i <location/to/key.pem> lyikservices@98.70.99.42
    ```
    