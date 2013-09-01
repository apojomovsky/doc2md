#! /usr/bin/env python
# encoding: utf-8
"""
Very lightweight docstring to Markdown converter.


### License

Copyright © 2013 Thomas Gläßle <t_glaessle@gmx.de>

This work  is free. You can  redistribute it and/or modify  it under the
terms of the Do What The Fuck  You Want To Public License, Version 2, as
published by Sam Hocevar. See the COPYING file for more details.

This program  is free software.  It comes  without any warranty,  to the
extent permitted by applicable law.


### Description

Little convenience tool to extract docstrings from a module or class and
convert them to GitHub Flavoured Markdown: 

https://help.github.com/articles/github-flavored-markdown

Its purpose is to quickly generate `README.md` files for small projects.


### API

The interface consists of the following functions:

 - `doctrim(docstring)`
 - `doc2md(docstring, title)`

You can run this script from the command line like:

$ doc2md.py module-name [class-name] > README.md


### Limitations

At the moment  this is suited only  for a very specific use  case. It is
hardly forseeable, if I will decide to improve on it in the near future.

"""
import re
import sys

def doctrim(docstring):
    """
    Remove indentation from docstring.

    This is taken from:
    http://www.python.org/dev/peps/pep-0257/#handling-docstring-indentation

    sys.maxint had to be replaced by sys.maxsize for python3.

    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

def unindent(lines):
    """
    Remove common indentation from string.
    """
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = []
    if indent < sys.maxsize:
        for line in lines:
            trimmed.append(line[indent:])
    return trimmed

def code_block(lines, language=''):
    """
    Mark the code segment for syntax highlighting.
    """
    return ['```' + language] + lines + ['```']

def doctest2md(lines):
    """
    Convert the given doctest to a syntax highlighted markdown segment.
    """
    is_only_code = True
    lines = unindent(lines)
    for line in lines:
        if not line.startswith('>>> ') and not line.startswith('... ') and line not in ['>>>', '...']:
            is_only_code = False
            break
    if is_only_code:
        orig = lines
        lines = []
        for line in orig:
            lines.append(line[4:])
    return lines

def doc_code_block(lines, language):
    if language == 'python':
        lines = doctest2md(lines)
    return code_block(lines, language)


def find_sections(lines):
    """
    Find all section names and return a list with their names.
    """
    reg_section = re.compile('^#+ ')
    sections = []
    for line in lines:
        if reg_section.match(line):
            part = line.partition(' ')
            sections.append((len(part[0]), part[2]))
    return sections

def make_toc(sections):
    """
    Generate table of contents for array of section names.
    """
    if not sections:
        return []
    outer = min(n for n,t in sections)
    refs = []
    for ind,sec in sections:
        ref = sec.lower()
        ref = ref.replace(' ', '-')
        ref = ref.replace('?', '')
        refs.append("    "*(ind-outer) + "- [%s](#%s)" % (sec, ref))
    return refs


def doc2md(docstr, title):
    """
    Convert a docstring to a markdown text.
    """
    text = doctrim(docstr)
    lines = text.split('\n')

    sections = find_sections(lines)
    if sections:
        level = min(n for n,t in sections)
    else:
        level = 2
    md = [
        "#"*max(level-1, 1) + " " + title,
        "",
        lines.pop(0),
        ""
    ]
    md += make_toc(sections)
    is_code = False
    for line in lines:
        trimmed = line.lstrip()
        if is_code:
            if line:
                code.append(line)
            else:
                is_code = False
                md += doc_code_block(code, language)
                md += [line]
        elif trimmed.startswith('>>> '):
            is_code = True
            language = 'python'
            code = [line]
        elif trimmed.startswith('$ '):
            is_code = True
            language = 'bash'
            code = [line]
        else:
            md += [line]
    if is_code:
        md += doc_code_block(code, language)
    return "\n".join(md)


if __name__ == "__main__":
    # parse the program arguments
    import argparse
    parser = argparse.ArgumentParser(
            description='Convert docstrings to markdown.')

    parser.add_argument(
            'module', help='The module containing the docstring.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
            'entry', nargs='?',
            help='Convert only docstring of this entry in module.')
    parser.add_argument(
            '-t', '--title', dest='title',
            help='Document title (default is module name)')
    args = parser.parse_args()

    import importlib
    import inspect
    import os

    def add_path(*pathes):
        for path in reversed(pathes):
            if path not in sys.path:
                sys.path.insert(0, path)

    file = inspect.getfile(inspect.currentframe())
    add_path(os.path.realpath(os.path.abspath(os.path.dirname(file))))
    add_path(os.getcwd())

    mod_name = args.module
    if mod_name.endswith('.py'):
        mod_name = mod_name.rsplit('.py', 1)[0]
    title = args.title or mod_name.replace('_', '-')

    module = importlib.import_module(mod_name)

    if args.entry:
        docstr = module.__dict__[args.entry].__doc__
    else:
        docstr = module.__doc__
    print(doc2md(docstr, title))

