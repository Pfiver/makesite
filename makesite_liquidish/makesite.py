#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2018 Sunaina Pai
# Copyright (c) 2022 Patrick Pfeifer
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Make static website/blog with Python."""
import glob
import json
import os
import re
import shutil
import sys
from os import path

import yaml


def fread(filename):
    """Read file and close the file."""
    with open(filename, 'r') as f:
        return f.read()


def fwrite(filename, text):
    """Write content to file and close the file."""
    basedir = os.path.dirname(filename)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    with open(filename, 'w') as f:
        f.write(text)


def log(msg, *args):
    """Log message with specified arguments."""
    sys.stderr.write(msg.format(*args) + '\n')


def parse_headers(page_src, params):
    """Parse headers in text and yield (key, value, end-index) tuples."""
    end = 0
    for match in re.finditer(r'\s*<!--\s*(.+?)\s*:\s*(.+?)\s*-->\s*|.+', page_src):
        if not match.group(1):
            break
        params[match.group(1)] = match.group(2)
        end = match.end()

    return page_src[end:]


def eval_dotted_expression(ctx, expr, default=None):
    """
    translate dot- to bracket-notation
    e.g. site.items[0].name ==> site["items"][0]["name"]
    """
    expression = re.sub(r'\.(\w+)(?=[.\s\[\])]|$)', r'["\1"]', expr)
    try:
        return eval(expression, {}, ctx)
    except KeyError:
        return default


def render_expressions(template, params):
    """Replace placeholders in template with values from params."""
    def get_value(match):
        return str(eval_dotted_expression(params, match.group(1), match.group(0)))
    return re.sub(r'{{\s*([^}\s]+)\s*}}', get_value, template)


def render(template, params):
    """Process {% if ... %}, {% for ... %} and "bare" blocks."""
    out = []
    nesting = 0
    block_start = 0
    block_proc = None
    post_start = 0
    for match in re.finditer(r'{%\s*(if |else|for |end)(.+?)\s*%}', template):
        if match.group(1) in ('if ', 'for '):
            if nesting == 0:
                # pre
                out.append(render_expressions(template[post_start:match.start()], params))
                block_proc = get_block_processor(*match.groups(), params)
                block_start = match.end()
            nesting += 1
        if match.group(1) in ('else', ''):
            if nesting == 1:
                # block
                block_template = template[block_start:match.start()]
                block_proc(lambda block_params: out.append(render(block_template, block_params)))
                block_proc.negate = True  # re-use the same processor with inverted logic
                block_start = match.end()
        if match.group(1) in ('end', ''):
            nesting -= 1
            if nesting == 0:
                # block
                block_template = template[block_start:match.start()]
                block_proc(lambda block_params: out.append(render(block_template, block_params)))
                post_start = match.end()
    # post
    out.append(render_expressions(template[post_start:], params))

    return "".join(out)


def get_block_processor(key, expr, params):
    proc = None
    if key == 'if ':
        def proc(render_function):
            if eval_dotted_expression(params, expr) ^ proc.negate:
                render_function(params)
        proc.negate = False
    if key == 'for ':
        names, expr = expr.split(" in ")
        names = re.split(r',\s*', names)
        if len(names) == 1:
            def pack(elements):
                return {names[0]: elements}
        else:
            def pack(elements):
                return {name: elem for name, elem in zip(names, elements)}

        def proc(render_function):
            for elements in eval_dotted_expression(params, expr):
                render_function(params | pack(elements))
    return proc


def get_lang(file):
    return re.search(r'(?:_(\w\w))?.html', file).group(1) or ''


def make_page(name, layout, params, lang=''):
    """Generate pages from page content."""
    dst, src = get_src_dst(name, lang)
    log('Rendering {} => {} ...', src, dst)

    page_params = params | {
        'name': name,
        'lang': lang,
        'lang_names': {
            'en': name,
            'de': name + '_de'
        }
    }

    page_src = fread(src)
    page_src = parse_headers(page_src, page_params)
    content = render(page_src, page_params)
    layout_params = page_params | {'content': content}
    output = render(layout, layout_params)

    fwrite(dst, output)


def get_src_dst(page_name, lang):
    src = page_name
    dst = 'site/' + page_name
    if lang:
        if not path.exists(src + '_' + lang + '.html'):
            src += '.html'
        else:
            src += '_' + lang + '.html'
        dst += '_' + lang + '.html'
    else:
        src += '.html'
        dst += '.html'
    return dst, src


def main():
    params = {}

    try:
        params.update(yaml.safe_load(fread('config.yml')))
    except Exception:
        reply = input("Config file not found. Do you want to create an example site ? [Y/n] ")
        if reply and not reply.lower().startswith("y"):
            return
        from importlib import resources
        shutil.copytree(resources.path('makesite_liquidish', 'example_site'), 'example_site')
        print()
        print("copied example site to 'example_site'.")
        print("Now you can 'cd' into it and run 'makesite' again.")
        print()
        return

    for gallery_data in (d + '/gallery-data.json' for d in ('.', 'site')):
        if path.exists(gallery_data):
            params.update({
                'galleries': json.loads(fread(gallery_data))
            })

    layout_files = glob.glob("layout*.html")

    page_names = [file[:-5] for file in glob.glob("*.html")
                  if not get_lang(file) and not file.startswith("layout")]

    for file in layout_files:
        lang = get_lang(file)
        layout_params = dict(params)
        layout = parse_headers(fread(file), layout_params)
        for name in page_names:
            make_page(name, layout, layout_params, lang)

    for f in 'assets logo.png favicon.ico style.css'.split(' '):
        if path.isdir(f):
            shutil.copytree(f, 'site/' + f, dirs_exist_ok=True)
        elif path.exists(f):
            shutil.copy(f, 'site/' + f)


if __name__ == '__main__':
    main()
