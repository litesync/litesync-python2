#!/bin/sh
python2.7 setup.py build
(cd build/lib.linux-x86_64-2.7 && python2.7 -c "from litesync import test; test.test()" )

