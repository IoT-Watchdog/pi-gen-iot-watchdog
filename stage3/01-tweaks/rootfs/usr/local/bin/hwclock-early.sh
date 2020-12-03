#!/bin/sh
# time!

echo "current time sw: $(date)"
for i in `seq 1 10`; do
  /sbin/hwclock --hctosys 2>/dev/null && echo "hwclock-early success rnd 1.$i: $(hwclock --get)" && exit 0
  sleep 0.2
done
for i in `seq 1 10`; do
  /sbin/hwclock --hctosys 2>/dev/null && echo "hwclock-early success rnd 2.$i: $(hwclock --get)" && exit 0
  sleep 1
done
for i in `seq 1 10`; do
  /sbin/hwclock --hctosys 2>/dev/null && echo "hwclock-early success rnd 3.$i: $(hwclock --get)" && exit 0
  sleep 5
done
echo "all tries (1 minute) for hwclock unsuccessful, exit"
exit 1
