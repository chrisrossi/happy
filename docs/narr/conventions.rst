Happy Conventions
=================

Happy components use the :term:`WSGI` protocol and are compatible, at a low
level, with any `WSGI` based framework or application.  Happy uses
:term:`WebOb` request and response objects to hide the 'bare' :term:`WSGI`
protocol.  :term:`WebOb` is quickly becoming the de facto standard among
:term:`WSGI` frameworks and its continued adoption will only facilitate more
greatly reusability and sharing of component libraries like Happy.

Responders
----------

The most used convention in Happy is the :term:`responder protocol`.  In
essence, the `responder protocol` is little more than the :term:`WSGI` protocol
recast to use :term:`WebOb` request and response objects.  A :term:`responder`
is a callable which accects a single :term:`Request` object argument and
returns a :term:`Response` object:

.. code-block:: python

   def responder(request):
      return response  # may be None

A responder may either return a :term:`WebOb` response, or ``None`` if a
responder chooses not to handle a request.  A return type of ``None`` can
indicate to a caller that another responder should be tried or that a
'404 Not Found' should be returned to the client.

A responder can be referred to by other names according to its intended use.
It can be an entire application, a :term:`controller`, a :term:`view', a
:term:`dispatcher`, a :term:`filter` (or :term:`middleware`), etc...  As such
this protocol can be used to encapsulate just about any level of a web
application, from the most general high level pieces of your application to
the smallest, most specific.

Using WSGI with Happy Responders
--------------------------------

XXX
