"""Serialize address recipes and authored strings for Lua 5.1/LuaJIT."""
import json
import re

def lua(value):
    if isinstance(value, str):
        # Lua 5.1 has decimal byte escapes, not JSON's Unicode escapes.
        return re.sub(r'\\u00([0-9a-f]{2})', lambda m: '\\%03d' % int(m[1], 16),
                      json.dumps(value, ensure_ascii=False))
    if isinstance(value, bool): return 'true' if value else 'false'
    if value is None: return 'nil'
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, list): return '{' + ','.join(map(lua, value)) + '}'
    return '{' + ','.join('[' + lua(k) + ']=' + lua(v) for k, v in value.items()) + '}'
