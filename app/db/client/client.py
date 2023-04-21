import sqlalchemy

from sqlalchemy.orm import sessionmaker


class PostgreSQLConnection:

    def __init__(self, host, port, user, password, db_name):
        self.user = user
        self.password = password
        self.db_name = db_name

        self.host = host
        self.port = port

        self.connection = self.connect()


        session = sessionmaker(
            bind=self.connection.engine,
            autoflush=True,
            enable_baked_queries=False,
            expire_on_commit=True
        )

        self.session = session()

    def get_connection(self):
        engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/'
                                          f'{self.db_name}', client_encoding='utf8')
        return engine.connect()

    def connect(self):
        connection = self.get_connection()
        return self.get_connection()

    def execute_query(self, query):
        res = self.connection.execute(query)
        return res


    