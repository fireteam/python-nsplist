import nsplist


def encode_bin(data):
    data = data.encode('hex')
    joined = ' '.join(data[i:i + 2] for i in range(0, len(data), 2))
    return '< ' + joined + ' >'


def test_dict():
    data = '{\n\t"x" = "0";\n\t"y" = "1";\n\t"z" = "2";\n\t"t" = "3";\n}'
    plist = nsplist.loads(data)

    assert plist['x'] == '0'
    assert plist['y'] == '1'
    assert plist['z'] == '2'
    assert plist['t'] == '3'


def test_list():
    data = '("a", "b", c,)'
    plist = nsplist.loads(data)
    assert plist == ['a', 'b', 'c']


# def test_strange_strings():
#     """From https://code.google.com/p/plist"""
#     data = '''{
#   "key&\102"="value&\U0042==";
#   key2 = "strangestring\\\"";
#   key3 = "strangestring\\";
# }'''
#     plist = nsplist.loads(data)
#     assert plist == {}


# def test_all_types():
#     """From https://code.google.com/p/plist"""
#     data = '''{
#     keyA = valueA;
#     "key&\102" = "value&\U0042";
#     date = "2011-11-28T09:21:30Z";
#     data = <00000004 10410820 82>;
#     array = (
#         YES,
#         NO,
#         87,
#         3.14159
#     );
# }'''
#     plist = nsplist.loads(data)
#     assert plist == {}


def test_binary():
    data = '\xae\x9fg=\xe6\xaa?\x0bvS5\xfas\xea\x1c\xa7'
    blob = encode_bin(data)

    plist = nsplist.loads(blob)

    assert data == plist
