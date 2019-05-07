import json

def read_database(filename="db.json"):
    db = json.load(open(filename))

    output = {}
    if 'key_mapping' in db:
        # New database format
        for sha1 in db['key_mapping']:
            output[sha1] = {
                'sha1': sha1,
                'key': db['keys'][db['key_mapping'][sha1]]['key'],
                'scramble': db['keys'][db['key_mapping'][sha1]]['scramble'],
                'counter': db['keys'][db['key_mapping'][sha1]]['counter']
            }

    else:
        # Old database format
        for entry in db:
            output[entry['sha1']] = entry

    return output
