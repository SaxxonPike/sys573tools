import argparse
import base64
import glob
import hashlib
import json
import os

import bruteforce_keys
import database

from collections import OrderedDict
from multiprocessing import Pool

def get_sha1(filename):
    with open(filename, "rb") as infile:
        data = infile.read()
        m = hashlib.sha1()
        m.update(data)
        sha1 = m.hexdigest()

    return sha1


def process_entry(entry):
    fileinfo, input_dat, input_mp3, counter, output_key = entry

    if os.path.exists(output_key):
        return

    print("Processing", input_dat, input_mp3)
    key, scramble = bruteforce_keys.bruteforce_keys(input_dat, input_mp3, counter)

    if key == None or scramble == None:
        print("Couldn't find keys for", input_dat, "%02x" % counter)
        return

    print(fileinfo['filename'], counter)

    fileinfo['key'] = key
    fileinfo['scramble'] = scramble

    json.dump(fileinfo, open(output_key, "w"), indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-list', help='Input process list', required=True)
    parser.add_argument('--input-db', help='Input process list', required=True)
    parser.add_argument('--input-dat', help='Input ciphertext folder', required=True)
    parser.add_argument('--input-plain', help='Input plaintext folder', required=True)
    parser.add_argument('--output', help='Output keys folder for individual files', required=True)
    parser.add_argument('--output-db', help='Output database file', required=True)
    parser.add_argument('--cores', help='Number of cores to use', default=None)

    args = parser.parse_args()

    db = database.read_database(args.input_db)
    process_list = json.load(open(args.input_list))

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    bucket = []
    for fileinfo in process_list:
        input_dat = os.path.join(args.input_dat, fileinfo['filename'].upper() + ".DAT")
        input_mp3 = os.path.join(args.input_plain, fileinfo['filename'] + ".mp3")
        output_key = os.path.join(args.output, fileinfo['filename'] + ".json")

        if 'sha1' not in fileinfo:
            fileinfo['sha1'] = get_sha1(input_dat)

        sha1 = fileinfo['sha1']

        if sha1 in db:
            print("Already have key for %s, skipping..." % fileinfo['filename'])
            continue

        counter = int(str(fileinfo['key3']), 0)

        bucket.append((fileinfo, input_dat, input_mp3, counter, output_key))

    p = Pool(processes=int(args.cores) if args.cores else None) # Use as many cores as possible
    p.map(process_entry, bucket)

    # These shouldn't be in the database already so go ahead and add new entries
    json_files = glob.glob(os.path.join(args.output, "*.json"))
    db_json = json.load(open(args.input_db), object_pairs_hook=OrderedDict)
    for keyfile in json_files:
        keyinfo = json.load(open(keyfile))

        if isinstance(keyinfo['key1'], str):
            keyinfo['key1'] = int(keyinfo['key1'][2:], 16)

        if isinstance(keyinfo['key2'], str):
            keyinfo['key2'] = int(keyinfo['key2'][2:], 16)

        if isinstance(keyinfo['key3'], str):
            keyinfo['key3'] = int(keyinfo['key3'][2:], 16)

        key = "%04x_%04x_%02x" % (keyinfo['key1'], keyinfo['key2'], keyinfo['key3'])

        if key not in db_json['keys']:
            db_json['keys'][key] = OrderedDict([
                ("key", keyinfo['key']),
                ("scramble", keyinfo['scramble']),
                ("counter", int(str(keyinfo['key3']), 0)),
            ])

        else:
            rkey = db_json['keys'][key]['key']
            rscramble = bytearray(base64.b64decode(db_json['keys'][key]['scramble']))
            rscramble2 = bytearray(base64.b64decode(keyinfo['scramble']))

            for i in range(len(rscramble)):
                rscramble[i] |= rscramble2[i]

            db_json['keys'][key] = OrderedDict([
                ("key", rkey),
                ("scramble", base64.b64encode(rscramble).decode('ascii')),
                ("counter", int(str(keyinfo['key3']), 0)),
            ])

        db_json['key_mapping'][keyinfo['sha1'].upper()] = key

    json.dump(db_json, open(args.output_db, "w"), indent=4)
