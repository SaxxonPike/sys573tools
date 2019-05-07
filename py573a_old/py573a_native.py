import argparse
import base64
import hashlib
import json
import os
import struct
import sys

import database

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


def decrypt(data, key, scramble, counter):
    output_data = bytearray(len(data))

    data_len = len(data) // 2
    key_len = len(key)
    scramble_len = len(scramble)
    output_idx = 0

    for idx in range(0, data_len):
        output_word = 0
        cur_data = (data[(idx * 2) + 1] << 8) | data[(idx * 2)]

        for cur_bit in range(0, 8):
            even_bit_shift = (cur_bit * 2) & 0xff
            odd_bit_shift = (cur_bit * 2 + 1) & 0xff

            is_even_bit_set = int((cur_data & (1 << even_bit_shift)) != 0)
            is_odd_bit_set = int((cur_data & (1 << odd_bit_shift)) != 0)
            is_key_bit_set = int((key[idx % key_len] & (1 << cur_bit)) != 0)
            is_scramble_bit_set = int((scramble[idx % scramble_len] & (1 << cur_bit)) != 0)
            is_counter_bit_set = int((counter & (1 << cur_bit)) != 0)
            is_counter_bit_inv_set =  int(counter & (1 << ((7 - cur_bit) & 0xff)) != 0)

            if is_scramble_bit_set == 1:
                is_even_bit_set, is_odd_bit_set = is_odd_bit_set, is_even_bit_set

            if ((is_even_bit_set ^ is_counter_bit_inv_set ^ is_key_bit_set)) == 1:
                output_word |= 1 << even_bit_shift

            if (is_odd_bit_set ^ is_counter_bit_set) == 1:
                output_word |= 1 << odd_bit_shift

        output_data[output_idx] = (output_word >> 8) & 0xff
        output_data[output_idx+1] = output_word & 0xff
        output_idx += 2

        counter = (counter + 1) & 0xff

    return bytearray(output_data)


def encrypt(data, key, scramble, counter):
    output_data = bytearray(len(data))

    data_len = len(data) // 2
    key_len = len(key)
    scramble_len = len(scramble)
    output_idx = 0

    for idx in range(0, data_len):
        output_word = 0
        cur_data = (data[(idx * 2)] << 8) | data[(idx * 2) + 1]

        for cur_bit in range(0, 8):
            even_bit_shift = (cur_bit * 2) & 0xff
            odd_bit_shift = (cur_bit * 2 + 1) & 0xff

            is_even_bit_set = int((cur_data & (1 << even_bit_shift)) != 0)
            is_odd_bit_set = int((cur_data & (1 << odd_bit_shift)) != 0)
            is_key_bit_set = int((key[idx % key_len] & (1 << cur_bit)) != 0)
            is_scramble_bit_set = int((scramble[idx % scramble_len] & (1 << cur_bit)) != 0)
            is_counter_bit_set = int((counter & (1 << cur_bit)) != 0)
            is_counter_bit_inv_set =  int(counter & (1 << ((7 - cur_bit) & 0xff)) != 0)

            set_even_bit = is_even_bit_set ^ is_counter_bit_inv_set ^ is_key_bit_set
            set_odd_bit = is_odd_bit_set ^ is_counter_bit_set

            if is_scramble_bit_set == 1:
                set_even_bit, set_odd_bit = set_odd_bit, set_even_bit

            if set_even_bit == 1:
                output_word |= 1 << even_bit_shift

            if set_odd_bit == 1:
                output_word |= 1 << odd_bit_shift

        output_data[output_idx] = output_word & 0xff
        output_data[output_idx+1] = (output_word >> 8) & 0xff
        output_idx += 2

        counter = (counter + 1) & 0xff

    return bytearray(output_data)


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
        output_data = decrypt(data, key, scramble, counter)

    elif args.encrypt:
        output_data = encrypt(data, key, scramble, counter)

    with open(args.output, "wb") as outfile:
        outfile.write(output_data)
