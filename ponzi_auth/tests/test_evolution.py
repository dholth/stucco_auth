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
    ponzi_auth.tables.initialize(session) # catch 'already created' case
    ponzi_auth.tables.upgrade(session)

    versions = {}
    for row in session.query(ponzi_evolution.SchemaVersion):
        versions[row.package] = row.version

    assert 'ponzi_evolution' in versions, versions
    assert 'ponzi_auth' in versions, versions
    assert versions['ponzi_auth'] == ponzi_auth.tables.SCHEMA_VERSION

    session.commit()

    # the automatically added admin user
    assert session.query(ponzi_auth.tables.User).count() > 0
