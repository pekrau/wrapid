wrapid: Micro framework built on Python WSGI for RESTful server APIs
--------------------------------------------------------------------

- Designed for a RESTful resource-oriented architecture.
- Provides the basis for a well-organized API uniform for all representations,
  including HTML for human browsers, and JSON for programmatic access.
- Includes HTML output generation classes (derived from the HyperText module).
- Predefined class for HTML representation in a standard page layout.
- Built-in support to produce documentation of the API by introspection.
- Agnostic as to back-end storage; no Object-Relational Manager (ORM),
  or other built-in DB connection.
- Uses Python WSGI as the web server interface.

The framework defines four distinct phases in the server's processing
of a request. The application code built on the framework can use
an HTTP Response exception to jump out of the normal processing
during any of the four phases.

1. Prepare: connect to a database, authenticate the request, etc.
2. Handling: update database, modify server-side resources, etc.
3. Data: Collect the data for the response.
4. Response: Select the representation, and return the response data in it.

The source code distribution contains an example implementation 'example.py',
which illustrates a few of the features. To install it, enable the mod_wsgi
module in your Apache2 installation, and add the contents of the file
'apache2.cnf' (supplied in the distribution) to your Apache2 configuration
file 'sites-available/default' (or similar).

The wrapid framework is written in Python 2.6. The following source code
packages are needed:

- [https://github.com/pekrau/wrapid](https://github.com/pekrau/wrapid):
 Source code for the wrapid framework.
- [http://pypi.python.org/pypi/Markdown](http://pypi.python.org/pypi/Markdown):
  Package **Markdown** for producing HTML from text using the simple markup
  language [Markdown](http://daringfireball.net/projects/markdown/).

An installation showing the example code can be viewed at
[http://tools.scilifelab.se/wrapid](http://tools.scilifelab.se/wrapid).
