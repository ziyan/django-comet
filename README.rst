============
Django Comet
============

This project provides three different server-side push (a.k.a. comet) mechanisms:

 * Ajax long polling, including cross-origin
 * XML HTTP RPC long polling
 * Websocket

These mechanisms are provided through tornado

Requirements
============

 * git+git://github.com/joshmarshall/tornadorpc.git
 * git+git://github.com/evilkost/brukva.git
 * redis
 * tornado

USAGE
=====

Simply add comet to your INSTALLED_APPS.

Suppose you need to signal your users when some events happen, the user is logged in on several client devices.

Before a client for a particular user can be signaled, it needs a token. To generate a token, simply register the client::

    token = comet.utils.register('a unique identifier for the user, not the client, e.g. a UUID')

Save this token in a session, and give it to the client through embedding in html or returned by ajax call.

Tokens expire in 15 mins, however, they can be renewed by calling register again with the token as the second argument.

To signal a user (actually its one or many clients), simply::

    comet.utils.signal('the unique identifier for the user', [{'message': 'event 1'}, {'event': 2}])

Note that the second argument needs to be an array.

A sample coffeescript for client-side code is provided.
