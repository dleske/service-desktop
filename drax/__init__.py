# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=import-outside-toplevel
#
import os

from flask import Flask, current_app
from . import config
from . import db
from .version import version

# project codename: Digital Research Alliance eXperience
CODENAME = 'drax'

def inject_custom_vars():
  """
  Inject custom variables into the context available for templates.
  """

  return dict(
    title=current_app.config.application.title,
    css_override=current_app.config.application.css,
    resources_uri=current_app.config['RESOURCE_URI'],
    login_uri=current_app.config['LOGIN_URI'],
    logout_uri=current_app.config['LOGOUT_URI'],
    version=version
  )

def create_app(test_config=None):

  # create app
  app = Flask(__name__, instance_relative_config=True)

  # initialize configuration
  conf = config.init_config(CODENAME, app.instance_path)

  # configure app
  app.config.from_mapping(
    SECRET_KEY='dev'
  )
  # TODO: this needs mergeconf v0.4
  #app.config.from_mapping(conf)
  app.config['DATABASE_URI'] = conf['DATABASE_URI']
  app.config['RESOURCE_URI'] = conf['RESOURCE_URI']
  app.config['LOGIN_URI'] = conf['LOGIN_URI']
  app.config['LOGOUT_URI'] = conf['LOGOUT_URI']
  app.config['LDAP_URI'] = conf['LDAP_URI']
  app.config['LDAP_BINDDN'] = conf['LDAP_BINDDN']
  app.config['LDAP_PASSWORD'] = conf['LDAP_PASSWORD']
  app.config['LDAP_SKIP_TLS'] = conf['LDAP_SKIP_TLS']
  app.config['LDAP_TLS_REQCERT'] = conf['LDAP_TLS_REQCERT']

  # load test config, if given
  if test_config:
    app.config.from_mapping(test_config)

  # ensure the instance folder exists
  try:
    os.makedirs(app.instance_path)
  except OSError:
    pass

  init_app(app)

  from . import dashboard
  app.register_blueprint(dashboard.bp)

  from . import auth
  app.register_blueprint(auth.bp)

  # make custom variables available to all templates
  app.context_processor(inject_custom_vars)

  return app

def init_app(app):
  app.teardown_appcontext(db.close_db)
  #app.teardown_appcontext(log.close_log)
  app.cli.add_command(db.init_db_command)
  app.cli.add_command(db.seed_db_command)
  app.cli.add_command(db.upgrade_db_command)
