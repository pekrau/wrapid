""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

To do:
- Check Last-Modified for static files
- return 415 Unsupported Media Type for wrong inrepr
- allow key 'verbosity' in data to determine which level
  of output for JSON: 'min' gives list of keys to include
- use html_representation for get_documentation?
- authorization: part of Method? to allow documenting it
- valid responses other than 200: 303 See Other, 204 No Content...
"""


__version__ = '1.2'
