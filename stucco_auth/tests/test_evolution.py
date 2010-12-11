"""Verify schema versioning is setup correctly."""

import sqlalchemy.orm

def test_evolution():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    import stucco_evolution
    import stucco_auth.tables

    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(engine)
    session = Session()

    stucco_auth.tables.initialize(session)
    stucco_auth.tables.initialize(session) # catch 'already created' case
    stucco_auth.tables.upgrade(session)

    versions = {}
    for row in session.query(stucco_evolution.SchemaVersion):
        versions[row.package] = row.version

    assert 'stucco_evolution' in versions, versions
    assert 'stucco_auth' in versions, versions
    assert versions['stucco_auth'] == stucco_auth.tables.SCHEMA_VERSION

    session.commit()

    # the automatically added admin user
    assert session.query(stucco_auth.tables.User).count() > 0
