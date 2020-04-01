def create(connection):
    import os
    import logging
    import stucco_auth.tables
    import sqlalchemy.orm
    import codecs

    log = logging.getLogger(__name__)

    stucco_auth.tables.Base.metadata.create_all(connection)
    
    session = sqlalchemy.orm.sessionmaker()(bind=connection)

    if session.query(stucco_auth.tables.User).count() == 0:
        password = codecs.encode(os.urandom(8), 'hex')
        admin = stucco_auth.tables.User(username=u'admin',
                                        first_name=u'Administrator',
                                        last_name=u'',
                                        email=u'admin@example.org')
        admin.set_password(password)
        session.add(admin)

        log.info("Created admin user. Username: admin, Password: %s", password)

        session.flush()
