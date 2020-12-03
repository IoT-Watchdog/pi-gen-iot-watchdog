# IoT-Watchdog Image generator - via pi-gen 

before first build:
```
./prepare.sh
```
regular build:
```
./build.sh
```
## How does it work?

IoT-Watchdog uses [ntopng](https://github.com/ntop/ntopng/blob/dev/doc/README.geolocation.md) (community edition) to log network traffic.

Ntopng is configured to log traffic connections ("flows") into local mysql-db.

The IoT-Watchdog frontend [ng-unrvl](https://github.com/IoT-Watchdog/ng-unrvl) reads out the flows and displays it.

For displaying on the map, a local maxmind GeoIP DB is required.

### Notes on GeoIP database:

Maxmind's GeoIP database (var/lib/GeoIP) shall not be redistributed.

How to install it manually:

https://github.com/ntop/ntopng/blob/dev/doc/README.geolocation.md
