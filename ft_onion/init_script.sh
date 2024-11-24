#!/bin/bash
service ssh start

echo ". torsocks on" >> ~/.bashrc

exec supervisord -c /etc/supervisor/supervisord.conf