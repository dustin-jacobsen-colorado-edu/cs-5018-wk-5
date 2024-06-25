release: ./release.sh
analyzer: PYTHONPATH="${PYTHONPATH}:$(pwd)" venv/bin/python src/analyzer.py 
poller: PYTHONPATH="${PYTHONPATH}:$(pwd)" venv/bin/python src/poller.py
web: PYTHONPATH="${PYTHONPATH}:$(pwd)" PORT="$PORT" venv/bin/python src/web.py 
