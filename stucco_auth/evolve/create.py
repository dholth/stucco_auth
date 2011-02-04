def create(session):
    import os
    import logging
    import stucco_auth.tables

    log = logging.getLogger(__name__)

    stucco_auth.tables.Base.metadata.create_all(session.bind)

    if session.query(stucco_auth.tables.User).count() == 0:
        password = os.urandom(4).encode('hex')
        admin = stucco_auth.tables.User(username='admin',
                                        first_name='Administrator',
                                        last_name='',
                                        email='admin@example.org')
        admin.set_password(password)
        session.add(admin)

        log.info("Created admin user. Username: admin, Password: %s", password)
