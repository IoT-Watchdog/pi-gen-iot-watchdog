#!/bin/bash

echo "setting mysql pw on first run:"
echo "ALTER USER 'root'@'localhost' IDENTIFIED BY 'jKD7ubqVeg';" | mysql -u root --skip-password
echo "done setting mysql pw on first run:"

mysql --defaults-extra-file=/etc/mysql/reset.cnf < /usr/local/bin/reset_ntopng.sql
