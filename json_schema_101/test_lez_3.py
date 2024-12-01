from jsonschema import validate
schema = {
    "type" : "object",
    "properties" : {
        "price" : {"type" : "number"},
        "name" : {"type" : "string"},
    },
}
# content of text tample.py
def func(x):
    return x +1

def test_answer():
    assert func(3) == 4

def test_jsonschema_invalid():
    # If no exception is raised by validate(), the instance is valid.
    assert validate_wrapper(instance={"name" : "Eggs", "price" : 34.99}, schema=schema) == True

def validate_wrapper(instance, schema):
    try:
        validate(instance = instance, schema = schema)
        return True
    except:
        return False


def test_function_output_with_snapshot(snapshot):
    snapshot.snapshot_dir = 'snapshots'  # This line is optional.
    pierino=func(5)
    pierino_stringa=str(pierino)
    snapshot.assert_match(pierino_stringa, 'foo_output.txt') 



frutti = """frutti,prezzo,colore,sapore
pera,75,verde,buono
mela,30,rosso,gucci
ananas,13,giallo, schifo
"""


def test_function_output_with_snapshot_csv(snapshot):
    snapshot.snapshot_dir = 'snapshots'  # This line is optional.
    snapshot.assert_match(frutti, 'frutti.csv') 


