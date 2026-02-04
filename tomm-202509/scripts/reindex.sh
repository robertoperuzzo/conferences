#!/bin/bash

# Typesense Re-indexing Helper Script
# This script makes it easy to re-index collections with common configurations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MAX_DOCS=5
FORCE_RECREATE=true
LOG_LEVEL="INFO"

print_usage() {
    echo -e "${BLUE}Typesense Re-indexing Helper${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -a, --all               Re-index all extraction methods and strategies"
    echo "  -m, --method METHOD     Re-index specific extraction method"
    echo "  -s, --strategy STRATEGY Re-index specific chunking strategy"
    echo "  -d, --docs NUM          Number of documents to process (default: 5, use -1 for all)"
    echo "  -p, --production        Production mode (all documents, verbose logging)"
    echo "  -q, --quick             Quick mode (3 documents, minimal logging)"
    echo "  -n, --no-recreate       Don't force recreation of collections"
    echo "  --stats                 Show collection statistics only"
    echo "  --list                  List available extraction methods only"
    echo ""
    echo "Examples:"
    echo "  ./scripts/reindex.sh -a                   # Re-index all with 5 docs (development)"
    echo "  ./scripts/reindex.sh -a -p                # Re-index all with all docs (production)"
    echo "  ./scripts/reindex.sh -m unstructured      # Re-index unstructured extraction method"
    echo "  ./scripts/reindex.sh -q                   # Quick re-index with 3 docs"
    echo "  ./scripts/reindex.sh --stats              # Show collection statistics"
}

run_indexer() {
    local cmd="python -m src.indexer"
    
    if [ "$SHOW_STATS" = true ]; then
        cmd="$cmd --stats"
    elif [ "$LIST_METHODS" = true ]; then
        cmd="$cmd --list-methods"
    else
        if [ "$INDEX_ALL" = true ]; then
            cmd="$cmd --index-all"
        fi
        
        if [ -n "$EXTRACTION_METHOD" ]; then
            cmd="$cmd --extraction-method $EXTRACTION_METHOD"
        fi
        
        if [ -n "$CHUNKING_STRATEGY" ]; then
            cmd="$cmd --chunking-strategy $CHUNKING_STRATEGY"
        fi
        
        cmd="$cmd --max-documents $MAX_DOCS"
        
        if [ "$FORCE_RECREATE" = true ]; then
            cmd="$cmd --force-recreate"
        fi
    fi
    
    cmd="$cmd --log-level $LOG_LEVEL"
    
    echo -e "${BLUE}Running:${NC} $cmd"
    echo ""
    
    # Change to workspace directory
    cd /workspace
    
    # Run the command
    eval $cmd
}

check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "src/indexer/__main__.py" ] && [ ! -f "src/indexer/cli.py" ]; then
        echo -e "${RED}Error: Not in workspace directory or indexer module not found${NC}"
        echo "Please run this script from the /workspace directory"
        exit 1
    fi
    
    # Check if Typesense is accessible
    if ! curl -s http://localhost:8108/health > /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Typesense might not be running at localhost:8108${NC}"
        echo "Make sure Typesense service is started"
    fi
    
    # Check if data directories exist
    if [ ! -d "data/processed" ] || [ ! -d "data/chunks" ]; then
        echo -e "${RED}Error: Data directories not found${NC}"
        echo "Expected: data/processed/ and data/chunks/"
        exit 1
    fi
    
    echo -e "${GREEN}Prerequisites OK${NC}"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -a|--all)
            INDEX_ALL=true
            shift
            ;;
        -m|--method)
            EXTRACTION_METHOD="$2"
            shift 2
            ;;
        -s|--strategy)
            CHUNKING_STRATEGY="$2"
            shift 2
            ;;
        -d|--docs)
            MAX_DOCS="$2"
            shift 2
            ;;
        -p|--production)
            MAX_DOCS=-1
            LOG_LEVEL="INFO"
            echo -e "${YELLOW}Production mode: Processing ALL documents${NC}"
            shift
            ;;
        -q|--quick)
            MAX_DOCS=3
            LOG_LEVEL="WARNING"
            echo -e "${YELLOW}Quick mode: Processing 3 documents only${NC}"
            shift
            ;;
        -n|--no-recreate)
            FORCE_RECREATE=false
            shift
            ;;
        --stats)
            SHOW_STATS=true
            shift
            ;;
        --list)
            LIST_METHODS=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [ "$INDEX_ALL" != true ] && [ -z "$EXTRACTION_METHOD" ] && [ "$SHOW_STATS" != true ] && [ "$LIST_METHODS" != true ]; then
    echo -e "${RED}Error: Must specify --all, --method, --stats, or --list${NC}"
    print_usage
    exit 1
fi

if [ -n "$CHUNKING_STRATEGY" ] && [ -z "$EXTRACTION_METHOD" ]; then
    echo -e "${RED}Error: --strategy requires --method${NC}"
    print_usage
    exit 1
fi

# Main execution
echo -e "${GREEN}Typesense Re-indexing Helper${NC}"
echo "================================"
echo ""

check_prerequisites

if [ "$SHOW_STATS" != true ] && [ "$LIST_METHODS" != true ]; then
    echo -e "${BLUE}Configuration:${NC}"
    if [ "$INDEX_ALL" = true ]; then
        echo "  Mode: Index all extraction methods and strategies"
    else
        echo "  Mode: Index specific extraction method"
        echo "  Extraction Method: $EXTRACTION_METHOD"
        if [ -n "$CHUNKING_STRATEGY" ]; then
            echo "  Chunking Strategy: $CHUNKING_STRATEGY"
        fi
    fi
    echo "  Max Documents: $MAX_DOCS"
    echo "  Force Recreate: $FORCE_RECREATE"
    echo "  Log Level: $LOG_LEVEL"
    echo ""
    
    # Estimate time
    if [ "$MAX_DOCS" = "-1" ]; then
        echo -e "${YELLOW}⏱️  Estimated time: 1-2 hours (full dataset)${NC}"
    elif [ "$MAX_DOCS" -le 5 ]; then
        echo -e "${YELLOW}⏱️  Estimated time: 5-10 minutes${NC}"
    else
        echo -e "${YELLOW}⏱️  Estimated time: 10-30 minutes${NC}"
    fi
    echo ""
    
    read -p "Continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    echo ""
fi

# Run the indexer
echo -e "${GREEN}Starting re-indexing...${NC}"
echo ""

if run_indexer; then
    echo ""
    echo -e "${GREEN}✅ Re-indexing completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Refresh your frontend application"
    echo "2. Test search functionality"
    echo "3. Verify scores are displaying correctly"
    echo ""
    echo "Logs saved to: /workspace/logs/indexer.log"
else
    echo ""
    echo -e "${RED}❌ Re-indexing failed!${NC}"
    echo "Check the logs for more details: /workspace/logs/indexer.log"
    exit 1
fi
