"""
Utility functions.
"""

def get_flash(request):
    """Return and delete a list of flash message(s) or []"""
    session = request.session
    return session.pop('flash', [])

def set_flash(request, message):
    """Append message to the current session's 'flash' value."""
    session = request.session
    session['flash'] = session.get('flash', [])
    session['flash'].append(message)
    session.save()