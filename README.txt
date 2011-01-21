stucco_auth
===========

SQLAlchemy-backed username/password authentication for the Pyramid web 
framework.

What You Get
------------

- Versioned schema with stucco_evolution
- SQLAlchemy-mapped User, Group, and Settings classes
- BCRYPT password encryption with cryptacular
- Pyramid views to login and logout
- Traversal, not routes
- Jinja2 templates for the views
- Uni-Form CSS themed login form
- YUI 3 CSS in the base template
- 99% test coverage

Requirements
------------

It's easy enough to add the stucco_auth views to your application by calling::

	from pyramid.config import Configurator
	config = Configurator(...)
	config.include('stucco_auth.config')
	
Unfortunately, stucco_auth requires many things from a host Pyramid application
before it will work properly:

- A configured authentication and authorization policy. Login and logout views
  don't make sense otherwise.
- A transaction-managed SQLAlchemy session made available as request.db
- request.session for flash messages
- Jinja2 templating
- 