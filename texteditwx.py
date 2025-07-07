#!/usr/bin/env python
# -*- coding: utf-8 -*-
# texteditwx.py
# by Yukiharu Iwamoto
# 2025/7/7 11:25:51 AM

version = '2025/7/7 11:25:51 AM'

import sys

# Maximaの場所
if sys.platform == 'win32': # windowsの場合
    import glob
    maxima_location = glob.glob(r'C:\maxima*\bin\maxima.bat')[0]
else: # mac, linuxの場合
    maxima_location = 'maxima'

import os
languages = os.environ.get('LANG')
#languages = ['en']
#languages = ['ja']

import re
import wx # python3 -> pip install wxPython, python 2 -> pip install wxPython==4.1.0
import wx.grid
import platform
import gettext
import codecs
import datetime
import pyperclip # pip install pyperclip
import requests
import zenhan
import ast
import webbrowser

if sys.platform != 'darwin':
    import locale # required for a format '%p' (AM/PM) in strftime

def decode_if_necessary(s):
    return s.decode('CP932' if sys.platform == 'win32' else 'UTF-8') if sys.version_info.major <= 2 and type(s) is str else s

def encode_if_necessary(s):
    return s.encode('CP932' if sys.platform == 'win32' else 'UTF-8') if sys.version_info.major <= 2 and type(s) is unicode else s

# How to make translation
# (1) mkdir -p locale/en/LC_MESSAGES
# (2) If you already have old locale/en/LC_MESSAGES/messages.po, rename it by following command:
#     mv locale/en/LC_MESSAGES/messages.po locale/en/LC_MESSAGES/messages.po.old
# (3) xgettext -o locale/messages.pot matplotlibwx.py && msginit --locale=en --input=locale/messages.pot --output-file=locale/en/LC_MESSAGES/messages.po
# (4) If you did not skip the step (2), merge files by following command:
#     msgmerge locale/en/LC_MESSAGES/messages.po.old locale/en/LC_MESSAGES/messages.po --output-file=locale/en/LC_MESSAGES/messages.po
#     rm locale/en/LC_MESSAGES/messages.po.old
# (5) Edit locale/en/LC_MESSAGES/messages.po
# (6) msgfmt -o locale/en/LC_MESSAGES/messages.mo locale/en/LC_MESSAGES/messages.po
#     - Reverse opetration can be done by 'msgunfmt'
gettext.translation(
    domain = 'messages',
    localedir = os.path.join(os.path.dirname(os.path.realpath(decode_if_necessary(__file__))), 'locale'),
    languages = languages,
    fallback = True
).install()

if sys.platform == 'darwin':
    import unicodedata

def get_file_from_google_drive(file_id):
    r = requests.get('https://drive.google.com/uc', params = {'export': 'download', 'id': file_id})
    if r.ok:
        if b'Google Drive - Virus scan warning' in r.content:
            cookies = r.cookies.get_dict()
            if cookies:
                for k in cookies.keys():
                    if k.startswith('download_warning_'):
                        code = cookies[k]
                        break
            else: # https://github.com/wkentaro/gdown/blob/1bf9e20442a0df57eec3e75a15ef4115dbec9b2f/gdown/download.py#L32
                m = re.search(b'id="downloadForm" action=".+?&amp;confirm=(.+?)"', r.content)
                if m:
                    code = m[1]
                else:
                    m = re.search(b'&amp;confirm=t&amp;uuid=(.+?)"', r.content)
                    if m:
                        code = m[1]
            r = requests.get('https://drive.google.com/uc',
                params = {'export': 'download', 'confirm': code, 'id': file_id}, cookies = cookies)
            if not r.ok:
                return None
        return r.content, r.apparent_encoding # type(r.content) = str (Python 2); bytes (Python 3)
    else:
        return None

def get_file_from_github_public(user, repository, branch, file_path):
    r = requests.get('https://raw.githubusercontent.com/' + user + '/' + repository + '/' + branch + '/' + file_path)
    if r.ok:
        return r.content, r.apparent_encoding # type(r.content) = str (Python 2); bytes (Python 3)
    else:
        return None

def time_str_a_is_newer_than_b(a, b):
    reg = re.compile(r'([0-9]+)\s*[/\-]\s*([0-9]+)\s*[/\-]\s*([0-9]+)\s+([0-9]+)\s*:\s*([0-9]+)\s*(?::\s*([0-9]+)\s*)?([AaPp][Mm])*')
    ra = reg.search(a)
    rb = reg.search(b)
    if ra is None or rb is None:
        return False
    time_a = [int(i) if i is not None else 0 for i in ra.groups()[:-1]]
    time_b = [int(i) if i is not None else 0 for i in rb.groups()[:-1]]
    # year, month, date, hour, minute, second, AM/PM
    if ra.groups()[-1] is not None and ra.groups()[-1].upper() == 'PM':
        time_a[3] += 12
    if rb.groups()[-1] is not None and rb.groups()[-1].upper() == 'PM':
        time_b[3] += 12
    return True if time_a > time_b else False

def correct_file_name_in_unicode(file_name):
    if sys.version_info.major <= 2 and type(file_name) is str:
        file_name = file_name.decode('UTF-8')
    if file_name == '':
        return ''
    file_name = os.path.normpath(file_name.strip())
    if sys.platform == 'darwin':
        # 濁点なし文字と濁点に分離されている文字->濁点付きの文字
        file_name = unicodedata.normalize('NFC', file_name)
    elif sys.platform == 'win32':
        # os.path.normpath should be done prior to replace(os.sep, os.altsep)
        file_name = file_name.replace(os.sep, os.altsep)
    elif file_name.startswith('file:'):
        file_name = file_name[5:]
    return file_name # unicode

def str_diff(str1, str2):
    if str1 == '' or str2 == '':
        return [0, str1, str2]
    l1 = len(str1)
    l2 = len(str2)
    i = 0
    while str1[i] == str2[i]:
        i += 1
        if i == l1:
            return [i, '', str2[i:]]
        elif i == l2:
            return [i, str1[i:], '']
    j = -1
    while str1[j] == str2[j]:
        if l1 + j == i:
            return [i, '', str2[i:j]]
        elif l2 + j == i:
            return [i, str1[i:j], '']
        j -= 1
    j += 1
    return [i, str1[i:l1 + j], str2[i:l2 + j]] # j < 0

def str_range_between(s, selection, parentheses):
    if not isinstance(parentheses[0], (tuple, list)):
        parentheses = (parentheses,)
    s0 = s[:selection[0]]
    l0 = selection[0] - 1
    p = []
    r = None
    while l0 >= 0:
        for i in parentheses:
            if s0[l0:].startswith(i[1]):
                p.append(i[0])
                break
            if s0[l0:].startswith(i[0]):
                if len(p) == 0:
                    r = i[1]
                elif p[-1] == i[0]:
                    p.pop()
                break
        if r is not None:
            break
        l0 -= 1
    if r is None:
        return None
    l1 = selection[1]
    while l1 < len(s):
        for i in parentheses:
            if s[l1:].startswith(i[0]):
                p.append(i[1])
                break
            if s[l1:].startswith(i[1]):
                if len(p) == 0:
                    if i[1] == r:
                        return [l0, l1 + len(r)]
                    else:
                        return None
                if p[-1] == i[1]:
                    p.pop()
                break
        l1 += 1
    return None

def str_levels(s, parentheses = None, literals = None, literal_escape = ''):
    if parentheses is None:
        parentheses = tuple()
    elif not isinstance(parentheses[0], (tuple, list)):
        parentheses = (parentheses,)
    if literals is None:
        literals = tuple()
    elif not isinstance(literals[0], (tuple, list)):
        literals = (literals,)
    i = start = 0
    literal = False
    level = 0
    levels = []
    p = []
    while i < len(s):
        if literal:
            for j in literals:
                if (s[i:].startswith(j[1]) and
                    (i < len(literal_escape) or s[i - len(literal_escape):i] != literal_escape) and
                    len(p) > 0 and p[-1] == j[1]):
                    i += len(j[1])
                    if start < i:
                        levels.append((start, i, level))
                    p.pop()
                    literal = False
                    level -= 1
                    start = i
                    break
            if not literal:
                continue
        else:
            for j in literals:
                if (s[i:].startswith(j[0]) and
                    (i < len(literal_escape) or s[i - len(literal_escape):i] != literal_escape)):
                    if start < i:
                        levels.append((start, i, level))
                    p.append(j[1])
                    literal = True
                    level += 1
                    start = i
                    i += len(j[0])
                    break
            if literal:
                continue
            i_is_increased = False
            for j in parentheses:
                if s[i:].startswith(j[0]):
                    if start < i:
                        levels.append((start, i, level))
                    p.append(j[1])
                    level += 1
                    start = i
                    i += len(j[0])
                    i_is_increased = True
                    break
                if s[i:].startswith(j[1]):
                    if len(p) > 0 and p[-1] == j[1]:
                        i += len(j[1])
                        if start < i:
                            levels.append((start, i, level))
                        p.pop()
                        level -= 1
                        start = i
                        i_is_increased = True
                        break
            if i_is_increased:
                continue
        i += 1
    if start < len(s):
        levels.append((start, len(s), level))
    return levels

def line_numbered_str(s, head = True, prefix = '', suffix = ': '):
    s_has_lf_in_last_line = s.endswith('\n')
    s_has_cr = s.find('\r') != -1
    lines = s.replace('\r', '').split('\n')
    n = len(lines)
    if s_has_lf_in_last_line:
        n += 1
    fmt = prefix + '%' + str(len('%d' % n)) + 'd' + suffix
    s = ''
    r = '\r\n' if s_has_cr else '\n'
    if head:
        for i, line in enumerate(lines, start = 1):
            s += fmt % i + line + r
    else:
        for i, line in enumerate(lines, start = 1):
            s += line + fmt % i + r
    if not s_has_lf_in_last_line:
        s = s[:-len(r)]
    return s

def resub_outside(pat_repl, string, inside_pattern = r'"(\\.|[^"])*"'):
    # pat_repl = (pattern, replacement) or (pattern, replacement),)
    # r'"(\\.|[^"])*"' -> string enclosed in double quotes
    if not isinstance(pat_repl[0], (list, tuple)):
        pat_repl = (pat_repl,)
    s = ''
    while len(string) > 0:
        m = re.search(inside_pattern, string) # string which allows escape characters
        if m:
            t = string[:m.start()]
            for p, r in pat_repl:
                t = re.sub(p, r, t)
            s += t + m[0]
            string = string[m.end():]
        else:
            t = string
            for p, r in pat_repl:
                t = re.sub(p, r, t)
            s += t
            break
    return s

openfoam_src = 'https://develop.openfoam.com/Development/openfoam/tree/maintenance-v2106/src/'

def openfoam_bc_template_string(bc, indent = '', include_src_url = False):
    s = indent + '{\n' + indent + '\ttype ' + bc[0] + ';\n'
    if bc[1] != '':
        s += indent + '\t// ' + bc[1].replace('\n', '\n' + indent + '\t// ') + '\n'
    if bc[2] != '':
        s += indent + '\t' + bc[2].replace('\n', '\n' + indent + '\t') + '\n'
    if include_src_url and bc[3] != '':
        s += indent + '\t// ' + bc[3] + '\n'
    s += indent + '}\n'
    return s

class Maxima(object):
    def __init__(self):
        self.init()

    def init(self):
        if sys.platform == 'win32':
            import pexpect.popen_spawn as psp # pip install pexpect
            self.maxima = psp.PopenSpawn(maxima_location + ' -q')
        else:
            import pexpect # pip install pexpect
            self.maxima = pexpect.spawn(maxima_location, ['-q'])
        self.maxima.expect('.+')
        self.in_help = False
        self.commands_list = []
        for c in ('display2d: false$', 'kill(labels)$'):
            self.maxima.sendline(c)
            while True:
                self.maxima.expect('.+')
                if sys.version_info.major > 2:
                    self.maxima.after = self.maxima.after.decode('UTF-8')
                if re.search(r'\(%i\d\)', self.maxima.after):
                    break
        self.last_input = '/* (%i1): */'

    def reset(self):
        for c in ('reset()$', 'display2d: false$'):
            self.maxima.sendline(c)
            while True:
                self.maxima.expect('.+')
                if sys.version_info.major > 2:
                    self.maxima.after = self.maxima.after.decode('UTF-8')
                if re.search(r'\(%i\d\)', self.maxima.after):
                    break

    def expect(self, pattern, timeout = -1):
        # if timeout = -1, default value (30 s) is used.
        # if timeout = None, timeout never occures.
        try:
            self.maxima.expect(pattern, timeout)
            if sys.version_info.major > 2:
                # bytes -> str
                self.maxima.before = self.maxima.before.decode('UTF-8')
                self.maxima.after = self.maxima.after.decode('UTF-8')
            # maximaの改行コードは\r\nらしい
            self.maxima.before = self.maxima.before.replace('\r', '')
            self.maxima.after = self.maxima.after.replace('\r', '')
            if sys.platform.startswith('linux') and self.maxima.before.endswith(self.maxima.after):
                self.maxima.before = self.maxima.before[:-len(self.maxima.after)]
        except:
#            print(sys.exc_info())
            with wx.MessageDialog(None, _(u'{}\nMaximaを再起動します．').format(sys.exc_info()[0]),
                _(u'例外発生'), style = wx.ICON_ERROR) as md:
                md.ShowModal()
            if sys.platform == 'win32':
                self.maxima.kill(0)
            else:
                self.maxima.close()
            self.init()
            raise

    def send_commands(self, commands, replace = False):
        debug = False
        if debug:
            print('send_commands')
        if len(self.commands_list) > 0:
            commands_list_remain = self.commands_list
            self.commands_list = []
        else:
            commands_list_remain = None
        commands = re.sub(r'/\*(\*(?!/)|[^*])*\*/', '', commands) # remove comment
        while True:
            m = re.search(':lisp |[;$]', commands)
            if m:
                if m[0] == ':lisp ':
                    m = commands.find(';')
                    if m != -1:
                        self.commands_list.append(commands[:m + 1].strip())
                        commands = commands[m + 1:]
                    else:
                        self.commands_list.append(commands.strip() + ';')
                        break
                else:
                    c = commands[:m.end()].strip()
                    if c not in ';$':
                        self.commands_list.append(c)
                    commands = commands[m.end():]
            else:
                c = commands.strip()
                if c != '':
                    if c[-1] not in ';$':
                        c += ';'
                    self.commands_list.append(c)
                break
        if commands_list_remain is not None:
            self.commands_list.extend(commands_list_remain)
        if debug:
            print('    commands_list = {}'.format(self.commands_list))
        outputs = []
        while len(self.commands_list) > 0:
            c = self.commands_list.pop(0)
            self.maxima.sendline(c)
            if debug:
                print('    ----------')
                print('    command = "{}"'.format(c))
            try:
                self.expect(r"(\(%i\d+\)|Enter space-separated numbers, `all' or `none':|.+\?)\s*$")
            except:
                raise
            if self.maxima.before.startswith(c + '\n'):
                 self.maxima.before = self.maxima.before[len(c) + 1:]
            if debug:
                print('    before = "{}"'.format(self.maxima.before))
                print('    after = "{}"'.format(self.maxima.after))
            if self.maxima.after.startswith('(%i'):
                self.last_input = self.maxima.after
                s = self.maxima.before.lstrip('\n').rstrip()
                while c.endswith(';') and s == '':
                    self.expect(r'\(%i\d+\)')
                    if self.maxima.before.startswith(c + '\n'):
                        self.maxima.before = self.maxima.before[len(c) + 1:]
                    s = self.maxima.before.lstrip('\n').rstrip()
                if debug:
                    print('    s = "{}"'.format(s))
                if c.endswith('$') and (s == '' or s.startswith('(%i') or s.endswith('$')):
                    if ('incorrect syntax: ' in s or s.endswith(' -- an error. To debug this try: debugmode(true);') or
                        'Maxima encountered a Lisp error: ' in s):
                        l_output = len(s)
                        s = '/* ERROR: */\n' + s
                        if replace:
                            s = c + '\n' + s
                    else:
                        l_output = 0
                    continue
                i = len(s) - 5
                m = None
                while i >= 0: # search (%o<number>) from tail
                    m = re.match(r'(\(%o\d+\))(.*)', s[i:], re.DOTALL)
                    if m:
                        break
                    else:
                        i -= 1
                if re.match(r'(for|thru|while|unless) |(s?print|printf|display) *\(', c):
                    if m: # re.match(r'(\(%o\d+\))(.*)', s[i:])
                        s = self.modify_output(s[:i], remove_new_lines = False)
                        if not replace:
                            s += '\n\n/* ' + m[1] + ': */\n' + self.modify_output(m[2])
                    else:
                        s = self.modify_output(s, remove_new_lines = False)
                    l_output = len(s)
                elif m: # re.match(r'(\(%o\d+\))(.*)', s[i:])
                    if c.startswith('? ') or self.in_help:
                        l_output = 0
                        s = '/* HELP: */\n' + s[:i].rstrip()
                        if self.in_help:
                            self.in_help = False
                    elif c.startswith('example('):
                        l_output = 0
                        s = '/* EXAMPLE: */\n' + s[:i].rstrip()
                    else:
                        s = self.modify_output(m[2])
                        l_output = len(s)
                        if not replace:
                            s = '/* ' + m[1] + ': */\n' + s
                elif c.startswith(':lisp '):
                    if not replace:
                        l_output = len(s)
                        s = '/* lisp: */\n' + s
                elif s.startswith('Warning: '):
                    i = s.find('\n\n')
                    if i != -1:
                        s = s[:i]
                    l_output = len(s)
                    s = '/* WARNING */\n' + s
                elif ('incorrect syntax: ' in s or s.endswith(' -- an error. To debug this try: debugmode(true);') or
                    'Maxima encountered a Lisp error: ' in s):
                    l_output = len(s)
                    s = '/* ERROR: */\n' + s
                    if replace:
                        s = c + '\n' + s
                else:
                    print('\n----- UNCLEAR OUTPUT -----\n{}\n'.format(s))
                    l_output = 0
                    continue
                if debug:
                    print('    outputs = "{}"'.format(s))
                    print('    ----------')
                outputs.append(s)
            elif self.maxima.after.startswith("Enter space-separated numbers, `all' or `none':"):
                # example: ?? plot
                outputs.append(
                    self.maxima.before.lstrip('\n') + self.maxima.after.rstrip() + '\n\n')
                self.in_help = True
                return outputs, 0
            else:
                # example: sum(x^i, i, 0, inf), simpsum;
                #          integrate(sin(2*%pi/lambda*(x - c*t)), t, 0, lambda/(2*%pi*c));
                i = re.search(r'[$;]', self.maxima.after)
                if i is not None:
                    self.maxima.after = self.maxima.after[i.end():]
                outputs.append(self.maxima.after.strip() + '\n\n')
                return outputs, 0
        self.last_input = '/* ' + self.last_input.strip() + ': */'
        return outputs, l_output # l_output is used for selection range in a display

    @staticmethod
    def remove_redundant_parentheses(s):
        debug = False
        if debug:
            print('remove_redundant_parentheses')
            print('    initial string = "{}"'.format(s))
        priority = {
            'initial value': 1000,
            '!!': 100,
            '!':   90, # a!!! = (a!!)!
            '^^':  80, # a^^b! = a^^(b!)
            '^':   80, # a^b! = a^(b!)
            '**':  80, # a**b! = a**(b!)
            '.':   70, # a.b^c = a.(b^c)
            '/':   60, # a/b.c = a/(b.c)
            '*':   59, # a*b.c = a*(b.c), conversion (a*b)/c = a*b/c is done by adding another condition
            '+':   50, # a + b*c = a + (b*c)
            '-':   50, # a + b*c = a + (b*c)
            }
        if len(s) == 0:
            return '', 0, ''
        if s[0] == '-':
            min_priority = last_priority = priority['*']
            r = '-'
            s = s[1:]
        else:
            min_priority = last_priority = priority['initial value']
            r = ''
        while len(s) > 0:
            if debug:
                print('    while, s = "{}"'.format(s))
            #                1        1   2                                  2 3                          3
            m = re.search(r'"(\\.|[^"])*"|(!!?|\^\^?|\*\*?|\.(?![0-9])|[/+\-])|([_A-Za-z][_A-Za-z0-9\[\]]*)?\(|\)|\[|\]', s)
            if m:
                if m[1]: # string enclosed in double quotes:
                    r += s[:m.end()]
                    s = s[m.end():]
                    if debug:
                        print('    skip string, r = "{}"'.format(r))
                elif m[2]: # operator
                    last_priority = priority[m[2]]
                    if r.endswith('^') and s[0] == '-': # not update min_priority in the case of a^-b
                        pass
                    elif min_priority > last_priority:
                        min_priority = last_priority
                    r += s[:m.end()]
                    s = s[m.end():]
                    if debug:
                        print('    operator {}, min_priority = {}'.format(m[2], min_priority))
                elif m[0] == '(':
                    r += s[:m.end() - 1] # string before '('
                    if debug:
                        print('    (')
                        print('        r = "{}"'.format(r))
                    inside, inside_priority, s = Maxima.remove_redundant_parentheses(s[m.end():])
                    if debug:
                        print('        inside = "{}", inside_priority = {}, s = "{}"'.format(
                            inside, inside_priority, s))
                    m = re.match(r'!!?|\^\^?|\*\*?|\.(?![0-9])|[/+\-]', s)
                    if m:
                        if debug:
                            print('        following operator = "{}"'.format(m[0]))
                        if not r.endswith('%e^-') and (last_priority <= inside_priority >= priority[m[0]] or
                            inside_priority == priority['*'] and m[0] == '/'): # conversion (a*b)/c = a*b/c is done here
                            r += inside + s[:m.end()]
                        else: # append parentheses in the case of %e^-(a*b)
                            r += '(' + inside + ')' + s[:m.end()]
                        last_priority = priority[m[0]]
                        if min_priority > last_priority:
                            min_priority = last_priority
                        s = s[m.end():]
                    else: # no operator follows after a closing parenthesis
                        if debug:
                            print(f'        no following operator, r = {r}')
                        if not r.endswith('%e^-') and last_priority <= inside_priority:
                            r += inside
                        else: # append parentheses in the case of %e^-(a*b)
                            r += '(' + inside + ')'
                    if debug:
                        print('        r = "{}", min_priority = "{}"'.format(r, min_priority))
                elif m[0] == ')':
                    r += s[:m.end() - 1] # string before ')'
                    if debug:
                        print('    ), r = "{}", remainder = "{}"'.format(r, s[m.end():]))
                    return r, min_priority, s[m.end():]
                elif m[0] == '[':
                    r += s[:m.end()] # string until '['
                    if debug:
                        print('    [')
                        print('        r = "{}"'.format(r))
                    inside, _, s = Maxima.remove_redundant_parentheses(s[m.end():])
                    r += inside # including ']'
                    if debug:
                        print('        r = "{}"'.format(r))
                elif m[0] == ']':
                    r += s[:m.end()] # string until ']'
                    if debug:
                        print('    ], r = "{}", remainder = "{}"'.format(r, s[m.end():]))
                    return r, min_priority, s[m.end():]
                else: # function
                    if debug:
                        print('    function = "{}", '.format(m[3]))
                    r += s[:m.end()]
                    inside, _, s = Maxima.remove_redundant_parentheses(s[m.end():])
                    if m[3] == 'diff' and inside.endswith(',1') and inside[:-2].count(',') == 1:
                        r += inside[:-2] + ')'
                    else:
                        r += inside + ')'
                    if debug:
                        print('    function, r = "{}", '.format(r))
            else:
                r += s
                if debug:
                    print('    no operator/function/(, r = "{}"'.format(r))
                break
        if debug:
            print('    return, r = "{}", min_priority = {}'.format(r, min_priority))
        return r, min_priority, ''

    def modify_output(self, s, remove_new_lines = True):
        debug = False
        if debug:
            print('modify_output 0 = "{}"'.format(s))
        if remove_new_lines:
            # r'"(\\.|[^"])*"' -> string enclosed in double quotes
            s = resub_outside((r' *\n *', ''), s, r'"(\\.|[^"])*"').strip()
        s = resub_outside(((' ', ''), # remove spaces
                           (r"'?([_A-Za-z][_A-Za-z0-9]*)\(", r'\1(')), # 'func( -> func(
                           s, r'"(\\.|[^"])*"')
        if debug:
            print('modify_output 1 = "{}"'.format(s))
        s = self.remove_redundant_parentheses(s)[0]
        if debug:
            print('modify_output 2 = "{}"'.format(s))
        s = resub_outside(((r'([^(^\[=,])-', r'\1 - '),
                           (r'([+=])', r' \1 '),
                           (',',  ', '),
                           (r'([^_A-Za-z](?:[0-9]+\.?|\.[0-9]+)[eb]) ([-+]) ([0-9])', r'\1\2\3')), # 1.0e + 10 -> 1.0e+10
                           s, r'"(\\.|[^"])*"')
        if debug:
            print('modify_output 3 = "{}"'.format(s))
        return s

    def __del__(self):
        try:
            self.maxima.sendline('quit();')
        except:
            pass
        if sys.platform == 'win32':
            self.maxima.kill(0)
        else:
            self.maxima.close()

class MyTextCtrl(wx.TextCtrl):
    colors = (
        (0, 0, 0), # black
        (255, 0, 0), # red
        (0, 0, 255), # blue
        (255, 165, 0), # orange
        (0, 128, 0), # green
        (128, 0, 0), # maroon
        (192, 192, 192), # silver
        (255, 0, 255) # fuchsia magenta
    )
    str_menu_wo_shortcut = _(u'通常入力モード')
    str_menu_with_shortcut = _(u'コマンドショートカットモード')
    str_wo_shortcut = _(u'Shift+EnterでMaximaコマンドを評価します．上下を空行で挟まれた部分，または選択部分をMaximaコマンドとして解釈します．\n' +
        u'EscキーでMaximaコマンドのショートカットが使えるようになります．')
    str_with_shortcut = _(
        u'p[A]rtfrac: 部分分数分解 | [D]iff: 微分 | [E]xpand: 展開 | [F]actor: 因数分解 | [H]line: 区切り線 | ' +
        u'[I]ntegrate: 積分 | f[L]oat: 数値化 | [M]ultthru: 先頭を各項にかけて展開 | s[O]lve: 方程式を解く | ' +
        u'[P]arenthesis: 丸括弧でくくる | ise[Q]ual: 両辺が等しいか | [R]at: 項でまとめる | [S]implify: 簡単化 | ' +
        u's[U]bst: 後で代入 | e[V]: 先に代入\n' +
        u'Escキーで通常入力に戻ります．')
    completion_expressions = (
        '%e',
        '%gamma',
        '%i',
        '%pi',
        ':lisp $%;',
        'abs(x)',
        'acos(x)',
        'acosh(x)',
        'asin(x)',
        'asinh(x)',
        'assume(x > 0, ...)$ /* <-> forget(x > 0, ...)$ */ facts();',
        'atan(x)',
        'atanh(x)',
        'atan2(y, x)',
        'atvalue(f(x), x = x0, f0)',
        "bc2(ode2('diff(y, x) ..., y, x), x = x1, y = y1, x = x2, y = y2)",
        'binomial(n, k)',
        'ceiling(x)',
        'cos(x)',
        'cosh(x)',
        'determinant(matrix)',
        'depends(f_1, x_1, ..., [f_n, g_n], [x_n, y_n])',
        'dependencies',
        'diag([a11, a22, ...]) /* needs load("diag") */',
        'diff(expr, x)',
        'diff(expr, x, n)',
        'display(expr_1, ..., expr_n)',
        'eigenvalues(matrix)',
        'eigenvectors(matrix)',
        'erf(x)',
        'erfc(x)',
        'ev(expr, x = a)',
        'exp(x)',
        'example(topic)',
        'expand(expr)',
        'declare(a_1, integer, ...)$ /* <-> remove(a_1, integer, ...)$ */ facts();',
        "desolve('diff(f(x), x) ..., f(x))",
        "desolve(['diff(f(x), x) ..., 'diff(g(x), x) ...], [f(x), g(x)])",
        'factor(expr)',
        'factorial(n)',
        'facts()',
        'float(expr)',
        'floor(x)',
        'forget(x > 0, ...)$',
        'for variable: initial_value step increment thru limit do (body, ...)',
        'for variable: initial_value step increment while condition do (body, ...)',
        'for variable: initial_value step increment unless condition do (body, ...)',
        'for variable in [list] do (body, ...)',
        'for variable in [list] do (body, ...)',
        'fullratsimp(expr)',
        'fpprec: digits$',
        "ic1(ode2('diff(y, x) ..., y, x), x = x0, y = y0)",
        "ic2(ode2('diff(y, x) ..., y, x), x = x0, y = y0, 'diff(y, x) = dy0)",
        'ident(n)',
        'if cond_1 then expr_1',
        'if cond_1 then expr_1 else expr_0',
        'if cond_1 then expr_1 elseif cond_2 then expr_2 elseif ... else expr_0',
        'inf /* real positive infinity */',
        'infinity /* complex infinity */',
        'integrate(expr, x)',
        'integrate(expr, x, a, b)',
        'invert(matrix)',
        'kill(a_1, ...)$',
        'kill(all)$',
        'kron_delta(x1, x2, ...)',
        'levi_civita([i, j, k]) /* needs load("itensor") */',
        'limit(expr, x, val)',
        'matrix([a_11, ...], [a_21, ...])',
        'makelist(expr, i, i_0, i_1)',
        'max(x_1, ...)',
        'minf /* real negative infinity */',
        'min(x_1, ...)',
        'mod(x, y)',
        'multthru(expr)',
        'multthru(x, expr)',
        'newline()',
        "ode2('diff(y, x) ..., y, x)",
        "ode2('diff(y, x) ..., y, x); bc2(%, x = x1, y = y1, x = x2, y = y2)",
        "ode2('diff(y, x) ..., y, x); ic1(%, x = x0, y = y0)",
        "ode2('diff(y, x) ..., y, x); ic2(%, x = x0, y = y0, 'diff(y, x) = dy0)",
        'partfrac(expr, x)',
        'plot2d(f(x), [x, x_min, x_max], [style, lines], [color, red], [legend, "f(x)"], [xlabel, "x"], ' +
            '[ylabel, "y"], [y, y_min, y_max])$',
        'plot2d([f(x), g(x)], [x, x_min, x_max], [style, lines], [color, red], [legend, "f(x)", "g(x)"], ' +
            '[xlabel, "x"], [ylabel, "y"], [y, y_min, y_max])$',
        'plot2d(discrete, [x_0, ...], [y_0, ...], [x, x_min, x_max], [style, points], [color, red], ' +
            '[legend, "series 1"], [xlabel, "x"], [ylabel, "y"], [y, y_min, y_max])$',
        'plot2d(discrete, [x_0, y_0], [x_1, y_1], [x, x_min, x_max], [style, points], [color, red], ' +
            '[legend, "series 1"], [xlabel, "x"], [ylabel, "y"], [y, y_min, y_max])$',
        'print(expr_1, ..., expr_n)',
        'printf(true, "string", expr_1, ..., expr_n) /* format example: ~d~t~3,1e~t~g~% */',
        'product(expr, i, i_0, i_1)',
        'product(expr, i, i_0, i_1), simpproduct',
        'radcan(expr)',
        'rat(expr, x_1, ...)',
        'rationalize(expr)',
        'ratsimp(expr)',
        'remove(a_1, integer, ...)$',
        'round(x)',
        'simpproduct',
        'simpsum',
        'sin(x)',
        'sinh(x)',
        'solve(expr, x)',
        'solve([eqn_1, ...], [x_1, ...])',
        'sprint(expr_1, ..., expr_n) /* in one line */',
        'sqrt(x)',
        'subst(a, x, expr)',
        'sum(expr, i, i_0, i_1)',
        'sum(expr, i, i_0, i_1), simpsum',
        'tan(x)',
        'tanh(x)',
        'taylor(expr, x, a, n)',
        'thru count do (body, ...)',
        'trigexpand(expr)',
        'trigsimp(expr)',
        'transpose(matrix)',
        'unless  unless condition do (body, ...)',
        'while condition do (body, ...)',
    )

    def __init__(self, parent, id = wx.ID_ANY, value = wx.EmptyString, pos = wx.DefaultPosition,
            size = wx.DefaultSize, style = 0, font = None):
        if sys.platform == 'win32' and value == wx.EmptyString:
            # Font is never reflected as long as value is empty
            super(MyTextCtrl, self).__init__(parent, id, ' ', pos, size, style)
            self.SetSelection(0, 1)
        else:
            super(MyTextCtrl, self).__init__(parent, id, value, pos, size, style)
        self.font = font
        self.escape_from_shortcut_function = None
        if self.font is not None:
            self.SetFont(self.font)
        self.maxima = Maxima()
        self.shortcut = False
        self.last_value = self.GetValue() # unicode
        self.operations = [[0, '', self.last_value]]
        self.operation_index = len(self.operations)
        self.record_op = True
        self.completion_from = None
        self.completion_candidates = []
        self.completion_index = 0
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)
        if sys.platform == 'darwin':
            try:
                self.OSXDisableAllSmartSubstitutions()
            except:
                pass
        self.debug = False

    def shorten(self, s):
        return s if len(s) <= 23 else s[:10] + '...' + s[-10:]

    def record_operation(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        v = self.GetValue() # unicode
        d = str_diff(self.last_value, v)
        if d[1] == '' and d[2] == '':
            self.operation_index = len(self.operations)
            return
        if self.debug:
            print(u'{}: "{}" -> "{}"'.format(sys._getframe().f_code.co_name, self.shorten(self.last_value), self.shorten(v)))
            print(u'{}: d = {}'.format(sys._getframe().f_code.co_name, [d[0], self.shorten(d[1]), self.shorten(d[2])]))
        l = self.operations[-1]
        if (self.operation_index == len(self.operations) and
            l[1] == '' and d[1] == '' and len(d[2]) == 1 and l[0] + len(l[2]) == d[0]):
            #                                l[0]    l[0] + len(l[2])
            #                                 |             |
            # l: [i_l, '', 'aaaaaaaaaaaaaa']  aaaaaaaaaaaaaa|
            # d: [i_d, '', 'a'             ]                a
            #                                               |
            #                                              d[0]
            l[2] += d[2]
        elif (self.operation_index == len(self.operations) and
            l[2] == '' and d[2] == '' and len(d[1]) == 1 and d[0] + len(d[1]) == l[0]):
            #                                 l[0]
            #                                  |
            # l: [i_l, 'aaaaaaaaaaaaaa', '']   aaaaaaaaaaaaaa
            # d: [i_d, 'a',              '']  a|
            #                                 ||
            #                                /  \
            #                             d[0]  d[0] + len(d[1])
            l[0] = d[0]
            l[1] = d[1] + l[1]
        else:
            self.operations.append(d)
            if len(self.operations) > 100:
                del self.operations[:len(self.operations) - 100]
            self.operation_index = len(self.operations)
        if self.debug:
            print(u'{}: operations = {}'.format(sys._getframe().f_code.co_name,
                [[i[0], self.shorten(i[1]), self.shorten(i[2])] for i in self.operations]))
        self.last_value = v # unicode

    def WriteText(self, text, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        super(MyTextCtrl, self).WriteText(text)
        self.record_op = True

    def SetValue(self, value, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        super(MyTextCtrl, self).SetValue(value)
        self.record_op = True

    def Replace(self, from_, to_, value, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        super(MyTextCtrl, self).Replace(from_, to_, value)
        self.record_op = True

    def Remove(self, from_, to_, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        super(MyTextCtrl, self).Remove(from_, to_)
        self.record_op = True

    def Cut(self, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        super(MyTextCtrl, self).Cut()
        pyperclip.copy(pyperclip.paste())
        self.record_op = True

    def Copy(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        super(MyTextCtrl, self).Copy()
        pyperclip.copy(pyperclip.paste())

    def Paste(self, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.record_op = record_op
        pyperclip.copy(pyperclip.paste())
        super(MyTextCtrl, self).Paste()
        self.record_op = True

    def OnText(self, event):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        if self.record_op:
            self.record_operation()
        if self.font is not None:
            self.SetFont(self.font)
        self.SetModified(True)

    def insert_shortcut(self, prefix, postfix, selection_wo_original, find = None, replace = None, record_op = True):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        v = self.GetStringSelection()
        if find is not None:
            v = re.sub(find, replace, v)
        self.Replace(s[0], s[1], prefix + v + postfix, record_op)
        self.SetSelection(
            s[0] + (selection_wo_original[0] if selection_wo_original[0] <= len(prefix)
            else len(v) + selection_wo_original[0] - 1),
            s[0] + (selection_wo_original[1] if selection_wo_original[1] <= len(prefix)
            else len(v) + selection_wo_original[1] - 1))

    def OnCharHook(self, event):
#        print(event.GetKeyCode())
        if sys.platform.startswith('linux'):
            if event.GetModifiers() == wx.MOD_SHIFT:
                if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                    self.send_commands_to_maxima()
                    return
                elif event.GetKeyCode() == wx.WXK_SPACE:
                    self.completion()
                    return
            elif event.GetModifiers() == wx.MOD_CONTROL:
                if event.GetKeyCode() == wx.WXK_RIGHT:
                    self.indent(u'    ')
                    return
                elif event.GetKeyCode() == wx.WXK_LEFT:
                    self.unindent(u'    ')
                    return
                elif event.GetKeyCode() == wx.WXK_DOWN:
                    self.indent(u'\t')
                    return
                elif event.GetKeyCode() == wx.WXK_UP:
                    self.unindent(u'\t')
                    return
        if self.shortcut:
            if event.GetKeyCode() == ord('A'):
                #                      0123456789  0  12345
                self.insert_shortcut(u'(partfrac(', u', x))', (13, 14))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('D'):
                #                      012345  6  78901
                self.insert_shortcut(u'(diff(', u', x))', (9, 10))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('E'):
                #                      01234567  8  90
                self.insert_shortcut(u'(expand(', u'))', (1, 10))
            elif event.GetKeyCode() == ord('F'):
                #                      01234567  8  90
                self.insert_shortcut(u'(factor(', u'))', (1, 10))
            elif event.GetKeyCode() == ord('H'):
                self.WriteText(u'/* -------------------------------------------------- */\n')
            elif event.GetKeyCode() == ord('I'):
                #                      01234567890  1  23456
                self.insert_shortcut(u'(integrate(', u', x))', (14, 15))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('L'):
                #                      0123456  7  89
                self.insert_shortcut(u'(float(', u'))', (1, 9))
            elif event.GetKeyCode() == ord('M'):
                #                      0123456789  0  12
                self.insert_shortcut(u'(multthru(', u'))', (1, 12))
            elif event.GetKeyCode() == ord('O'):
                #                      0123456  7  89012
                self.insert_shortcut(u'(solve(', u', x))', (10, 11))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('P'):
                #                      0  1  2
                self.insert_shortcut(u'(', u')', (1, 2))
            elif event.GetKeyCode() == ord('Q'):
                #                      0123456789  0  123
                self.insert_shortcut(u'(is(equal(', u')))', (1, 13), r'\s+=\s+', u', ')
            elif event.GetKeyCode() == ord('R'):
                #                      01234  5  67890
                self.insert_shortcut(u'(rat(', u', x))', (8, 9))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('S'):
                #                      01234567890123456789012345678  9  0123
                self.insert_shortcut(u'(trigsimp(fullratsimp(radcan(', u'))))', (1, 33))
            elif event.GetKeyCode() == ord('U'):
                #                      0123456789012  3  45
                self.insert_shortcut(u'(subst(a, x, ', u'))', (7, 11))
                self.escape_from_shortcut_function(event)
            elif event.GetKeyCode() == ord('V'):
                #                      0123  4  567890123
                self.insert_shortcut(u'(ev(', u', x = a))', (7, 12))
                self.escape_from_shortcut_function(event)
            else:
                event.Skip()
        else:
            self.record_op = True
            event.Skip()
            if self.completion_from is not None and event.GetModifiers() != wx.MOD_SHIFT:
                self.completion_from = None

    def Undo(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.completion_from = None
        if self.operation_index == 0:
            return
        elif self.operation_index == len(self.operations):
            self.record_operation()
        self.operation_index -= 1
        o = self.operations[self.operation_index]
        if self.debug:
            print(u'{}: "{}" -> "{}"'.format(sys._getframe().f_code.co_name, self.shorten(o[2]), self.shorten(o[1])))
            if o[2] != self.GetRange(o[0], o[0] + len(o[2])):
                print(u'{}: !!!!! "{}" != "{}"'.format(sys._getframe().f_code.co_name, o[2], self.GetRange(o[0], o[0] + len(o[2]))))
        self.Replace(o[0], o[0] + len(o[2]), o[1], record_op = False)

    def Redo(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.completion_from = None
        if self.operation_index == len(self.operations):
            return
        o = self.operations[self.operation_index]
        if self.debug:
            print(u'{}: "{}" -> "{}"'.format(sys._getframe().f_code.co_name, self.shorten(o[1]), self.shorten(o[2])))
            if o[1] != self.GetRange(o[0], o[0] + len(o[1])):
                print(u'{}: !!!!! "{}" != "{}"'.format(sys._getframe().f_code.co_name, o[1], self.GetRange(o[0], o[0] + len(o[1]))))
        self.Replace(o[0], o[0] + len(o[1]), o[2], record_op = False)
        self.operation_index += 1

    def LoadFile(self, filename, fileType = wx.TEXT_TYPE_ANY):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        with open(filename, 'rb') as f:
            s = f.read()
        try:
            s = s.decode('UTF-8') # unicode
            char_code = 'UTF-8'
        except:
            s = s.decode('CP932') # unicode
            char_code = 'CP932'
        if s.find('\r\n') != -1:
            return_code = 'CR+LF'
            s = s.replace(u'\r\n', u'\n').replace(u'\r', u'\n')
        elif s.find('\r') != -1:
            return_code = 'CR'
            s = s.replace(u'\r', u'\n')
        else:
            return_code = 'LF'
        self.SetValue(s)
        return char_code, return_code

    def completion(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        if self.completion_from is None:
            s = self.GetSelection()
            v = self.GetValue() # unicode
            i = s[0] - 1
            while True:
                if i < 0:
                    self.completion_from = 0
                    break
                elif v[i] in r'/\%+-^_?:':
                    self.completion_from = i
                    break
                elif v[i] not in u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
                    self.completion_from = i + 1
                    break
                i -= 1
            p = v[self.completion_from:s[1]]
            if len(p) == 0:
                self.completion_from = None
                return
            self.completion_candidates = [i for i in self.completion_expressions
                if i.lower().startswith(p.lower()) or i.upper().startswith(p.upper())]
            if len(self.completion_candidates) == 0:
                self.completion_from = None
                return
            self.completion_index = 0
        self.completion_forward()

    def completion_forward(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        if self.completion_from is not None:
            self.completion_index %= len(self.completion_candidates)
            self.Replace(self.completion_from, self.GetSelection()[1],
                self.completion_candidates[self.completion_index], record_op = False)
#            self.SetSelection(self.completion_from, self.GetInsertionPoint())
            self.completion_index += 1

    def completion_backward(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        if self.completion_from is not None:
            self.completion_index = (self.completion_index - 2)%len(self.completion_candidates)
            self.Replace(self.completion_from, self.GetSelection()[1],
                self.completion_candidates[self.completion_index], record_op = False)
#            self.SetSelection(self.completion_from, self.GetInsertionPoint())
            self.completion_index += 1

    def send_commands_to_maxima(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] == s[1]:
            v = self.GetValue() # unicode
            # a + b;\n
            # \n
            # b + c;\n
            # c + d;\n
            # \n
            # d + e;
            i = v.rfind(u'\n\n', 0, s[0])
            if i == -1:
                i = 0
            else:
                i += 2
            j = v.find(u'\n\n', s[0])
            if j == -1:
                j = len(v.rstrip())
            commands = v[i:j]
            m = re.match(r'(?:/\* \(%i\d+\): \*/\n)+', commands)
            if m:
                commands = commands[m.end():]
                self.Remove(i, i + m.end(), record_op = False)
                j -= m.end()
            if commands == '':
                return
            elif commands[-1] not in u';$':
                self.SetInsertionPoint(j)
                self.WriteText(u';')
                j += 1
            self.SetInsertionPoint(i)
            self.WriteText(self.maxima.last_input + u'\n')
            self.SetInsertionPoint(j + len(self.maxima.last_input) + 1)
            try:
                outputs, l_output = self.maxima.send_commands(commands)
                if len(outputs) > 0:
                    self.WriteText(u'\n\n' + u'\n\n'.join(outputs))
                    j = self.GetInsertionPoint()
                    self.SetSelection(j - l_output, j)
            except:
#                print(sys.exc_info())
                pass
        else:
            try:
                outputs, l_output = self.maxima.send_commands(self.GetStringSelection(), replace = True)
                self.Replace(s[0], s[1], u'\n'.join(outputs))
                j = self.GetInsertionPoint()
                self.SetSelection(j - l_output, j)
            except:
#                print(sys.exc_info())
                pass

    def set_negative(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            ss = self.GetStringSelection()
            try:
                v = u'\n'.join(self.maxima.send_commands(u'-(' + ss + u')', replace = True)[0])
                if ss[0] == u'(' and ss[-1] == u')':
                    v = u'(' + v + u')'
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))
            except:
#                print(sys.exc_info())
                pass

    def set_reciprocal(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            try:
                v = u'\n'.join(self.maxima.send_commands(u'1/(' + self.GetStringSelection() + u')', replace = True)[0])
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))
            except:
#                print(sys.exc_info())
                pass

    def multiply(self, multiplier):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        if s[0] != s[1]:
            try:
                v = u'\n'.join(self.maxima.send_commands(
                    u'multthru(' + multiplier + u',' + self.GetStringSelection() + u')', replace = True)[0])
                w = self.GetStringSelection()
                if w[0] == u'(' and w[-1] == u')':
                    s[0] += 1
                    s[1] -= 1
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))
            except:
#                print(sys.exc_info())
                pass

    def plus(self, additive):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        if s[0] != s[1]:
            try:
                v = u'\n'.join(self.maxima.send_commands(additive + u'+' + self.GetStringSelection(), replace = True)[0])
                w = self.GetStringSelection()
                if w[0] == u'(' and w[-1] == u')':
                    s[0] += 1
                    s[1] -= 1
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))
            except:
#                print(sys.exc_info())
                pass

    def power(self, exponent):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        if s[0] != s[1]:
            try:
                v = u'\n'.join(self.maxima.send_commands(u'(' + self.GetStringSelection() + u')^(' + exponent + u')', replace = True)[0])
                w = self.GetStringSelection()
                if w[0] == u'(' and w[-1] == u')':
                    s[0] += 1
                    s[1] -= 1
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))
            except:
#                print(sys.exc_info())
                pass

    def exchange_hands(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = self.GetStringSelection()
            l = v.split(u'=')
            if len(l) > 1:
                v = u' = '.join([i.strip() for i in reversed(l)])
                self.Replace(s[0], s[1], v)
                self.SetSelection(s[0], s[0] + len(v))

    def declare_integer(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = self.GetStringSelection()
            w = u'(' + u', integer, '.join([i.strip() for i in  v.split(u',')]) + u', integer)'
            v = u'declare' + w + u'$ /* <-> remove' + w + u'$ */ facts();'
            self.Replace(s[0], s[1], v)
            self.SetInsertionPoint(s[0] + len(v))

    def select_bracket(self, parentheses):
        r = str_range_between(self.GetValue(), self.GetSelection(), parentheses)
        if r is None:
            print('\a') # beep
        else:
            self.SetSelection(*r)

    def colorize_texts(self, parentheses = None, literals = None, literal_escape = ''):
        for i in str_levels(self.GetValue(), parentheses, literals, literal_escape):
            j = i[2]%len(self.colors)
            self.SetStyle(i[0], i[1],
                wx.TextAttr(wx.Colour(self.colors[j][0], self.colors[j][1], self.colors[j][2], 255)))

    def reset_styles(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        self.SetStyle(0, len(self.GetValue()), wx.TextAttr(wx.BLACK, wx.WHITE))
        if self.font is not None:
            self.SetFont(self.font)

    def re_sub_in_top_level(self, pattern, repl, parentheses = None, literals = None, literal_escape = ''):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetStringSelection()
        levels = str_levels(s, parentheses, literals, literal_escape)
        if len(levels) == 0:
            return
        top = min([i[2] for i in levels])
        r = ''
        for i in levels:
            if i[2] == top:
                r += re.sub(pattern, repl, s[i[0]:i[1]])
            else:
                r += s[i[0]:i[1]]
        return r

    def indent(self, indenter = u' '):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        v = self.GetValue()
        s[0] = v.rfind(u'\n', 0, s[0]) + 1
        s[1] = v.find(u'\n', max(s[1] - 1, s[0]))
        if s[1] == -1:
            s[1] = len(v)
        v = re.sub(r'(^|\n)', r'\1' + indenter, v[s[0]:s[1]])
        self.Replace(s[0], s[1], v)
        self.SetSelection(s[0], s[0] + len(v))

    def unindent(self, indenter = None):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        v = self.GetValue()
        s[0] = v.rfind(u'\n', 0, s[0]) + 1
        s[1] = v.find(u'\n', s[1])
        if s[1] == -1:
            s[1] = len(v)
        if indenter is None:
            v = re.sub(r'(^|\n)[^\n]', r'\1', v[s[0]:s[1]])
        else:
            v = re.sub(r'(^|\n)' + indenter, r'\1', v[s[0]:s[1]])
        self.Replace(s[0], s[1], v)
        self.SetSelection(s[0], s[0] + len(v))

    def change_leading_space_to_tab(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = w = self.GetStringSelection()
        else:
            v = w = self.GetValue()
        while True:
            w, n = re.subn(r'((?:^|\n)\s*)[ 　]{4}', r'\1\t', w)
            if n == 0:
                break
        if v != w:
            if s[0] != s[1]:
                self.Replace(s[0], s[1], w)
                self.SetSelection(s[0], s[0] + len(w))
            else:
                self.SetValue(w)

    def change_leading_tab_to_space(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = w = self.GetStringSelection()
        else:
            v = w = self.GetValue()
        while True:
            w, n = re.subn(r'((?:^|\n)\s*)\t', r'\1    ', w)
            if n == 0:
                break
        if v != w:
            if s[0] != s[1]:
                self.Replace(s[0], s[1], w)
                self.SetSelection(s[0], s[0] + len(w))
            else:
                self.SetValue(w)

    def delete_trailing_spaces(self):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = w = self.GetStringSelection()
        else:
            v = w = self.GetValue()
        w = re.sub(r'[ \t]+(\n|$)', r'\1', w)
        if v != w:
            if s[0] != s[1]:
                self.Replace(s[0], s[1], w)
                self.SetSelection(s[0], s[0] + len(w))
            else:
                self.SetValue(w)

    def transform_chars(self, method = 'upper'):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = self.GetSelection()
        if s[0] != s[1]:
            v = w = self.GetStringSelection()
        else:
            v = w = self.GetValue()
        if method == 'upper':
            w = v.upper()
        elif method == 'lower':
            w = v.lower()
        elif method == 'capitalize':
            w = v.capitalize()
        elif method == 'title':
            w = v.title()
        elif method == 'swapcase':
            w = v.swapcase()
        elif method == 'zenkaku':
            w = zenhan.h2z(v)
        elif method == 'hankaku':
            w = zenhan.z2h(v)
        if v != w:
            if s[0] != s[1]:
                self.Replace(s[0], s[1], w)
                self.SetSelection(s[0], s[0] + len(w))
            else:
                self.SetValue(w)

    def line_numbered(self, head = True, prefix = '', suffix = ': '):
        if self.debug:
            print('----- ' + sys._getframe().f_code.co_name + ' -----')
        s = list(self.GetSelection())
        v = self.GetValue()
        s[0] = v.rfind(u'\n', 0, s[0]) + 1
        s[1] = v.find(u'\n', max(s[1] - 1, s[0]))
        if s[1] == -1:
            s[1] = len(v)
        v = line_numbered_str(v[s[0]:s[1]], head, prefix, suffix)
        self.Replace(s[0], s[1], v)
        self.SetSelection(s[0], s[0] + len(v))

    def reset_maxima(self):
        self.maxima.reset()

    def __del__(self):
        try:
            del self.maxima
        except:
            pass

class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window, parent):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.parent = parent

    def OnDropFiles(self, x, y, filenames):
        if os.path.isfile(filenames[-1]):
            self.window.SetFocus()
            self.window.SetPath(correct_file_name_in_unicode(filenames[-1]))
            self.parent.load_doc(filenames[-1])
            return True
        else:
            return False

class MyTable(wx.grid.GridTableBase):
    def __init__(self):
        wx.grid.GridTableBase.__init__(self)

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data[0])

    def GetRowLabelValue(self, row):
        try:
            return self.row_labels[row]
        except:
            return str(row + 1).decode('UTF-8') if sys.version_info.major <= 2 else str(row + 1)

    def GetColLabelValue(self, col):
        return self.col_labels[col]

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def GetTypeName(self, row, col):
        return self.data_types[col]

    def AppendRows(self, numRows = 1):
        self.data.extend([self.new_data[:] for i in range(numRows)])
        return True

    def InsertRows(self, pos = 0, numRows = 1):
        self.data[pos:pos] = [self.new_data[:] for i in range(numRows)]
        return True

    def DeleteRows(self, pos = 0, numRows = 1):
        try:
            if self.GetNumberRows() == 0:
                return False
            del self.data[pos:pos + numRows]
            return True
        except:
            return False

class TableForFind(MyTable):
    def __init__(self, data = None):
        MyTable.__init__(self)
        self.row_label_size = 40
        self.col_label_size = 22
        self.COL_ACTIVE = 0
        self.COL_RE = 1
        self.COL_FIND = 2
        self.COL_REPLACE = 3
        self.col_labels = (_(u'検索対象'), _(u'正規表現'), _(u'検索文字列'), _(u'置換文字列'))
        self.col_sizes = (60, 60, 220, 220)
        self.tooltips = ((_(u'検索対象にしたくない時にはチェックを外します'), _(u'Pythonのreモジュールの文法に従います'), None, None),)
        self.data_types = (wx.grid.GRID_VALUE_BOOL, wx.grid.GRID_VALUE_BOOL,
                           wx.grid.GRID_VALUE_STRING, wx.grid.GRID_VALUE_STRING)
        self.new_data = [True, False, None, None]
        if data is None:
            self.data = [self.new_data[:], self.new_data[:], self.new_data[:], self.new_data[:], self.new_data[:],
                self.new_data[:], self.new_data[:], self.new_data[:], self.new_data[:], self.new_data[:]]
        elif sys.version_info.major <= 2:
            self.data = [[i[self.COL_ACTIVE], i[self.COL_RE],
                i[self.COL_FIND].decode('UTF-8') if type(i[self.COL_FIND]) is str else i[self.COL_FIND],
                i[self.COL_REPLACE].decode('UTF-8') if type(i[self.COL_REPLACE]) is str else i[self.COL_REPLACE]]
                for i in data]
        else:
            self.data = data

    def GetValue(self, row, col):
        if col in (self.COL_ACTIVE, self.COL_RE):
            return u'1' if self.data[row][col] else ''
        else:
            return '' if self.data[row][col] is None else self.data[row][col]

    def SetValue(self, row, col, value):
        if col in (self.COL_ACTIVE, self.COL_RE):
            self.data[row][col] = bool(value)
        else:
            value = value.decode('UTF-8') if sys.version_info.major <= 2 and type(value) is str else value
            self.data[row][col] = None if value == '' else value

    def Clear(self):
        for i in range(self.GetNumberRows()):
            self.data[i] = self.new_data[:]

    def DataString(self):
        if len(self.data) == 0:
            return 'None'
        s = u'['
        for i in self.data:
            s += u'[{}, {}, '.format(i[self.COL_ACTIVE], i[self.COL_RE])
            if i[self.COL_FIND] is not None:
                s += u"'" + i[self.COL_FIND].replace('\\', r'\\').replace('\n', r'\n').replace("'", r'\'') + u"', "
            else:
                s += u'None, '
            if i[self.COL_REPLACE] is not None:
                s += u"'" + i[self.COL_REPLACE].replace('\\', r'\\').replace('\n', r'\n').replace("'", r"\'") + u"'], "
            else:
                s += u'None], '
        return s[:-2] + u']'

class GridWithCellToolTip(wx.grid.Grid):
    def __init__(self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.DefaultSize,
        style = wx.WANTS_CHARS, name = '', table = None):
        wx.grid.Grid.__init__(self, parent, id, pos, size, style, name)
        self.table = table
        if self.table is not None:
            self.SetTable(self.table, takeOwnership = True)
            try:
                self.SetRowLabelSize(self.table.row_label_size)
            except:
                pass
            try:
                self.SetColLabelSize(self.table.col_label_size)
            except:
                pass
            try:
                for i, j in enumerate(self.table.col_sizes):
                    self.SetColSize(i, j)
            except:
                pass
        self.EnableDragRowSize(False) # needed to avoid "Segmentation fault: 11" in button_delete_gridOnButtonClick
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.OnMouseOver)

    def OnMouseOver(self, event):
        # Method to calculate where the mouse is pointing and then set the tooltip dynamically.
        # https://stackoverflow.com/questions/20589686/tooltip-message-when-hovering-on-cell-with-mouse-in-wx-grid-wxpython
        try:
            if self.table.tooltips is not None:
                # Use CalcUnscrolledPosition() to get the mouse position within the entire grid including what's offscreen
                c = self.XYToCell(*self.CalcUnscrolledPosition(event.GetX(), event.GetY()))
                row = min(c.Row, len(self.table.tooltips) - 1)
                col = min(c.Col, len(self.table.tooltips[0]) - 1)
                s = self.table.tooltips[row][col]
                if s is None:
                    s = ''
                event.GetEventObject().SetToolTip(s)
        except:
#            print(sys.exc_info())
            pass
        event.Skip()

    def AppendRows(self, numRows = 1, updateLabels = True):
        if wx.grid.Grid.AppendRows(self, numRows, updateLabels):
            self.UpdateView(numRows)
            return True
        else:
            return False

    def InsertRows(self, pos = 0, numRows = 1, updateLabels = True):
        if wx.grid.Grid.InsertRows(self, pos, numRows, updateLabels):
            self.UpdateView(numRows)
            return True
        else:
            return False

    def DeleteRows(self, pos = 0, numRows = 1, updateLabels = True):
        if wx.grid.Grid.DeleteRows(self, pos, numRows, updateLabels):
            self.UpdateView(-numRows)
            return True
        else:
            return False

    def UpdateView(self, numOfRowsIncreased):
        self.BeginBatch()
        self.ProcessTableMessage(
            wx.grid.GridTableMessage(self.table, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, numOfRowsIncreased))
        self.ProcessTableMessage(
            wx.grid.GridTableMessage(self.table, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES))
        self.EndBatch()
        self.AdjustScrollbars()
        self.ForceRefresh()

    def Copy(self):
        col = self.GetGridCursorCol()
        if self.table.data_types[col] == wx.grid.GRID_VALUE_STRING:
            pyperclip.copy(self.table.GetValue(self.GetGridCursorRow(), col))

    def Paste(self):
        col = self.GetGridCursorCol()
        if self.table.data_types[col] == wx.grid.GRID_VALUE_STRING:
            self.table.SetValue(self.GetGridCursorRow(), col, pyperclip.paste())
            self.ForceRefresh()

    def Cut(self):
        col = self.GetGridCursorCol()
        if self.table.data_types[col] == wx.grid.GRID_VALUE_STRING:
            row = self.GetGridCursorRow()
            pyperclip.copy(self.table.GetValue(row, col))
            self.table.SetValue(row, col, None)
            self.ForceRefresh()

###########################################################################
## Class DialogFind
###########################################################################

class DialogFind(wx.Dialog):
    colors = (
        (255, 0, 0), # red
        (0, 0, 255), # blue
        (255, 165, 0), # orange
        (0, 128, 0), # green
        (128, 0, 0), # maroon
        (255, 0, 255), # fuchsia magenta
        (128, 0, 128), # purple
        (165, 42, 42) # brown
    )

    def __init__(self, target, font, find_data = None):
        wx.Dialog.__init__(self, None, id = wx.ID_ANY, title = _(u'検索／置換'), pos = wx.DefaultPosition,
            size = wx.Size(600, 360),
            style = wx.DEFAULT_DIALOG_STYLE | wx.MINIMIZE_BOX | wx.RESIZE_BORDER)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.grid_find = GridWithCellToolTip(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0,
            name = 'grid_find', table = TableForFind(find_data))
        self.grid_find.SetDefaultCellAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        attr = wx.grid.GridCellAttr()
        attr.SetAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
        self.grid_find.SetColAttr(self.grid_find.table.COL_FIND, attr)
        attr = wx.grid.GridCellAttr()
        attr.SetAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
        self.grid_find.SetColAttr(self.grid_find.table.COL_REPLACE, attr)
        if font is not None:
            self.grid_find.SetDefaultCellFont(font)
        bSizer1.Add(self.grid_find, 1, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.button_invert_active = wx.Button(self, wx.ID_ANY, u'!検索対象', wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_invert_active.SetToolTip(_(u'選択している行の検索対象のチェックを逆転させます'))
        bSizer2.Add(self.button_invert_active, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_invert_re = wx.Button(self, wx.ID_ANY, _(u'!正規表現'), wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_invert_re.SetToolTip(_(u'選択している行の正規表現チェックを逆転させます'))
        bSizer2.Add(self.button_invert_re, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_insert_find = wx.Button(self, wx.ID_ANY, u'+',
            wx.DefaultPosition, wx.Size(45, -1), 0, name = 'igrid_find')
        self.button_insert_find.SetToolTip(_(u'上に行を追加'))
        bSizer2.Add(self.button_insert_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_delete_find = wx.Button(self, wx.ID_ANY, u'-',
            wx.DefaultPosition, wx.Size(45, -1), 0, name = 'dgrid_find')
        self.button_delete_find.SetToolTip(_(u'選択している行を削除'))
        bSizer2.Add(self.button_delete_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_clear_find = wx.Button(self, wx.ID_ANY, _(u'リセット'),
            wx.DefaultPosition, wx.DefaultSize, 0, name = 'cgrid_find')
        self.button_clear_find.SetToolTip(_(u'検索/置換文字列を全て消去します'))
        bSizer2.Add(self.button_clear_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_increase_find = wx.Button(self, wx.ID_ANY, u'▼',
            wx.DefaultPosition, wx.Size(45, -1), 0, name = 'igrid_find')
        self.button_increase_find.SetToolTip(_(u'選択している行を下に移動'))
        bSizer2.Add(self.button_increase_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_decrease_find = wx.Button(self, wx.ID_ANY, u'▲',
            wx.DefaultPosition, wx.Size(45, -1), 0, name = 'dgrid_find')
        self.button_decrease_find.SetToolTip(_(u'選択している行を上に移動'))
        bSizer2.Add(self.button_decrease_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_variable = wx.Button(self, wx.ID_ANY, _(u'変数'),
            wx.DefaultPosition, wx.DefaultSize, 0, name = 'dgrid_find')
        self.button_variable.SetToolTip(_(u'選択している行の文字列にプログラムの変数とみなす正規表現を適用します'))
        bSizer2.Add(self.button_variable, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        bSizer1.Add(bSizer2, 0, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.button_colorize = wx.Button(self, wx.ID_ANY, _(u'色で区別'), wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_colorize.SetToolTip(_(u'検索文字列を背景色で区別します'))
        bSizer2.Add(self.button_colorize, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_clear = wx.Button(self, wx.ID_ANY, _(u'色を消す'), wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_clear.SetToolTip(_(u'背景色を消します'))
        bSizer2.Add(self.button_clear, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        bSizer2.Add((0, 0), 1, wx.EXPAND, 5 )

        self.checkBox_ignore_case = wx.CheckBox(self, wx.ID_ANY, _(u'大文字小文字を無視'), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.checkBox_ignore_case, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5 )

        self.checkBox_rewind = wx.CheckBox(self, wx.ID_ANY, _(u'最後まで検索したら最初から検索'),
            wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.checkBox_rewind, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        bSizer1.Add(bSizer2, 0, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        bSizer2.Add((0, 0), 1, wx.EXPAND, 5 )

        self.button_rep_all = wx.Button(self, wx.ID_ANY, _(u'全てを置換'), wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_rep_all.SetToolTip(_(u'領域が選択されている場合，その領域内のみ置換します．'))
        bSizer2.Add(self.button_rep_all, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_find_prev = wx.Button(self, wx.ID_ANY, _(u'前を検索'), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.button_find_prev, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_find_next = wx.Button(self, wx.ID_ANY, _(u'次を検索'), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.button_find_next, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_replace = wx.Button(self, wx.ID_ANY, _(u'置換'), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.button_replace, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_rep_find = wx.Button(self, wx.ID_ANY, _(u'置換&&次を検索'), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.button_rep_find, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        bSizer1.Add(bSizer2, 0, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.button_invert_active.Bind(wx.EVT_BUTTON, self.button_invert_activeOnButtonClick)
        self.button_invert_re.Bind(wx.EVT_BUTTON, self.button_invert_reOnButtonClick)
        self.button_insert_find.Bind(wx.EVT_BUTTON, self.button_insert_gridOnButtonClick)
        self.button_delete_find.Bind(wx.EVT_BUTTON, self.button_delete_gridOnButtonClick)
        self.button_clear_find.Bind(wx.EVT_BUTTON, self.button_clear_gridOnButtonClick)
        self.button_increase_find.Bind(wx.EVT_BUTTON, self.button_increase_gridOnButtonClick)
        self.button_decrease_find.Bind(wx.EVT_BUTTON, self.button_decrease_gridOnButtonClick)
        self.button_variable.Bind(wx.EVT_BUTTON, self.button_variableOnButtonClick)
        self.button_colorize.Bind(wx.EVT_BUTTON, self.button_colorizeOnButtonClick)
        self.button_clear.Bind(wx.EVT_BUTTON, self.button_clearOnButtonClick)
        self.button_rep_all.Bind(wx.EVT_BUTTON, self.button_rep_allOnButtonClick)
        self.button_find_prev.Bind(wx.EVT_BUTTON, self.button_find_prevOnButtonClick)
        self.button_find_next.Bind(wx.EVT_BUTTON, self.button_find_nextOnButtonClick)
        self.button_replace.Bind(wx.EVT_BUTTON, self.button_replaceOnButtonClick)
        self.button_rep_find.Bind(wx.EVT_BUTTON, self.button_rep_findOnButtonClick)

        self.target = target
        self.found = None

    def button_invert_activeOnButtonClick(self, event):
        t = self.grid_find.table
        for i in self.grid_find.GetSelectedRows():
            t.data[i][t.COL_ACTIVE] = not t.data[i][t.COL_ACTIVE]
        self.grid_find.ForceRefresh()

    def button_invert_reOnButtonClick(self, event):
        t = self.grid_find.table
        for i in self.grid_find.GetSelectedRows():
            t.data[i][t.COL_RE] = not t.data[i][t.COL_RE]
        self.grid_find.ForceRefresh()

    def button_insert_gridOnButtonClick(self, event):
        self.FindWindowByName(event.GetEventObject().GetName()[1:],
            event.GetEventObject().GetParent()).InsertRows(0, 1)

    def button_append_gridOnButtonClick(self, event):
        self.FindWindowByName(event.GetEventObject().GetName()[1:],
            event.GetEventObject().GetParent()).AppendRows(1)

    def button_delete_gridOnButtonClick(self, event):
        grid = self.FindWindowByName(event.GetEventObject().GetName()[1:], event.GetEventObject().GetParent())
        row, col = grid.GetGridCursorRow(), grid.GetGridCursorCol()
        grid.DeleteRows(row, 1)
        if grid.GetNumberRows() > 0:
            grid.SetGridCursor(min(row, grid.GetNumberRows() - 1), col)

    def button_clear_gridOnButtonClick(self, event):
        grid = self.FindWindowByName(event.GetEventObject().GetName()[1:], event.GetEventObject().GetParent())
        grid.ClearGrid()
        grid.ForceRefresh()

    def button_increase_gridOnButtonClick(self, event):
        grid = self.FindWindowByName(event.GetEventObject().GetName()[1:], event.GetEventObject().GetParent())
        row, col = grid.GetGridCursorRow(), grid.GetGridCursorCol()
        if row != len(grid.table.data) - 1:
            grid.table.data[row], grid.table.data[row + 1] = grid.table.data[row + 1], grid.table.data[row]
            grid.SetGridCursor(row + 1, col)

    def button_decrease_gridOnButtonClick(self, event):
        grid = self.FindWindowByName(event.GetEventObject().GetName()[1:], event.GetEventObject().GetParent())
        row, col = grid.GetGridCursorRow(), grid.GetGridCursorCol()
        if row != 0:
            grid.table.data[row], grid.table.data[row - 1] = grid.table.data[row - 1], grid.table.data[row]
            grid.SetGridCursor(row - 1, col)

    def button_variableOnButtonClick(self, event):
        t = self.grid_find.table
        row = self.grid_find.GetGridCursorRow()
        t.data[row][t.COL_RE] = True
        t.data[row][t.COL_FIND] = (r'([\t\n +\-*/^=(){}\[\],.:;?' + "'" + r'"%&<>\\#]|^)' +
            ('' if t.data[row][t.COL_FIND] is None else t.data[row][t.COL_FIND]) +
            r'([\t\n +\-*/^=(){}\[\],.:;?' + "'" + r'"%&<>\\#]|$)')
        t.data[row][t.COL_REPLACE] = (r'\1' +
            ('' if t.data[row][t.COL_REPLACE] is None else t.data[row][t.COL_REPLACE]) +
            r'\2')
        self.grid_find.ForceRefresh()

    def button_colorizeOnButtonClick(self, event):
#        self.target.reset_styles()
        v = self.target.GetValue()
        n = 0
        found = []
        for i in self.grid_find.table.data:
            if not i[self.grid_find.table.COL_ACTIVE] or i[self.grid_find.table.COL_FIND] is None:
                continue
            if i[self.grid_find.table.COL_RE]:
                m = re.search(i[self.grid_find.table.COL_FIND], v)
                if m:
                    found.append([m.start(), m.end(), i, n])
                    n += 1
            elif self.checkBox_ignore_case.GetValue():
                m = re.search(i[self.grid_find.table.COL_FIND], v, flags = re.IGNORECASE)
                if m:
                    found.append([m.start(), m.end(), i, n])
                    n += 1
            else:
                m = v.find(i[self.grid_find.table.COL_FIND])
                if m != -1:
                    found.append([m, m + len(i[self.grid_find.table.COL_FIND]), i, n])
                    n += 1
        shift = 0
        while len(found) > 0:
            found.sort(key = lambda x: (x[0], x[3]))
            start, end, i, n = found[0][0], found[0][1], found[0][2], found[0][3]
            j = n%len(self.colors)
            self.target.SetStyle(shift + start, shift + end,
                wx.TextAttr(wx.BLACK, wx.Colour(self.colors[j][0], self.colors[j][1], self.colors[j][2], 110)))
            v = v[end:]
            shift += end
            refind = []
            for j in range(len(found)):
                if found[0][0] < end:
                    refind.append((found[0][2], found[0][3]))
                    del found[0]
                else:
                    break
            for j in found:
                j[0] -= end
                j[1] -= end
            for j in refind:
                i, n = j[0], j[1]
                if i[self.grid_find.table.COL_RE]:
                    m = re.search(i[self.grid_find.table.COL_FIND], v)
                    if m:
                        found.append([m.start(), m.end(), i, n])
                elif self.checkBox_ignore_case.GetValue():
                    m = re.search(i[self.grid_find.table.COL_FIND], v, flags = re.IGNORECASE)
                    if m:
                        found.append([m.start(), m.end(), i, n])
                else:
                    m = v.find(i[self.grid_find.table.COL_FIND])
                    if m != -1:
                        found.append([m, m + len(i[self.grid_find.table.COL_FIND]), i, n])

    def button_clearOnButtonClick(self, event):
        self.target.reset_styles()

    def insert_find(self, row, value):
        for i in range(len(self.grid_find.table.data)):
            if self.grid_find.table.data[i][self.grid_find.table.COL_FIND] == value:
                self.grid_find.table.data.insert(0, self.grid_find.table.data[i])
                del self.grid_find.table.data[i + 1]
                self.grid_find.UpdateView(0)
                return
        n = 0
        if self.grid_find.table.data[0][self.grid_find.table.COL_FIND] is not None:
            n = 1
            self.grid_find.table.InsertRows(0, 1)
        self.grid_find.table.SetValue(0, self.grid_find.table.COL_FIND, value)
        self.grid_find.UpdateView(n)

    def insert_replace(self, row, value):
        n = 0
        if self.grid_find.table.data[0][self.grid_find.table.COL_REPLACE] is not None:
            n = 1
            self.grid_find.table.InsertRows(0, 1)
        self.grid_find.table.SetValue(0, self.grid_find.table.COL_REPLACE, value)
        self.grid_find.UpdateView(n)

    def button_rep_allOnButtonClick(self, event):
        s = self.target.GetSelection()
        v0 = self.target.GetValue() if s[0] == s[1] else self.target.GetStringSelection()
        n = 0
        found = []
        for i in self.grid_find.table.data:
            if not i[self.grid_find.table.COL_ACTIVE] or i[self.grid_find.table.COL_FIND] is None:
                continue
            if i[self.grid_find.table.COL_RE]:
                m = re.search(i[self.grid_find.table.COL_FIND], v0)
                if m:
                    found.append([m.start(), m.end(), i, n])
                    n += 1
            elif self.checkBox_ignore_case.GetValue():
                m = re.search(i[self.grid_find.table.COL_FIND], v0, flags = re.IGNORECASE)
                if m:
                    found.append([m.start(), m.end(), i, n])
                    n += 1
            else:
                m = v0.find(i[self.grid_find.table.COL_FIND])
                if m != -1:
                    found.append([m, m + len(i[self.grid_find.table.COL_FIND]), i, n])
                    n += 1
        v1 = ''
        while len(found) > 0:
            found.sort(key = lambda x: (x[0], x[3]))
            start, end, i = found[0][0], found[0][1], found[0][2]
            if i[self.grid_find.table.COL_RE]:
                v1 += v0[:start] + re.sub(i[self.grid_find.table.COL_FIND],
                    '' if i[self.grid_find.table.COL_REPLACE] is None else i[self.grid_find.table.COL_REPLACE],
                    v0[start:end])
            elif self.checkBox_ignore_case.GetValue():
                v1 += v0[:start] + re.sub(i[self.grid_find.table.COL_FIND],
                    '' if i[self.grid_find.table.COL_REPLACE] is None else i[self.grid_find.table.COL_REPLACE],
                    v0[start:end], flags = re.IGNORECASE)
            else:
                if i[self.grid_find.table.COL_REPLACE] is None:
                    v1 += v0[:start]
                else:
                    v1 += v0[:start] + i[self.grid_find.table.COL_REPLACE]
            v0 = v0[end:]
            refind = []
            for j in range(len(found)):
                if found[0][0] < end:
                    refind.append((found[0][2], found[0][3]))
                    del found[0]
                else:
                    break
            for j in found:
                j[0] -= end
                j[1] -= end
            for j in refind:
                i, n = j[0], j[1]
                if i[self.grid_find.table.COL_RE]:
                    m = re.search(i[self.grid_find.table.COL_FIND], v0)
                    if m:
                        found.append([m.start(), m.end(), i, n])
                elif self.checkBox_ignore_case.GetValue():
                    m = re.search(i[self.grid_find.table.COL_FIND], v0, flags = re.IGNORECASE)
                    if m:
                        found.append([m.start(), m.end(), i, n])
                else:
                    m = v0.find(i[self.grid_find.table.COL_FIND])
                    if m != -1:
                        found.append([m, m + len(i[self.grid_find.table.COL_FIND]), i, n])
        v1 += v0
        if s[0] == s[1]:
            self.target.SetValue(v1)
            self.target.SetInsertionPointEnd()
        else:
            self.target.Replace(s[0], s[1], v1)
            self.target.SetSelection(s[0], s[0] + len(v1))

    def find_prev_between(self, start, end):
        v = self.target.GetValue()
        self.found = None
        for i in self.grid_find.table.data:
            if not i[self.grid_find.table.COL_ACTIVE] or i[self.grid_find.table.COL_FIND] is None:
                continue
            if i[self.grid_find.table.COL_RE]:
                m = re.search(i[self.grid_find.table.COL_FIND], v[start:end])
                if m and (self.found is None or m.start() > self.found[0]):
                    self.found = [m.start(), m.end(), i]
            elif self.checkBox_ignore_case.GetValue():
                m = re.search(i[self.grid_find.table.COL_FIND], v[start:end], flags = re.IGNORECASE)
                if m and (self.found is None or m.start() > self.found[0]):
                    self.found = [m.start(), m.end(), i]
            else:
                m = v[start:end].find(i[self.grid_find.table.COL_FIND])
                if m != -1 and (self.found is None or m > self.found[0]):
                    self.found = [m, m + len(i[self.grid_find.table.COL_FIND]), i]
        if self.found is not None:
            self.found[0] += start
            self.found[1] += start

    def button_find_prevOnButtonClick(self, event):
        end = self.target.GetInsertionPoint()
        for start in range(end - 1, -1, -1):
            self.find_prev_between(start, end)
            if self.found is not None:
                self.target.SetSelection(self.found[0], self.found[1])
                self.target.ShowPosition(self.found[0])
                return
        if self.checkBox_rewind.GetValue():
            end = self.target.GetLastPosition()
            for start in range(end - 1, -1, -1):
                self.find_prev_between(start, end)
                if self.found is not None:
                    self.target.SetSelection(self.found[0], self.found[1])
                    self.target.ShowPosition(self.found[0])
                    return
        print('\a') # beep

    def find_next_from(self, point):
        v = self.target.GetValue()
        self.found = None
        for i in self.grid_find.table.data:
            if not i[self.grid_find.table.COL_ACTIVE] or i[self.grid_find.table.COL_FIND] is None:
                continue
            if i[self.grid_find.table.COL_RE]:
                m = re.search(i[self.grid_find.table.COL_FIND], v[point:])
                if m and (self.found is None or m.start() < self.found[0]):
                    self.found = [m.start(), m.end(), i]
            elif self.checkBox_ignore_case.GetValue():
                m = re.search(i[self.grid_find.table.COL_FIND], v[point:], flags = re.IGNORECASE)
                if m and (self.found is None or m.start() < self.found[0]):
                    self.found = [m.start(), m.end(), i]
            else:
                m = v[point:].find(i[self.grid_find.table.COL_FIND])
                if m != -1 and (self.found is None or m < self.found[0]):
                    self.found = [m, m + len(i[self.grid_find.table.COL_FIND]), i]
        if self.found is not None:
            self.found[0] += point
            self.found[1] += point

    def button_find_nextOnButtonClick(self, event):
        self.find_next_from(self.target.GetSelection()[1])
        if self.found is not None:
            self.target.SetSelection(self.found[0], self.found[1])
            self.target.ShowPosition(self.found[0])
            return
        elif self.checkBox_rewind.GetValue():
            self.find_next_from(0)
            if self.found is not None:
                self.target.SetSelection(self.found[0], self.found[1])
                self.target.ShowPosition(self.found[0])
                return
        print('\a') # beep

    def button_replaceOnButtonClick(self, event):
        s = self.target.GetStringSelection()
        if self.found is None or s == '':
            return
        if self.found[2][self.grid_find.table.COL_RE]:
            m = re.match(self.found[2][self.grid_find.table.COL_FIND], s)
            if m and m.end() == len(s):
                if self.found[2][self.grid_find.table.COL_REPLACE] is not None:
                    self.target.WriteText(re.sub(self.found[2][self.grid_find.table.COL_FIND],
                        self.found[2][self.grid_find.table.COL_REPLACE], s))
                else:
                    self.target.Remove(*self.target.GetSelection())
        elif self.checkBox_ignore_case.GetValue():
            m = re.match(self.found[2][self.grid_find.table.COL_FIND], s, flags = re.IGNORECASE)
            if m and m.end() == len(s):
                if self.found[2][self.grid_find.table.COL_REPLACE] is not None:
                    self.target.WriteText(re.sub(self.found[2][self.grid_find.table.COL_FIND],
                        self.found[2][self.grid_find.table.COL_REPLACE], s))
                else:
                    self.target.Remove(*self.target.GetSelection())
        elif s == self.found[2][self.grid_find.table.COL_FIND]:
            if self.found[2][self.grid_find.table.COL_REPLACE] is not None:
                self.target.WriteText(self.found[2][self.grid_find.table.COL_REPLACE])
            else:
                self.target.Remove(*self.target.GetSelection())

    def button_rep_findOnButtonClick(self, event):
        self.button_replaceOnButtonClick(event)
        self.button_find_nextOnButtonClick(event)

    def __del__(self):
        pass

###########################################################################
## Class FrameMain
###########################################################################

class FrameMain(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id = wx.ID_ANY,
            title = u'texteditwx (' + version + u') by Python ' + platform.python_version(),
            pos = wx.DefaultPosition, size = wx.Size(800, 700), style = wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        font = wx.Font(pointSize = 12, family = wx.FONTFAMILY_TELETYPE, style = wx.FONTSTYLE_NORMAL,
            weight = wx.FONTWEIGHT_NORMAL, underline = False, faceName = (u'MS ゴシック' if sys.platform == 'win32'
            else ('Monaco' if sys.platform == 'darwin' else 'Ubuntu Mono')))

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        staticText1 = wx.StaticText(self, wx.ID_ANY, _(u'ファイル：'), wx.DefaultPosition, wx.DefaultSize, 0)
        staticText1.Wrap(-1)
        bSizer2.Add(staticText1, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT, 5)

        self.filePicker = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString,
            _(u'ファイルを開く'), u'*.*', wx.DefaultPosition, wx.DefaultSize,
            wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
        self.filePicker.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        self.filePicker.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.filePicker.SetToolTip(_(u'ドラッグ&ドロップで決めることもできます．'))
        self.filePicker.SetDropTarget(MyFileDropTarget(self.filePicker, self))
        bSizer2.Add(self.filePicker, 1, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.char_codes = ('UTF-8', 'CP932')
        self.choice_char_code = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, self.char_codes, 0)
        self.choice_char_code.SetSelection(0)
        bSizer2.Add(self.choice_char_code, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT, 5)

        self.return_codes = ('LF', 'CR+LF', 'CR')
        self.choice_return_code = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, self.return_codes, 0)
        self.choice_return_code.SetSelection(0)
        bSizer2.Add(self.choice_return_code, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        bSizer1.Add(bSizer2, 0, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.button_plus = wx.Button(self, wx.ID_ANY, u'+', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_plus.SetToolTip(_(u'選択部分に足し算を作用させます'))
        bSizer2.Add(self.button_plus, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_minus = wx.Button(self, wx.ID_ANY, u'-', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_minus.SetToolTip(_(u'選択部分に引き算を作用させます'))
        bSizer2.Add(self.button_minus, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_multiply = wx.Button(self, wx.ID_ANY, u'*', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_multiply.SetToolTip(_(u'選択部分にかけ算を作用させます'))
        bSizer2.Add(self.button_multiply, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_divide = wx.Button(self, wx.ID_ANY, u'/', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_divide.SetToolTip(_(u'選択部分に割り算を作用させます'))
        bSizer2.Add(self.button_divide, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_power = wx.Button(self, wx.ID_ANY, u'^', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_power.SetToolTip(_(u'選択部分に累乗を作用させます'))
        bSizer2.Add(self.button_power, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        staticText1 = wx.StaticText(self, wx.ID_ANY, _(u'作用させる要素：'), wx.DefaultPosition, wx.DefaultSize, 0)
        staticText1.Wrap(-1)
        bSizer2.Add(staticText1, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 5)
        self.textCtrl_affect = wx.TextCtrl(self, wx.ID_ANY, u'2', wx.DefaultPosition, wx.Size(60, -1), 0)
        if font is not None:
            self.textCtrl_affect.SetFont(font)
        bSizer2.Add(self.textCtrl_affect, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.button_reciprocal = wx.Button(self, wx.ID_ANY, u'⇅', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_reciprocal.SetToolTip(_(u'選択部分を逆数にする'))
        bSizer2.Add(self.button_reciprocal, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_exchange_hands = wx.Button(self, wx.ID_ANY, u'⇄', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_exchange_hands.SetToolTip(_(u'選択部分の右辺と左辺を入れ替える'))
        bSizer2.Add(self.button_exchange_hands, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        bSizer2.Add((0, 0), 1, wx.EXPAND, 5 )

        self.button_left_shift = wx.Button(self, wx.ID_ANY, u'←', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_left_shift.SetToolTip(_(u'選択している行の左端1文字を削除します'))
        bSizer2.Add(self.button_left_shift, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.button_right_shift = wx.Button(self, wx.ID_ANY, u'→', wx.DefaultPosition, wx.Size(45, -1), 0)
        self.button_right_shift.SetToolTip(_(u'選択している行の左端に文字を追加します'))
        bSizer2.Add(self.button_right_shift, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        staticText1 = wx.StaticText(self, wx.ID_ANY, _(u'追加する文字：'), wx.DefaultPosition, wx.DefaultSize, 0)
        staticText1.Wrap(-1)
        bSizer2.Add(staticText1, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 5)
        self.textCtrl_shift = wx.TextCtrl(self, wx.ID_ANY, u'# ', wx.DefaultPosition, wx.Size(60, -1), 0)
        if font is not None:
            self.textCtrl_shift.SetFont(font)
        self.textCtrl_shift.SetToolTip(_(u'タブには\\t，改行には\\nを入力して下さい．'))
        bSizer2.Add(self.textCtrl_shift, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        bSizer1.Add(bSizer2, 0, wx.EXPAND, 5)

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3DSASH)
        self.splitter.Bind(wx.EVT_IDLE, self.splitterOnIdle)
        self.splitter.SetMinimumPaneSize(1)

        self.panel1 = wx.Panel(self.splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.textCtrl_edit = MyTextCtrl(self.panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
            wx.TE_MULTILINE | wx.TE_NOHIDESEL | wx.TE_RICH | wx.TE_PROCESS_TAB, font)
        # wx.TE_NOHIDESEL is required to avoid a caret display problem in windows
        # wx.TE_RICH is required to avoid a problem associated with CR+LF
        self.textCtrl_edit.escape_from_shortcut_function = self.menuItem_command_shortcutOnMenuSelection
        bSizer2.Add(self.textCtrl_edit, 1, wx.ALL | wx.EXPAND, 5)
        self.panel1.SetSizer(bSizer2)
        self.panel1.Layout()
        bSizer2.Fit(self.panel1)

        self.panel2 = wx.Panel(self.splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.textCtrl_help = wx.TextCtrl(self.panel2, wx.ID_ANY, self.textCtrl_edit.str_wo_shortcut,
            wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE | wx.TE_NOHIDESEL | wx.TE_RICH | wx.TE_READONLY)
        # wx.TE_NOHIDESEL is required to avoid a caret display problem in windows
        # wx.TE_RICH is required to avoid a problem associated with CR+LF
        if font is not None:
            self.textCtrl_help.SetFont(font)
        bSizer2.Add(self.textCtrl_help, 1, wx.ALL | wx.EXPAND, 5)
        self.panel2.SetSizer(bSizer2)
        self.panel2.Layout()
        bSizer2.Fit(self.panel2)

        self.sash_pos = 440
        self.splitter.SplitHorizontally(self.panel1, self.panel2, self.sash_pos)
        bSizer1.Add(self.splitter, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        self.menubar = wx.MenuBar(0)

        self.menu_file = wx.Menu()
        self.menuItem_open = wx.MenuItem(self.menu_file, wx.ID_ANY, _(u'開く') + '\tCtrl+O',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_file.Append(self.menuItem_open)
        self.menu_file.AppendSeparator()
        self.menuItem_save = wx.MenuItem(self.menu_file, wx.ID_ANY, _(u'保存') + '\tCtrl+S',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_file.Append(self.menuItem_save)
        self.menuItem_save_as = wx.MenuItem(self.menu_file, wx.ID_ANY, _(u'別名で保存') + '\tShift+Ctrl+S',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_file.Append(self.menuItem_save_as)
        self.menu_file.AppendSeparator()
        self.menuItem_quit = wx.MenuItem(self.menu_file, wx.ID_ANY, _(u'終了') + '\tCtrl+Q',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_file.Append(self.menuItem_quit)
        self.menubar.Append(self.menu_file, _(u'ファイル') + '(&F)')

        self.menu_edit = wx.Menu()
        self.menuItem_undo = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'取り消す') + '\tCtrl+Z',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_undo)
        self.menuItem_redo = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'やり直す') + '\tShift+Ctrl+Z',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_redo)
        self.menu_edit.AppendSeparator()
        self.menuItem_cut = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'カット') + '\tCtrl+X',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_cut)
        self.menuItem_copy = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'コピー') + '\tCtrl+C',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_copy)
        self.menuItem_paste = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'ペースト') + '\tCtrl+V',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_paste)
        self.menuItem_select_all = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'全てを選択') + '\tCtrl+A',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_select_all)
        self.menu_edit.AppendSeparator()
        self.menuItem_find = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'検索/置換') + '\tCtrl+F',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_find)
        self.menuItem_find_next = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'次を検索') + '\tCtrl+G',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_find_next)
        self.menuItem_find_prev = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'前を検索') + '\tShift+Ctrl+G',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_find_prev)
        self.menuItem_replace = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'置換') + '\tCtrl+' +
            # MacOS Venturaで，@がShift+;に変換されてしまう問題の対処
            ('_' if sys.platform == 'darwin' and int(platform.mac_ver()[0].split('.')[0]) >= 13 else '='),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_replace)
        self.menuItem_rep_find = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'置換&&次を検索') + '\tCtrl+L',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_rep_find)
        self.menuItem_rep_all = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'全てを置換'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_rep_all)
        self.menuItem_append_find = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'選択部分を検索に追加') + '\tCtrl+E',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_append_find)
        self.menuItem_append_replace = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'選択部分を置換に追加') + '\tShift+Ctrl+E',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_append_replace)
        self.menu_edit.AppendSeparator()
        self.menuItem_left_shift = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'左端1文字を削除') + '\tCtrl+[',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_left_shift)
        self.menuItem_right_shift = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'左端に文字を追加') + '\tCtrl+]',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_right_shift)
        self.menu_edit.AppendSeparator()
        self.menuItem_delete_trailing_spaces = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'右端の空白を消去'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_delete_trailing_spaces)
        self.menu_edit.AppendSeparator()
        self.menu_transform_chars = wx.Menu()
        self.menuItem_set_upper = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'大文字にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_set_upper)
        self.menuItem_set_lower = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'小文字にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_set_lower)
        self.menuItem_capitalize = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'文章の先頭を大文字にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_capitalize)
        self.menuItem_set_title = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'単語の先頭を大文字にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_set_title)
        self.menuItem_swap_case = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'大文字小文字を入れ替える'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_swap_case)
        self.menuItem_zenkaku = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'全角にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_zenkaku)
        self.menuItem_hankaku = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'半角にする'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_transform_chars.Append(self.menuItem_hankaku)
        self.menu_edit.AppendSubMenu(self.menu_transform_chars, _(u'文字種の変換'))
        self.menu_line_numbered = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'先頭に行番号を挿入'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menu_line_numbered)
        self.menu_edit.AppendSeparator()
        self.menuItem_bracket = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'括弧でくくられた部分を選択') + '\tCtrl+B',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_bracket)
        self.menu_edit.AppendSeparator()
        self.menuItem_completion = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'補完') + '\tShift+Space',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_completion)
        self.menuItem_completion_backward = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'前の補完候補') + '\tShift+Esc',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_completion_backward)
        self.menu_edit.AppendSeparator()
        self.menuItem_datetime = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'日時を挿入'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_datetime)
        self.menu_edit.AppendSeparator()
        self.menuItem_colorize_texts = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'文字に色をつける') + '\tCtrl+D',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_colorize_texts)
        self.menuItem_reset_styles = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u'文字色をリセット') + '\tShift+Ctrl+D',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_reset_styles)
        self.menu_edit.AppendSeparator()
        self.menuItem_insert_return = wx.MenuItem(self.menu_edit, wx.ID_ANY, _(u',+-=の後で改行する') + '\tCtrl+' +
            # MacOS Venturaで，@がShift+2に変換されてしまう問題の対処
            ('`' if sys.platform == 'darwin' and int(platform.mac_ver()[0].split('.')[0]) >= 13 else '@'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_edit.Append(self.menuItem_insert_return)
        self.menubar.Append(self.menu_edit, _(u'編集') + '(&E)')

        self.menu_maxima = wx.Menu()
        self.menuItem_evaluate = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'評価') + '\tShift+Enter',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_evaluate)
        self.menu_maxima.AppendSeparator()
        self.menuItem_negative = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'選択部分に-1をかける') + '\tCtrl+-',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_negative)
        self.menuItem_reciprocal = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'選択部分を逆数にする') + '\tCtrl+~',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_reciprocal)
        self.menuItem_exchange_hands = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'選択部分の右辺と左辺を入れ替える') + '\tCtrl+|',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_exchange_hands)
        self.menuItem_declare_integer = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'選択部分を整数であると仮定する') + '\tCtrl+I',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_declare_integer)
        self.menu_maxima.AppendSeparator()
        self.menuItem_command_shortcut = wx.MenuItem(self.menu_maxima, wx.ID_ANY,
            self.textCtrl_edit.str_menu_with_shortcut + '\tEsc', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_command_shortcut)
        self.menu_maxima.AppendSeparator()
        self.menuItem_reset_maxima = wx.MenuItem(self.menu_maxima, wx.ID_ANY, _(u'リセット'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_maxima.Append(self.menuItem_reset_maxima)
        self.menubar.Append(self.menu_maxima, 'Maxima(&M)')

        self.menu_python = wx.Menu()
        self.menuItem_python_header = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'シバンを挿入'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_python_header)
        self.menu_python.AppendSeparator()
        self.menuItem_python_indent = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'字下げ') + '\tCtrl+Right',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_python_indent)
        self.menuItem_python_unindent = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'字上げ') + '\tCtrl+Left',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_python_unindent)
        self.menu_python.AppendSeparator()
        self.menuItem_python_comment = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'コメントアウト') + '\tCtrl+3',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_python_comment)
        self.menuItem_python_uncomment = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'アンコメント') + '\tCtrl+2',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_python_uncomment)
        self.menu_python.AppendSeparator()
        self.menuItem_leading_tab_to_space = wx.MenuItem(self.menu_python, wx.ID_ANY, _(u'左端のタブを半角スペース4個に変換'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_python.Append(self.menuItem_leading_tab_to_space)
        self.menubar.Append(self.menu_python, 'Python(&P)')

        self.menu_OF = wx.Menu()
        self.menuItem_OF_indent = wx.MenuItem(self.menu_OF, wx.ID_ANY, _(u'字下げ') + '\tCtrl+Down',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF.Append(self.menuItem_OF_indent)
        self.menuItem_OF_unindent = wx.MenuItem(self.menu_OF, wx.ID_ANY, _(u'字上げ') + '\tCtrl+Up',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF.Append(self.menuItem_OF_unindent)
        self.menu_OF.AppendSeparator()
        self.menuItem_OF_comment = wx.MenuItem(self.menu_OF, wx.ID_ANY, _(u'コメントアウト') + '\tCtrl+5',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF.Append(self.menuItem_OF_comment)
        self.menuItem_OF_uncomment = wx.MenuItem(self.menu_OF, wx.ID_ANY, _(u'アンコメント') + '\tCtrl+4',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF.Append(self.menuItem_OF_uncomment)
        self.menu_OF.AppendSeparator()
        self.menuItem_leading_space_to_tab = wx.MenuItem(self.menu_OF, wx.ID_ANY, _(u'左端の空白4個をタブに変換'),
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF.Append(self.menuItem_leading_space_to_tab)
        self.menu_OF.AppendSeparator()
        self.menu_OF_bc = wx.Menu()
        self.menu_OF_bc_C = wx.Menu()
        self.menuItem_OF_calculated = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'calculated',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_C.Append(self.menuItem_OF_calculated)
        self.menuItem_OF_compressible_alphatWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'compressible::alphatWallFunction', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_C.Append(self.menuItem_OF_compressible_alphatWallFunction)
        self.menuItem_OF_compressible_turbulentTemperatureCoupledBaffleMixed = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'compressible::turbulentTemperatureCoupledBaffleMixed', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_C.Append(self.menuItem_OF_compressible_turbulentTemperatureCoupledBaffleMixed)
        self.menuItem_OF_compressible_turbulentTemperatureRadCoupledMixed = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'compressible::turbulentTemperatureRadCoupledMixed', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_C.Append(self.menuItem_OF_compressible_turbulentTemperatureRadCoupledMixed)
        self.menuItem_OF_cyclic = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'cyclic',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_C.Append(self.menuItem_OF_cyclic)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_C, _(u'Cで始まるもの'))
        self.menu_OF_bc_E = wx.Menu()
        self.menuItem_OF_empty = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'empty',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_E.Append(self.menuItem_OF_empty)
        self.menuItem_OF_epsilonWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'epsilonWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_E.Append(self.menuItem_OF_epsilonWallFunction)
        self.menuItem_OF_externalWallHeatFluxTemperature = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'externalWallHeatFluxTemperature', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_E.Append(self.menuItem_OF_externalWallHeatFluxTemperature)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_E, _(u'Eで始まるもの'))
        self.menu_OF_bc_F = wx.Menu()
        self.menuItem_OF_fixedFluxPressure = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'fixedFluxPressure',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_fixedFluxPressure)
        self.menuItem_OF_fixedGradient = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'fixedGradient',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_fixedGradient)
        self.menuItem_OF_fixedValue = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'fixedValue',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_fixedValue)
        self.menuItem_OF_flowRateInletVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'flowRateInletVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_flowRateInletVelocity)
        self.menuItem_OF_freestreamPressure = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'freestreamPressure',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_freestreamPressure)
        self.menuItem_OF_freestreamVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'freestreamVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_F.Append(self.menuItem_OF_freestreamVelocity)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_F, _(u'Fで始まるもの'))
        self.menu_OF_bc_G = wx.Menu()
        self.menuItem_OF_greyDiffusiveRadiationViewFactor = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'greyDiffusiveRadiationViewFactor', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_G.Append(self.menuItem_OF_greyDiffusiveRadiationViewFactor)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_G, _(u'Gで始まるもの'))
        self.menu_OF_bc_I = wx.Menu()
        self.menuItem_OF_inletOutlet = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'inletOutlet',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_I.Append(self.menuItem_OF_inletOutlet)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_I, _(u'Iで始まるもの'))
        self.menu_OF_bc_K = wx.Menu()
        self.menuItem_OF_kqRWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'kqRWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_K.Append(self.menuItem_OF_kqRWallFunction)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_K, _(u'Kで始まるもの'))
        self.menu_OF_bc_M = wx.Menu()
        self.menuItem_OF_movingWallVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'movingWallVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_M.Append(self.menuItem_OF_movingWallVelocity)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_M, _(u'Mで始まるもの'))
        self.menu_OF_bc_N = wx.Menu()
        self.menuItem_OF_nutkRoughWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'nutkRoughWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_N.Append(self.menuItem_OF_nutkRoughWallFunction)
        self.menuItem_OF_nutkWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'nutkWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_N.Append(self.menuItem_OF_nutkWallFunction)
        self.menuItem_OF_nutUWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'nutUWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_N.Append(self.menuItem_OF_nutUWallFunction)
        self.menuItem_OF_noSlip = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'noSlip',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_N.Append(self.menuItem_OF_noSlip)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_N, _(u'Nで始まるもの'))
        self.menu_OF_bc_O = wx.Menu()
        self.menuItem_OF_omegaWallFunction = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'omegaWallFunction',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_O.Append(self.menuItem_OF_omegaWallFunction)
        self.menuItem_OF_outletInlet = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'outletInlet',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_O.Append(self.menuItem_OF_outletInlet)
        self.menuItem_OF_outletPhaseMeanVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'outletPhaseMeanVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_O.Append(self.menuItem_OF_outletPhaseMeanVelocity)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_O, _(u'Oで始まるもの'))
        self.menu_OF_bc_P = wx.Menu()
        self.menuItem_OF_pressureInletOutletVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'pressureInletOutletVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_P.Append(self.menuItem_OF_pressureInletOutletVelocity)
        self.menuItem_OF_prghPressure = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'prghPressure',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_P.Append(self.menuItem_OF_prghPressure)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_P, _(u'Pで始まるもの'))
        self.menu_OF_bc_R = wx.Menu()
        self.menuItem_OF_rotatingWallVelocity = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'rotatingWallVelocity',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_R.Append(self.menuItem_OF_rotatingWallVelocity)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_R, _(u'Rで始まるもの'))
        self.menu_OF_bc_S = wx.Menu()
        self.menuItem_OF_slip = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'slip',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_S.Append(self.menuItem_OF_slip)
        self.menuItem_OF_surfaceNormalFixedValue = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'surfaceNormalFixedValue',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_S.Append(self.menuItem_OF_surfaceNormalFixedValue)
        self.menuItem_OF_symmetry = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'symmetry',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_S.Append(self.menuItem_OF_symmetry)
        self.menuItem_OF_symmetryPlane = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'symmetryPlane',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_S.Append(self.menuItem_OF_symmetryPlane)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_S, _(u'Sで始まるもの'))
        self.menu_OF_bc_T = wx.Menu()
        self.menuItem_OF_totalPressure = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'totalPressure',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_T.Append(self.menuItem_OF_totalPressure)
        self.menuItem_OF_turbulentIntensityKineticEnergyInlet = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'turbulentIntensityKineticEnergyInlet', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_T.Append(self.menuItem_OF_turbulentIntensityKineticEnergyInlet)
        self.menuItem_OF_turbulentMixingLengthDissipationRateInlet = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'turbulentMixingLengthDissipationRateInlet', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_T.Append(self.menuItem_OF_turbulentMixingLengthDissipationRateInlet)
        self.menuItem_OF_turbulentMixingLengthFrequencyInlet = wx.MenuItem(self.menu_OF, wx.ID_ANY,
            u'turbulentMixingLengthFrequencyInlet', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_T.Append(self.menuItem_OF_turbulentMixingLengthFrequencyInlet)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_T, _(u'Tで始まるもの'))
        self.menu_OF_bc_V = wx.Menu()
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_V, _(u'Vで始まるもの'))
        self.menu_OF_bc_Z = wx.Menu()
        self.menuItem_OF_variableHeightFlowRate = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'variableHeightFlowRate',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_V.Append(self.menuItem_OF_variableHeightFlowRate)
        self.menu_OF_bc.AppendSubMenu(self.menu_OF_bc_Z, _(u'Zで始まるもの'))
        self.menuItem_OF_zeroGradient = wx.MenuItem(self.menu_OF, wx.ID_ANY, u'zeroGradient',
            wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_OF_bc_Z.Append(self.menuItem_OF_zeroGradient)
        self.menu_OF.AppendSubMenu(self.menu_OF_bc, _(u'境界条件の雛形'))
        self.menubar.Append(self.menu_OF, 'OpenFOAM(&O)')

        self.menu_help = wx.Menu()
        self.menuItem_update = wx.MenuItem(self.menu_help, wx.ID_ANY, _(u'アップデート'), wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_help.Append(self.menuItem_update)
        self.menuItem_movie = wx.MenuItem(self.menu_help, wx.ID_ANY, _(u'使い方の動画'), wx.EmptyString, wx.ITEM_NORMAL)
        self.menu_help.Append(self.menuItem_movie)
        self.menubar.Append(self.menu_help, _(u'ヘルプ') + '(&H)')

        self.SetMenuBar(self.menubar)

        # Connect Events
        self.Bind(wx.EVT_CLOSE, self.FrameMainOnClose)
        self.filePicker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFileChanged)
        self.button_left_shift.Bind(wx.EVT_BUTTON, self.menuItem_left_shiftOnMenuSelection)
        self.button_right_shift.Bind(wx.EVT_BUTTON, self.menuItem_right_shiftOnMenuSelection)
        self.button_plus.Bind(wx.EVT_BUTTON, self.button_plusOnButtonClick)
        self.button_minus.Bind(wx.EVT_BUTTON, self.button_minusOnButtonClick)
        self.button_multiply.Bind(wx.EVT_BUTTON, self.button_multiplyOnButtonClick)
        self.button_divide.Bind(wx.EVT_BUTTON, self.button_divideOnButtonClick)
        self.button_power.Bind(wx.EVT_BUTTON, self.button_powerOnButtonClick)
        self.button_reciprocal.Bind(wx.EVT_BUTTON, self.menuItem_reciprocalOnMenuSelection)
        self.button_exchange_hands.Bind(wx.EVT_BUTTON, self.menuItem_exchange_handsOnMenuSelection)
        self.Bind(wx.EVT_MENU, self.menuItem_openOnMenuSelection, id = self.menuItem_open.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_saveOnMenuSelection, id = self.menuItem_save.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_save_asOnMenuSelection, id = self.menuItem_save_as.GetId())
        self.Bind(wx.EVT_MENU, self.FrameMainOnClose, id = self.menuItem_quit.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_undoOnMenuSelection, id = self.menuItem_undo.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_redoOnMenuSelection, id = self.menuItem_redo.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_cutOnMenuSelection, id = self.menuItem_cut.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_copyOnMenuSelection, id = self.menuItem_copy.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_pasteOnMenuSelection, id = self.menuItem_paste.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_select_allOnMenuSelection, id = self.menuItem_select_all.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_findOnMenuSelection, id = self.menuItem_find.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_find_nextOnMenuSelection, id = self.menuItem_find_next.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_find_prevOnMenuSelection, id = self.menuItem_find_prev.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_replaceOnMenuSelection, id = self.menuItem_replace.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_rep_findOnMenuSelection, id = self.menuItem_rep_find.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_rep_allOnMenuSelection, id = self.menuItem_rep_all.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_append_findOnMenuSelection, id = self.menuItem_append_find.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_append_replaceOnMenuSelection, id = self.menuItem_append_replace.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_left_shiftOnMenuSelection, id = self.menuItem_left_shift.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_right_shiftOnMenuSelection, id = self.menuItem_right_shift.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_delete_trailing_spacesOnMenuSelection, id = self.menuItem_delete_trailing_spaces.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_set_upperOnMenuSelection, id = self.menuItem_set_upper.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_set_lowerOnMenuSelection, id = self.menuItem_set_lower.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_capitalizeOnMenuSelection, id = self.menuItem_capitalize.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_set_titleOnMenuSelection, id = self.menuItem_set_title.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_swap_caseOnMenuSelection, id = self.menuItem_swap_case.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_zenkakuOnMenuSelection, id = self.menuItem_zenkaku.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_hankakuOnMenuSelection, id = self.menuItem_hankaku.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_line_numberedOnMenuSelection, id = self.menu_line_numbered.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_bracketOnMenuSelection, id = self.menuItem_bracket.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_completionOnMenuSelection, id = self.menuItem_completion.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_completion_backwardOnMenuSelection, id = self.menuItem_completion_backward.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_datetimeOnMenuSelection, id = self.menuItem_datetime.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_colorize_textsOnMenuSelection, id = self.menuItem_colorize_texts.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_reset_stylesOnMenuSelection, id = self.menuItem_reset_styles.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_insert_returnOnMenuSelection, id = self.menuItem_insert_return.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_evaluateOnMenuSelection, id = self.menuItem_evaluate.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_negativeOnMenuSelection, id = self.menuItem_negative.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_reciprocalOnMenuSelection, id = self.menuItem_reciprocal.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_exchange_handsOnMenuSelection, id = self.menuItem_exchange_hands.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_declare_integerOnMenuSelection, id = self.menuItem_declare_integer.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_command_shortcutOnMenuSelection, id = self.menuItem_command_shortcut.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_reset_maximaOnMenuSelection, id = self.menuItem_reset_maxima.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_python_headerOnMenuSelection, id = self.menuItem_python_header.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_python_indentOnMenuSelection, id = self.menuItem_python_indent.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_python_unindentOnMenuSelection, id = self.menuItem_python_unindent.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_python_commentOnMenuSelection, id = self.menuItem_python_comment.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_python_uncommentOnMenuSelection, id = self.menuItem_python_uncomment.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_leading_tab_to_spaceOnMenuSelection, id = self.menuItem_leading_tab_to_space.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_indentOnMenuSelection, id = self.menuItem_OF_indent.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_unindentOnMenuSelection, id = self.menuItem_OF_unindent.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_commentOnMenuSelection, id = self.menuItem_OF_comment.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_uncommentOnMenuSelection, id = self.menuItem_OF_uncomment.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_leading_space_to_tabOnMenuSelection, id = self.menuItem_leading_space_to_tab.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_calculatedOnMenuSelection, id = self.menuItem_OF_calculated.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_compressible_alphatWallFunctionOnMenuSelection,
            id = self.menuItem_OF_compressible_alphatWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_compressible_turbulentTemperatureCoupledBaffleMixedOnMenuSelection,
            id = self.menuItem_OF_compressible_turbulentTemperatureCoupledBaffleMixed.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_compressible_turbulentTemperatureRadCoupledMixedOnMenuSelection,
            id = self.menuItem_OF_compressible_turbulentTemperatureRadCoupledMixed.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_cyclicOnMenuSelection, id = self.menuItem_OF_cyclic.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_emptyOnMenuSelection, id = self.menuItem_OF_empty.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_epsilonWallFunctionOnMenuSelection, id = self.menuItem_OF_epsilonWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_externalWallHeatFluxTemperatureOnMenuSelection,
            id = self.menuItem_OF_externalWallHeatFluxTemperature.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_fixedFluxPressureOnMenuSelection, id = self.menuItem_OF_fixedFluxPressure.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_fixedGradientyOnMenuSelection, id = self.menuItem_OF_fixedGradient.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_fixedValueOnMenuSelection, id = self.menuItem_OF_fixedValue.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_flowRateInletVelocityOnMenuSelection, id = self.menuItem_OF_flowRateInletVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_freestreamPressureOnMenuSelection, id = self.menuItem_OF_freestreamPressure.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_freestreamVelocityOnMenuSelection, id = self.menuItem_OF_freestreamVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_greyDiffusiveRadiationViewFactorOnMenuSelection,
            id = self.menuItem_OF_greyDiffusiveRadiationViewFactor.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_inletOutletOnMenuSelection, id = self.menuItem_OF_inletOutlet.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_kqRWallFunctionOnMenuSelection, id = self.menuItem_OF_kqRWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_movingWallVelocityOnMenuSelection, id = self.menuItem_OF_movingWallVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_nutkRoughWallFunctionOnMenuSelection, id = self.menuItem_OF_nutkRoughWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_nutkWallFunctionOnMenuSelection, id = self.menuItem_OF_nutkWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_nutUWallFunctionOnMenuSelection, id = self.menuItem_OF_nutUWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_noSlipOnMenuSelection, id = self.menuItem_OF_noSlip.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_omegaWallFunctionOnMenuSelection, id = self.menuItem_OF_omegaWallFunction.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_outletInletOnMenuSelection, id = self.menuItem_OF_outletInlet.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_outletPhaseMeanVelocityOnMenuSelection, id = self.menuItem_OF_outletPhaseMeanVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_pressureInletOutletVelocityOnMenuSelection,
            id = self.menuItem_OF_pressureInletOutletVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_prghPressureOnMenuSelection, id = self.menuItem_OF_prghPressure.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_rotatingWallVelocityOnMenuSelection, id = self.menuItem_OF_rotatingWallVelocity.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_slipOnMenuSelection, id = self.menuItem_OF_slip.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_surfaceNormalFixedValueOnMenuSelection, id = self.menuItem_OF_surfaceNormalFixedValue.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_symmetryOnMenuSelection, id = self.menuItem_OF_symmetry.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_symmetryPlaneOnMenuSelection, id = self.menuItem_OF_symmetryPlane.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_totalPressureOnMenuSelection, id = self.menuItem_OF_totalPressure.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_turbulentIntensityKineticEnergyInletOnMenuSelection,
            id = self.menuItem_OF_turbulentIntensityKineticEnergyInlet.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_turbulentMixingLengthDissipationRateInletOnMenuSelection,
            id = self.menuItem_OF_turbulentMixingLengthDissipationRateInlet.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_turbulentMixingLengthFrequencyInletOnMenuSelection,
            id = self.menuItem_OF_turbulentMixingLengthFrequencyInlet.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_variableHeightFlowRateOnMenuSelection, id = self.menuItem_OF_variableHeightFlowRate.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_OF_zeroGradientOnMenuSelection, id = self.menuItem_OF_zeroGradient.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_updateOnMenuSelection, id = self.menuItem_update.GetId())
        self.Bind(wx.EVT_MENU, self.menuItem_movieOnMenuSelection, id = self.menuItem_movie.GetId())

        self.backup_path = correct_file_name_in_unicode(os.path.join(os.path.dirname(
            os.path.realpath(decode_if_necessary(__file__))), u'backup_texteditwx.txt')) # unicode
        if os.path.isfile(self.backup_path):
            with codecs.open(self.backup_path, 'r', encoding = 'UTF-8') as f:
                backup = ast.literal_eval('{' + f.read() + '}')
        else:
            backup = {}
        backup.setdefault('find_data', None)
        self.cwd = correct_file_name_in_unicode(decode_if_necessary(os.getcwd())) # unicode
        self.filePicker.SetInitialDirectory(self.cwd)

        self.dialog_find = DialogFind(self.textCtrl_edit, font, backup['find_data'])
        self.textCtrl_edit.SetFocus()
        if sys.platform != 'darwin':
            locale.setlocale(locale.LC_TIME, 'C') # required for a format '%p' (AM/PM) in strftime

    def __del__(self):
        pass

    def splitterOnIdle(self, event):
        self.splitter.SetSashPosition(self.sash_pos)
        self.splitter.Unbind(wx.EVT_IDLE)

    def save_backup(self):
        if os.path.isfile(self.backup_path):
            with open(self.backup_path, 'r') as f:
                backup = ast.literal_eval('{' + f.read() + '}')
        else:
            backup = {}
        backup['find_data'] = self.dialog_find.grid_find.table.DataString()
        with codecs.open(self.backup_path, 'w', encoding = 'UTF-8') as f:
            for k, v in backup.items():
                f.write(u"'{}': {},\n".format(k, v))

    def FrameMainOnClose(self, event):
        self.save_backup()
        if self.textCtrl_edit.IsModified():
            with wx.MessageDialog(self,
                _(u'書類を保存しますか？') if self.filePicker.GetPath() == ''
                    else _(u'書類を ') + self.filePicker.GetPath() + _(u' に保存しますか？'),
                _(u'保存'), style = wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION) as md:
                r = md.ShowModal()
            if r == wx.ID_YES:
                self.menuItem_saveOnMenuSelection(None)
            elif r == wx.ID_CANCEL:
                return
        quit()

    def OnFileChanged(self, event):
        p = correct_file_name_in_unicode(event.GetEventObject().GetPath()) # unicode
        event.GetEventObject().SetPath(p)
        if os.path.isfile(p) and event.GetEventObject().GetWindowStyle() & wx.FLP_FILE_MUST_EXIST:
            self.load_doc(p)

    def load_doc(self, path):
        path = correct_file_name_in_unicode(path) # unicode
        char_code, return_code = self.textCtrl_edit.LoadFile(path)
        self.choice_char_code.SetSelection(self.char_codes.index(char_code))
        self.choice_return_code.SetSelection(self.return_codes.index(return_code))
        self.filePicker.SetPath(path)
        self.cwd = os.path.dirname(path)
        self.filePicker.SetInitialDirectory(self.cwd)

    def button_plusOnButtonClick(self, event):
        self.textCtrl_edit.plus(self.textCtrl_affect.GetValue())

    def button_minusOnButtonClick(self, event):
        self.textCtrl_edit.plus('-(' + self.textCtrl_affect.GetValue() + ')')

    def button_multiplyOnButtonClick(self, event):
        self.textCtrl_edit.multiply(self.textCtrl_affect.GetValue())

    def button_divideOnButtonClick(self, event):
        self.textCtrl_edit.multiply('1/(' + self.textCtrl_affect.GetValue() + ')')

    def button_powerOnButtonClick(self, event):
        self.textCtrl_edit.power(self.textCtrl_affect.GetValue())

    def menuItem_openOnMenuSelection(self, event):
        with wx.FileDialog(self, _(u'ファイルを開く'), style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            fd.SetDirectory(self.cwd)
            if fd.ShowModal() == wx.ID_CANCEL:
                return
            self.load_doc(fd.GetPath())

    def save_commands(self, path):
        self.save_backup()
        path = correct_file_name_in_unicode(path) # unicode
        with codecs.open(path, 'wb', encoding = self.char_codes[self.choice_char_code.GetSelection()]) as f:
            v = self.textCtrl_edit.GetValue()
            return_code = self.return_codes[self.choice_return_code.GetSelection()]
            if return_code == 'CR+LF':
                v = v.replace(u'\n', u'\r\n')
            elif return_code == 'CR':
                v = v.replace(u'\n', u'\r')
            f.write(v)
        # self.textCtrl_edit.SaveFile(path) used in windows includes CR in return codes
        self.filePicker.SetPath(path)
        self.textCtrl_edit.SetModified(False)

    def menuItem_saveOnMenuSelection(self, event):
        if self.filePicker.GetPath() == '':
            self.menuItem_save_asOnMenuSelection(event)
        else:
            self.save_commands(self.filePicker.GetPath())

    def menuItem_save_asOnMenuSelection(self, event):
        with wx.FileDialog(self, _(u'ファイルを保存'), wildcard = u'All files (*)|*',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fd:
            fd.SetDirectory(self.cwd)
            fd.SetFilename(u'Untitled.txt')
            if fd.ShowModal() == wx.ID_CANCEL:
                return
            self.save_commands(fd.GetPath())

    def menuItem_undoOnMenuSelection(self, event):
        try:
            self.FindFocus().Undo()
        except:
            pass

    def menuItem_redoOnMenuSelection(self, event):
        try:
            self.FindFocus().Redo()
        except:
            pass

    def menuItem_cutOnMenuSelection(self, event):
        try:
            self.FindFocus().Cut()
        except:
            pass

    def menuItem_copyOnMenuSelection(self, event):
        try:
            self.FindFocus().Copy()
        except:
            pass

    def menuItem_pasteOnMenuSelection(self, event):
        try:
            self.FindFocus().Paste()
        except:
            pass

    def menuItem_select_allOnMenuSelection(self, event):
        try:
            self.FindFocus().SelectAll()
        except:
            pass

    def menuItem_findOnMenuSelection(self, event):
        self.dialog_find.Show()
        self.dialog_find.Raise()
        self.dialog_find.grid_find.SetGridCursor(0, self.dialog_find.grid_find.table.COL_FIND)

    def menuItem_find_nextOnMenuSelection(self, event):
        self.dialog_find.button_find_nextOnButtonClick(event)

    def menuItem_find_prevOnMenuSelection(self, event):
        self.dialog_find.button_find_prevOnButtonClick(event)

    def menuItem_replaceOnMenuSelection(self, event):
        self.dialog_find.button_replaceOnButtonClick(event)

    def menuItem_rep_findOnMenuSelection(self, event):
        self.dialog_find.button_rep_findOnButtonClick(event)

    def menuItem_rep_allOnMenuSelection(self, event):
        self.dialog_find.button_rep_allOnButtonClick(event)

    def menuItem_append_findOnMenuSelection(self, event):
        s = self.textCtrl_edit.GetStringSelection()
        if s != '':
            self.dialog_find.insert_find(0, s)

    def menuItem_append_replaceOnMenuSelection(self, event):
        s = self.textCtrl_edit.GetStringSelection()
        if s != '':
            self.dialog_find.insert_replace(0, s)

    def menuItem_left_shiftOnMenuSelection(self, event):
        self.textCtrl_edit.unindent()

    def menuItem_right_shiftOnMenuSelection(self, event):
        self.textCtrl_edit.indent(self.textCtrl_shift.GetValue())

    def menuItem_delete_trailing_spacesOnMenuSelection(self, event):
        self.textCtrl_edit.delete_trailing_spaces()

    def menuItem_set_upperOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('upper')

    def menuItem_set_lowerOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('lower')

    def menuItem_capitalizeOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('capitalize')

    def menuItem_set_titleOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('title')

    def menuItem_swap_caseOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('swapcase')

    def menuItem_zenkakuOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('zenkaku')

    def menuItem_hankakuOnMenuSelection(self, event):
        self.textCtrl_edit.transform_chars('hankaku')

    def menuItem_line_numberedOnMenuSelection(self, event):
        self.textCtrl_edit.line_numbered(head = True, prefix = '', suffix = ': ')

    def menuItem_bracketOnMenuSelection(self, event):
        self.textCtrl_edit.select_bracket(((u'(', u')'), (u'{', u'}'), (u'[', u']')))

    def menuItem_completionOnMenuSelection(self, event):
        if self.textCtrl_edit.HasFocus():
            self.textCtrl_edit.completion()
        else:
            event.Skip()

    def menuItem_completion_backwardOnMenuSelection(self, event):
        if self.textCtrl_edit.HasFocus() and self.textCtrl_edit.completion_from is not None:
            self.textCtrl_edit.completion_backward()
        else:
            event.Skip()

    def menuItem_datetimeOnMenuSelection(self, event):
        if sys.platform == 'win32':
            self.textCtrl_edit.WriteText(datetime.datetime.now().strftime(u'%Y/%m/%d %I:%M:%S %p').
                replace('/0', '/').replace(' 0', ' '))
        else:
            self.textCtrl_edit.WriteText(datetime.datetime.now().strftime(u'%Y/%-m/%-d %-I:%M:%S %p'))

    def menuItem_colorize_textsOnMenuSelection(self, event):
        self.textCtrl_edit.colorize_texts(parentheses = ((u'(', u')'), (u'{', u'}'), (u'[', u']')),
            literals = ((u'"', u'"'), (u"'", u"'")), literal_escape = u'\\')

    def menuItem_reset_stylesOnMenuSelection(self, event):
        self.textCtrl_edit.reset_styles()

    def menuItem_insert_returnOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(re.sub('^(\\-|\\+)\\n', '\\1',
            self.textCtrl_edit.re_sub_in_top_level('(,|\\+|\\-|=)\\s*', '\\1\n',
                parentheses = ((u'(', u')'), (u'{', u'}'), (u'[', u']')),
                literals = ((u'"', u'"'), (u"'", u"'")), literal_escape = u'\\')))

    def menuItem_evaluateOnMenuSelection(self, event):
        self.textCtrl_edit.send_commands_to_maxima()

    def menuItem_negativeOnMenuSelection(self, event):
        self.textCtrl_edit.set_negative()

    def menuItem_reciprocalOnMenuSelection(self, event):
        self.textCtrl_edit.set_reciprocal()

    def menuItem_exchange_handsOnMenuSelection(self, event):
        self.textCtrl_edit.exchange_hands()

    def menuItem_declare_integerOnMenuSelection(self, event):
        self.textCtrl_edit.declare_integer()

    def menuItem_command_shortcutOnMenuSelection(self, event):
        if self.textCtrl_edit.shortcut:
            self.textCtrl_edit.shortcut = False
            self.textCtrl_help.SetValue(self.textCtrl_edit.str_wo_shortcut)
            self.menuItem_command_shortcut.SetItemLabel(self.textCtrl_edit.str_menu_with_shortcut + '\tEsc')
        else:
            self.textCtrl_edit.shortcut = True
            self.textCtrl_help.SetValue(self.textCtrl_edit.str_with_shortcut)
            self.menuItem_command_shortcut.SetItemLabel(self.textCtrl_edit.str_menu_wo_shortcut + '\tEsc')

    def menuItem_reset_maximaOnMenuSelection(self, event):
        self.textCtrl_edit.reset_maxima()

    def menuItem_python_headerOnMenuSelection(self, event):
        self.textCtrl_edit.SetInsertionPoint(0)
        self.textCtrl_edit.WriteText("#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\nif __name__ == '__main__':")

    def menuItem_python_indentOnMenuSelection(self, event):
        self.textCtrl_edit.indent(u'    ')

    def menuItem_python_unindentOnMenuSelection(self, event):
        self.textCtrl_edit.unindent(u'    ')

    def menuItem_python_commentOnMenuSelection(self, event):
        self.textCtrl_edit.indent(u'#')

    def menuItem_python_uncommentOnMenuSelection(self, event):
        self.textCtrl_edit.unindent(u'#')

    def menuItem_leading_tab_to_spaceOnMenuSelection(self, event):
        self.textCtrl_edit.change_leading_tab_to_space()

    def menuItem_OF_indentOnMenuSelection(self, event):
        self.textCtrl_edit.indent(u'\t')

    def menuItem_OF_unindentOnMenuSelection(self, event):
        self.textCtrl_edit.unindent(u'\t')

    def menuItem_OF_commentOnMenuSelection(self, event):
        self.textCtrl_edit.indent(u'//')

    def menuItem_OF_uncommentOnMenuSelection(self, event):
        self.textCtrl_edit.unindent(u'//')

    def menuItem_leading_space_to_tabOnMenuSelection(self, event):
        self.textCtrl_edit.change_leading_space_to_tab()

    def menuItem_OF_calculatedOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('calculated',
            u'他の変数から計算可能であることを表す．\n壁面でない境界におけるnutの境界条件としてよく使われる．',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/basic/calculated'),
            indent = '\t'))

    def menuItem_OF_compressible_alphatWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('compressible::alphatWallFunction',
            u'alphat = mut/Prt（mut: 乱流粘性係数）から壁面乱流温度拡散率を計算する．',
            u'Prt 0.85; // 乱流プラントル数\nvalue $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/' +
            'wallFunctions/alphatWallFunctions/alphatWallFunction'),
            indent = '\t'))

    def menuItem_OF_compressible_turbulentTemperatureCoupledBaffleMixedOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('compressible::turbulentTemperatureCoupledBaffleMixed',
            u'境界の両側で熱流束が一致するように温度Tを決める．\n' +
            u'-kappa*(T_boundary - T)/delta =\n  -kappa_nbr*(T_nbr - T_boundary)/delta_nbr',
            u'Tnbr T; // 隣接する場の名前．普通はT．\n' +
            u'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/' +
            'turbulentTemperatureCoupledBaffleMixed'),
            indent = '\t'))

    def menuItem_OF_compressible_turbulentTemperatureRadCoupledMixedOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('compressible::turbulentTemperatureRadCoupledMixed',
            u'熱ふく射も含めて，境界の両側で熱流束が一致するように温度Tを決める．\n' +
            u'-kappa*(T_boundary - T)/delta + qr =\n  -kappa_nbr*(T_nbr - T_boundary)/delta_nbr - qr_nbr +\n' +
            u'  (delta*rho*Cp + delta_nbr*rho_nbr*Cp_nbr)*\n  (T_boundary - T_old)/dt',
            u'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
            u'thermalInertia false; // 境界付近の温度の時間的変化を考慮に入れるか\n' +
            u'// falseだとdt = ∞（定常）またはCp = 0に相当する．',
            openfoam_src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/' +
            'turbulentTemperatureRadCoupledMixed'),
            indent = '\t'))

    def menuItem_OF_cyclicOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('cyclic',
            u'周期境界\nconstant/polyMesh/boundaryで\nneighbourPatchを指定しないといけない．\n' +
            u'http://penguinitis.g1.xrea.com/study/OpenFOAM/cyclic/cyclic.html',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/constraint/cyclic'),
            indent = '\t'))

    def menuItem_OF_emptyOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('empty',
            u'1次元または2次元解析の時に，計算しない方向に垂直な面であることを示す．',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/constraint/empty'),
            indent = '\t'))

    def menuItem_OF_epsilonWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('epsilonWallFunction',
            u'epsilonの壁面境界条件',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/' +
            'wallFunctions/epsilonWallFunctions/epsilonWallFunction'),
            indent = '\t'))

    def menuItem_OF_externalWallHeatFluxTemperatureOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('externalWallHeatFluxTemperature',
            u'壁面からの熱伝達',
            u'mode flux;\n// flux→熱流束q | power→熱量Q | coefficient→熱伝達率h = q/(T - Ta)\n' +
            u'q uniform 100; // fluxの時に使用\n// Q 100; // powerの時に使用\n' +
            u'// h 10; // coefficientの時に使用\n// Ta 500; // 外部温度, coefficientの時に使用\n' +
            u'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/externalWallHeatFluxTemperature'),
            indent = '\t'))

    def menuItem_OF_fixedFluxPressureOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('fixedFluxPressure',
            u'速度境界条件を満足するようにp_rghを設定',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure'),
            indent = '\t'))

    def menuItem_OF_fixedGradientyOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('fixedGradient',
            u'こう配をgradientで決めた値にする．',
            u'gradient uniform 1.2; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/basic/fixedGradient'),
            indent = '\t'))

    def menuItem_OF_fixedValueOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('fixedValue',
            u'valueで決めた値に固定',
            u'value uniform 1.2; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/basic/fixedValue'),
            indent = '\t'))

    def menuItem_OF_flowRateInletVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('flowRateInletVelocity',
            '体積流量または質量流量で流入速度を設定し，\n境界に平行な方向の速度は0にする．',
            'volumetricFlowRate 0.1; // 体積流量, massFlowRateとは併用できない．\n' +
            '// massFlowRate 0.1; // 質量流量, volumetricFlowRateとは併用できない．\n' +
            '// rhoInlet 1; // 密度, massFlowRateの場合に必要\n' +
            'extrapolateProfile false;\n// true→内側と相似な速度分布で流入 | false→一様流入\n' +
            'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/flowRateInletVelocity'),
            indent = '\t'))

    def menuItem_OF_freestreamPressureOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('freestreamPressure',
            'pに対する自由流入出条件．freestreamVelocityと併用する．\n' +
            '境界垂直方向と流速方向が完全に同じ向きで\n' +
            '流入する時はzeroGradienに規定し，\n' +
            '流出する時はfreestreamValueにする．\n' +
            '完全に同じでないときは，これらの間を連続的に変化させたものを使う．',
            'freestreamValue uniform 1.0e+05;',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/freestreamPressure'),
            indent = '\t'))

    def menuItem_OF_freestreamVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('freestreamVelocity',
            'Uに対する自由流入出条件．freestreamPressureと併用する．\n' +
            '境界垂直方向と流速方向が完全に同じ向きで\n' +
            '流入する時はfreestreamValueに規定し，\n' +
            '流出する時はzeroGradientにする．\n' +
            '完全に同じでないときは，これらの間を連続的に変化させたものを使う．',
            'freestreamValue uniform (100 0 0);',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/freestreamVelocity'),
            indent = '\t'))

    def menuItem_OF_greyDiffusiveRadiationViewFactorOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('greyDiffusiveRadiationViewFactor',
            u'形態係数を利用してふく射による熱流速を決定する．\n' +
            u'壁面は灰色体（ふく射率にはconstant/radiationPropertiesの中にある\nemissivityを利用？）とする．',
            u'qro uniform 0; // 外部から入るふく射による熱流束',
            openfoam_src + 'thermophysicalModels/radiation/derivedFvPatchFields/greyDiffusiveViewFactor'),
            indent = '\t'))

    def menuItem_OF_inletOutletOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('inletOutlet',
            u'計算領域内に流入する場合→inletValueで決めた値に設定\n計算領域外に流出する場合→zeroGradient',
            u'inletValue uniform 0; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/inletOutlet'),
            indent = '\t'))

    def menuItem_OF_kqRWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('kqRWallFunction',
            u'高レイノルズ数型乱流モデルにおけるk, q, Rの壁面境界条件\nzeroGrdientのラッパー',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/' +
            'wallFunctions/kqRWallFunctions/kqRWallFunction'),
            indent = '\t'))

    def menuItem_OF_movingWallVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('movingWallVelocity',
            u'Uに使用\n移動壁面の場合のnoSlip条件，壁面が移動しなければnoSlipと同じ',
            u'value uniform (0 0 0); // 初期速度',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/movingWallVelocity'),
            indent = '\t'))

    def menuItem_OF_nutkRoughWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('nutkRoughWallFunction',
            u'荒い壁面に対するnutの境界条件\n' +
            u'nutkWallFunctionで使っている式に，\n壁面荒さ（凹凸の高さ）Ks，定数Csによる補正を加えている．\n' +
            u'https://dergipark.org.tr/en/download/article-file/202910',
            u'Ks uniform 0; // 単位はm，0だと滑面\nCs uniform 0.5; // 0.5 - 1.0，大きいほど荒さの影響大\n' +
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/' +
            'nutWallFunctions/nutkRoughWallFunction'),
            indent = '\t'))

    def menuItem_OF_nutkWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('nutkWallFunction',
            u'壁面に対するnutの境界条件，標準的\n' +
            u'yPlus = C_mu^0.25*sqrt(k)*y/nuから格子中心のyPlusを求め，\n対数則領域内に格子中心があるかどうかを判断する．\n' +
            u'ある場合，対数速度分布から得られる壁面せん断応力\ntau_w = mu*kappa*yPlus/log(E*yPlus)*(u/y)\n' +
            u'になるように乱流粘性係数を設定する．\nhttps://www.slideshare.net/fumiyanozaki96/openfoam-36426892',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/' +
            'nutWallFunctions/nutkWallFunction'),
            indent = '\t'))

    def menuItem_OF_nutUWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('nutUWallFunction',
            u'壁面に対するnutの境界条件\n' +
            u'格子中心での速度u，壁からの距離y，対数速度分布から得られる関係\n' +
            u'yPlus*log(E*yPlus) = kappa*u*y/nuから格子中心のyPlusを求め，\n対数則領域内に格子中心があるかどうかを判断する．\n' +
            u'ある場合，対数速度分布から得られる壁面せん断応力\ntau_w = mu*kappa*yPlus/log(E*yPlus)*(u/y)\n' +
            u'になるように乱流粘性係数を設定する．\nhttps://www.slideshare.net/fumiyanozaki96/openfoam-36426892',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/' +
            'nutWallFunctions/nutUWallFunction'),
            indent = '\t'))

    def menuItem_OF_noSlipOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('noSlip',
            u'U = (0 0 0)に規定',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/noSlip'),
            indent = '\t'))

    def menuItem_OF_omegaWallFunctionOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('omegaWallFunction',
            u'壁面に対するomegaの境界条件',
            u'value $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/' +
            'omegaWallFunctions/omegaWallFunction'),
            indent = '\t'))

    def menuItem_OF_outletInletOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('outletInlet',
            u'計算領域外に流出する場合→outletValueで決めた値に設定\n計算領域内に流入する場合→zeroGradient',
            u'outletValue uniform 0; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/outletInlet'),
            indent = '\t'))

    def menuItem_OF_outletPhaseMeanVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('outletPhaseMeanVelocity',
            u'alphaで示す相の平均流出流速がUmeanになるように規定する．\n' +
            u'典型的な例としては，曳航水槽による船周りの流れシミュレーションで，\n入口と出口の水位が同じになるようにする場合に使う．',
            u'alpha alpha.water;\nUmean 1.2;',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/outletPhaseMeanVelocity'),
            indent = '\t'))

    def menuItem_OF_pressureInletOutletVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('pressureInletOutletVelocity',
            u'Uに使用\n計算領域内に流入する場合→垂直方向成分はこう配が0，\n接線方向成分はtangentialVelocityのうちの接線方向成分のみ\n' +
            u'計算領域外に流出する場合→全成分でこう配が0',
            u'tangentialVelocity uniform (0 0 0);\nvalue $internalField; // 実際には使わないけど必要',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/pressureInletOutletVelocity'),
            indent = '\t'))

    def menuItem_OF_prghPressureOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('prghPressure',
            u'p_rghに使用\n設定したいpの値からp_rghを計算して設定する．\n対応するパッチのpにはcalculatedを使う．',
            u'rho rhok; // 計算で用いる密度の変数名，rhoまたはrhok\n// pの次元がPaの場合→rho，m^2/s^2にの場合→rhok\n' +
            u'p uniform 0; // 設定したいpの値',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/prghPressure'),
            indent = '\t'))

    def menuItem_OF_rotatingWallVelocityOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('rotatingWallVelocity',
            u'速度を回転物体表面の速度と一致させる',
            u'origin (0 0 0); // 回転中心\n' +
            u'axis (0 0 1); // 回転軸\n' +
            u'omega (0 0 1); // 右ねじが進む向きを正とした角速度 [rps]',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/rotatingWallVelocity'),
            indent = '\t'))

    def menuItem_OF_slipOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('slip',
            u'非粘性流れの壁面境界条件',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/slip'),
            indent = '\t'))

    def menuItem_OF_surfaceNormalFixedValueOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('surfaceNormalFixedValue',
            u'境界に垂直な方向の速度を外向きを正として設定し，平行方向の速度は0にする．',
            u'refValue uniform -10; // 垂直方向速度',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/surfaceNormalFixedValue'),
            indent = '\t'))

    def menuItem_OF_symmetryOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('symmetry',
            u'対称境界，境界が曲がっていても使える',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/constraint/symmetry'),
            indent = '\t'))

    def menuItem_OF_symmetryPlaneOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('symmetryPlane',
            u'対称境界，完全な平面にしか使えない',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/constraint/symmetryPlane'),
            indent = '\t'))

    def menuItem_OF_totalPressureOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('totalPressure',
            u'pまたはp_rghに使用\np0で決めた値が全圧（p_rghの場合は全圧 + rho*g*z）になるように設定',
            u'p0 uniform 0;',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/totalPressure'),
            indent = '\t'))

    def menuItem_OF_turbulentIntensityKineticEnergyInletOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('turbulentIntensityKineticEnergyInlet',
            u'計算領域内に流入する場合→k = 1.5*(intensity*局所速度)^2に規定\n計算領域外に流出する場合→zeroGradient',
            u'intensity 0.05;\nvalue $internalField; // 実際には使わないけど必要',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/turbulentIntensityKineticEnergyInlet'),
            indent = '\t'))

    def menuItem_OF_turbulentMixingLengthDissipationRateInletOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('turbulentMixingLengthDissipationRateInlet',
            u'計算領域内に流入する場合→epsilon = C_mu^0.75*k^1.5/混合距離, C_mu = 0.09に規定\n計算領域外に流出する場合→zeroGradient',
            u'mixingLength 0.001; // 混合距離，ふつうは0.07*管内径ぐらいの大きさ\nvalue $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/RAS/derivedFvPatchFields/' +
            'turbulentMixingLengthDissipationRateInlet'),
            indent = '\t'))

    def menuItem_OF_turbulentMixingLengthFrequencyInletOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('turbulentMixingLengthFrequencyInlet',
            u'計算領域内に流入する場合→omega = k^0.5/(C_mu^0.25*混合距離), C_mu = 0.09に規定\n計算領域外に流出する場合→zeroGradient',
            u'mixingLength 0.001; // 混合距離，ふつうは0.07*管内径ぐらいの大きさ\nvalue $internalField; // 実際には使わないけど必要',
            openfoam_src + 'TurbulenceModels/turbulenceModels/RAS/derivedFvPatchFields/' +
            'turbulentMixingLengthFrequencyInlet'),
            indent = '\t'))

    def menuItem_OF_variableHeightFlowRateOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('variableHeightFlowRate',
            u'alphaに使用\n' +
            u'alpha < lowerBoundの時→alpha = lowerBound，\n' +
            u'lowerBound < alpha < upperBoundの時→zeroGradient，\n' +
            u'upperBound < alpha の時→alpha = upperBound',
            u'lowerBound 0.0;\nupperBound 1.0;',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/derived/variableHeightFlowRate'),
            indent = '\t'))

    def menuItem_OF_zeroGradientOnMenuSelection(self, event):
        self.textCtrl_edit.WriteText(openfoam_bc_template_string(('zeroGradient',
            u'こう配が0，境界での値 = セル中心での値にする．',
            '',
            openfoam_src + 'finiteVolume/fields/fvPatchFields/basic/zeroGradient'),
            indent = '\t'))

    def menuItem_updateOnMenuSelection(self, event):
#        s = get_file_from_google_drive('1Rm9P1CIbn_YUuvpMYj39MSF7djuVnPPV')
        s = get_file_from_github_public(user = 'gitwamoto', repository = 'texteditwx',
            branch = 'main', file_path = 'texteditwx.py')
        if s is None:
            with wx.MessageDialog(self,
                _(u'GitHubに接続できませんでした．後でやり直して下さい．'),
                _(u'接続エラー'), style = wx.ICON_ERROR) as md:
                md.ShowModal()
            return
        m = re.search(b"version\\s*=\\s*'([0-9/ :APM]+)'\n", s[0])
        if m is not None and time_str_a_is_newer_than_b(a = m[1].decode(s[1]), b = version):
            p = correct_file_name_in_unicode(os.path.realpath(decode_if_necessary(__file__)))
            with open(p, 'wb') as f:
                f.write(s[0])
            pd = os.path.dirname(p)
#            d = os.path.join(pd, u'locale', u'en', u'LC_MESSAGES')
#            if not os.path.isdir(d):
#                os.makedirs(d)
#            s = get_file_from_github_public(user = 'gitwamoto', repository = 'texteditwx',
#                branch = 'main', file_path = 'locale/en/LC_MESSAGES/messages.mo')
#            if s is not None:
#                with open(os.path.join(d, u'messages.mo'), 'wb') as f:
#                    f.write(s[0])
#            s = get_file_from_github_public(user = 'gitwamoto', repository = 'texteditwx',
#                branch = 'main', file_path = 'locale/en/LC_MESSAGES/messages.po')
#            if s is not None:
#                with open(os.path.join(d, u'messages.po'), 'wb') as f:
#                    f.write(s[0])
#            s = get_file_from_github_public(user = 'gitwamoto', repository = 'texteditwx',
#                branch = 'main', file_path = 'locale/messages.pot')
#            if s is not None:
#                with open(os.path.join(pd, u'locale', u'messages.pot'), 'wb') as f:
#                    f.write(s[0])
#            s = get_file_from_github_public(user = 'gitwamoto', repository = 'texteditwx',
#                branch = 'main', file_path = 'README.md')
#            if s is not None:
#                with open(os.path.join(pd, u'README.md'), 'wb') as f:
#                    f.write(s[0])
            if os.path.isfile(os.path.join(pd, u'modules_needed.txt')):
                os.remove(os.path.join(pd, u'modules_needed.txt'))
            with wx.MessageDialog(self, _(u'アップデートされました．再起動します．'),
                _(u'アップデート完了'), style = wx.ICON_INFORMATION) as md:
                md.ShowModal()
                os.execv(sys.executable, ['python', __file__])
        else:
            with wx.MessageDialog(self, _(u'アップデートの必要はありません．'),
                _(u'プログラムは最新です．'), style = wx.ICON_INFORMATION) as md:
                md.ShowModal()

    def menuItem_movieOnMenuSelection(self, event):
        webbrowser.open(url = 'https://youtu.be/2z8mbayskQU')

if __name__ == '__main__':
    # if __name__ == '__main__'下はグローバルスコープです。
    # そこで定義された変数は、すべてグローバル変数になるということです。
    if len(sys.argv) > 1 and sys.argv[1] == '-h':
        print(u'Usage: {} <file_name>'.format(os.path.basename(decode_if_necessary(sys.argv[0]))))
        sys.exit()
    app = wx.App()
    frame_main = FrameMain(None)
    if len(sys.argv) > 1:
        frame_main.load_doc(sys.argv[1])
    frame_main.Show()
    app.MainLoop()
