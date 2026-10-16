"""Valida todos os JSON do relatório contra os schemas oficiais (clone de microsoft/json-schemas)."""
import json, os, sys, glob
from referencing import Registry, Resource
from jsonschema import Draft7Validator

if len(sys.argv) < 3:
    sys.exit("Uso: python validar.py <pasta_do_relatorio> <pasta_clone_de_microsoft/json-schemas>")
SCHEMAS = sys.argv[2]
PREFIX = "https://developer.microsoft.com/json-schemas/"

def retrieve(uri):
    if uri.startswith(PREFIX):
        path = os.path.join(SCHEMAS, uri[len(PREFIX):])
        with open(path) as f:
            return Resource.from_contents(json.load(f))
    raise LookupError(uri)

registry = Registry(retrieve=retrieve)
root = sys.argv[1]
erros = 0; n = 0
for path in glob.glob(os.path.join(root, "**", "*.json"), recursive=True) + glob.glob(os.path.join(root, "**", "*.pbir"), recursive=True):
    data = json.load(open(path, encoding="utf-8"))
    sch = data.get("$schema") if isinstance(data, dict) else None
    if not sch or not sch.startswith(PREFIX):
        continue
    try:
        schema = retrieve(sch).contents
    except Exception as e:
        print("SEM SCHEMA LOCAL:", path, sch); continue
    v = Draft7Validator(schema, registry=registry)
    errs = list(v.iter_errors(data))
    n += 1
    for e in errs[:5]:
        erros += 1
        print(f"ERRO {os.path.relpath(path, root)}: {'/'.join(map(str, e.absolute_path))}: {e.message[:300]}")
print(f"{n} arquivos validados, {erros} erros")
