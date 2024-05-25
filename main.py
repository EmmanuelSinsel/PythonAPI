from server import Server, Http_status
import test_app.router as app
from generator import Database, Generator

status = Http_status()

api = Server(HOST="127.0.0.1", PORT=4201, SHOW_URLS=False)

db = Database(host="localhost"
              , port=3306
              , database="fim"
              , username="root"
              , password="piedras123"
              , db_type="mysql")

gen = Generator()

api.router.add_router(gen.build_all(database=db,
                                    prefix="local",
                                    ask_for_tables=False,
                                    ask_for_methods=False))

api.router.add_router(app.routes)

api.run()
