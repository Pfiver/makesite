#!/usr/bin/env python
""""asdf"""

from livereload import Server
from makesite_liquidish import main

server = Server()
server.watch('*.html', main)
server.watch('*.css', main)
server.watch('*.md', main)
server.serve(root='site')
