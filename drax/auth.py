# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=assigning-non-slot
# NOTE: "assigning-non-slot" test is broken in Pylint; can remove when
#       https://github.com/PyCQA/pylint/issues/3793 resolved
#
import functools

from flask import (
  Blueprint, g, request, session, redirect, url_for, flash
)
from werkzeug.exceptions import abort
from drax.log import get_log
from drax.ldap import get_ldap

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
  user_id = session.get('uid')

  if user_id is None:
    g.user = None
  else:
    g.user = {
      'id': session['uid'],
      'cn': session['cn'],
      'admin': session['admin']
    }


def admin_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if not session.get('admin'):
      abort(403)
    return view(**kwargs)
  return wrapped_view

# TODO: remove exception and fix nesting
# pylint: disable=too-many-nested-blocks
def login_optional(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):

    if g.user is None:

      # clear any existing login cruft
      session.clear()

      authenticated_user = None

      # use mapping in reverse proxy configuration to map REMOTE_USER from
      # authentication module to X_AUTHENTICATED_USER
      # TODO: this has to be configurable
      if 'X_AUTHENTICATED_USER' in request.headers:
        authenticated_user = request.headers['X_AUTHENTICATED_USER']
      get_log().debug("X_AUTHENTICATED_USER = %s", authenticated_user)

      # check if externally authenticated
      if authenticated_user:

        # access-related attributes to retrieve
        access_attrs = ['eduPersonAffiliation', 'eduPersonEntitlement']

        # get user information into session
        details = get_ldap().get_person(authenticated_user, access_attrs)
        get_log().debug("LDAP details for %s: %s", authenticated_user, details)

        if details:
          try:
            for key in ['cn', 'givenName', 'preferredLanguage']:
              session[key] = details[key]
          except KeyError:
            # all of these are required and/or present in a valid user
            # representing a real user, so without them the app is forbidden
            get_log().error("Incomplete LDAP information for %s",
              authenticated_user)
            del session['uid']
          else:
            # set this after the rest as this establishes a valid authentication
            session['uid'] = authenticated_user

            # copy into session
            session['access'] = {}
            for access in access_attrs:
              if access in details:
                session['access'][access] = details[access]

            # check if user has rights to this service
            if 'eduPersonEntitlement' in details:

              # has admin rights?
              # TODO: configuration item or something else
              session['admin'] = 'bleep-blorp' in details['eduPersonEntitlement']

              # default for those with admin rights is to show admin view
              session['admin_view'] = session['admin']

            else:
              session['admin'] = False
              session['admin_view'] = False

            load_logged_in_user()

            session['authenticated_externally'] = True

    return view(**kwargs)

  return wrapped_view

# ---------------------------------------------------------------------------
#                                                                   routes
# ---------------------------------------------------------------------------

@bp.route('/')
@login_optional
def login():
  """
  This is used to get login information and redirect to the main dashboard.
  This route seems to do nothing but should be used as the route protected
  by SSO to establish optional authentication.
  """
  # check whether authentication happened
  if 'uid' not in session:
    get_log().debug("Do not have UID set after attempt to authenticate")
    flash('Could not authenticate.  Do you need an account?')
  get_log().debug("In /auth/ and about to redirect to dashboard")
  return redirect(url_for('dashboard.index'))

@bp.route('/logout')
def logout():
  """
  This is used to clear the session.
  """
  session.clear()
  return redirect(url_for('dashboard.index'))
