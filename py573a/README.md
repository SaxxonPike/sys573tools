# py573a

A Python recreation of 573a.jar with less Java, less GUI, less obfuscation, less encryption, and less Shiba Inus.

## Usage

```
usage: py573a.py [-h] [--input INPUT] [--output OUTPUT] [--sha1 SHA1]
                 (--decrypt | --encrypt | --list)

optional arguments:
  -h, --help       show this help message and exit
  --input INPUT    Input file
  --output OUTPUT  Output file
  --sha1 SHA1      Force usage of a specific SHA-1 for encryption keys
                   (optional)
  --decrypt        Decrypt input file
  --encrypt        Encrypt input file
  --list           List all songs in database
```

Without `--output (filename.mp3)` being specified, it will automatically output a file in the same location as input.dat/.mp3 with a .mp3/.dat extension.

### Decryption
Decrypt a DAT file. The correct key is determined by the SHA-1 hash of the file. You can manually specify the SHA-1, or else the program will automatically calculate the SHA-1 hash of the input file. The SHA-1 hash must exist in the database for decryption to be possible.

```
python py573a.py --decrypt --input input.dat
```


### Encryption
Encrypt a replacement MP3 file using an existing key. The SHA-1 must exist in the database for encryption to be possible.

```
python py573a.py --encrypt --input input.mp3 --output test.dat --sha1 0123456789abcdef0123456789abcdef01234567
```


### List
List mode displays a list of all songs in the database. You could also open db.json directly to view the same information.

```
python py573a.py --list
```
