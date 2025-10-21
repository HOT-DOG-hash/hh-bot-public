import pathlib
import sys

base_dir = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(base_dir))

from backend.app.models import Base

_tables = list(Base.metadata.tables.keys())
print("OK, tables:", _tables)
assert "users" in _tables and "resumes" in _tables, "ожидались таблицы users/resumes"
