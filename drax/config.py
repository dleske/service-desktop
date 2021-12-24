# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import os
import mergeconf

# TODO: update for mergeconf >= 0.5
def init_config(codename, path):

  # initialize config object
  conf = mergeconf.MergeConf(codename.upper())

  # application configuration
  conf_app = conf.add_section('application')
  conf_app.add('title', default=_('Service Desktop'))
  conf_app.add('css')

  # configuration for database
  def_db_uri = f'file:///{path}/{codename}.sqlite'
  conf.add('DATABASE_URI', value=def_db_uri)

  # configuration for authorization
  conf.add('ENTITLEMENT_ADMIN', value='drax.example.org/admin')

  # default location of static, external resources
  conf.add('RESOURCE_URI', value='static')

  # SSO-related login/logout
  conf.add('LOGIN_URI')
  conf.add('LOGOUT_URI')

  # LDAP configurables
  conf.add('LDAP_URI')
  conf.add('LDAP_BINDDN')
  conf.add('LDAP_PASSWORD')
  conf.add('LDAP_SKIP_TLS', value=False, type=bool)
  conf.add('LDAP_TLS_REQCERT', value='demand')

  # determine configuration file
  def_conf_file = os.path.join(path, f'{codename}.conf')
  if not os.path.exists(def_conf_file):
    def_conf_file = None

  # parse configuration file and secretly merge with what's in environment
  # TODO: (mergeconf) Update the name of this to not sound like it's just
  #       parsing configuration file but also handling environment, and
  #       command-line parameters.  With command-line arguments, maybe
  #       merge(def_conf_file, args)
  conf.parse(def_conf_file)

  return conf
