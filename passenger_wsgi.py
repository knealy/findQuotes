import sys, os

# Add your application directory to the Python path
INTERP = os.path.expanduser("/home/cloutroll/python/bin/python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add the application directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your Flask application
from run import app as application 