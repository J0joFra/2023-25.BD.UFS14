from jsonschema import validate
schema = {
    "type": "object",
    "properties": {
        "price": {"type": "number"},
        "name": {"type": "string"},
    },
}

# content of test_template.py
def func(x):
    return x + 1

def test_answer():
    assert func(3) == 4

def test_jsonschema_invalid():
    assert validate_wrapper(instance={"name": "Eggs", "price": 34.99}, schema=schema) == True

def validate_wrapper(instance, schema):
    try:
        validate(instance=instance, schema=schema)
        return True
    except:
        return False

def test_function_output_with_snapshot(snapshot):
    snapshot.snapshot_dir = 'snapshots' 
    test_func = func(5)
    test_func_stringa = str(test_func)
    snapshot.assert_match(test_func_stringa, 'foo_output.txt')

veicoli = """veicolo,prezzo,colore,tipo
auto,20000,rosso,berlina
moto,15000,nero,sportiva
bicicletta,500,verde,urbana
"""

def test_function_output_with_snapshot_csv(snapshot):
    snapshot.snapshot_dir = 'snapshots' 
    snapshot.assert_match(veicoli, 'veicoli.csv')
