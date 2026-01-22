#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset


alembic upgrade head
python -m app.check_db
uvicorn app.main:app --host 0.0.0.0 --port $PORT

