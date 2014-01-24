"""Implementation of PListDecoder
"""
import re
import sys
import binascii

from nsplist.scanner import make_scanner

__all__ = ['PListDecoder']


def linecol(doc, pos):
    lineno = doc.count('\n', 0, pos) + 1
    if lineno == 1:
        colno = pos
    else:
        colno = pos - doc.rindex('\n', 0, pos)
    return lineno, colno


def errmsg(msg, doc, pos, end=None):
    # Note that this function is called from _json
    lineno, colno = linecol(doc, pos)
    if end is None:
        fmt = '{0}: line {1} column {2} (char {3})'
        return fmt.format(msg, lineno, colno, pos)
        #fmt = '%s: line %d column %d (char %d)'
        #return fmt % (msg, lineno, colno, pos)
    endlineno, endcolno = linecol(doc, end)
    fmt = '{0}: line {1} column {2} - line {3} column {4} (char {5} - {6})'
    return fmt.format(msg, lineno, colno, endlineno, endcolno, pos, end)
    #fmt = '%s: line %d column %d - line %d column %d (char %d - %d)'
    #return fmt % (msg, lineno, colno, endlineno, endcolno, pos, end)


STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', re.VERBOSE | re.DOTALL)

DEFAULT_ENCODING = "ascii"


def py_scanstring(s, end, encoding=None, _m=STRINGCHUNK.match):
    """Scan the string s for a plist quoted string. End is the index of the
    character in s after the quote that started the plist string.
    Unescapes all valid plist string escape sequences and raises ValueError
    on attempt to decode an invalid string.

    Returns a tuple of the decoded string and the index of the character in s
    after the end quote."""
    if encoding is None:
        encoding = DEFAULT_ENCODING
    chunks = []
    _append = chunks.append
    begin = end - 1
    while 1:
        chunk = _m(s, end)
        if chunk is None:
            raise ValueError(
                errmsg("Unterminated string starting at", s, begin))
        end = chunk.end()
        content, terminator = chunk.groups()
        # Content is contains zero or more unescaped string characters
        if content:
            if not isinstance(content, unicode):
                content = unicode(content, encoding)
            _append(content)
        # Terminator is the end of string, a literal control character,
        # or a backslash denoting that an escape sequence follows
        if terminator == '"':
            break
        elif terminator != '\\':
            #msg = "Invalid control character %r at" % (terminator,)
            msg = "Invalid control character {0!r} at".format(terminator)
            raise ValueError(errmsg(msg, s, end))
        try:
            esc = s[end]
        except IndexError:
            raise ValueError(
                errmsg("Unterminated string starting at", s, begin))
        # If not a unicode escape sequence, must be in the lookup table
        if esc != 'U':
            msg = "Invalid \\escape: " + repr(esc)
            raise ValueError(errmsg(msg, s, end))
        else:
            # Unicode escape sequence
            esc = s[end + 1:end + 5]
            next_end = end + 5
            if len(esc) != 4:
                msg = "Invalid \\UXXXX escape"
                raise ValueError(errmsg(msg, s, end))
            uni = int(esc, 16)
            # Check for surrogate pair on UCS-4 systems
            if 0xd800 <= uni <= 0xdbff and sys.maxunicode > 65535:
                msg = "Invalid \\UXXXX\\UXXXX surrogate pair"
                if not s[end + 5:end + 7] == '\\u':
                    raise ValueError(errmsg(msg, s, end))
                esc2 = s[end + 7:end + 11]
                if len(esc2) != 4:
                    raise ValueError(errmsg(msg, s, end))
                uni2 = int(esc2, 16)
                uni = 0x10000 + (((uni - 0xd800) << 10) | (uni2 - 0xdc00))
                next_end += 6
            char = unichr(uni)
            end = next_end
        # Append the unescaped character
        _append(char)
    return u''.join(chunks), end

scanstring = py_scanstring


WHITESPACE = re.compile(r'[ \t\n\r]*', re.VERBOSE | re.MULTILINE | re.DOTALL)
WHITESPACE_STR = ' \t\n\r'


def PListDictionary(s_and_end, encoding, scan_once, scan_name,
                    _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    if nextchar in _ws:
        end = _w(s, end).end()
        nextchar = s[end:end + 1]
    # Trivial empty object
    if nextchar == '}':
        return pairs, end + 1
    while True:
        try:
            key, end = scan_name(s, end)
        except StopIteration:
            raise ValueError(errmsg("Expecting property name", s, end))

        # To skip some function call overhead we optimize the fast paths where
        # the plist key separator is "= " or just "=".
        if s[end:end + 1] != '=':
            end = _w(s, end).end()
            if s[end:end + 1] != '=':
                raise ValueError(errmsg("Expecting = delimiter", s, end))

        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration:
            raise ValueError(errmsg("Expecting dictionary", s, end))
        pairs_append((key, value))

        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar != ';':
            raise ValueError(errmsg("Expecting ; delimiter", s, end - 1))

        try:
            nextchar = s[end]
            if nextchar in _ws:
                end += 1
                nextchar = s[end]
                if nextchar in _ws:
                    end = _w(s, end + 1).end()
                    nextchar = s[end]
        except IndexError:
            nextchar = ''

        if nextchar == '}':
            end += 1
            break

    pairs = dict(pairs)
    return pairs, end


def PListArray(s_and_end, scan_once, scan_name,
               _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    values = []
    nextchar = s[end:end + 1]
    if nextchar in _ws:
        end = _w(s, end + 1).end()
        nextchar = s[end:end + 1]
    # Look-ahead for trivial empty array
    if nextchar == ')':
        return values, end + 1
    _append = values.append
    while True:
        try:
            value, end = scan_once(s, end)
        except StopIteration:
            raise ValueError(errmsg("Expecting object", s, end))
        _append(value)
        nextchar = s[end:end + 1]
        if nextchar in _ws:
            end = _w(s, end + 1).end()
            nextchar = s[end:end + 1]
        end += 1
        if nextchar == ')':
            break
        elif nextchar != ',':
            raise ValueError(errmsg("Expecting , delimiter", s, end))

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        nextchar = s[end:end + 1]
        if nextchar == ')':
            end += 1
            break

    return values, end


HEX_RE = re.compile(r'([0-9A-Fa-f]{1,2})', re.VERBOSE | re.DOTALL)
SPACES_RE = re.compile(r'\ *', re.VERBOSE | re.DOTALL)


def PListBinary(s_and_end, _h=HEX_RE.match,
                _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    values = []
    nextchar = s[end:end + 1]
    if nextchar in _ws:
        end = _w(s, end + 1).end()
        nextchar = s[end:end + 1]
    # Look-ahead for trivial empty array
    if nextchar == '>':
        return None, end + 1
    _append = values.append
    while True:
        m = _h(s, end)
        if m is None:
            raise ValueError(errmsg("Expecting hexadecimal number", s, end))
        value = m.groups()[0]
        end = m.end()
        _append(value)
        nextchar = s[end:end + 1]
        if nextchar not in _ws:
            raise ValueError(errmsg("Expecting whitespace", s, end))
        else:
            end = _w(s, end + 1).end()
            nextchar = s[end:end + 1]
        if nextchar == '>':
            end += 1
            break

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        nextchar = s[end:end + 1]
        if nextchar == '>':
            end += 1
            break

    return binascii.a2b_hex(''.join(values)), end


class PListDecoder(object):
    """Simple NeXSTSTEP property list decoder

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | PList         | Python            |
    +===============+===================+
    | string        | unicode           |
    +---------------+-------------------+
    | binary data   | bytes             |
    +---------------+-------------------+
    | dictionary    | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    """

    def __init__(self, encoding=None):
        self.encoding = encoding
        self.parse_dictionary = PListDictionary
        self.parse_array = PListArray
        self.parse_string = scanstring
        self.parse_binary = PListBinary
        self.scan_once = make_scanner(self)

    def decode(self, s, _w=WHITESPACE.match):
        """Return the Python representation of ``s`` (a ``str`` or ``unicode``
        instance containing a plist document)

        """
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())
        end = _w(s, end).end()
        if end != len(s):
            raise ValueError(errmsg("Extra data", s, end, len(s)))
        return obj

    def raw_decode(self, s, idx=0):
        """Decode a plist document from ``s`` (a ``str`` or ``unicode``
        beginning with a plist document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.

        This can be used to decode a plist document from a string that may
        have extraneous data at the end.

        """
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration:
            raise ValueError("No plist object could be decoded")
        return obj, end
