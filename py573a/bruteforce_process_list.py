import argparse
import glob
import hashlib
import json
import os

import bruteforce_keys

from collections import OrderedDict
from multiprocessing import Pool

def read_database(filename="db.json"):
    db = json.load(open(filename))

    output = {}

    for entry in db:
        output[entry['sha1']] = entry

    return output


def read_database_keys(filename="process_list.json", input_db=None):
    db = json.load(open(filename))

    output = {}

    for entry in db:
        k = "%04x_%04x" % (int(str(entry['key1']), 0), int(str(entry['key2']), 0))

        if k not in output:
            output[k] = []

        if input_db:
            for k2 in input_db:
                if entry['filename'].lower() == input_db[k2]['filename'].lower().replace(".dat", ""):
                    entry['sha1'] = k2

        output[k].append(entry)

    return output


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

    print(fileinfo['filename'], sha1, counter)

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

    db = read_database(args.input_db)
    db_by_key = read_database_keys(args.input_list, input_db=db)
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

        # Find songs with the same key
        # k = "%04x_%04x" % (int(fileinfo['key1'], 0), int(fileinfo['key2'], 0))

        # for entry in db_by_key[k]:
        #     input_dat2 = os.path.join(args.input_dat, entry['filename'].upper() + ".DAT")
        #     print("%s %s %d" % (entry['filename'], get_sha1(input_dat2), int(entry['key3'], 0)))

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

        entry = OrderedDict([
            ("game", ""),
            ("artist", ""),
            ("title", ""),
            ("filename", keyinfo['filename'].upper() + ".DAT"),
            ("sha1", keyinfo['sha1']),
            ("status", "UNVERIFIED"),
            ("key", keyinfo['key']),
            ("scramble", keyinfo['scramble']),
            ("counter", int(str(keyinfo['key3']), 0)),
        ])

        db_json.append(entry)

    json.dump(db_json, open(args.output_db, "w"), indent=4)
