#!/bin/bash
# IAS Curriculum VPS Deployment and Verification Script
# Run AFTER importing n8n workflow via UI
# Author: Dr. Mani Saint-Victor, MD
# Date: 2026-01-02

set -e

echo "=========================================="
echo "IAS Curriculum VPS Deployment"
echo "=========================================="
echo ""

# Configuration
VPS_HOST="72.61.78.89"
VPS_USER="mani"
SSH_KEY="$HOME/.ssh/mani_vps"
N8N_URL="https://$VPS_HOST:5678"
WEBHOOK_PATH="/webhook/ias/v1/manipulate"
WEBHOOK_URL="$N8N_URL$WEBHOOK_PATH"

echo "📋 Pre-flight checks..."
echo ""

# 1. Check VPS connectivity
echo "1️⃣ Checking VPS connectivity..."
if ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" "echo '✓ VPS accessible'"; then
    echo "✅ VPS connection successful"
else
    echo "❌ Cannot connect to VPS"
    exit 1
fi
echo ""

# 2. Check n8n status
echo "2️⃣ Checking n8n status..."
N8N_STATUS=$(ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" "docker ps --filter name=n8n --format '{{.Status}}'")
if [[ $N8N_STATUS == *"Up"* ]]; then
    echo "✅ n8n is running: $N8N_STATUS"
else
    echo "❌ n8n is not running"
    exit 1
fi
echo ""

# 3. Check HMAC secret
echo "3️⃣ Checking HMAC secret..."
HMAC_SET=$(ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" "docker exec n8n sh -c 'echo \$MEMEVOLVE_HMAC_SECRET' | wc -c")
if [ "$HMAC_SET" -gt 10 ]; then
    echo "✅ HMAC secret is configured"
else
    echo "⚠️  HMAC secret not set - workflow will reject requests"
    echo "   Set it in n8n container environment variables"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# 4. Verify workflow file is on VPS
echo "4️⃣ Verifying workflow file..."
if ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" "test -f /tmp/ias-unified-manager.json"; then
    echo "✅ Workflow file present: /tmp/ias-unified-manager.json"
else
    echo "❌ Workflow file not found on VPS"
    echo "   Copying now..."
    scp -i "$SSH_KEY" n8n-workflows/ias-unified-manager.json "$VPS_USER@$VPS_HOST:/tmp/"
    echo "✅ Workflow file copied"
fi
echo ""

# 5. Manual import reminder
echo "=========================================="
echo "⚠️  MANUAL STEP REQUIRED"
echo "=========================================="
echo ""
echo "You must import the workflow via n8n UI:"
echo ""
echo "1. Open browser: $N8N_URL"
echo "2. Navigate to: Workflows → Import from File"
echo "3. Select: /tmp/ias-unified-manager.json"
echo "4. Click 'Activate' toggle"
echo ""
echo "Press ENTER when workflow is imported and activated..."
read

echo ""
echo "6️⃣ Verifying webhook endpoint..."

# Try to access webhook (will fail if not activated, but that's expected)
WEBHOOK_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d '{"test":"ping"}' || echo "000")

if [ "$WEBHOOK_STATUS" == "401" ] || [ "$WEBHOOK_STATUS" == "400" ] || [ "$WEBHOOK_STATUS" == "500" ]; then
    echo "✅ Webhook endpoint is accessible (HTTP $WEBHOOK_STATUS)"
    echo "   (Error expected - we're not sending valid signature)"
elif [ "$WEBHOOK_STATUS" == "000" ] || [ "$WEBHOOK_STATUS" == "404" ]; then
    echo "❌ Webhook endpoint not accessible"
    echo "   Make sure workflow is activated in n8n"
    exit 1
else
    echo "✅ Webhook endpoint accessible (HTTP $WEBHOOK_STATUS)"
fi
echo ""

# 7. Copy population script to VPS
echo "7️⃣ Copying population script to VPS..."
scp -i "$SSH_KEY" scripts/populate_ias_unified.py "$VPS_USER@$VPS_HOST:/tmp/"
echo "✅ Population script copied"
echo ""

# 8. Prepare to run population
echo "=========================================="
echo "🚀 Ready to Populate Curriculum"
echo "=========================================="
echo ""
echo "Run this command on VPS to populate:"
echo ""
echo "ssh -i $SSH_KEY $VPS_USER@$VPS_HOST"
echo "cd /tmp"
echo "python3 populate_ias_unified.py"
echo ""
echo "Or run it from here:"
read -p "Run population now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "8️⃣ Populating IAS curriculum..."
    ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" "cd /tmp && python3 populate_ias_unified.py"
    echo ""
    echo "=========================================="
    echo "✅ IAS Curriculum Deployment Complete!"
    echo "=========================================="
else
    echo ""
    echo "⏸️  Population skipped - run manually when ready"
fi

echo ""
echo "📊 Deployment Summary:"
echo "  - VPS: $VPS_HOST"
echo "  - n8n URL: $N8N_URL"
echo "  - Webhook: $WEBHOOK_PATH"
echo "  - Workflow: ias-unified-manager"
echo "  - Status: Ready for use"
echo ""
echo "🎯 Next Steps:"
echo "  1. Test webhook with: curl -k $WEBHOOK_URL"
echo "  2. Update Replay Loop data when ready"
echo "  3. Build AI coaching integrations"
echo ""
