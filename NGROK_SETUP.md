# 🌐 Ngrok Setup for External Access

This guide helps you expose your AI Support Bot to the internet using ngrok, allowing external access to both the chat interface and API.

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Ngrok Account
1. Go to [ngrok.com](https://ngrok.com) and sign up for free
2. Verify your email address
3. Log into your dashboard at [dashboard.ngrok.com](https://dashboard.ngrok.com)

### Step 2: Get Your Auth Token
1. In your ngrok dashboard, go to **"Your Authtoken"**
2. Copy your authtoken (looks like: `2ABC123...xyz`)
3. Run this command in terminal:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

### Step 3: Start Your AI Support Bot
```bash
# Make sure your bot is running
docker-compose up -d

# Verify services are up
docker-compose ps
```

### Step 4: Create Ngrok Tunnel
```bash
# Start ngrok tunnel (this will create a public URL)
ngrok http 80
```

You'll see output like:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:80
```

### Step 5: Access Your Bot Publicly! 🎉

**Your AI Support Bot is now live at the ngrok URL!**

- **Chat Interface**: `https://abc123.ngrok-free.app`
- **API Base**: `https://abc123.ngrok-free.app/api/v1/`
- **Health Check**: `https://abc123.ngrok-free.app/api/v1/health`

---

## 🔧 Advanced Usage

### Multiple Services (Paid Plan Required)

For paid ngrok accounts, you can expose both frontend and API separately:

```bash
# Terminal 1: Frontend
ngrok http 80 --subdomain=my-chatbot

# Terminal 2: API (requires paid plan)
ngrok http 8000 --subdomain=my-chatbot-api
```

### Using Configuration File

Create `~/.ngrok2/ngrok.yml`:
```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN_HERE
tunnels:
  frontend:
    proto: http
    addr: 80
    subdomain: my-ai-bot
  api:
    proto: http  
    addr: 8000
    subdomain: my-ai-bot-api
```

Then start both:
```bash
ngrok start --all
```

---

## 🛠️ API Testing with Public URL

Once ngrok is running, you can test the API from anywhere:

```bash
# Replace YOUR_NGROK_URL with your actual ngrok URL
export NGROK_URL="https://abc123.ngrok-free.app"

# Test chat API
curl -X POST $NGROK_URL/api/v1/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "How do I reset my password?"}'

# Test FAQ suggestions
curl $NGROK_URL/api/v1/faq/suggestions?limit=5

# Health check
curl $NGROK_URL/api/v1/health
```

---

## 📱 Mobile & External Access

Your AI Support Bot is now accessible from:

- **Any device on the internet**
- **Mobile phones** (responsive design)
- **Other developers** for API integration
- **Webhook integrations** 
- **Third-party applications**

---

## 🔒 Security Considerations

### Free Plan Limitations:
- URLs change every restart (use paid plan for consistent URLs)
- Limited to 1 tunnel simultaneously
- Basic rate limiting

### Production Recommendations:
- Use paid ngrok plan for stable subdomains
- Enable authentication: `ngrok http 80 --basic-auth="user:password"`
- Monitor usage in ngrok dashboard
- Consider VPN or firewall rules for sensitive data

---

## 🚨 Troubleshooting

### "Authentication Failed"
```bash
# Add your authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### "Port Not Available" 
```bash
# Check if Docker is running
docker-compose ps

# Restart services if needed
docker-compose restart
```

### "Tunnel Not Working"
```bash
# Check ngrok dashboard
open http://localhost:4040

# Verify local service works
curl http://localhost/api/v1/health
```

### Multiple Tunnels (Free Account)
Free accounts only support 1 tunnel. For multiple services:
1. Use the frontend tunnel (`/api/v1/` routes are proxied)
2. Or upgrade to paid plan
3. Or use alternative services like localtunnel

---

## 💡 Alternative Solutions

If ngrok doesn't work for you:

### 1. Localtunnel (Free)
```bash
npm install -g localtunnel
lt --port 80
```

### 2. Serveo (Free)
```bash
ssh -R 80:localhost:80 serveo.net
```

### 3. Bore (Free)
```bash
cargo install bore-cli
bore local 80 --to bore.pub
```

---

## 📞 Support

If you encounter issues:
1. Check [ngrok documentation](https://ngrok.com/docs)
2. Visit [ngrok community](https://community.ngrok.com) 
3. Review our [main README](./README.md)
4. Check [ngrok dashboard](https://dashboard.ngrok.com) for usage/errors

**Happy tunneling! 🚀**