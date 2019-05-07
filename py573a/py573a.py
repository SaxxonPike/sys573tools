import argparse
import base64
import hashlib
import json
import os
import struct
import sys

import database
import enc573

DATABASE_FILENAME = "db.json"

db_loaded = None

def get_database(filename=DATABASE_FILENAME):
    global db_loaded

    if not db_loaded:
        db_loaded = database.read_database(filename)

    return db_loaded


def get_key_information(sha1):
    db = get_database()
    sha1 = sha1.upper()

    song = db.get(sha1, None)

    if song:
        if 'key' in song:
            return (bytearray(base64.b64decode(song['key'])), None, None)

        else:
            return (song['key1'], song['key2'], song['key3'])

    return (None, None, None)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', help='Input file', default=None)
    parser.add_argument('--output', help='Output file', default=None)
    parser.add_argument('--sha1', help='Force usage of a specific SHA-1 for encryption keys (optional)', default=None)

    parser.add_argument('--key1', help='Key 1 (optional)', default=None, type=int)
    parser.add_argument('--key2', help='Key 2 (optional)', default=None, type=int)
    parser.add_argument('--key3', help='Key 3 (optional)', default=None, type=int)

    args = parser.parse_args()

    if not args.input:
        parser.print_help(sys.stderr)
        exit(-1)

    if not os.path.exists(args.input):
        print("Could not find file:", args.input)
        exit(-1)

    if args.output is None:
        args.output = os.path.splitext(args.input)[0] + '.MP3'

    if os.path.dirname(args.output) and not os.path.exists(os.path.dirname(args.output)):
        os.makedirs(os.path.dirname(args.output))

    with open(args.input, "rb") as infile:
        data = infile.read()

    key1 = args.key1
    key2 = args.key2
    key3 = args.key3

    if key1 is None or key2 is None or key3 is None:
        sha1 = args.sha1
        if sha1 is None:
            m = hashlib.sha1()
            m.update(data)
            sha1 = m.hexdigest()

        if sha1 is None:
            raise Exception("A SHA-1 must be set to continue")

        print("Using SHA-1:", sha1)

        key1, key2, key3 = get_key_information(sha1)
        if key1 is None:
            raise Exception("Couldn't find key information for file with SHA-1 hash of %s" % (sha1))

    if isinstance(key1, int) and isinstance(key2, int) and isinstance(key3, int):
        output_data = enc573.decrypt(data, len(data) // 2, key1, key2, key3)

    else:
        output_data = enc573.decrypt_ddrsbm(data, len(data) // 2, key1, bytearray([key1[-1]]) + key1[:-1], len(key1))

    with open(args.output, "wb") as outfile:
        outfile.write(output_data)

    print("Saved to", args.output)


if __name__ == "__main__":
    main()