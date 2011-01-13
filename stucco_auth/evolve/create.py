def create(session):
    import stucco_auth.tables
    stucco_auth.tables.Base.metadata.create_all(session.bind)
