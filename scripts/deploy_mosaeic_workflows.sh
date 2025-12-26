#!/bin/bash
#
# Deploy MoSAEIC v1 n8n workflows to VPS
# Feature: MoSAEIC (Mental State Capture)
#
# Prerequisites:
#   1. SSH access to VPS (72.61.78.89) as mani or root
#   2. n8n running on VPS at port 5678
#   3. N8N_API_KEY configured in n8n instance
#
# Environment Variables Required on VPS n8n:
#   - MEMORY_WEBHOOK_TOKEN: HMAC signature validation
#   - NEO4J_BASIC_AUTH: Base64 encoded "neo4j:password"
#
# Usage:
#   ./scripts/deploy_mosaeic_workflows.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$PROJECT_ROOT/n8n-workflows"

VPS_HOST="${VPS_HOST:-72.61.78.89}"
VPS_USER="${VPS_USER:-mani}"
N8N_PORT="${N8N_PORT:-5678}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "MoSAEIC v1 Workflow Deployment"
echo "Target: $VPS_HOST"
echo "=========================================="
echo

# MoSAEIC workflows to deploy
MOSAEIC_WORKFLOWS=(
    "mosaeic_v1_capture_create.json"
    "mosaeic_v1_pattern_detect.json"
    "mosaeic_v1_profile_initialize.json"
)

# Check if workflow files exist
echo "Checking workflow files..."
for workflow in "${MOSAEIC_WORKFLOWS[@]}"; do
    if [[ -f "$WORKFLOWS_DIR/$workflow" ]]; then
        echo -e "  ${GREEN}✓${NC} $workflow"
    else
        echo -e "  ${RED}✗${NC} $workflow (NOT FOUND)"
        exit 1
    fi
done
echo

# Check SSH connectivity
echo "Testing SSH connectivity..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes "$VPS_USER@$VPS_HOST" exit 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} SSH connection successful"
else
    echo -e "  ${RED}✗${NC} Cannot connect via SSH to $VPS_USER@$VPS_HOST"
    echo "  Add your SSH key: ssh-copy-id $VPS_USER@$VPS_HOST"
    exit 1
fi
echo

# Check if n8n is running on VPS
echo "Checking n8n on VPS..."
N8N_STATUS=$(ssh "$VPS_USER@$VPS_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:$N8N_PORT/healthz" 2>/dev/null || echo "000")
if [[ "$N8N_STATUS" == "200" ]]; then
    echo -e "  ${GREEN}✓${NC} n8n is running on port $N8N_PORT"
else
    echo -e "  ${RED}✗${NC} n8n not responding (HTTP $N8N_STATUS)"
    echo "  Check if n8n container is running: docker ps | grep n8n"
    exit 1
fi
echo

# Create temporary directory on VPS
echo "Preparing deployment..."
TMP_DIR=$(ssh "$VPS_USER@$VPS_HOST" "mktemp -d")

# Copy workflows to VPS
echo "Copying workflows to VPS..."
for workflow in "${MOSAEIC_WORKFLOWS[@]}"; do
    scp -q "$WORKFLOWS_DIR/$workflow" "$VPS_USER@$VPS_HOST:$TMP_DIR/"
    echo -e "  ${GREEN}✓${NC} Copied $workflow"
done
echo

# Display deployment options
echo "=========================================="
echo "Deployment Options"
echo "=========================================="
echo
echo "The workflows have been copied to: $VPS_HOST:$TMP_DIR"
echo
echo -e "${YELLOW}Option 1: Manual Import via n8n UI${NC}"
echo "  1. SSH tunnel: ssh -L 5678:localhost:5678 $VPS_USER@$VPS_HOST"
echo "  2. Open: http://localhost:5678"
echo "  3. Workflows > Import from File"
echo "  4. Import each workflow from $TMP_DIR/"
echo "  5. Configure environment variables (see below)"
echo "  6. Activate each workflow"
echo
echo -e "${YELLOW}Option 2: n8n CLI Import${NC}"
echo "  SSH into VPS and run:"
echo "    docker exec n8n n8n import:workflow --input=$TMP_DIR/mosaeic_v1_capture_create.json"
echo "    docker exec n8n n8n import:workflow --input=$TMP_DIR/mosaeic_v1_pattern_detect.json"
echo "    docker exec n8n n8n import:workflow --input=$TMP_DIR/mosaeic_v1_profile_initialize.json"
echo
echo -e "${YELLOW}Option 3: n8n REST API Import${NC}"
echo "  Requires N8N_API_KEY. See curl examples below."
echo
echo "=========================================="
echo "Required n8n Environment Variables"
echo "=========================================="
echo
echo "Set these in n8n Settings > Environment Variables:"
echo
echo "  MEMORY_WEBHOOK_TOKEN=<your-webhook-secret>"
echo "    Used for HMAC signature validation on incoming requests"
echo
echo "  NEO4J_BASIC_AUTH=<base64-encoded-credentials>"
echo "    Format: base64('neo4j:your-password')"
echo "    Generate: echo -n 'neo4j:yourpassword' | base64"
echo
echo "=========================================="
echo "Webhook Endpoints (after activation)"
echo "=========================================="
echo
echo "  POST http://$VPS_HOST:$N8N_PORT/webhook/mosaeic/v1/profile/initialize"
echo "       Initialize user profile with SelfConcept, Aspects, ThreatPredictions"
echo
echo "  POST http://$VPS_HOST:$N8N_PORT/webhook/mosaeic/v1/capture/create"
echo "       Create MoSAEIC capture (5 windows: senses, actions, emotions, impulses, cognitions)"
echo
echo "  POST http://$VPS_HOST:$N8N_PORT/webhook/mosaeic/v1/pattern/detect"
echo "       Detect patterns from captures (recurring beliefs, behaviors)"
echo
echo "=========================================="
echo "cURL API Import Examples"
echo "=========================================="
echo
echo "# Get API key from n8n Settings > API > Create API Key"
echo "export N8N_API_KEY='your-api-key'"
echo
echo "# Import workflows"
for workflow in "${MOSAEIC_WORKFLOWS[@]}"; do
    name="${workflow%.json}"
    echo "curl -X POST 'http://localhost:5678/api/v1/workflows' \\"
    echo "  -H 'X-N8N-API-KEY: \$N8N_API_KEY' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d @$TMP_DIR/$workflow"
    echo
done
echo

# Cleanup instruction
echo "=========================================="
echo "Cleanup"
echo "=========================================="
echo "After importing, remove temp files:"
echo "  ssh $VPS_USER@$VPS_HOST 'rm -rf $TMP_DIR'"
echo
echo -e "${GREEN}Workflow files staged successfully!${NC}"
