"""NeXTSTEP property list token scanner
"""
import re

__all__ = ['make_scanner']


ALPHANUMERIC_RE = re.compile(r'(\w+)', re.VERBOSE | re.DOTALL)


def py_make_scanner(context):
    parse_dictionary = context.parse_dictionary
    parse_array = context.parse_array
    parse_string = context.parse_string
    parse_binary = context.parse_binary
    match_alphanumeric = ALPHANUMERIC_RE.match
    encoding = context.encoding

    # see http://code.google.com/p/networkpx/wiki/PlistSpec#Text
    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration

        if nextchar == '"':
            return parse_string(string, idx + 1, encoding)
        elif nextchar == '{':
            return parse_dictionary((string, idx + 1), encoding, _scan_once,
                _scan_name)
        elif nextchar == '(':
            return parse_array((string, idx + 1), _scan_once, _scan_name)
        elif nextchar == '<':
            return parse_binary((string, idx + 1))

        m = match_alphanumeric(string, idx)
        if m is not None:
            return m.groups()[0], m.end()
        else:
            raise StopIteration

    def _scan_name(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration

        if nextchar == '"':
            return parse_string(string, idx + 1, encoding)

        m = match_alphanumeric(string, idx)
        if m is not None:
            return m.groups()[0], m.end()
        else:
            raise StopIteration

    return _scan_once

make_scanner = py_make_scanner
