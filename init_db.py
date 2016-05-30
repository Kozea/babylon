import os

from babylon import init_db

os.remove('/tmp/babylone.db')

init_db()
