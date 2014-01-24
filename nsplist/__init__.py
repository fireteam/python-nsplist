__all__ = [
    'load', 'loads',
    'PListDecoder',
]

from .decoder import PListDecoder


_default_decoder = PListDecoder()


def load(fp):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a NeXTSTEP property list document) to a Python object.
    """
    return loads(fp.read())


def loads(s):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a
    NeXTSTEP property list document) to a Python object.

    If ``s`` is a ``str`` instance and is encoded with an ASCII based encoding
    other than utf-8 (e.g. latin-1) then an appropriate ``encoding`` name
    must be specified. Encodings that are not ASCII based (such as UCS-2)
    are not allowed and should be decoded to ``unicode`` first.
    """
    return _default_decoder.decode(s)
