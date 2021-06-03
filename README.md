LiteSync for Python 2.7
=======================

This is a fork of [pysqlite](https://github.com/ghaering/pysqlite)

Online documentation can be found [here](https://pysqlite.readthedocs.org/en/latest/sqlite3.html).


Installation
------------

You must install some LiteSync library for this one to work. It can be either
pre-compiled binaries or you can compile it by yourself. You can start with
the [free version](http://litesync.io/en/download.html).

Then run:

```
git clone --depth=1 https://gitlab.com/litesync/litesync-python2
cd litesync-python2
python setup.py build install
```


Usage
-----

```
import litesync
import json
import time

conn = litesync.connect('file:app.db?node=secondary&connect=tcp://server:port')

# check if the db is ready
while True:
    result = conn.cursor().execute("PRAGMA sync_status").fetchone()
    status = json.loads(result[0])
    if status["db_is_ready"]: break
    time.sleep(0.250)

# now we can use the db connection
...
```
