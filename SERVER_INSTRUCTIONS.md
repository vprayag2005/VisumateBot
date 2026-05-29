# Server Management Instructions

This document contains all the necessary commands and details to manage the VisumateBot on your Azure Linux VM.

## 1. Connecting to the Server
To log into your Azure virtual machine, open your local terminal and run:
```bash
ssh azureuser@4.240.92.54
```

## 2. Pulling Code Updates
If you make changes to your bot's code locally and push them to GitHub, you need to pull those updates onto the server so they take effect.
```bash
cd ~/VisumateBot
git pull origin main
```
*Note: Make sure to stop the running bot (Ctrl+C) before pulling changes, and then start it again afterward.*

## 3. Starting the Bot
To run the bot normally:
```bash
cd ~/VisumateBot
source venv/bin/activate
python3 main.py
```

## 4. Running the Bot 24/7 (Background)
If you just run `python3 main.py`, the bot will stop when you close your SSH terminal. To keep it running in the background, use `tmux`.

**Start a background session:**
```bash
tmux new -s bot
cd ~/VisumateBot
source venv/bin/activate
python3 main.py
```
**Leave it running (Detach):** 
Press `Ctrl + B`, let go of both keys, and then press `D`. You can now safely close your terminal.

**Return to the bot (Attach):**
Next time you log into the server, you can see the bot's logs by running:
```bash
tmux attach -t bot
```

## 5. Adding a Swap File (Fixing memory freezes)
Since video processing uses a lot of RAM, the `Standard_B2ats_v2` VM (1GB RAM) will freeze and crash. You must add a 4GB swap file (virtual memory) to fix this. Run these commands once:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
After running this, your VM will effectively have 5GB of memory and will no longer get completely stuck during video generation.
