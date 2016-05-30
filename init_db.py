import os

import babylon

os.remove('/tmp/babylone.db')
babylon.db.create_all()
