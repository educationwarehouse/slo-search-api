#!/bin/bash
# Generate self-signed SSL certificate for development

mkdir -p ssl

if [ -f ssl/selfsigned.key ]; then
    echo "SSL certificates already exist in ssl/"
    read -p "Regenerate? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 0
    fi
fi

echo "Generating self-signed SSL certificate..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/selfsigned.key \
    -out ssl/selfsigned.crt \
    -subj "/C=NL/ST=Netherlands/L=Amsterdam/O=SLO/CN=localhost"

chmod 600 ssl/selfsigned.key
chmod 644 ssl/selfsigned.crt

echo "✓ SSL certificates generated in ssl/"
echo "⚠ These are self-signed - browsers will show warnings"
echo "For production, use Let's Encrypt: certbot certonly --webroot"
