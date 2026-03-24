## Update Script
```bash
cd /home/sanamo/MCMerchant/MerchantBot
docker build -t merchantbot:latest .
docker rm -f merchantbot 2>/dev/null || true
docker run -d \
  --name merchantbot \
  --restart unless-stopped \
  --env-file .env \
  -p 8088:8088 \
  -v merchantbot_data:/data \
  merchantbot:latest
```