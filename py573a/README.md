# py573a

A Python recreation of 573a.jar with less Java, less GUI, less obfuscation, less encryption, and less Shiba Inus.

py573a.py requires Cython. Build the required files using `python setup.py build_ext --inplace`.

py573a_native.py contains the decryption algorithm in native Python, in case you want to use the tool in an environment where Cython is inconvenient. Note: This version will be slower, but it should be easier to use without installing Cython and a C compiler, etc.

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


### Database
The database as of current writing (2019/04/02) contains everything I could find on the System 573 Digital I/O platform with some exceptions:
- Dance Dance Revolution Solo Bass Mix
  - Does something weird with how it uses the FPGA so more research is required. I will definitely get this done when I can.
- Guitar Freaks/Drummania Multisession Unit-related audio
  - These are used by System 573 Digital I/O games (GFDM) but the hardware itself is different. As far as I can tell from my research, the multisession unit decrypts the data itself and sends the audio out over RCA. The connection to the System 573 Digital I/O hardware is for serial communication to communicate with the server running on the multisession unit in order to tell it what files to load and similar actions. The unit is entirely self-contained. I will take a look at this but it's possibly out of scope of this project, and hard to work on without having the actual hardware.
- Dance Dance Revolution Solo 2000 (JAA/AAA)
  - The following files are on the disc but are not referenced (which means no keys available) as far as I can tell:
    - `DAT/S2H189R8.DAT`
    - `DAT/E2ON849P.DAT`
    - `DAT/M17189R8.DAT`
  - These files may still be recoverable, but a stronger bruteforce method will be required.

As away to verify the output data without listening to every individual MP3, I have run mp3val over all of the MP3s decrypted from every game on the platform. A total of 9 files have shown some sign of corruption in the MP3 frames. I will investigate these 9 files in further detail soon to determine if it's an error with decryption or an error with the source data that's on the disc (be it corruption in the dumps or the MP3 data was originally corrupt in the first place).

Everything else, to my knowledge, should be decryptable. Please create an issue on this repository if you find something that isn't covered by the tool or is broken.



### How to decrypt songs not found in this database
If in the future more data is discovered that isn't covered by this tool, it is still possible to generate the required keys using all of the information found in this repository if you have access to a real System 573 Digital I/O machine.

1. Gather required data
  - Gather all of the full .DAT files, as well as samples of the files (a 0x2000 sample off the top of every file is what I used for creating this database)
  - Gather list of keys required to decrypt specified .DAT on real hardware...
    - Look for something named similar to mp3_tab.bin in the game's GAME.DAT or the PCCARD*.DAT files (or similar) (requires you to have a tool to dump the filesystem)
    - MAME method
      1. Load game in MAME
      2. Go to sound test menu
      3. Save a memory dump starting from 0x80000000 with about 0x400000 of data
      4. Hover over sound test that plays MP3 file
      5. Check debug log for MP3 key 1/2/3 and then search the memory dump to find the MP3 table
      6. Dump entire MP3 table from memory
    - Hardware memory method: Same as MAME method but you dump the memory from the hardware, as well as maybe some well placed hooks (reference hwdecodertool maybe)
2. Generate decryption disc with samples and decryption list from data gathered in step
3. Connect the logic analyzer
  - Connect your logic analyzer to pins 30 and 32 on the MAS3507D chip
  - Reference: http://www.mas-player.de/mp3/download/mas3507d.pdf, page 36, fig 4-4 "44-pin PQFP package" (NOT the PLCC package)
4. Run disc on real hardware. This will automatically decrypt all of the data on the disc that was in the decryption list.
  - Run your logic analyzer from start to end @ 2 MHz, PulseView is recommended since it stores all samples in memory until you save them. sigrok-ci is also acceptable but you may run into issues with your logic analyzer quitting very fast if your system can't keep up with capturing at 2 MHz to a file on disk.
5. Convert the capture to a binary output
  - `sigrok-cli -P spi:wordsize=8:miso=D1:clk=D0:cpol=1:cpha=1 -i input.sr -A spi="MISO data" > input.txt`
  - Convert input.txt to a binary file (if you've done everything up to this point then this is trivial, just read the hex bytes from the text file info a binary file)
6. Split the data into individual files based on the order that they were written to the decryption list on disc.
7. Run bruteforce_process_list.py on the decryption list with the plaintext headers against the full encrypted DAT files and wait for the keys to be bruteforced
  - It may take a few minutes to bruteforce a key depending on your system
  - bruteforce_process_list.py will try to use as many cores as possible, with each core handling 1 bruteforce process
  - Don't forget to run `python setup.py build_ext --inplace` to compile the Cython code
8. If successful, you should see keys flying across the terminal
  - A key is determined to be successful if it is possible to decrypt the encrypted DAT to match the plaintext MP3 file, so the more data you use for your input samples (for example, 0x8000 instead of 0x2000), the more accurate the end result should be.

WARNING: The current db.json was created using the power of a 112 core server. It would probably take a long time to bruteforce everything with consumer grade hardware. Expect a few hours for a single game.
