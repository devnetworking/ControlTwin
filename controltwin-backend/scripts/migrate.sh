#!/bin/bash
# ControlTwin — Database Migration Script

set -e

COMMAND=${1:-"upgrade head"}
ENVIRONMENT=${2:-"development"}

echo "ControlTwin DB Migration"
echo "Command  : $COMMAND"
echo "Env      : $ENVIRONMENT"

case "$1" in
  "upgrade")
    echo "Upgrading to: ${2:-head}"
    python -m alembic upgrade ${2:-head}
    ;;
  "downgrade")
    echo "Downgrading to: ${2:-'-1'}"
    python -m alembic downgrade ${2:-'-1'}
    ;;
  "revision")
    echo "Creating revision: $2"
    python -m alembic revision --autogenerate -m "$2"
    ;;
  "history")
    python -m alembic history --verbose
    ;;
  "current")
    python -m alembic current --verbose
    ;;
  "seed")
    echo "Applying seed data..."
    python -m alembic upgrade 0002_seed
    ;;
  "reset")
    echo "WARNING: Full reset — downgrade to base then upgrade to head"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      python -m alembic downgrade base
      python -m alembic upgrade head
    fi
    ;;
  *)
    echo "Usage: $0 {upgrade|downgrade|revision|history|current|seed|reset} [target]"
    echo ""
    echo "Examples:"
    echo "  $0 upgrade              # upgrade to latest"
    echo "  $0 upgrade 0001         # upgrade to specific revision"
    echo "  $0 downgrade -1         # rollback one revision"
    echo "  $0 revision 'add_index' # create new autogenerate revision"
    echo "  $0 seed                 # apply seed data"
    echo "  $0 reset                # full reset (dev only)"
    exit 1
    ;;
esac

echo "Done."
