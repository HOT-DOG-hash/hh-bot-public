import pathlib
import sys

sys.path.append(str(pathlib.Path("migrations").resolve().parent))

from backend.app.models import Base
tables = list(Base.metadata.tables.keys())
print("OK, tables:", tables)
assert "users" in tables and "resumes" in tables, "Метаданные не видят модели user/resume"
