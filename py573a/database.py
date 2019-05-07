import json

def get_hex(input):
    if isinstance(input, int):
        return input

    input = input[2:] if input.startswith("0x") else input
    return int(input, 16)


def read_database(filename="db.json"):
    db = json.load(open(filename))

    output = {}
    for sha1 in db['key_mapping']:
        if isinstance(db['key_mapping'][sha1], str) and db['key_mapping'][sha1] in db.get('keys', {}):
            output[sha1] = {
                'sha1': sha1,
                'key': db['keys'][db['key_mapping'][sha1]]
            }

        else:
            k = db['key_mapping'][sha1]
            output[sha1] = {
                'sha1': sha1,
                'key1': get_hex(k[0]),
                'key2': get_hex(k[1]),
                'key3': get_hex(k[2])
            }

    return output
