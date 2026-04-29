#!/bin/bash
# Expose local backend via Cloudflare Tunnel (no account needed for quick mode)
# Install once: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
#
# Usage: bash tunnel.sh
#
# The tunnel prints a URL like https://random-name.trycloudflare.com
# Paste that URL into:
#   - GitHub repo → Settings → Secrets → VITE_API_URL
#   - Then trigger a redeploy on Cloudflare Pages

echo "Starting Cloudflare Tunnel for backend (port 8000)..."
echo ""
echo "Copy the https://*.trycloudflare.com URL printed below."
echo "Paste it as VITE_API_URL in GitHub Secrets, then redeploy."
echo ""

cloudflared tunnel --url http://localhost:8000
