 wrapid: Web Resource API server framework built on Python WSGI.
----------------------------------------------------------------

- Designed for a RESTful resource-oriented architecture.
- Provides basis for a well-organized API uniform for all representations,
  including HTML for human browsers, and JSON and other content types
  for programmatic access.
- Predefined class for HTML representation in a standard page layout.
- Built-in support to produce documentation of the API by introspection.
- Agnostic as to back-end storage; no Object-Relational Manager (ORM),
  or other built-in DB connection.
- Written in Python 2.6 using WSGI as the web server interface.

The framework defines four distinct phases in the server's processing
of a request. The code built on the framework can use an HTTP Response
exception to jump out of the normal processing during any of the four phases.

1. Prepare: connect to a database, authenticate the request, etc.
2. Handling: update database, modify server-side resources, etc.
3. Data: Get the data for the response.
4. Response: Select the representation, and return the response data in it.

The source code distribution contains an example implementation 'example.py',
which illustrates a few of the features. To install it, enable the mod_wsgi
module in your Apache2 installation, and add the contents of the file
'apache2.cnf' (in the distribution) to your Apache2 configuration file
'sites-available/default' (or similar).

The wrapid source code lives at
[https://github.com/pekrau/wrapid](https://github.com/pekrau/wrapid).
It relies on the package **HyperText** at
[https://github.com/pekrau/hypertext](https://github.com/pekrau/hypertext).

An installation showing the example code can be viewed at
[http://tools.scilifelab.se/wrapid](http://tools.scilifelab.se/wrapid).
