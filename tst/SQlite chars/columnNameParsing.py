import os
import codecs
import sqlite3 as dbapi

THIS_ROOT = os.path.dirname(os.path.realpath(__file__))
REGISTERS_DB_PATH = os.path.join(THIS_ROOT,'Registers2017_fake.sqlite3')

def quote_identifier(s, errors="strict"):
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""
    


def test_identifier(identifier):
    "Tests an identifier to ensure it's handled properly."
    conn = dbapi.connect(location=REGISTERS_DB_PATH,detect_types=dbapi.PARSE_DECLTYPES)
    cur=conn.cursor()
    cur.execute("CREATE TABLE " + quote_identifier(identifier) + " (foo)")
    assert identifier == c.execute("SELECT name FROM SQLITE_MASTER").fetchone()[0]

print(quote_identifier("%")) # works
quote_identifier("???") # works
quote_identifier(chr(0x20000)) # works

print(quote_identifier("Fo\x00o!", "replace")) # prints "Fo?o!"
print(quote_identifier("Fo\x00o!", "ignore")) # prints "Foo!"
