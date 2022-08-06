#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2018 Sunaina Pai
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

import os
import re
import shutil
import sys


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


def render(template, params):
    """Replace placeholders in template with values from params."""
    return re.sub(r'{{\s*([^}\s]+)\s*}}',
                  lambda match: str(params.get(match.group(1), match.group(0))),
                  template)


def make_page(src_path, dst_path, layout, params):
    """Generate pages from page content."""
    log('Rendering {} => {} ...', src_path, dst_path)

    page_params = params | {
        'name': os.path.basename(src_path).split('.')[0]
    }
    page_src = fread(src_path)
    page_src = parse_headers(page_src, page_params)
    content = render(page_src, page_params)
    layout_params = page_params | {'content': content}
    output = render(layout, layout_params)

    fwrite(dst_path, output)


def main():
    if os.path.isdir('site'):
        shutil.rmtree('site')

    params = {}

    layout = fread('layout.html')

    make_page('index.html', 'site/index.html', layout, params)
    make_page('contact.html', 'site/contact.html', layout, params)
    make_page('about.html', 'site/about.html', layout, params)

    shutil.copy('style.css', 'site/style.css')


if __name__ == '__main__':
    main()
