from sqlalchemy import BIGINT, BOOLEAN, DATE, DATETIME, Enum
from sqlalchemy import DOUBLE, FLOAT, INTEGER, Interval, LargeBinary
from sqlalchemy import NUMERIC, PickleType, SMALLINT, String, TEXT, TIME
from sqlalchemy import Unicode, UnicodeText, UUID, ARRAY, BINARY
from sqlalchemy import BLOB, CHAR, DECIMAL, DOUBLE_PRECISION, CLOB
from sqlalchemy import JSON, NCHAR, NVARCHAR, REAL, TIMESTAMP
from sqlalchemy import VARBINARY, VARCHAR
sqltypes = {
    "ARRAY": ARRAY,
    "BIGINT": BIGINT,
    "BINARY": BINARY,
    "BLOB": BLOB,
    "BOOLEAN": BOOLEAN,
    "CHAR": CHAR,
    "CLOB": CLOB,
    "DATE": DATE,
    "DATETIME": DATETIME,
    "DECIMAL": DECIMAL,
    "DOUBLE": DOUBLE,
    "DOUBLE_PRECISION": DOUBLE_PRECISION,
    "FLOAT": FLOAT,
    "INT": INTEGER,
    "JSON": JSON,
    "INTEGER": INTEGER,
    "NCHAR": NCHAR,
    "NVARCHAR": NVARCHAR,
    "NUMERIC": NUMERIC,
    "REAL": REAL,
    "SMALLINT": SMALLINT,
    "TEXT": TEXT,
    "TIME": TIME,
    "TIMESTAMP": TIMESTAMP,
    "UUID": UUID,
    "VARBINARY": VARBINARY,
    "VARCHAR": VARCHAR,
    "LONGBLOB": LargeBinary,
    "TINYINT": INTEGER,
    "LONGTEXT": TEXT
}

mapped_sqltypes = {
    "ARRAY": str,
    "BIGINT": int,
    "BINARY": str,
    "BLOB": str,
    "BOOLEAN": bool,
    "CHAR": str,
    "CLOB": str,
    "DATE": str,
    "DATETIME": str,
    "DECIMAL": float,
    "DOUBLE": float,
    "DOUBLE_PRECISION": float,
    "FLOAT": float,
    "INT": int,
    "JSON": str,
    "INTEGER": int,
    "NCHAR": str,
    "NVARCHAR": str,
    "NUMERIC": int,
    "REAL": float,
    "SMALLINT": int,
    "TEXT": str,
    "TIME": str,
    "TIMESTAMP": str,
    "UUID": str,
    "VARBINARY": str,
    "VARCHAR": str,
    "LONGBLOB": str,
    "TINYINT": int,
    "LONGTEXT": str
}