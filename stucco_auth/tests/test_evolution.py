"""Verify schema versioning is setup correctly."""

import sqlalchemy.orm

def test_evolution():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    import stucco_evolution
    import stucco_auth.tables
    import stucco_auth.evolve

    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    connection = engine.connect()

    trans = connection.begin()
    try:
        stucco_evolution.initialize(connection)
        stucco_evolution.create_or_upgrade_packages(connection, 'stucco_auth')

        session = sqlalchemy.orm.sessionmaker()(bind=connection)

        versions = {}
        for row in session.query(stucco_evolution.SchemaVersion):
            versions[row.package] = row.version

        assert 'stucco_evolution' in versions, versions
        assert 'stucco_auth' in versions, versions
        assert versions['stucco_auth'] == stucco_auth.evolve.VERSION

        session.commit()

        # the automatically added admin user
        assert session.query(stucco_auth.tables.User).count() > 0

    finally:
        connection.close()
