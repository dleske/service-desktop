# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from flask import Blueprint, render_template, url_for, session, redirect
from .db import get_db
from .auth import login_optional
from .access import evaluate_access

bp = Blueprint('dashboard', __name__)

# ---------------------------------------------------------------------------
#                                                                       sql
# ---------------------------------------------------------------------------

SQL_GET_ALL_UNAUTHENTICATED = '''
  SELECT    category, service, title, description, url, icon_url, sso
  FROM      all_services
  WHERE     language = ? AND access IS NULL
'''

SQL_GET_ALL = '''
  SELECT    category, service, title, description, access, url, icon_url, sso
  FROM      all_services
  WHERE     language = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def _get_services_itor_auth(language):

  res = get_db().execute(SQL_GET_ALL, (language,)).fetchall()

  # if user is defined in session, we need to make the access decisions
  # be nice if there was a library to do this officially
  for rec in res:
    restriction = rec['access']
    if restriction:
      # TODO: if access not match entitlements, affiliations, etc.
      # if access not match:
      #   next or continue or whatever
      if not evaluate_access(restriction, session['access']):
        continue
    yield rec

def _get_services_itor_anon(language):

  res = get_db().execute(SQL_GET_ALL_UNAUTHENTICATED, (language,)).fetchall()
  for rec in res:
    yield rec

def _get_services():

  # TODO: get language from browser, user record, preferences
  # TODO: log and/or flash if LDAP record doesn't match browser
  language = 'en'

  # get iterator appropriate for type of access
  if 'uid' in session:
    services = _get_services_itor_auth(language)
  else:
    services = _get_services_itor_anon(language)

  # we assume that the all_services view orders by category
  # pylint: disable=unsubscriptable-object
  categories = None
  for rec in services:
    if categories is None:
      categories = []
      categories.append((rec['category'], []))
      categories[0][1].append(dict(rec))
    elif categories[-1][0] == rec['category']:
      categories[-1][1].append(dict(rec))
    else:
      categories.append((rec['category'], []))
      categories[-1][1].append(dict(rec))
    if not categories[-1][1][-1].get('icon_url'):
      categories[-1][1][-1]['icon_url'] = None
  return categories

# ---------------------------------------------------------------------------
#                                                                    routes
# ---------------------------------------------------------------------------

# user dashboard
@bp.route('/')
@login_optional
def index():
  # redirect admin to admin dashboard if that's the view they want
  if session.get('admin_view'):
    return redirect(url_for('admin.admin'))
  return render_template('dashboard.html', services=_get_services())

# special route for navigating to the user dashboard and remembering not to
# show the admin dashboard by default next time
@bp.route('/user')
#@login_required
def user_view_redirect():

  if session.get('admin'):
    session['admin_view'] = False
  return redirect(url_for('dashboard.index'))
