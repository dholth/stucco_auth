"""
Minimal ctypes binding for cracklib.

Daniel Holth <dholth@fastmail.fm>
"""

from ctypes import CDLL, c_char_p
from ctypes.util import find_library

_cracklib = CDLL(find_library('crack'))

_cracklib.FascistCheck.restype = c_char_p

def fascist_check(pw, dictpath="/usr/share/cracklib/pw_dict"):
    """Check password pw against dictionary, returning an error message or None."""
    if isinstance(pw, unicode):
        pw = pw.encode('utf-8')
    if isinstance(pw, basestring) and isinstance(dictpath, basestring):
        return _cracklib.FascistCheck(pw, dictpath)
    raise TypeError("Arguments must be strings.")
