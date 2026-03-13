#!/bin/bash
# Simple wrapper around Makefile for backwards compatibility
# Use 'make help' for full options

case $1 in
    build)
        if [ "$2" = "all" ]; then
            make build-all
        else
            make build IMAGE="$2"
        fi
        ;;
    run)
        shift
        make run IMAGE="$1"
        ;;
    *)
        echo "This script is deprecated. Use Makefile instead:"
        echo ""
        make help
        ;;
esac
