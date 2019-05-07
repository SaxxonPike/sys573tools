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
        return (bytearray(base64.b64decode(song['key'])), bytearray(base64.b64decode(song['scramble'])), song['counter'])

    return (None, None, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', help='Input file', default=None)
    parser.add_argument('--output', help='Output file', default=None)
    parser.add_argument('--sha1', help='Force usage of a specific SHA-1 for encryption keys (optional)', default=None)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--decrypt', help='Decrypt input file', action='store_true')
    group.add_argument('--encrypt', help='Encrypt input file', action='store_true')

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

    sha1 = args.sha1
    if args.decrypt and sha1 is None:
        m = hashlib.sha1()
        m.update(data)
        sha1 = m.hexdigest()

    if sha1 is None:
        raise Exception("A SHA-1 must be set to continue")

    print("Using SHA-1:", sha1)

    key, scramble, counter = get_key_information(sha1)
    if key is None or scramble is None or counter is None:
        raise Exception("Couldn't find key information for file with SHA-1 hash of %s" % (sha1))

    if args.decrypt:
        output_data = enc573.decrypt(data, len(data) // 2, key, len(key), scramble, len(scramble), counter)

    elif args.encrypt:
        output_data = enc573.encrypt(data, len(data) // 2, key, len(key), scramble, len(scramble), counter)

    with open(args.output, "wb") as outfile:
        outfile.write(output_data)
