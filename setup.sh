#!/bin/bash

set -e

# Install SuperMemory MCP
echo "Installing SuperMemory MCP..."
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client vscode --oauth=yes

# Install cognee
echo "Installing cognee..."
pip3 install cognee

# Configure MCP for Claude Code CLI
echo "Configuring cognee MCP for Claude Code..."
CLAUDE_CONFIG="$HOME/.claude/settings.json"

if [ -f "$CLAUDE_CONFIG" ]; then
    # Merge with existing config using jq if available
    if command -v jq &> /dev/null; then
        jq '.mcpServers.cognee = {"command": "python3", "args": ["-m", "cognee.mcp"]}' "$CLAUDE_CONFIG" > "$CLAUDE_CONFIG.tmp" && mv "$CLAUDE_CONFIG.tmp" "$CLAUDE_CONFIG"
        echo "Updated existing Claude Code config."
    else
        echo "Warning: jq not installed. Please manually add cognee to $CLAUDE_CONFIG"
    fi
else
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"
    cat > "$CLAUDE_CONFIG" << 'EOF'
{
  "mcpServers": {
    "cognee": {
      "command": "python3",
      "args": ["-m", "cognee.mcp"]
    }
  }
}
EOF
    echo "Created new Claude Code config."
fi

# Also configure for Cline/Cursor (macOS path)
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLINE_CONFIG="$HOME/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
else
    CLINE_CONFIG="$HOME/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
fi

mkdir -p "$(dirname "$CLINE_CONFIG")"
if [ -f "$CLINE_CONFIG" ] && command -v jq &> /dev/null; then
    jq '.mcpServers.cognee = {"command": "python3", "args": ["-m", "cognee.mcp"]}' "$CLINE_CONFIG" > "$CLINE_CONFIG.tmp" && mv "$CLINE_CONFIG.tmp" "$CLINE_CONFIG"
    echo "Updated existing Cline/Cursor config."
else
    cat > "$CLINE_CONFIG" << 'EOF'
{
  "mcpServers": {
    "cognee": {
      "command": "python3",
      "args": ["-m", "cognee.mcp"]
    }
  }
}
EOF
    echo "Created new Cline/Cursor config."
fi

echo "Setup complete. Restart Claude Code and Cursor."
