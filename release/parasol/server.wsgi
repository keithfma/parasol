# activate virtualenv - comment out if not needed
# see: http://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html
import os
python_home = '/home/keith/venv/p'
activate_this = os.path.join(python_home, 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

# import flask application with expected name
from parasol.server import app as application

