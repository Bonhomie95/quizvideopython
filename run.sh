cd /home/bonhomie/quizvideopython || exit 1

source .venv/bin/activate

python -m src.main >> logs/cron.log 2>&1
