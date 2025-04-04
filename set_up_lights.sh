#!/bin/bash
# Run first command
sudo python plan.py

# Run second command in background and get its PID
sudo python view_plans.py &
PIDsecond=$!

# Wait 5 seconds
sleep 5

# Kill the second command
kill $PIDsecond

# Change directory and run web server
cd web
sudo python client.py