"""Deliver the unified collection while retaining independent source projects."""
import sys
from collection import build,install
if __name__=='__main__':
 build()
 if '--assemble' not in sys.argv:install()
