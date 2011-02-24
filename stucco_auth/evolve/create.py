def create(connection):
    import os
    import logging
    import stucco_auth.tables
    import sqlalchemy.orm

    log = logging.getLogger(__name__)

    stucco_auth.tables.Base.metadata.create_all(connection)
    
    session = sqlalchemy.orm.sessionmaker()(bind=connection)

    if session.query(stucco_auth.tables.User).count() == 0:
        password = os.urandom(4).encode('hex')
        admin = stucco_auth.tables.User(username='admin',
                                        first_name='Administrator',
                                        last_name='',
                                        email='admin@example.org')
        admin.set_password(password)
        session.add(admin)

        log.info("Created admin user. Username: admin, Password: %s", password)

        session.flush()