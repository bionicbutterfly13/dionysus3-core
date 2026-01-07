#!/bin/bash
# Ralph Orchestrator Skill - Dionysus Integration
# Invokes the customized ralph-orchestrator for iterative task completion

set -e

# Configuration
RALPH_DIR="/Volumes/Asylum/dev/dionysus3-core/ralph-orchestrator"
RALPH_CONFIG="$RALPH_DIR/ralph-dionysus.yml"
DEFAULT_PROMPT_FILE="PROMPT.md"
DEFAULT_MAX_ITERATIONS=50

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    local level=$1
    local msg=$2
    case $level in
        INFO) echo -e "${BLUE}[Ralph]${NC} $msg" ;;
        SUCCESS) echo -e "${GREEN}[Ralph]${NC} $msg" ;;
        WARN) echo -e "${YELLOW}[Ralph]${NC} $msg" ;;
        ERROR) echo -e "${RED}[Ralph]${NC} $msg" ;;
    esac
}

show_help() {
    cat << EOF
Ralph Orchestrator - Autonomous Iteration Engine

Usage: /ralph [OPTIONS] [PROMPT_TEXT]

Options:
    -f, --file FILE         Prompt file (default: PROMPT.md)
    -i, --iterations N      Max iterations (default: 50)
    -c, --cost AMOUNT       Max cost in USD (default: 10.0)
    -v, --verbose           Verbose output
    -d, --dry-run          Test mode without execution
    -h, --help             Show this help

Examples:
    /ralph                                  # Use PROMPT.md in current dir
    /ralph "Implement user authentication"  # Inline prompt
    /ralph -f my-task.md -i 100            # Custom file, 100 iterations
    /ralph -v "Debug the API endpoint"      # Verbose mode

The Ralph Wiggum Technique:
    "Put AI in a loop until task is done"

    Ralph continuously runs against a prompt file, checking git diffs
    and agent responses to determine completion. It integrates with:
    - HeartbeatAgent (OODA loop)
    - Meta-ToT (decision analysis)
    - Graphiti (knowledge graph context)

EOF
}

# Parse arguments
PROMPT_FILE="$DEFAULT_PROMPT_FILE"
MAX_ITERATIONS="$DEFAULT_MAX_ITERATIONS"
MAX_COST="10.0"
VERBOSE=""
DRY_RUN=""
INLINE_PROMPT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--file)
            PROMPT_FILE="$2"
            shift 2
            ;;
        -i|--iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        -c|--cost)
            MAX_COST="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        *)
            INLINE_PROMPT="$1"
            shift
            ;;
    esac
done

# Check if Ralph is installed
if [[ ! -d "$RALPH_DIR" ]]; then
    log ERROR "Ralph orchestrator not found at $RALPH_DIR"
    log INFO "Run: git clone https://github.com/mikeyobrien/ralph-orchestrator.git $RALPH_DIR"
    exit 1
fi

# Create inline prompt file if needed
if [[ -n "$INLINE_PROMPT" ]]; then
    PROMPT_FILE=".ralph_inline_prompt.md"
    log INFO "Creating inline prompt: $INLINE_PROMPT"
    cat > "$PROMPT_FILE" << EOF
# Ralph Task

$INLINE_PROMPT

## Success Criteria

The task is complete when:
- All requirements are implemented
- Tests pass
- Documentation is updated
- Code is committed to git

## Notes

This is an inline prompt. Ralph will iterate until completion signals are detected.
EOF
fi

# Verify prompt file exists
if [[ ! -f "$PROMPT_FILE" ]]; then
    log ERROR "Prompt file not found: $PROMPT_FILE"
    log INFO "Create a PROMPT.md file or use inline prompts: /ralph \"your task\""
    exit 1
fi

# Create Dionysus-specific config if needed
if [[ ! -f "$RALPH_CONFIG" ]]; then
    log INFO "Creating Dionysus-specific Ralph configuration"
    cat > "$RALPH_CONFIG" << 'CONFIGEOF'
# Ralph Orchestrator - Dionysus Configuration
# Customized for consciousness-aware autonomous reasoning

agent: auto
prompt_file: PROMPT.md
max_iterations: 50
max_runtime: 7200  # 2 hours
checkpoint_interval: 10
retry_delay: 2

# Resource limits
max_tokens: 500000
max_cost: 10.0
context_window: 200000
context_threshold: 0.8

# Features
archive_prompts: true
git_checkpoint: true
enable_metrics: true
verbose: false
dry_run: false

# Telemetry settings
iteration_telemetry: true
output_preview_length: 500

# Safety settings
max_prompt_size: 10485760
allow_unsafe_paths: false

# Adapter-specific configurations
adapters:
  claude:
    enabled: true
    timeout: 600  # 10 minutes for complex reasoning
    max_retries: 3
    tool_permissions:
      allow_all: true
CONFIGEOF
fi

# Run Ralph orchestrator
log INFO "🚀 Starting Ralph orchestrator"
log INFO "   Prompt: $PROMPT_FILE"
log INFO "   Max Iterations: $MAX_ITERATIONS"
log INFO "   Max Cost: \$$MAX_COST"

cd "$RALPH_DIR" || exit 1

# Activate virtual environment and run
if command -v uv &> /dev/null; then
    uv run python -m ralph_orchestrator \
        --config "$RALPH_CONFIG" \
        --prompt-file "$PWD/../$PROMPT_FILE" \
        --max-iterations "$MAX_ITERATIONS" \
        --max-cost "$MAX_COST" \
        $VERBOSE \
        $DRY_RUN
else
    log ERROR "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Cleanup inline prompt if used
if [[ -n "$INLINE_PROMPT" ]]; then
    rm -f "$PROMPT_FILE"
fi

log SUCCESS "✅ Ralph orchestration complete"
