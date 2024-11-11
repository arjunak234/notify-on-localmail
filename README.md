# notify-on-localmail

Get desktop notification when you receive a local mail

# Installation

Copy the systemd unit and timer files to ~/.config/systemd/user/ and enable them with

`systemctl --user --now enable notify-on-localmail.timer`

Install the python script to `/usr/local/bin`

`sudo cp notify-on-localmail.py /usr/local/bin/`
