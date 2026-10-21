#!/bin/bash
# Merkle Tree Signature Script
# Generates cryptographic Merkle tree signatures for repository files

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MERKLE_DIR=".merkle"
MERKLE_TREE_FILE="$MERKLE_DIR/tree.txt"
MERKLE_ROOT_FILE="$MERKLE_DIR/root.txt"
MERKLE_METADATA_FILE="$MERKLE_DIR/metadata.json"

# Function to display usage
usage() {
    echo "Usage: $0 [full|incremental]"
    echo ""
    echo "Arguments:"
    echo "  full         - Generate complete Merkle tree for all tracked files"
    echo "  incremental  - Update Merkle tree for changed files only (default)"
    echo ""
    echo "The script generates a cryptographic Merkle tree signature for repository files."
    exit 1
}

# Function to calculate SHA-256 hash of a file
hash_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        sha256sum "$file" | awk '{print $1}'
    else
        echo ""
    fi
}

# Function to hash two values together (for Merkle tree construction)
hash_pair() {
    local left="$1"
    local right="$2"
    echo -n "${left}${right}" | sha256sum | awk '{print $1}'
}

# Function to initialize Merkle directory
init_merkle_dir() {
    if [[ ! -d "$MERKLE_DIR" ]]; then
        echo -e "${YELLOW}Creating Merkle directory...${NC}"
        mkdir -p "$MERKLE_DIR"
        echo "$MERKLE_DIR/" >> .gitignore 2>/dev/null || true
    fi
}

# Function to get list of tracked files
get_tracked_files() {
    git ls-files | grep -v "^$MERKLE_DIR/" | sort
}

# Function to build Merkle tree
build_merkle_tree() {
    mode="$1"
    
    echo -e "${YELLOW}Building Merkle tree ($mode mode)...${NC}"
    
    # Get list of files
    if [[ "$mode" == "full" ]]; then
        files=$(get_tracked_files)
    else
        # For incremental, get changed files
        files=$(git diff --name-only HEAD 2>/dev/null || get_tracked_files)
        if [[ -z "$files" ]]; then
            echo -e "${GREEN}No changed files detected. Using all tracked files.${NC}"
            files=$(get_tracked_files)
        fi
    fi
    
    if [[ -z "$files" ]]; then
        echo -e "${RED}No files to process${NC}"
        return 1
    fi
    
    # Create temporary file for leaf hashes
    TEMP_HASHES=$(mktemp)
    > "$MERKLE_TREE_FILE"
    
    echo -e "${YELLOW}Hashing files...${NC}"
    count=0
    while IFS= read -r file; do
        if [[ -f "$file" ]] && [[ ! "$file" =~ ^\. ]]; then  # Skip hidden files
            file_hash=$(hash_file "$file")
            if [[ -n "$file_hash" ]]; then
                echo "$file:$file_hash" >> "$MERKLE_TREE_FILE"
                echo "$file_hash" >> "$TEMP_HASHES"
                count=$((count + 1))
                if [[ $((count % 50)) -eq 0 ]]; then
                    echo -e "  Processed $count files..."
                fi
            fi
        fi
    done <<< "$files"
    
    echo -e "${GREEN}Hashed $count files${NC}"
    
    # Build Merkle tree from leaf hashes
    CURRENT_LEVEL="$TEMP_HASHES"
    NEXT_LEVEL=$(mktemp)
    
    while [[ $(wc -l < "$CURRENT_LEVEL") -gt 1 ]]; do
        > "$NEXT_LEVEL"
        
        while read -r left; do
            read -r right || right="$left"  # Duplicate last if odd number
            parent=$(hash_pair "$left" "$right")
            echo "$parent" >> "$NEXT_LEVEL"
        done < "$CURRENT_LEVEL"
        
        rm "$CURRENT_LEVEL"
        CURRENT_LEVEL="$NEXT_LEVEL"
        NEXT_LEVEL=$(mktemp)
    done
    
    # The last remaining hash is the Merkle root
    merkle_root=$(cat "$CURRENT_LEVEL")
    echo "$merkle_root" > "$MERKLE_ROOT_FILE"
    
    # Cleanup temporary files
    rm -f "$CURRENT_LEVEL" "$NEXT_LEVEL" "$TEMP_HASHES"
    
    # Generate metadata
    cat > "$MERKLE_METADATA_FILE" << EOF
{
  "merkle_root": "$merkle_root",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "mode": "$mode",
  "file_count": $count,
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'N/A')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
}
EOF
    
    echo -e "${GREEN}✓ Merkle root: $merkle_root${NC}"
    echo -e "${GREEN}✓ Metadata saved to $MERKLE_METADATA_FILE${NC}"
    
    return 0
}

# Function to verify Merkle tree
verify_merkle_tree() {
    if [[ ! -f "$MERKLE_ROOT_FILE" ]]; then
        echo -e "${RED}No Merkle root found. Run with 'full' to generate.${NC}"
        return 1
    fi
    
    local stored_root=$(cat "$MERKLE_ROOT_FILE")
    echo -e "${YELLOW}Stored Merkle root: $stored_root${NC}"
    
    # TODO: Implement verification logic
    echo -e "${GREEN}✓ Merkle tree verification (placeholder)${NC}"
    
    return 0
}

# Main execution
main() {
    local mode="${1:-incremental}"
    
    if [[ "$mode" != "full" && "$mode" != "incremental" && "$mode" != "verify" ]]; then
        usage
    fi
    
    echo -e "${GREEN}=== Merkle Tree Signature System ===${NC}"
    echo ""
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}Error: Not a git repository${NC}"
        exit 1
    fi
    
    # Initialize Merkle directory
    init_merkle_dir
    
    # Execute based on mode
    case "$mode" in
        full|incremental)
            build_merkle_tree "$mode"
            ;;
        verify)
            verify_merkle_tree
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}=== Complete ===${NC}"
}

# Run main function
main "$@"
