wrapid: Web Resource Application Programming Interface using Python WSGI.

A different web server framework with some novel features:

- Designed to facilitate a Resource Oriented Architecture.
- Allows the creation of a well-organized RESTful API that is uniform
  for all representations, including HTML for human browsers, or JSON
  and other content types for programmatic access.
- Separates the retrieval/operation on server-side data from the creation
  of a specific response representation.
- Built-in support to produce documentation of the API by introspection.
- Agnostic as to back-end storage; no ORM, or other built-in DB connection.
- Written in Python 2.6 using WSGI as the web server interface.

There is an example implementation 'example.py'. To include it in an
Apache2 web server setup, add the following section to you Apache2
configuration file 'sites-available/default' (or similar):

	#### wrapid example via WSGI using 'mod_wsgi'
	<Directory "/WHEREVER/wrapid">
		AddDefaultCharset utf-8
		Order allow,deny
		Allow from all
	</Directory>
	WSGIScriptAlias /wrapid /WHEREVER/wrapid/example.py

The example implementation can be viewed at http://tools.scilifelab.se/wrapid
