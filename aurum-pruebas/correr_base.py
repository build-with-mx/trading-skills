import sys
sys.argv=["x"]
from base_sim import codigo
__file__ = __import__("os").path.abspath("prueba_general.py")
exec(codigo())
