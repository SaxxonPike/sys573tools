import argparse
import base64
import binascii
import itertools

import hexdump

import bruteforce
import enc573

def bruteforce_keys(input_dat, input_plain, counter):
    data = open(input_dat, "rb").read()
    data_mp3 = open(input_plain, "rb").read()

    min_size = min(len(data), len(data_mp3))
    data = data[:min_size]
    data = data[:min_size]

    key_build, scramble_build, likely_key_size = bruteforce.bruteforce_key(data, len(data), data_mp3, len(data_mp3), counter)

    if key_build is None or scramble_build is None:
        return None, None

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
