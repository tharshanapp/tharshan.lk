#!/bin/bash
# ============================================
# SSL Certificate Generation Script
# For testing/development purposes only
# For production, use Let's Encrypt or real certificates
# ============================================

echo "Generating self-signed SSL certificates..."

# Create ssl directory if it doesn't exist
mkdir -p ssl
cd ssl

# Generate private key
openssl genrsa -out private.key 2048

# Generate certificate signing request (CSR)
openssl req -new -key private.key -out certificate.csr \
    -subj "/C=LK/ST=Western/L=Colombo/O=OpenGov/OU=IT/CN=tharshan.lk"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in certificate.csr -signkey private.key -out certificate.crt

# Set proper permissions
chmod 600 private.key
chmod 644 certificate.crt

echo "SSL certificates generated successfully!"
echo ""
echo "Generated files:"
echo "  - private.key (keep this secure!)"
echo "  - certificate.crt"
echo ""
echo "⚠️  WARNING: These are self-signed certificates for testing only."
echo "For production deployment, use Let's Encrypt or purchase real SSL certificates."
echo ""
echo "To use Let's Encrypt (recommended for production):"
echo "  1. Install certbot: sudo apt-get install certbot"
echo "  2. Generate certificates: sudo certbot certonly --standalone -d tharshan.lk -d www.tharshan.lk"
echo "  3. Copy certificates to this directory:"
echo "     sudo cp /etc/letsencrypt/live/tharshan.lk/fullchain.pem certificate.crt"
echo "     sudo cp /etc/letsencrypt/live/tharshan.lk/privkey.pem private.key"