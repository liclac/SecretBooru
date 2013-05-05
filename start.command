#!/bin/bash
cd "$( dirname "${BASH_SOURCE[0]}" )"
uwsgi --daemonize /dev/null --pidfile /tmp/secretbooru-uwsgi.pid --http 127.0.0.1:9000 -p 4 -M -H .. --pp . --module secretbooru --callable app 
