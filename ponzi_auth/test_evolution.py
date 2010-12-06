"""Verify schema versioning is setup correctly."""

import sqlalchemy
import sqlalchemy.orm

def test_evolution():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import ponzi_evolution
    import ponzi_auth.tables

    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(engine)
    session = Session()

    ponzi_auth.tables.initialize(session)

    session.flush()

    versions = {}
    for row in session.execute("SELECT package, version FROM ponzi_evolution"):
        versions[row['package']] = row['version']

    assert 'ponzi_evolution' in versions, versions
    assert 'ponzi_auth' in versions, versions
    assert versions['ponzi_auth'] == ponzi_auth.tables.SCHEMA_VERSION

