#!/bin/sh
cd /home/suppord/autosanity2
git clone https://github.com/tndrcloud/autosanity_v2.git
mv ./autosanity_v2/* ./
rm -R ./autosanity_v2
chmod 777 ./*
rm -R /etc/asterisk/pjsip_custom
rm /etc/asterisk/pjsip.conf
mv ./extensions.conf /etc/asterisk/
mv ./pjsip.conf /etc/asterisk/
