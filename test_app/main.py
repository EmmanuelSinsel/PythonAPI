from APY.server.server import Server, Http_status
from APY.generator.generator import Database, Generator

status = Http_status()

api = Server(HOST="127.0.0.1", PORT=4201, SHOW_URLS=True)

db = Database(host="localhost"
              , port=3306
              , database="jucuas"
              , username="root"
              , password="piedras123"
              , db_type="mysql")

gen = Generator()

api.router.add_router(gen.build_all(database=db,
                                    prefix="local",
                                    ask_for_tables=False,
                                    ask_for_methods=False))

def test(a: int):
    return a, status.http_200()


api.router.add_get(function=test, url="test")


api.run()
