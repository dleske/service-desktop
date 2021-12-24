# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=C0415,disable=assigning-non-slot
# NOTE: "assigning-non-slot" test is broken in Pylint; can remove when
#       https://github.com/PyCQA/pylint/issues/3793 resolved
#
import os
from enum import Enum
import re
import click
from flask import current_app, g
from flask.cli import with_appcontext
from drax.log import get_log
from drax import exceptions

# Current database schema version
# format is string: YYYYMMDD
#
# This number must match the latest entry in the database's schemalog table,
# or an upgrade should be performed.
#
# See README in SQL scripts dir for guidance on updating the schema.
SCHEMA_VERSION = '20211005'

# query to fetch latest schema version
SQL_GET_SCHEMA_VERSION = """
  SELECT    version
  FROM      schemalog
  ORDER BY  version DESC
  LIMIT     1
"""

# scripts path
SQL_SCRIPTS_DIR = 'sql'

# This is used to queue custom DB-ready classes for to be registered for use
# with specific databases, once the appropriate database is identified and
# initialized.
_register_adapters_for = []
def queue_adapter_registration(cls):
  _register_adapters_for.append(cls)

def get_db():
  """
  Retrieve application's database object, initializing if necessary.
  """

  if 'db' not in g:
    g.db = open_db(current_app.config['DATABASE_URI'])

  return g.db


def open_db(uri):
  """
  Open database connection for appropriate database type based on URI and
  return the connection handle.
  """
  scheme = uri.split(':', 1)[0]

  if scheme == 'file':
    from .db_sqlite import open_db_sqlite, register_adapter
    db = open_db_sqlite(uri)

  elif scheme == 'postgresql':
    from .db_postgres import open_db_postgres, register_adapter
    db = open_db_postgres(uri)

  else:
    raise exceptions.UnsupportedDatabase(scheme)

  # register adapter(s) for bespoke classes
  for cls in _register_adapters_for:
    register_adapter(cls)

  return db


def close_db(e=None):
  db = g.pop('db', None)

  if e:
    get_log().info("Closing database in presence of error condition: '%s'", e)

  if db is not None:
    db.close()


def init_db(schema=None):
  db = get_db()

  if not schema:
    if db.type == 'sqlite':
      schema = f"{SQL_SCRIPTS_DIR}/schema.sql"
    elif db.type == 'postgres':
      schema = f"{SQL_SCRIPTS_DIR}/schema.psql"

  get_log().info("Initializing database with %s", schema)

  with current_app.open_resource(schema) as f:
    db.executescript(f.read().decode('utf8'))

  db.commit()


def seed_db(seedfile):
  db = get_db()

  get_log().info("Seeding database with %s", seedfile)

  with current_app.open_resource(seedfile) as f:
    db.executescript(f.read().decode('utf8'))

  db.commit()


def get_schema_version():
  db = get_db()
  try:
    vers = db.execute(SQL_GET_SCHEMA_VERSION).fetchone()['version']
  except Exception as e:
    get_log().error("Error in retrieving schema version: %s", e)
    raise exceptions.DatabaseException("Could not retrieve schema version") from e
  if not vers:
    get_log().error("Could not find latest schema version")
    raise exceptions.DatabaseException("Could not determine schema version")
  return (vers, SCHEMA_VERSION)


def upgrade_schema(data_updates=None):
  (actual, expected) = get_schema_version()
  if actual == expected:
    # trivial: actual matches expected, no action needed
    return (actual, expected, None)

  get_log().info("DB schema is at version %s; app expects %s", actual, expected)

  ## Find upgrade path.  Scripts are "${from}_to_${to}.[sql|psql]".  Might need
  ## to run several, such as if there is ${from}_to_int1.sql, int1_to_${to}.sql
  ## for example.

  ## Build dictionary of upgrade scripts keyed on their starting versions.
  ## Values are the ending version and the filename.
  scriptdict = {}

  # build regular expression for matching upgrade scripts
  db = get_db()
  if db.type == 'sqlite':
    ext = 'sql'
  elif db.type == 'postgres':
    ext = 'psql'
  regex = re.compile(rf'^([^_]+)_to_([^_]+)\.{ext}$')

  # iterate through each file and if it's an update script add it to dict
  # pylint: disable=unused-variable
  for root, dirs, files in os.walk(current_app.root_path + '/' + SQL_SCRIPTS_DIR):
    for file in files:
      m = regex.match(file)
      if m:
        if m[1] in scriptdict:
          # this should not happen
          description = 'Multiple upgrade scripts have the same starting ' \
            'version.  This is not supported and leaves no clear upgrade ' \
            f'path.  In conflict: {scriptdict[m[1]][1]} and {file}.  Trying ' \
            f'to upgrade schema from {actual} to {expected}'
          raise exceptions.ImpossibleSchemaUpgrade(description)
        scriptdict[m[1]] = (m[2], f"{root}/{file}")

  # find path through upgrades from actual to expected
  have_upgrade_path = False
  upgrades = {}
  current = str(actual)
  while current in scriptdict:
    upgrades[scriptdict[current][0]] = scriptdict[current][1]
    current = scriptdict[current][0]
    if current == expected:
      have_upgrade_path = True
      break

  if not have_upgrade_path:
    # this is a pretty serious application error
    description = \
      f'There is no upgrade path available from schema version {actual} (in ' \
      'the database) to {expected} (expected by the application). ' \
      'Available upgrades: {upgrades}'
    raise exceptions.ImpossibleSchemaUpgrade(description)

  # add in the data upgrade scripts, if any
  if data_updates:
    for (version, path) in data_updates.items():
      upgrades[version] = path

  # iterate through upgrade scripts
  actions = []
  for version in sorted(upgrades):
    upgrade = upgrades[version]
    with current_app.open_resource(upgrade) as f:
      get_log().info("Upgrading DB: %s (version %s)", upgrade, version)
      db.executescript(f.read().decode('utf8'))
    actions.append(f"Executed {upgrade}")

    db.commit()
  get_log().info("Upgraded DB.")

  return (actual, expected, actions)

@click.command('init-db')
@with_appcontext
def init_db_command():
  """Clear the existing data and create new tables."""
  init_db()
  click.echo('Initialized the database.')


@click.command('seed-db')
@click.argument('seedfile')
@with_appcontext
def seed_db_command(seedfile):
  """
  Clear existing data, create new tables, seed with test data.

  Note:
    Seedfile here is interpreted to be relative to client's current working
    directory.
  """

  init_db()
  seed_db(os.path.join(os.getcwd(), seedfile))
  click.echo('Initialized and seeded the database.')


@click.command('upgrade-db')
@with_appcontext
def upgrade_db_command():
  """Upgrade database to expected schema version."""

  try:
    (actual, expected, actions) = upgrade_schema()
    if actions:
      actionstr = "\n".join(actions)
      status_text = f"DB required upgrade from {actual} to {expected}\n{actionstr}"
    else:
      status_text = f"DB schema at {actual}, code schema at {expected}, no action taken"
    #status_code = 0
  except exceptions.ImpossibleSchemaUpgrade as e:
    status_text = str(e)
    #status_code = 1

  click.echo(status_text)
  # I don't like how this has some side effects as an exception
  #click.get_current_context().exit(status_code)


class DbEnum(Enum):
  """
  The DbEnum class augments the standard enumeration be making it more JSON-
  and database-friendly.  For JSON, it provides a serializable representation
  of the enumeration names that is readable and consistent with general JSON
  practice (full lowercase word) so for example ExampleEnum.EXAMPLE is
  returned as "example".  Automatic deserialization isn't possible so the
  get() class method is provided as an alternative to `ExampleEnum['example']`
  and will return ExampleEnum.EXAMPLE.

  For databases, the value is used which is typically a single character.  An
  adapter is created so the database modules correctly interpret the
  enumerations in both directions.
  """

  # pylint: disable=W0613
  def __init__(self, *args):
    cls = self.__class__
    # pylint: disable=W0143
    if any(self.value == e.value for e in cls):
      a = self.name
      e = cls(self.value).name
      raise ValueError(f"Values must be unique: {a!r} -> {e!r}")

    queue_adapter_registration(cls)

  def getquoted(self):
    return str.encode("'" + self.value + "'")

  # String representation is just the name--the value is used to store in
  # the database.  For display purposes, translation is appropriate (ex.
  # English translation of EXAMPLE is "Example"; French translation is--the
  # same)
  def __str__(self):
    return str(self.name)

  # For JSON serialization, use the lowercase representation of the name.
  # JSON should be readable so "resource":"cpu" is more readable than
  # "resource":"c"
  def serialize(self):
    return self.name.lower()

  # pylint: disable=raise-missing-from
  @classmethod
  def get(cls, key):
    try:
      return cls[key.upper()]
    except KeyError:
      raise KeyError(key)
