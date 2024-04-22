import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column

import logging

logging.disable(logging.WARNING)

from server import Router
from server import Http_status, Request

status = Http_status()


class Database:
    __host = ""
    __port = ""
    __database = ""
    __username = ""
    __password = ""
    __db_type = ""
    __params = ""

    def __init__(self, host, port, database, username, password, db_type):
        self.__host = host
        self.__port = port
        self.__database = database
        self.__username = username
        self.__password = password
        self.__db_type = db_type

    def connection(self):
        params = ("mysql://" + self.__username + ":" + self.__password + "@"
                  + self.__host + ":" + str(self.__port) + "/" + self.__database)
        engine = create_engine(params, echo=True)
        db = sessionmaker(bind=engine)
        conn = db()
        return conn

    def engine(self):
        params = ("mysql://" + self.__username + ":" + self.__password + "@"
                  + self.__host + ":" + str(self.__port) + "/" + self.__database)
        engine = create_engine(params, echo=True)
        return engine


class Generator:
    __engine = None
    __database_data = None

    def __init__(self, database: Database):
        self.__database_data = database
        self.__engine = database.engine()

    def build(self, table: str):
        md = sqlalchemy.MetaData()
        columns = self.discover_fields(table=table, metadata=md)
        methods = Methods(database=self.__database_data, table=table, fields=columns)
        return methods.generated

    def discover_fields(self, table: str, metadata: sqlalchemy.MetaData):
        table = sqlalchemy.Table(table, metadata, autoload_with=self.__engine)
        cols = []
        columns = table.c
        for c in columns:
            cols.append({
                "column": c.name,
                "type": c.type,
                "pk": c.primary_key
            })
        return cols


class Methods:
    __db = None
    __fields = None
    __table = None
    __table_obj = None
    __id = None
    generated = None

    def __init__(self, database: Database, table: str, fields: list):
        md = sqlalchemy.MetaData()
        self.__db = database.connection()
        self.__engine = database.engine()
        self.__table_obj = sqlalchemy.Table(table, md, autoload_with=self.__engine)
        self.__table = table
        self.__fields = fields
        print(fields)
        # OBTENER EL CAMPO ID O PRIMARY KEY DE LA TABLA
        selection = {}
        table_id = self.found_id()
        self.generated = Router(prefix=table)
        self.generate()

    def get_by_id(self):
        pass

    def get(self):
        return {"a1": "SI"}, status.http_200()

    def create(self, request: Request):
        return request, status.http_200()

    def delete(self):
        pass

    def update(self):
        pass

    def patch(self):
        pass

    def generate(self):
        self.generated.add_get(function=self.get_by_id, url="get_by_id")
        self.generated.add_get(function=self.get, url="get")
        self.generated.add_post(function=self.create, url="create")
        self.generated.add_delete(function=self.delete, url="delete")
        self.generated.add_put(function=self.update, url="update")
        self.generated.add_patch(function=self.patch, url="patch")

    def found_id(self):
        for item in self.__fields:
            if "ID" in str.upper(item['column']) and item['pk'] is True:
                return item['column']
            if "ID" in str.upper(item['column']):
                return item['column']
            if item['pk'] is True:
                return item['column']
            else:
                return False
