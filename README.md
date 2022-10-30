# makesite-liquidish

Based on the great work of Sunaina Pai: https://github.com/sunainapai/makesite

Usage:

    $ pip install makesite_liquidish
    $ makesite                                                                               
    Config file not found. Do you want to create an example site ? [Y/n]
    
    copied example site to 'example_site'.
    Now you can 'cd' into it and run 'makesite' again.
    
    $ cd example_site
    $ makesite
    Rendering index.html => site/index.html ...
    Rendering contact.html => site/contact.html ...
    Rendering galleries.html => site/galleries.html ...

    $ open site/index.html 

Release process:

1. get a pypi token:

        $ cat ~/.pypirc
        [pypi]
        username = __token__
        password = pypi-...

2. `$ setopt nonomatch # on zsh`
2. `$ rm -rf dist build *.egg-info */__pycache__ */example_site/_site`
3. `$ git clean -ndx`
4. `$ python -m build # or 'pyproject-build'`
5. `$ twine upload dist/*`
