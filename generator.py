import datetime

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.schema import ForeignKey
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
            params = ("postgresql+psycopg2://" + self.__username + ":" + self.__password + "@"
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
        try:
            print("Testing connection to " + db_type + " database on " + self.__host + ":" + str(self.__port))
            db = self.connection()
            db.execute(text('SELECT 1'))
            print('Connection successful')
            db.close()
        except:
            print("An error has ocurred while connecting to database")
            self.__database = None
            self.__engine = None

    def connection(self):
        db = sessionmaker(bind=self.__engine)
        conn = db()
        return conn

    def engine(self):
        return self.__engine


class Generator:
    __debug: bool = False

    def __init__(self, debug: bool = False):
        self.__debug = debug

    def build(self, database: Database, table: str, prefix: str, ask_for_methods: bool = None):
        engine = database.engine()
        if engine and database:
                if self.__debug:
                    print("Generating methods for table " + table)
                md = sqlalchemy.MetaData()
                self.check_generated(table=table, engine=engine)
                db_folder = engine.url.database + "-" + engine.url.drivername + "-" + engine.url.host
                f = open("./generated/" + db_folder + "/" + table + ".apy", "r")
                columns = None
                autoincrement = True
                if f.read() == '':
                    columns = self.discover_fields(table=table, metadata=md, engine=engine)
                methods = Methods(database=database,
                                  table=table,
                                  fields=columns,
                                  prefix=prefix,
                                  ask_for_methods=ask_for_methods)
                if self.__debug:
                    print("Succesful")
                return methods.generated


    def check_ask_for_tables(self):
        print("Do you want to pick specific tables for the generator? (y-yes, n-no) > ", end="")
        answer = input()
        while answer not in ["y", "yes", "n", "no"]:
            answer = input()
        if answer in ["y", "yes"]:
            return True
        else:
            return False

    def check_ask_for_methods(self):
        print("Do you want to pick specific methods for each table for the generator? (y-yes, n-no) > ", end="")
        answer = input()
        while answer not in ["y", "yes", "n", "no"]:
            answer = input()
        if answer in ["y", "yes"]:
            return True
        else:
            return False

    def build_all(self, database: Database,
                  prefix: str = None,
                  ask_for_tables: bool = None,
                  ask_for_methods: bool = None):
        engine = database.engine()
        if engine and database:
            first_time = False
            db_folder = engine.url.database + "-" + engine.url.drivername + "-" + engine.url.host
            if not os.path.exists("./generated/" + db_folder):
                first_time = True
            if ask_for_tables is None and not os.path.exists("./generated/" + db_folder):
                ask_for_tables = self.check_ask_for_tables()
            if ask_for_methods is None and ask_for_tables == True:
                ask_for_methods = self.check_ask_for_methods()
            from sqlalchemy import inspect
            inspector = inspect(engine)
            schemas = inspector.get_table_names()
            counter = 0
            methods = Router()
            if self.__debug:
                print("Using host: " + engine.url.host)
                print("Generating pack of methods for database: " + engine.url.database)
            for table in schemas:
                if ask_for_tables:
                    if not os.path.exists("./generated/" + db_folder + "/" + table + ".apy") and ask_for_tables:
                        print("Do you want include the table '" + table + "' in the generator? (y-yes, n-no) > ",
                              end="")
                        answer = input()
                        while answer not in ["y", "yes", "n", "no"]:
                            answer = input()
                        if answer in ["y", "yes"]:
                            methods.add_router(self.build(table=table,
                                                          database=database,
                                                          prefix=prefix,
                                                          ask_for_methods=ask_for_methods))
                else:
                    if os.path.exists("./generated/" + db_folder + "/" + table + ".apy") or first_time:
                        methods.add_router(self.build(table=table,
                                                      database=database,
                                                      prefix=prefix,
                                                      ask_for_methods=ask_for_methods))
            print("Method generation finished succesfuly")
            return methods

    def discover_fields(self, table: str, metadata: sqlalchemy.MetaData, engine: Database.engine):
        obj_table = sqlalchemy.Table(table,
                                 metadata,
                                 autoload_with=engine)
        ai = False
        if obj_table.autoincrement_column is not None:
            ai = obj_table.autoincrement_column.name
        cols = []
        columns = obj_table.columns
        for c in columns:
            has_fk = False
            fk = None
            if c.foreign_keys:
                has_fk = True
                fk = list(c.foreign_keys)[0].column
            ai_flag = False
            if ai:
                if ai == c.name:
                    ai_flag = True
            cols.append({
                "column": c.name,
                "type": c.type,
                "pk": c.primary_key,
                "ai": ai_flag,
                "fk": has_fk,
                "fk_field": fk
            })
        return cols

    def check_generated(self, table: str, engine: Database.engine):
        db_folder = engine.url.database + "-" + engine.url.drivername + "-" + engine.url.host
        if not os.path.exists("./generated"):
            os.mkdir("./generated")
        if not os.path.exists("./generated/" + db_folder):
            os.mkdir("./generated/" + db_folder)
        if not os.path.exists("./generated/" + db_folder + "/" + table + ".apy"):
            f = open("./generated/" + db_folder + "/" + table + ".apy", "x")
            f.close()


class Methods:
    generated = None
    __status = Http_status()
    __md = None
    __engine = None

    def __init__(self, database: Database, table: str, fields: list, prefix: str, ask_for_methods: bool):
        self.__md = sqlalchemy.MetaData()
        self.__engine = database.engine()
        table_id = None
        if fields is not None:
            table_id = self.found_id(fields=fields)
        method_data = self.read_api_files(table_id=table_id,
                                          table=table,
                                          columns=fields,
                                          engine=database.engine(),
                                          ask_for_methods=ask_for_methods)
        if fields is None:
            fields, table_id = self.extract_fields(data=method_data)
        table_obj, columns = self.generate_table_objects(table=table,
                                                         fields=fields,
                                                         table_id=table_id)
        self.generated = Router(prefix=prefix + "/" + table)
        methods_data = self.extract_methods_data(data=method_data)
        self.generate(methods_data=methods_data,
                      table_id=table_id,
                      fields=fields,
                      db=database.connection(),
                      table_obj=table_obj)

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
                "ai": col_info[3],
                "fk": col_info[4],
                "fk_field": col_info[5],
            })
            if col_info[2] == "True":
                table_id = col_info[0]
        return fields, table_id

    def extract_methods_data(self, data: str):
        methods = []
        while data != '' and data != '\n':
            begin = data.find("BEGIN") + 5
            end = data.find("END")
            method = data[begin:end]
            method = method[1:-1]
            method = method.replace('\t', '')
            method_raw = method.split('\n')
            if method_raw[-1] == '':
                method_raw.pop()
            recieve_index = method_raw.index("RECIEVE")
            json_index = method_raw.index("JSON")
            return_index = method_raw.index("RETURN")
            method_type = method_raw[0]
            method_name = method_raw[2]
            method_recieve = method_raw[recieve_index + 1:json_index]
            method_json = method_raw[json_index + 1:return_index]
            method_return = method_raw[return_index + 1:]
            methods.append({
                "method_type": method_type,
                "method_name": method_name,
                "method_recieve": method_recieve,
                "method_json": method_json,
                "method_return": method_return
            })
            data = data[end + 3:]
        return methods

    def generate_table_objects(self, table, fields, table_id):
        try:
            meta = MetaData()
            attributes = [table, meta]
            columns = []
            for i in fields:
                columns.append(i['column'])
                div = str(i['type']).split('(')
                i['type'] = div[0]
                new_column = None
                if i["column"] == table_id:
                    new_column = (Column(i['column'],
                                         sqltypes[i['type']],
                                         primary_key=True,
                                         )
                                  )
                else:
                    new_column = (Column(i['column'],
                                         type_=sqltypes[i['type']],
                                         )
                                  )
                attributes.append(new_column)
            return Table(*attributes), attributes[2:]
        except Exception as err:
            print("TABLE OBJECT",str(err))

    def check_ask_for_methods(self, table, method_type):
        print("Do you want to include the method type " + method_type +
              " for the table '" + table + "'? (y-yes, n-no) > ", end="")
        answer = input()
        while answer not in ["y", "yes", "n", "no"]:
            answer = input()
        if answer in ["y", "yes"]:
            return True
        else:
            return False

    def read_api_files(self, table_id, table, columns, engine, ask_for_methods):
        db_folder = engine.url.database + "-" + engine.url.drivername + "-" + engine.url.host
        f = open("./generated/" + db_folder + "/" + table + ".apy", "r")
        ask_response = None
        if f.read() == '':
            f.close()
            fw = open("./generated/" + db_folder + "/" + table + ".apy", "a")
            # DATOS DE LA TABLA
            fw.write("TABLE\n")
            fw.write(table + "\n")
            fw.write("COLUMNS\n")
            for c in columns:
                fw.write(
                    "\t" + str(c['column']) + "," +
                    str(c['type']) + "," +
                    str(c['pk']) + "," +
                    str(c['ai']) + "," +
                    str(c['fk']) + "," +
                    str(c['fk_field']) + "\n")
            # METODO GET
            if ask_for_methods:
                ask_response = self.check_ask_for_methods(table=table, method_type="GET")
            if ask_response or ask_for_methods is False:
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
            if ask_for_methods:
                ask_response = self.check_ask_for_methods(table=table, method_type="CREATE")
            if ask_response or ask_for_methods is False:
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
            if ask_for_methods:
                ask_response = self.check_ask_for_methods(table=table, method_type="PUT")
            if ask_response or ask_for_methods is False:
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
            if ask_for_methods:
                ask_response = self.check_ask_for_methods(table=table, method_type="DELETE")
            if ask_response or ask_for_methods is False:
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
            if ask_for_methods:
                ask_response = self.check_ask_for_methods(table=table, method_type="PATCH")
            if ask_response or ask_for_methods is False:
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
        f = open("./generated/" + db_folder + "/" + table + ".apy", "r")
        method_data = f.read()
        f.close()
        return method_data

    def generate(self, methods_data, table_id, fields, db, table_obj):
        for method in methods_data:
            if method['method_type'] == 'GET':
                get = self.make_get(method=method, table_id=table_id, db=db, table_obj=table_obj, fields=fields)
                meta = self.make_meta(method_data=method, table_obj=table_obj)
                self.generated.add_get(function=get,
                                       url=method['method_name'],
                                       meta=meta)

            if method['method_type'] == 'POST':
                post = self.make_post(method=method, db=db, table_obj=table_obj)
                meta = self.make_meta(method_data=method, table_obj=table_obj)
                self.generated.add_post(function=post,
                                        url=method['method_name'],
                                        meta=meta)

            if method['method_type'] == 'PUT':
                put = self.make_put(method=method, table_id=table_id, db=db, table_obj=table_obj)
                meta = self.make_meta(method_data=method, table_obj=table_obj)
                self.generated.add_put(function=put,
                                       url=method['method_name'],
                                       meta=meta)

            if method['method_type'] == 'DELETE':
                delete = self.make_delete(method=method, table_id=table_id, db=db, table_obj=table_obj)
                meta = self.make_meta(method_data=method, table_obj=table_obj)
                self.generated.add_delete(function=delete,
                                          url=method['method_name'],
                                          meta=meta)

            if method['method_type'] == 'PATCH':
                patch = self.make_patch(method=method, table_id=table_id, db=db, table_obj=table_obj)
                meta = self.make_meta(method_data=method, table_obj=table_obj)
                self.generated.add_patch(function=patch,
                                         url=method['method_name'],
                                         meta=meta)

    def extend_foreign_key(self, table, column, value, db):
        fk_table = Table(table, self.__md, autoload_with=self.__engine)
        column_object = getattr(fk_table.c, column)
        query = sqlalchemy.select(fk_table).where(column_object == value)
        res = db.execute(query).first()
        if res:
            data = {}
            columns = list(fk_table.columns)
            for row in range(len(res)):
                final_row = res[row]
                if type(res[row]) == datetime.datetime:
                    final_row = res[row].strftime("%m/%d/%Y, %H:%M:%S")
                data[columns[row].name] = final_row
            return data
        else:
            return value


    def make_get(self, method, table_id, db, table_obj, fields):
        def get(**kwargs):
            id = None
            if table_id in kwargs:
                id = kwargs[table_id]
            try:
                if id == None:
                    query = sqlalchemy.select(table_obj)
                    res = db.execute(query).fetchall()
                else:
                    column_object = getattr(table_obj.c, table_id)
                    fields_to_select = []
                    for column in method['method_return']:
                        col = column.split(",")
                        fields_to_select.append(getattr(table_obj.c, col[0]))

                    query = (sqlalchemy.select(*fields_to_select)
                             .where(column_object == int(id)))
                    res = db.execute(query).fetchall()
                # EXTEND FOREIGN KEYS
                fk_data = {}
                for fk in fields:
                    if fk['fk'] == "True":
                        temp_fk = str(fk['fk_field'].split("."))
                data = []
                for row in res:
                    temp = {}
                    for i in range(len(method['method_return'])):
                        final_row = row[i]
                        col = method['method_return'][i].split(",")
                        for field in fields:
                            if field['column'] == col[0] and field['fk'] == "True":
                                fk_data = field['fk_field'].split(".")
                                final_row = self.extend_foreign_key(table=fk_data[0],
                                                                    column=fk_data[1],
                                                                    value=row[i],
                                                                    db=db)
                        if type(row[i]) == datetime.datetime:
                            final_row = row[i].strftime("%m/%d/%Y, %H:%M:%S")
                        temp[col[0]] = final_row
                    data.append(temp)
                return data, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()
        return get

    def make_post(self, method, db, table_obj):
        def post(request):
            try:
                result = db.execute(sqlalchemy.insert(table_obj), [request])
                db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_201()
            except Exception as err:
                return {"status": err}, self.__status.http_400()

        return post

    def make_put(self, method, table_id, db, table_obj):
        def put(request, **kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(table_obj.c, table_id)
                result = db.execute(sqlalchemy.update(table_obj)
                                    .where(column_object == int(id)), [request])
                db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()

        return put

    def make_delete(self, method, table_id, db, table_obj):
        def delete(**kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(table_obj.c, table_id)
                result = db.execute(sqlalchemy.delete(table_obj)
                                    .where(column_object == int(id)))
                db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()

        return delete

    def make_patch(self, method, table_id, db, table_obj):
        def patch(request, **kwargs):
            try:
                id = kwargs[table_id]
                column_object = getattr(table_obj.c, table_id)
                result = db.execute(sqlalchemy.update(table_obj)
                                    .where(column_object == int(id)), [request])
                db.commit()
                ret = method['method_return'][0].split(',')
                return {"status": ret[0]}, self.__status.http_200()
            except Exception as err:
                return {"status": err}, self.__status.http_400()

        return patch

    def make_meta(self, method_data, table_obj):
        meta_recieve = []
        meta_json = []
        meta_returns = []
        for arg in method_data["method_recieve"]:
            arg_data = arg.split(',')
            arg_type = arg_data[1].split("(")
            if type(arg_type) == list:
                arg_type = arg_type[0]
            meta_recieve.append({
                "name": arg_data[0],
                "type": mapped_sqltypes[arg_type]
            })
        for arg in method_data["method_json"]:
            arg_data = arg.split(',')
            arg_type = arg_data[1].split("(")
            if type(arg_type) == list:
                arg_type = arg_type[0]
            meta_json.append({
                "name": arg_data[0],
                "type": mapped_sqltypes[arg_type]
            })
        meta = {
            "recieve": meta_recieve,
            "json": meta_json,
            "return": meta_returns,
            "table": table_obj
        }
        return meta

    def found_id(self, fields):
        for item in fields:
            if "ID" in str.upper(item['column']) and item['pk'] is True:
                return item['column']
            if "ID" in str.upper(item['column']):
                return item['column']
            if item['pk'] is True:
                return item['column']
            else:
                return False
