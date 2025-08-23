import sys, pathlib
sys.path.append(str(pathlib.Path("migrations").resolve().parent))

from app.models import Base
tables = list(Base.metadata.tables.keys())
print("OK, tables:", tables)
assert "user" in tables and "resume" in tables, "Метаданные не видят модели user/resume"
