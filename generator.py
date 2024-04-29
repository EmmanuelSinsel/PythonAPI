import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
import logging

logging.disable(logging.WARNING)

from server import Router
from server import Http_status, Request

status = Http_status()

from sqltypes import sqltypes, mapped_sqltypes

import json
import os
import re
import copy


class Database:
    __host = ""
    __port = ""
    __database = ""
    __username = ""
    __password = ""
    __db_type = ""
    __params = None
    __engine = None

    def __init__(self, host, port, database, username, password, db_type):
        self.__host = host
        self.__port = port
        self.__database = database
        self.__username = username
        self.__password = password
        self.__db_type = db_type
        params = None
        if db_type == 'mysql':
            params = ("mysql+pymysql://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        if db_type == 'postgresql':
            params = ("postgresql://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        if db_type == 'postgresql/psycopg2':
            params = ("postgresql+psycopg2://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        if db_type == 'postgresql/pg8000':
            params = ("postgresql+pg8000://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        if db_type == 'oracle':
            params = ("oracle://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        if db_type == 'oracle/cx_oracle':
            params = ("oracle://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port))
        if db_type == 'mssql':
            params = ("mssql+pyodbc://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port))
        if db_type == 'mssql/pymssql':
            params = ("mssql+pymssql://" + self.__username + ":" + self.__password + "@"
                      + self.__host + ":" + str(self.__port) + "/" + self.__database)
        self.__engine = create_engine(params, echo=True)

    def connection(self):
        db = sessionmaker(bind=self.__engine)
        conn = db()
        return conn

    def engine(self):
        return self.__engine


class Generator:
    __engine = None
    __database_data = None

    def __init__(self, database: Database):
        self.__database_data = database
        self.__engine = database.engine()

    def get_tables_metadata(self):
        from sqlalchemy import inspect
        inspector = inspect(self.__engine)
        schemas = inspector.get_table_names()
        for table in schemas:
            self.build(table)

    def build(self, table: str):
        md = sqlalchemy.MetaData()
        self.check_generated(table)
        f = open("./generated/" + table + ".apy", "r")
        columns = None
        autoincrement = True
        if f.read() == '':
            columns = self.discover_fields(table=table, metadata=md)
        methods = Methods(database=self.__database_data,
                          table=table,
                          fields=columns)
        return methods.generated

    def discover_fields(self, table: str, metadata: sqlalchemy.MetaData):
        table = sqlalchemy.Table(table,
                                 metadata,
                                 autoload_with=self.__engine)

        ai = table.autoincrement_column.name
        print(ai)
        cols = []
        columns = table.c
        for c in columns:
            ai_flag = False
            if ai == c.name:
                ai_flag = True
            cols.append({
                "column": c.name,
                "type": c.type,
                "pk": c.primary_key,
                "ai": ai_flag
            })
        return cols

    def check_generated(self, table):
        if not os.path.exists("./generated"):
            os.mkdir("./generated")
        if not os.path.exists("./generated/" + table + ".apy"):
            f = open("./generated/" + table + ".apy", "x")
            f.close()


class Methods:
    __db = None
    __fields = None
    __table = None
    __table_obj = None
    __id = None
    __object = None
    __engine = None
    generated = None
    __status = Http_status()
    __columns = None
    __column_names = []
    __id_column = None

    def __init__(self, database: Database, table: str, fields: list):
        md = sqlalchemy.MetaData()
        self.__db = database.connection()
        self.__engine = database.engine()
        self.__table = table
        self.__fields = fields
        table_id = None
        if fields != None:
            table_id = self.found_id()
        method_data = self.read_api_files(table_id=table_id, table=table, columns=fields)
        if fields == None:
            fields, table_id = self.extract_fields(data=method_data)
            self.__fields = fields
        self.generate_table_objects(table=table, fields=fields, table_id=table_id)
        self.generated = Router(prefix=table)
        methods_data = self.extract_methods_data(data=method_data)
        self.generate(methods_data=methods_data, table_id=table_id, fields=fields)


    def extract_fields(self, data: str):
        data = data.replace("\t", '')
        end = data.find("BEGIN")
        start = data.find("COLUMNS") + 7
        data = data[start:end]
        field_list = data.split('\n')
        field_list = field_list[1:-1]
        fields = []
        table_id = None
        for field in field_list:
            col_info = field.split(",")
            fields.append({
                "column": col_info[0],
                "type": col_info[1],
                "pk": col_info[2],
                "ai": col_info[3]
            })
            if col_info[2] == "True":
                table_id = col_info[0]
        return fields, table_id

    def extract_methods_data(self, data: str):
        methods = []
        while data != '' and data != '\n':
            begin = data.find("BEGIN")+5
            end = data.find("END")
            method = data[begin:end]
            method = method[1:-1]
            method = method.replace('\t','')
            method_raw = method.split('\n')
            if method_raw[-1] == '':
                method_raw.pop()
            recieve_index = method_raw.index("RECIEVE")
            json_index = method_raw.index("JSON")
            return_index = method_raw.index("RETURN")
            method_type = method_raw[0]
            method_name = method_raw[2]
            method_recieve = method_raw[recieve_index+1:json_index]
            method_json = method_raw[json_index+1:return_index]
            method_return = method_raw[return_index+1:]
            methods.append({
                "method_type":method_type,
                "method_name":method_name,
                "method_recieve":method_recieve,
                "method_json":method_json,
                "method_return":method_return
            })
            data = data[end+3:]
        return methods

    def generate_table_objects(self, table, fields, table_id):
        try:
            self.__id = table_id
            meta = MetaData()
            attributes = [table, meta]
            columns = []
            for i in fields:
                self.__column_names.append(i['column'])
                div = str(i['type']).split('(')
                i['type'] = div[0]
                if i["column"] == table_id:
                    attributes.append(Column(i['column'],
                                             sqltypes[i['type']],
                                             primary_key=True))
                    self.__id_column = (Column(i['column'],
                                               sqltypes[i['type']],
                                               primary_key=True))
                else:
                    if "VARCHAR" in i['type'] and i['type'][0] == "V":
                        attributes.append(Column(i['column'],
                                                 sqltypes['VARCHAR']))
                    elif "NVARCHAR" in i['type'] and i['type'][0] == "N":
                        attributes.append(Column(i['column'],
                                                 sqltypes['NVARCHAR']))
                    elif "CHAR" in i['type'] and i['type'][0] == "C":
                        attributes.append(Column(i['column'],
                                                 sqltypes['CHAR']))
                    else:
                        attributes.append(Column(i['column'],
                                                 sqltypes[i['type']]))
            self.__table_obj = Table(*attributes)
            self.__columns = attributes[2:]
        except Exception as err:
            print(err)

    def read_api_files(self, table_id, table, columns):
        f = open("./generated/" + table + ".apy", "r")
        if f.read() == '':
            f.close()
            fw = open("./generated/" + table + ".apy", "a")
            # DATOS DE LA TABLA
            fw.write("TABLE\n")
            fw.write(table + "\n")
            fw.write("COLUMNS\n")
            for c in columns:
                fw.write("\t" + str(c['column']) + "," + str(c['type']) + "," + str(c['pk']) + "," + str(c['ai']) + "\n")
            # METODO GET
            fw.write("BEGIN" + "\n")
            fw.write("\t" + "GET" + "\n")
            fw.write("\t" + "NAME" + "\n")
            fw.write("\t\t" + "get" + "\n")
            fw.write("\t" + "RECIEVE" + "\n")
            fw.write("\t\t" + table_id + ",INTEGER" + "\n")
            fw.write("\t" + "JSON" + "\n")
            fw.write("\t" + "RETURN" + "\n")
            for c in columns:
                fw.write("\t\t" + str(c['column']) + "," + str(c['type']) + "\n")
            fw.write("END" + "\n")
            # METODO POST
            fw.write("BEGIN" + "\n")
            fw.write("\t" + "POST" + "\n")
            fw.write("\t" + "NAME" + "\n")
            fw.write("\t\t" + "create" + "\n")
            fw.write("\t" + "RECIEVE" + "\n")
            fw.write("\t" + "JSON" + "\n")
            for c in columns:
                if c['column'] != table_id:
                    fw.write("\t\t" + str(c['column']) + "," + str(c['type']) + "\n")
                else:
                    if c['ai'] is False:
                        fw.write("\t\t" + str(c['column']) + "," + str(c['type']) + "\n")
            fw.write("\t" + "RETURN" + "\n")
            fw.write("\t\t" + "CREATED,201" + "\n")
            fw.write("END" + "\n")
            # METODO PUT
            fw.write("BEGIN" + "\n")
            fw.write("\t" + "PUT" + "\n")
            fw.write("\t" + "NAME" + "\n")
            fw.write("\t\t" + "update" + "\n")
            fw.write("\t" + "RECIEVE" + "\n")
            fw.write("\t\t" + table_id + ",INTEGER" + "\n")
            fw.write("\t" + "JSON" + "\n")
            for c in columns:
                if c['column'] != table_id:
                    fw.write("\t\t" + str(c['column']) + "," + str(c['type']) + "\n")
                else:
                    if c['ai'] is False:
                        fw.write("\t\t" + str(c['column']) + "," + str(c['type']) + "\n")
            fw.write("\t" + "RETURN" + "\n")
            fw.write("\t\t" + "UPDATED,200" + "\n")
            fw.write("END" + "\n")
            # METODO DELETE
            fw.write("BEGIN" + "\n")
            fw.write("\t" + "DELETE" + "\n")
            fw.write("\t" + "NAME" + "\n")
            fw.write("\t\t" + "delete" + "\n")
            fw.write("\t" + "RECIEVE" + "\n")
            fw.write("\t\t" + table_id + ",INTEGER" + "\n")
            fw.write("\t" + "JSON" + "\n")
            fw.write("\t" + "RETURN" + "\n")
            fw.write("\t\t" + "DELETED,200" + "\n")
            fw.write("END" + "\n")
            # METODO PATCH
            fw.write("BEGIN" + "\n")
            fw.write("\t" + "PATCH" + "\n")
            fw.write("\t" + "NAME" + "\n")
            fw.write("\t\t" + "patch" + "\n")
            fw.write("\t" + "RECIEVE" + "\n")
            fw.write("\t\t" + table_id + ",INTEGER" + "\n")
            fw.write("\t\t" + str(columns[1]['column']) + "," + str(columns[1]['type']) + "\n")
            fw.write("\t" + "JSON" + "\n")
            fw.write("\t" + "RETURN" + "\n")
            fw.write("\t\t" + "PATCHED,200" + "\n")
            fw.write("\t" + "END" + "\n")
            fw.close()
        f = open("./generated/" + table + ".apy", "r")
        method_data = f.read()
        f.close()
        return method_data

    def generate(self, methods_data, table_id, fields):
        field_list = []
        for f in fields:
            if f['column'] is not table_id:
                field_list.append(f['column'])
            if f['column'] == table_id and f['ai'] == 'False':
                field_list.append(f['column'])
        for method in methods_data:
            if method['method_type'] == 'GET':
                get = self.make_get(method=method, table_id=table_id)
                meta = self.make_meta(method_data=method)
                self.generated.add_get(function=get,
                                       url=method['method_name'],
                                       meta=meta)

            if method['method_type'] == 'POST':
                post = self.make_post(method=method, table_id=table_id, fields=field_list)
                meta = self.make_meta(method_data=method)
                self.generated.add_post(function=post,
                                        url=method['method_name'],
                                        meta=meta)

            if method['method_type'] == 'PUT':
                put = self.make_put(method=method, table_id=table_id)
                meta = self.make_meta(method_data=method)
                self.generated.add_put(function=put,
                                       url=method['method_name'],
                                       meta=meta)

            if method['method_type'] == 'DELETE':
                delete = self.make_delete(method=method, table_id=table_id)
                meta = self.make_meta(method_data=method)
                self.generated.add_delete(function=delete,
                                          url=method['method_name'],
                                          meta=meta)

            if method['method_type'] == 'PATCH':
                patch = self.make_patch(method=method, table_id=table_id, fields=field_list)
                meta = self.make_meta(method_data=method)
                self.generated.add_patch(function=patch,
                                         url=method['method_name'],
                                         meta=meta)

    def make_get(self, method, table_id):
        def get(**kwargs):
            id = kwargs[table_id]
            try:
                if id == None:
                    query = sqlalchemy.select(self.__table_obj)
                    res = self.__db.execute(query).fetchall()
                else:
                    column_object = getattr(self.__table_obj.c, self.__id)
                    fields_to_select = []
                    for column in method['method_return']:
                        col = column.split(",")
                        fields_to_select.append(getattr(self.__table_obj.c, col[0]))
                    query = (sqlalchemy.select(*fields_to_select)
                             .where(column_object == int(id)))
                    res = self.__db.execute(query).fetchall()
                data = []
                for row in res:
                    temp = {}
                    for i in range(len(method['method_return'])):
                        col = method['method_return'][i].split(",")
                        temp[col[0]] = row[i]
                    data.append(temp)
                return data, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()

        return get

    def make_post(self, method, table_id, fields):
        def post(request):
            try:
                result = self.__db.execute(sqlalchemy.insert(self.__table_obj),[request])
                self.__db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_201()
            except Exception as err:
                return {"status": err}, self.__status.http_400()
        return post

    def make_put(self, method, table_id):
        def put(request, **kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(self.__table_obj.c, self.__id)
                result = self.__db.execute(sqlalchemy.update(self.__table_obj)
                                           .where(column_object == int(id)),[request])
                self.__db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()
        return put

    def make_delete(self, method, table_id):
        def delete(**kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(self.__table_obj.c, self.__id)
                result = self.__db.execute(sqlalchemy.delete(self.__table_obj)
                                           .where(column_object == int(id)))
                self.__db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()
        return delete

    def make_patch(self, method, table_id, fields):
        def patch(request, **kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(self.__table_obj.c, self.__id)
                result = self.__db.execute(sqlalchemy.update(self.__table_obj)
                                           .where(column_object == int(id)), [request])
                self.__db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()
        return patch

    def make_meta(self, method_data):
        meta = []
        for arg in method_data["method_recieve"]:
            arg_data = arg.split(',')
            arg_type = arg_data[1].split("(")
            if type(arg_type) == list:
                arg_type = arg_type[0]
            meta.append({
                "name":arg_data[0],
                "type":mapped_sqltypes[arg_type]
            })
        return meta

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
