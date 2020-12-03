#!/bin/bash
cd /etc/apache2/mods-enabled
ln -s ../mods-available/headers.load
ln -s ../mods-available/rewrite.load
ln -s ../mods-available/proxy.conf
ln -s ../mods-available/proxy_html.conf
ln -s ../mods-available/proxy.load
ln -s ../mods-available/proxy_html.load
ln -s ../mods-available/proxy_http.load
