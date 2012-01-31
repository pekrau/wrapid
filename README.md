wrapid: Web Resource Application Programming Interface using Python WSGI
------------------------------------------------------------------------

A web server framework with the following features:

- Designed to facilitate a Resource Oriented Architecture.
- Allows the creation of a well-organized RESTful API that is uniform
  for all representations, including HTML for human browsers, or JSON
  and other content types for programmatic access.
- Agnostic as to back-end storage; no ORM, or other built-in DB connection.
- Built-in support to produce documentation of the API by introspection.
- Written in Python 2.6 using WSGI as the web server interface.

The framework defines four distinct phases in the processing of
a request on the server side: 

1. Prepare; connect to database, authenticate the request, etc.
2. Request handling; database updates, etc.
3. Get the data for the response.
4. Return the response using a representation to format the data.

The wrapid source code lives at
[github, user pekrau](https://github.com/pekrau/wrapid).

There is an example implementation 'example.py', which illustrates
a few of the features. Enable the mod_wsgi module in your Apache2
installation, and add the section from the file 'apache2.cnf'
in the distribution to your Apache2 configuration file
'sites-available/default' (or similar).

The example implementation can be viewed at
[http://tools.scilifelab.se/wrapid](http://tools.scilifelab.se/wrapid).
