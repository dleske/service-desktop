# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
"""
Routes for checking status of application and dependencies
"""

from flask import Blueprint
from .db import get_schema_version, upgrade_schema
from .ldap import get_ldap
from .exceptions import ImpossibleSchemaUpgrade


# establish blueprint
bp = Blueprint('status', __name__, url_prefix='/status')

# ---------------------------------------------------------------------------
#                                                                    HELPERS
# ---------------------------------------------------------------------------

def _check_status_app(statuses):

  # this is trivial
  statuses.append("I'm: Okay")
  return 200

def _check_status_db(statuses):

  status = 200

  # get schema version from database
  try:
    (actual, expected) = get_schema_version()
  except Exception as e:
    statuses.append(f"DB: Caught exception: {str(e).rstrip()}")
    status = 500
  else:
    if actual == expected:
      statuses.append(f"DB: Okay (schema version {actual})")
    else:
      statuses.append(f"DB: Schema version mismatch: {actual}, expected {expected}")
      status = 500

  return status

def _check_status_ldap(statuses):

  status = 200

  # try to get an LDAP record
  try:
    # TODO: make configurable
    # if config.ldap_canary:
    canary = get_ldap().get_person('canary')
  except Exception as e:
    statuses.append(f"LDAP: {e}")
    status = 500
  else:
    if not canary:
      statuses.append("LDAP: Basic query failed")
      status = 500
    else:
      statuses.append("LDAP: Okay")

  return status

# ---------------------------------------------------------------------------
#                                                                     ROUTES
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET'])
def get_status():
  """
  Reports app health apart from external dependencies.  This is so limited
  in order that it can be used as a liveness probe in Kubernetes.  Failing
  this would then result in restarts of the container, and basing that on
  the connections to LDAP, OTRS, etc. does not make sense.
  """

  statuses = []
  status = 200

  # run some tests
  status = _check_status_app(statuses)

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services/ldap', methods=['GET'])
def get_services_status_ldap():

  statuses = []
  status = 200

  status = max(status, _check_status_ldap(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services/db', methods=['GET'])
def get_services_status_db():

  statuses = []
  status = 200

  status = max(status, _check_status_db(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services', methods=['GET'])
def get_services_status():

  statuses = []
  status = 200

  status = max(status, _check_status_ldap(statuses))
  status = max(status, _check_status_db(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

# Use as a startup probe.  Will check DB schema version and update if necessary.
@bp.route('/db', methods=['GET'])
def update_db():
  try:
    (actual, expected, actions) = upgrade_schema()
    if actions:
      path = "\n".join(actions)
      status_text = f"DB required upgrade from {actual} to {expected}\n{path}"
    else:
      status_text = f"DB schema at {actual}, code schema at {expected}, no action taken"
    status_code = 200
  except ImpossibleSchemaUpgrade as e:
    status_text = str(e)
    status_code = 500

  return status_text, status_code, {'Content-type': 'text/plain; charset=utf-8'}
