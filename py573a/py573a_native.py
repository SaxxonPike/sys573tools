import argparse
import base64
import hashlib
import json
import os
import struct
import sys

DATABASE_FILENAME = "db.json"

def get_database(filename=DATABASE_FILENAME):
    return json.load(open(filename, "r"), encoding="utf-8")


def get_key_information(sha1):
    db = get_database()
    sha1 = sha1.lower()

    # key = "FClQzbcWBFOZBW5hG6P36/uCJQKjYzT+YqWq0Gg8EG0UYK0MXAvBXf/wijJmzduiTNR1o/Q+oi0iWOC0JW4XKx++WA/FWbu0znYiYMG4FEXkhdIYhA0CeMCUTLjB65c2bTrwbLi3zXUhK3MKEAGgKH+1KRcYYtqO"
    # scramble = "VQ5vGtSDj6ql9gQ4LQZ8fXMSwSZxY0ZJGrGNmLPJPpj5HrDnBiMsfx4iNxxmJcan4wZRLgsEV2NfSmEb/jRVD7PkbUhHFIi0oYrwIaLDahxLdlNcD9bq/9Su3BR1QmE2rYiH1CQYDSZcMKHAAYrdcldYC7KOm7DK"
    # counter = 0x82

    # key = "oFrxsixVGM5ijfJgCB03/gRkJwNrJvBc9IsZccPDCvDMj36Y1QOvP0DSujFmr1WLyJEDTpg0YR6M5KRJgHq19ujdkEbqlep4EAw0/QdGBSMvYrQYME/dtUvbEujdnn269yGNH2DymnWia5EDQIkSX4klYh2P54Zp"
    # scramble = "cjCJ12s2HQtGISkUTxKMufsWSDWDqL7zDgY7YCjR5KbotsUvBBJfd39CGfs6D00eQEBIY3U4vLSJ0mRkUROr9W9yWU8C4enUj5qUoeMHWRahipzRCgI/ZGwRJGZgPt0+FQNOVFxhOtk+C0laBIDA6/2wpKyRynVH"
    # counter = 0xe6

    # key = "7LcPWzaAzJ0/LnHO1Bnv1o16nPFHC3OHliwZf7JE"
    # scramble = "FEZtFwQiT1ZMMaeq1eej57XGKToccQOr1k02iLr+"
    # counter = 0xef

    key = "I971Ch1y5OE8EI82if+XTrNnmHAfdoxRgh1b5JIF"
    scramble = "FntfBoH6OfaBrtNHfAPvXzLpsMizj7/IGGUONUpZ"
    counter = 0x45

    return (bytearray(base64.b64decode(key)), bytearray(base64.b64decode(scramble)), counter)#song['counter'])

    for song in db:
        if song['sha1'].lower() == sha1:
            return (bytearray(base64.b64decode("oVvzsCxVGM5iifZkDB0/9gx0NwNrJvBc1Ks5UcOD")), bytearray(base64.b64decode("EiCJkQAgHAgAISkACxAIgGEQSCGDMAxCDAArYACR")), 0xe6)#song['counter'])

    return (None, None, None)


def print_database_list():
    db = get_database()

    for song in db:
        info = ""

        if song['title'] and song['artist']:
            info = "%s - %s" % (song['artist'], song['title'])

        elif song['title']:
            info = song['title']

        elif song['artist']:
            info = song['artist']

        print(song['game'], song['filename'], song['sha1'], info)


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
    group.add_argument('--list', help='List all songs in database', action='store_true')

    args = parser.parse_args()

    if args.list:
        print_database_list()
        exit(1)

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

    import hexdump
    hexdump.hexdump(key)
    print()
    hexdump.hexdump(scramble)

    if args.decrypt:
        output_data = decrypt(data, key, scramble, counter)

    elif args.encrypt:
        output_data = encrypt(data, key, scramble, counter)

    with open(args.output, "wb") as outfile:
        outfile.write(output_data)
