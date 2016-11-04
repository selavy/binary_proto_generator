#!/usr/bin/env python

import pprint
from collections import namedtuple

SPEC = '''
enum utp_bin_msg_type {
    UTP_BIN_MSG_TYPE_LOGON     = 0x01,
    UTP_BIN_MSG_TYPE_HEARTBEAT = 0x02,
    UTP_BIN_MSG_TYPE_NEW_ORDER = 0x03,
}

struct padding bytes(4) utp_bin_msg_hdr {
    u16 msg_type;
    u16 msg_length;
}

struct padding utp_bin_logon {
    utp_bin_msg_hdr hdr;
    u16 other;
}

struct utp_bin_test {
    utp_bin_logon logon;
    u16 other;
}
'''

DataType = namedtuple('DataType', ['name', 'size', 'signed', 'builtin'])
Struct = namedtuple('Struct', ['name', 'size', 'padding', 'members'])
StructItem = namedtuple('StructItem', ['name', 'dtype'])
Enum = namedtuple('Enum', ['name', 'size', 'values'])
EnumItem = namedtuple('EnumItem', ['name', 'value'])
DTYPES = {}

def read_from_tokens(tokens):
    if not tokens:
        raise Exception('unexpected EOF while reading')
    structs = []
    enums = []
    while tokens:
        token = tokens.pop(0)
        if token == 'struct':
            s = match_struct(tokens)
            size = 0
            for member in s.members:
                size += DTYPES[member.dtype].size
            structs.append(s)
            DTYPES[s.name] = DataType(name=s.name, size=size, signed=False, builtin=False)
        elif token == 'enum':
            e = match_enum(tokens)
            DTYPES[e.name] = DataType(name=e.name, size=e.size, signed=False, builtin=False)
            enums.append(e)
        else:
            raise Exception('Invalid token: "{!s}"'.format(token))

    return structs, enums

def match_enum(tokens):
    if not tokens:
        raise Exception('expected identifier after enum keyword')

    size = 8 # default to 1 byte for enums
    while tokens:
        if tokens[0] == 'bytes':
            tokens.pop(0)
            if not tokens or tokens[0] != '(':
                raise Exception('expected \'(\' after enum keyword')
            tokens.pop(0)
            if not tokens:
                raise Exception('expected size for enum in bytes attribute')
            size = int(tokens[0])
            tokens.pop(0)
            if not tokens or tokens[0] != ')':
                raise Exception('expected \')\' after enum keyword')
            tokens.pop(0)
        else:
             break   

    if not tokens:
        raise Exception('Expected enum name')         
    name = tokens[0]
    tokens.pop(0)

    if not tokens or tokens[0] != '{':
        raise Exception('Expected \'{\' after enum name')
    tokens.pop(0)
    
    values = []
    while tokens and tokens[0] != '}':
        item = match_enum_item(tokens)
        values.append(item)
        
    if tokens[0] == '}':
        tokens.pop(0)
        
    return Enum(name=name, size=size, values=values)

def match_enum_item(tokens):
    if not tokens:
        raise Exception('expected enum items')

    name = tokens[0]
    tokens.pop(0)
    if not tokens or tokens[0] != '=':
        raise Exception('Expected \'=\' after enum item name')
    tokens.pop(0)
    
    value = tokens[0]
    tokens.pop(0)
    
    if not tokens:
        raise Exception('Expected \',\' after enum item')
    elif tokens[0] == ',':
        tokens.pop(0)
    elif tokens[0] != '}':
        raise Exception('Expected \'}}\' to close enum type, got {}'.format(tokens[0]))

    return EnumItem(name=name, value=value)

def match_struct(tokens):
    if not tokens:
        raise Exception('expected identifier after struct keyword')
    size = -1 # unset
    padding = False
    while tokens:
        token = tokens[0]
        if token == 'bytes':
            tokens.pop(0)
            if not tokens or tokens[0] != '(':
                raise Exception('expected \'(\' after bytes keyword')
            tokens.pop(0)
            if not tokens:
                raise Exception('expected number of bytes for size of struct')
            size = int(tokens[0])
            tokens.pop(0)
            if not tokens or tokens[0] != ')':
                raise Exception('expected \')\' after bytes keyword')
            tokens.pop(0)
        elif token == 'padding':
            if padding:
                raise Exception('padding keyword cannot be specified twice')
            padding = True
            tokens.pop(0)
        else:
            break    
    token = tokens[0]
    name = token
    tokens.pop(0)
    if tokens[0] != '{':
        raise Exception('expected \'{{\' after struct name, got "{}"'.format(tokens[0]))
    tokens.pop(0)
    members = []
    while tokens and tokens[0] != '}':
        item = match_struct_item(tokens)
        members.append(item)
    if tokens[0] == '}':
        tokens.pop(0)
    return Struct(name=name, size=size, padding=padding, members=members)

def match_struct_item(tokens):
    if not tokens:
        raise Exception('expected struct item')
    token = tokens[0]
    if token in DTYPES:
        dtype = token
    else:
        raise Exception('invalid data type for member \'{}\''.format(token))
    tokens.pop(0)

    # TODO: match attributes if present

    if not tokens:
        raise Exception('expected data member name')
    token = tokens[0]
    name = token
    tokens.pop(0)

    if not tokens or tokens[0] != ';':
        raise Exception('expected \';\' after data member')
    tokens.pop(0)
    
    return StructItem(name=name, dtype=dtype)
        
if __name__ == '__main__':
    DTYPES['u16'] = DataType(name='u16', size=16, signed=False, builtin=True)
    DTYPES['u32'] = DataType(name='u32', size=32, signed=False, builtin=True)
    DTYPES['s16'] = DataType(name='u16', size=16, signed=True,  builtin=True)
    DTYPES['s32'] = DataType(name='u32', size=32, signed=True,  builtin=True)
    
    print SPEC
    tokens = SPEC.replace('{', ' { ').replace('}', ' } ').replace(';', ' ; ').replace('[', ' [ ').replace(']', ' ] ').replace('(', ' ( ').replace(')', ' ) ').replace(',', ' , ').split()

    ss, es = read_from_tokens(tokens)
    pprint.pprint(ss)
    pprint.pprint(es)

    pprint.pprint(DTYPES)
    

    
    
