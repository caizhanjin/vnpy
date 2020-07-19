# !/bin/bash
source activate vnpy

cd /root/vnpy/accounts/account_test

ps -ef|grep run_noui.py|grep -v grep|cut -c 9-15|xargs kill -9

nohup python run_noui.py &

ps -aux | grep "run_noui.py"

echo "Successful startup !"



