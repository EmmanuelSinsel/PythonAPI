from server import Server, Http_status
import test_app.router as app
from generator import Database, Generator

status = Http_status()

api = Server(HOST="127.0.0.1", PORT=4201)
api.MAX_REQUEST_SIZE = 30

db = Database(host="localhost"
              , port=3306
              , database="fim"
              , username="root"
              , password="piedras123"
              , db_type="mysql")

gen = Generator(database=db)

#gen.get_tables_metadata()
api.router.add_router(gen.build("usuarios"))

api.router.add_router(app.routes)

api.router.add_page("tavio", "docs.html")

api.run()
