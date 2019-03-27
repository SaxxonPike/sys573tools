import argparse
import json
import os
import struct
import sys

def get_hex(input):
    if isinstance(input, int):
        return input

    input = input[2:] if input.startswith("0x") else input
    return int(input, 16)


def get_folder_type(path, filename):
    path = path.lower()
    filename = filename.lower()

    for found_filename in os.listdir(os.path.join(path, "DYNAMIC")):
        found_filepath = os.path.join(path, "DYNAMIC", found_filename)
        if found_filename.lower() == filename and os.path.isfile(found_filepath):
            return 1

    for found_filename in os.listdir(os.path.join(path, "STATIC")):
        found_filepath = os.path.join(path, "STATIC", found_filename)
        if found_filename.lower() == filename and os.path.isfile(found_filepath):
            return 0

    return None


def generate_da_list(input_folder, dec_list):
    with open(os.path.join(input_folder, "DATA0", "DA_LIST.BIN"), "wb") as outfile:
        for fileinfo in sorted(dec_list, key=lambda x:x['filename']):
            folder_type = get_folder_type(os.path.join(input_folder, "DATA0"), fileinfo['filename'] + ".DAT")

            if not folder_type:
                print("Couldn't find", fileinfo['filename'])
                continue

            outfile.write(struct.pack("<H", folder_type))
            outfile.write(fileinfo['filename'].encode('ascii'))
            outfile.write(b'\0' * (10 - len(fileinfo['filename'].encode('ascii'))))


def generate_dec_list(input_folder, dec_list):
    with open(os.path.join(input_folder, "DATA5", "DEC_LIST.BIN"), "wb") as outfile:
        outfile.write(struct.pack("<I", len(dec_list)))

        for fileinfo in dec_list:
            outfile.write(struct.pack("<HHH", get_hex(fileinfo['key1']), get_hex(fileinfo['key2']), get_hex(fileinfo['key3'])))
            outfile.write(fileinfo['filename'].encode('ascii'))
            outfile.write(b'\0' * (64 - len(fileinfo['filename'].encode('ascii'))))

        outfile.write(b'\0' * (16 - (outfile.tell() % 16)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--data', help='Input game data path', required=True)
    parser.add_argument('--list', help='Input JSON decryption list', required=True)

    args = parser.parse_args()

    dec_list = json.load(open(args.list))

    generate_da_list(args.data, dec_list)
    generate_dec_list(args.data, dec_list)
