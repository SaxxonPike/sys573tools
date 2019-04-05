import argparse
import base64
import binascii
import itertools

import hexdump

import bruteforce
import enc573

def bruteforce_keys_ddrsbm(input_dat, counter, counter_step=1):
    input_dat = bytearray(open(input_dat, "rb").read()[0x40:0x63])
    input_plain = bytearray(b"\xff\xfb\x92\x64\x00\x00\x00\x00\x00\x69\x00\x00\x00\x00\x00\x00\x0d\x20\x00\x00\x00\x00\x00\x01\xa4\x00\x00\x00\x00\x00\x00\x34\x80\x00\x00")
    return bruteforce_keys(input_dat, input_plain, counter, counter_step)


def bruteforce_keys(input_dat, input_plain, counter, counter_step=1):

    if isinstance(input_dat, bytearray):
        data = input_dat

    else:
        data = open(input_dat, "rb").read()

    if isinstance(input_plain, bytearray):
        data_mp3 = input_plain

    else:
        data_mp3 = open(input_plain, "rb").read()

    min_size = min(len(data), len(data_mp3))
    data = data[:min_size]
    data = data[:min_size]

    key_build, scramble_build, likely_key_size = bruteforce.bruteforce_key(data, len(data), data_mp3, len(data_mp3), counter, counter_step)

    if key_build is None or scramble_build is None:
        return None, None

    key_build = key_build[:likely_key_size]
    scramble_build = scramble_build[:likely_key_size]

    if counter_step == 0:
        key_build = key_build[:0x10]
        scramble_pattern = bytearray([key_build[-1]]) + key_build[:-1]

    else:
        # Combine all scramble key parts that may be left over
        samples = [scramble_build[i:i + likely_key_size] for i in range(0, len(scramble_build), likely_key_size) if len(scramble_build[i:i + likely_key_size]) == likely_key_size]

        if len(samples) > 0:
            scramble_build = samples[0]

            for sample in samples[1:]:
                for idx, c in enumerate(sample):
                    scramble_build[idx] |= c

        # Find scramble key, reusing existing key to reduce the search space greatly.
        # Set cur_idx to a smaller number toward the end of the file for optimization reasons.
        # If the key is inaccurate, increase the amount of data to comb through here
        cur_idx = len(data_mp3) - (likely_key_size * 8)
        scramble_pattern = bruteforce.bruteforce_scramble_key(data, len(data), data_mp3, len(data_mp3), counter, cur_idx, key_build, scramble_build, counter_step)


    key = base64.b64encode(key_build).decode('ascii')
    scramble = base64.b64encode(scramble_pattern).decode('ascii')

    print("Key:", key)
    hexdump.hexdump(key_build)
    print()

    print("Scramble:", scramble)
    hexdump.hexdump(scramble_pattern)

    return key, scramble

def bruteforce_keys_counter(input_dat, input_plain):
    data = open(input_dat, "rb").read()
    data_mp3 = open(input_plain, "rb").read()

    min_size = min(len(data), len(data_mp3))
    data = data[:min_size]
    data = data[:min_size]

    key_build, scramble_build, likely_key_size, counter = bruteforce.bruteforce_key_counter(data, len(data), data_mp3, len(data_mp3))
    key_build = key_build[:likely_key_size]
    scramble_build = scramble_build[:likely_key_size]

    # Combine all scramble key parts that may be left over
    samples = [scramble_build[i:i + likely_key_size] for i in range(0, len(scramble_build), likely_key_size) if len(scramble_build[i:i + likely_key_size]) == likely_key_size]

    if len(samples) > 0:
        scramble_build = samples[0]

        for sample in samples[1:]:
            for idx, c in enumerate(sample):
                scramble_build[idx] |= c

    # Find scramble key, reusing existing key to reduce the search space greatly.
    # Set cur_idx to a smaller number toward the end of the file for optimization reasons.
    # If the key is inaccurate, increase the amount of data to comb through here
    cur_idx = len(data_mp3) - (likely_key_size * 8)
    scramble_pattern = bruteforce.bruteforce_scramble_key(data, len(data), data_mp3, len(data_mp3), counter, cur_idx, key_build, scramble_build)

    key = base64.b64encode(key_build).decode('ascii')
    scramble = base64.b64encode(scramble_pattern).decode('ascii')

    print("Key:", key)
    hexdump.hexdump(key_build)
    print()

    print("Scramble:", scramble)
    hexdump.hexdump(scramble_pattern)

    return key, scramble


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-dat', help='Input ciphertext file', required=True)
    parser.add_argument('--input-plain', help='Input plaintext file', required=True)
    parser.add_argument('--counter', help='Counter value', type=lambda x: int(x, 0), required=True)

    args = parser.parse_args()

    bruteforce_keys(args.input_dat, args.input_plain, args.counter)
