# ============================================================================
# FILE: util.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import json
import re
import os
import sys
import unicodedata
import glob
import traceback

from importlib.machinery import SourceFileLoader


def get_buffer_config(context, filetype, buffer_var, user_var, default_var):
    if buffer_var in context['bufvars']:
        return context['bufvars'][buffer_var]

    ft = filetype if (filetype in context['vars'][user_var] or
                      filetype in default_var) else '_'
    default = default_var.get(ft, '')
    return context['vars'][user_var].get(ft, default)


def get_simple_buffer_config(context, buffer_var, user_var):
    return (context['bufvars'][buffer_var]
            if buffer_var in context['bufvars']
            else context['vars'][user_var])


def set_pattern(variable, keys, pattern):
    for key in keys.split(','):
        variable[key] = pattern


def set_list(vim, variable, keys, list):
    return vim.call('deoplete#util#set_pattern', variable, keys, list)


def set_default(vim, var, val):
    return vim.call('deoplete#util#set_default', var, val)


def convert2list(expr):
    return (expr if isinstance(expr, list) else [expr])


def globruntime(runtimepath, path):
    ret = []
    for rtp in re.split(',', runtimepath):
        ret += glob.glob(rtp + '/' + path)
    return ret


def find_rplugins(context, source):
    """Search for base.py or *.py

    Searches $VIMRUNTIME/*/rplugin/python3/deoplete/$source[s]/
    """
    rtp = context.get('runtimepath', '').split(',')
    if not rtp:
        return

    sources = (
        os.path.join('rplugin/python3/deoplete', source, 'base.py'),
        os.path.join('rplugin/python3/deoplete', source, '*.py'),
        os.path.join('rplugin/python3/deoplete', source + 's', '*.py'),
    )

    for src in sources:
        for path in rtp:
            yield from glob.iglob(os.path.join(path, src))


def import_plugin(path, source, classname):
    """Import Deoplete plugin source class.

    If the class exists, add its directory to sys.path.
    """
    name = os.path.splitext(os.path.basename(path))[0]
    module_name = 'deoplete.%s.%s' % (source, name)

    module = SourceFileLoader(module_name, path).load_module()
    cls = getattr(module, classname, None)
    if not cls:
        return None

    dirname = os.path.dirname(path)
    if dirname not in sys.path:
        sys.path.insert(0, dirname)
    return cls


def debug(vim, expr):
    try:
        json_data = json.dumps(str(expr).strip())
    except Exception:
        vim.command('echomsg string(\'' + str(expr).strip() + '\')')
    else:
        vim.command('echomsg string(\'' + escape(json_data) + '\')')


def error(vim, msg):
    vim.call('deoplete#util#print_error', msg)


def error_tb(vim, msg):
    for line in traceback.format_exc().splitlines():
        error(vim, str(line))
    error(vim, '%s.  Use :messages for error details.' % msg)


def escape(expr):
    return expr.replace("'", "''")


def charpos2bytepos(encoding, input, pos):
    return len(bytes(input[: pos], encoding))


def bytepos2charpos(encoding, input, pos):
    return len(bytes(input, encoding)[: pos].decode(encoding))


def get_custom(custom, source_name, key, default):
    if source_name not in custom:
        return get_custom(custom, '_', key, default)
    elif key in custom[source_name]:
        return custom[source_name][key]
    elif key in custom['_']:
        return custom['_'][key]
    else:
        return default


def get_syn_names(vim):
    return vim.call('deoplete#util#get_syn_names')


def parse_file_pattern(f, pattern):
    p = re.compile(pattern)
    ret = []
    for l in f:
        ret += p.findall(l)
    return list(set(ret))


def parse_buffer_pattern(b, pattern, complete_str):
    p = re.compile(pattern)
    return [x for x in p.findall('\n'.join(b)) if x != complete_str]


def fuzzy_escape(string, camelcase):
    # Escape string for python regexp.
    p = re.sub(r'([a-zA-Z0-9_])', r'\1.*', re.escape(string))
    if camelcase and re.search(r'[A-Z]', string):
        p = re.sub(r'([a-z])', (lambda pat:
                                '['+pat.group(1)+pat.group(1).upper()+']'), p)
    p = re.sub(r'([a-zA-Z0-9_])\.\*', r'\1[^\1]*', p)
    return p


def load_external_module(file, module):
    current = os.path.dirname(os.path.abspath(file))
    module_dir = os.path.join(os.path.dirname(current), module)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)


def truncate_skipping(string, max, footer, footer_len):
    if len(string) <= max/2:
        return string
    if strwidth(string) <= max:
        return string

    footer += string[
            -len(truncate(string[::-1], footer_len)):]
    return truncate(string, max - strwidth(footer)) + footer


def truncate(string, max):
    if len(string) <= max/2:
        return string
    if strwidth(string) <= max:
        return string

    width = 0
    ret = ''
    for c in string:
        wc = charwidth(c)
        if width + wc > max:
            break
        ret += c
        width += wc
    return ret


def strwidth(string):
    width = 0
    for c in string:
        width += charwidth(c)
    return width


def charwidth(c):
    wc = unicodedata.east_asian_width(c)
    return 2 if wc == 'F' or wc == 'W' else 1
