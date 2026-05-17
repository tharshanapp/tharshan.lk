# OpenGov AI Assistant

A production-ready, full-stack RAG (Retrieval Augmented Generation) AI web application designed for Sri Lankan government officers to query Financial Regulations (FR), Procurement Guidelines, and Expenditure Codes (ECode) using natural language.

![OpenGov AI Assistant](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-Government%20Use-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.104-green)

## 🌟 Features

- **AI-Powered Q&A**: Ask questions in natural language and get accurate answers from official documents
- **RAG Technology**: Combines vector search with Google Gemini AI for precise responses
- **Source Citations**: Every answer includes references to source PDFs and page numbers
- **Multi-Category Support**: Separate knowledge bases for FR, Procurement Guidelines, and ECode
- **Web-Based PDF Upload**: Easy document management through the admin interface
- **Modern UI**: Professional government portal design with responsive layout
- **Production Ready**: Docker support, SSL ready, rate limiting, and security features

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │    AI Services  │
│  (HTML/CSS/JS)  │◄──►│   (FastAPI)      │◄──►│  (Gemini API)   │
│                 │    │                  │    │                 │
│  • Chat UI      │    │  • REST API      │    │  • LLM          │
│  • Admin Panel  │    │  • RAG Engine    │    │  • Embeddings   │
│  • File Upload  │    │  • Vector DB     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │   ChromaDB       │
                     │   (Vector DB)    │
                     └──────────────────┘
```

## 📁 Project Structure

```
OpenGov_AI_Assistant/
├── frontend/
│   ├── index.html          # Main SPA interface
│   ├── style.css           # Custom styles (glassmorphism theme)
│   ├── app.js              # Frontend JavaScript
│   └── assets/             # Images and icons
│
├── backend/
│   ├── main.py             # FastAPI application
│   ├── rag_engine.py       # RAG engine (ChromaDB integration)
│   ├── ingest.py           # PDF ingestion script
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   │
│   ├── data/
│   │   ├── FR/             # Financial Regulations PDFs
│   │   ├── Procurement/    # Procurement Guidelines PDFs
│   │   └── ECode/          # Expenditure Codes PDFs
│   │
│   └── vector_db/          # ChromaDB persistence (auto-created)
│
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Container orchestration
├── nginx.conf              # Nginx reverse proxy config
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Git

### ⚡ Quick Deploy (Automated)

```bash
# Make the quick-start script executable
chmod +x quick-start.sh

# Run the automated deployment script
./quick-start.sh
```

This script will:
- Check Docker installation
- Generate SSL certificates
- Configure environment variables
- Deploy the application

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/opengov-ai-assistant.git
cd opengov-ai-assistant
```

### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env file with your settings
nano backend/.env
```

**Required Environment Variables:**

```env
# Google Gemini API Key (REQUIRED)
GEMINI_API_KEY=your_actual_api_key_here

# Admin Token (change this!)
ADMIN_TOKEN=your_secure_random_token_here

# Application Settings
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Vector DB Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 3. Add PDF Documents

Place your PDF documents in the appropriate folders:

```bash
# Financial Regulations
cp your_fr_document.pdf backend/data/FR/

# Procurement Guidelines
cp your_procurement_document.pdf backend/data/Procurement/

# Expenditure Codes
cp your_ecode_document.pdf backend/data/ECode/
```

### 4. Run with Docker (Recommended)

```bash
# Build and start containers
docker-compose up -d

# Check logs
docker-compose logs -f opengov-ai

# Stop containers
docker-compose down
```

**Access the application:** http://localhost:8000

### 5. Run Locally (Development)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Ingest PDFs into vector database
python ingest.py

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Access the application:** http://localhost:8000

## 📚 Usage Guide

### Asking Questions

1. Open the application in your browser
2. Select a category from the dropdown (FR, Procurement, or ECode)
3. Type your question in the input field
4. Click "Ask AI" or press Enter
5. View the AI response with source citations

### Uploading Documents (Admin)

1. Click "Upload PDF" in the navigation
2. Enter the admin token (from `.env` file)
3. Click "Login"
4. Drag & drop or browse to select a PDF file
5. Select the appropriate category
6. Click "Upload & Process"
7. Wait for processing to complete

### Example Questions

**Financial Regulations:**
- "What are the rules for travel allowances?"
- "How do I process a payment voucher?"
- "What is the approval process for expenditures?"

**Procurement Guidelines:**
- "Explain the tender evaluation process"
- "What are the thresholds for different procurement methods?"
- "How to handle emergency procurement?"

**Expenditure Codes:**
- "What is the code for office supplies?"
- "How to classify capital expenditures?"
- "What code should be used for vehicle maintenance?"

## 🌐 Deployment

### GitHub Deployment

1. **Create a GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: OpenGov AI Assistant"
   git branch -M main
   git remote add origin https://github.com/yourusername/opengov-ai-assistant.git
   git push -u origin main
   ```

2. **Add to GitHub:**
   - Go to GitHub and create a new repository
   - Follow the instructions to push existing code

### VPS Deployment (Ubuntu/Debian)

#### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y
```

#### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/opengov-ai-assistant.git
cd opengov-ai-assistant

# Configure environment
cp backend/.env.example backend/.env
nano backend/.env  # Edit with your settings

# Add PDF documents
# Place your PDFs in backend/data/FR/, Procurement/, ECode/

# Build and run
docker-compose up -d

# Check status
docker-compose ps
```

#### 3. Configure Domain (tharshan.lk)

**Point your domain to server IP:**

1. Go to your domain registrar (e.g., Namecheap, GoDaddy)
2. Add A record: `@` → `YOUR_SERVER_IP`
3. Add A record: `www` → `YOUR_SERVER_IP`

**Update nginx.conf:**

```nginx
server_name tharshan.lk www.tharshan.lk;  # Already configured
```

#### 4. SSL Certificate Setup (Let's Encrypt - Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot certonly --standalone -d tharshan.lk -d www.tharshan.lk

# Certificates will be at:
# /etc/letsencrypt/live/tharshan.lk/fullchain.pem
# /etc/letsencrypt/live/tharshan.lk/privkey.pem

# Update nginx.conf to use these paths or copy to ssl/ folder
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/tharshan.lk/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/tharshan.lk/privkey.pem ssl/private.key

# Restart services
docker-compose restart nginx
```

**Auto-renewal:**

```bash
# Add to crontab
sudo crontab -e

# Add this line (renews daily at 2 AM)
0 2 * * * certbot renew --quiet
```

#### 5. HTTP-Only Deployment (If HTTPS is not available)

If you cannot set up SSL certificates, the application will work on HTTP:

```bash
# Access via HTTP
http://tharshan.lk
http://www.tharshan.lk

# Or directly via port 8000 (without nginx)
http://your-server-ip:8000
```

> **Note:** The application is configured to work on both HTTP (port 80) and HTTPS (port 443). If SSL certificates are not available, HTTP will still work.

### Render.com Deployment

1. **Create a new Web Service on Render**
2. **Connect your GitHub repository**
3. **Configure build and start commands:**

   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   - `GEMINI_API_KEY`: Your Gemini API key
   - `ADMIN_TOKEN`: Your secure admin token
   - `APP_ENV`: `production`

5. **Deploy**

> **Note:** Render's free tier has limitations. For production use, consider a paid plan or VPS deployment.

## 🔧 API Reference

### Endpoints

#### POST `/ask`
Ask a question to the AI assistant.

**Request:**
```json
{
  "question": "What are the travel allowance rates?",
  "category": "FR"
}
```

**Response:**
```json
{
  "answer": "According to the Financial Regulations...",
  "sources": [
    {
      "source": "FR_Guidelines_2023.pdf",
      "page": 15,
      "relevance_score": 0.92
    }
  ],
  "category": "FR",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### POST `/admin/upload`
Upload a PDF document (requires admin token).

**Headers:**
```
Authorization: Bearer YOUR_ADMIN_TOKEN
```

**Form Data:**
- `file`: PDF file
- `category`: FR | Procurement | ECode

#### GET `/stats/{category}`
Get statistics for a category (requires admin token).

#### GET `/health`
Health check endpoint.

## 🔒 Security Features

- **API Key Protection**: Gemini API key stored in environment variables
- **CORS Configuration**: Configurable allowed origins
- **Input Validation**: Question validation and prompt injection prevention
- **Rate Limiting**: API rate limiting (configurable)
- **Admin Authentication**: Token-based admin access
- **SSL/TLS Support**: Production-ready SSL configuration
- **Security Headers**: X-Frame-Options, CSP, etc.

## 🛠️ Troubleshooting

### Common Issues

**1. "Gemini API not configured" warning**
- Solution: Set `GEMINI_API_KEY` in `.env` file

**2. "No relevant information found"**
- Solution: Upload PDF documents to the appropriate category folders

**3. "Connection error" in frontend**
- Solution: Ensure backend is running and CORS is properly configured

**4. Docker build fails**
- Solution: Increase Docker memory limit or use `--no-cache` flag

**5. Vector database errors**
- Solution: Delete `backend/vector_db/` folder and restart

### Viewing Logs

```bash
# Docker logs
docker-compose logs -f opengov-ai

# Application logs (local deployment)
tail -f backend/logs/app.log
```

### Reset Everything

```bash
# Stop and remove containers
docker-compose down -v

# Remove vector database
rm -rf backend/vector_db/

# Restart
docker-compose up -d
```

## 📊 Performance Optimization

### For Large Document Collections

1. **Increase chunk size** (in `.env`):
   ```env
   CHUNK_SIZE=1500
   CHUNK_OVERLAP=300
   ```

2. **Use more powerful embeddings** (modify `rag_engine.py`):
   ```python
   model_name="sentence-transformers/all-mpnet-base-v2"
   ```

3. **Increase similarity search results**:
   ```python
   k=10  # Instead of default 5
   ```

### For High Traffic

1. **Enable caching** (nginx.conf already configured)
2. **Increase rate limits** if needed
3. **Use multiple workers** in Docker:
   ```bash
   docker-compose up -d --scale opengov-ai=3
   ```
4. **Add Redis** for session management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed for Government Use only. See LICENSE file for details.

## 👨‍💻 Developer

**Developed by Tharshan.lk**

- Website: [https://tharshan.lk](https://tharshan.lk)
- Email: info@tharshan.lk

## 🙏 Acknowledgments

- **Google Gemini** - AI language model
- **LangChain** - LLM orchestration framework
- **ChromaDB** - Vector database
- **FastAPI** - Modern Python web framework
- **Bootstrap** - Frontend framework
- **Font Awesome** - Icons

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Contact: info@tharshan.lk
- Documentation: [Wiki](https://github.com/yourusername/opengov-ai-assistant/wiki)

---

**Last Updated:** January 2024  
**Version:** 1.0.0