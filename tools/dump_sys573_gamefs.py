import argparse
import ctypes
import json
import os
import string


def get_filename_hash(filename):
    filename_hash = 0

    for _, c in enumerate(filename):
        for i in range(6):
            filename_hash = ctypes.c_int(
                ((filename_hash >> 31) & 0x4c11db7) ^ ((filename_hash << 1) | ((ord(c) >> i) & 1))
            ).value

    return filename_hash & 0xffffffff


def decrypt_data_internal(data, key):
    def calculate_crc32(input):
        crc = -1

        for c in bytearray(input, encoding='ascii'):
            crc ^= c << 24

            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x4C11DB7
                else:
                    crc <<= 1

        return crc


    decryption_key = calculate_crc32(key)

    for i in range(len(data)):
        data[i] ^= (decryption_key >> 8) & 0xff # This 8 can be variable it seems, but it usually is 8?

    return data


def decrypt_data(data, input_key):
    def calculate_key(input_str):
        key = 0

        for cur in input_str.upper():
            if cur in string.ascii_uppercase:
                key -= 0x37

            elif cur in string.ascii_lowercase:
                key -= 0x57

            elif cur in string.digits:
                key -= 0x30

            key += ord(cur)

        return key & 0xff

    val = 0x41C64E6D
    key1 = (val * calculate_key(input_key)) & 0xffffffff
    counter = 0

    for idx, c in enumerate(data):
        val = ((key1 + counter) >> 5) ^ c
        data[idx] = val & 0xff
        counter += 0x3039

    return data


def decode_lz(input_data):
    output = bytearray()
    input_data = bytearray(input_data)
    idx = 0
    distance = 0
    control = 0

    while True:
        control >>= 1

        if (control & 0x100) == 0:
            control = input_data[idx] | 0xff00
            idx += 1

        data = input_data[idx]
        idx += 1

        if (control & 1) == 0:
            output.append(data)
            continue

        length = None
        if (data & 0x80) == 0:
            distance = ((data & 0x03) << 8) | input_data[idx]
            length = (data >> 2) + 2
            idx += 1

        elif (data & 0x40) == 0:
            distance = (data & 0x0f) + 1
            length = (data >> 4) - 7

        if length is not None:
            start_offset = len(output)
            idx2 = 0

            while idx2 <= length:
                output.append(output[(start_offset - distance) + idx2])
                idx2 += 1

            continue

        if data == 0xff:
            break

        length = data - 0xb9
        while length >= 0:
            output.append(input_data[idx])
            idx += 1
            length -= 1

    return output


common_extensions = [
    'bin', 'exe', 'dat', 'rom', 'o'
]

mambo_common_extensions = [
    'bin.new', 'cmp', 'vas', 'olb', 'pup', 'cpr'
]

ddr_common_extensions = [
    'cmt', 'tim', 'cms', 'lmp', 'per', 'csq', 'ssq', 'cmm',
    'pos', 'ctx', 'lst', 'tmd', 'vab', 'sbs', 'can', 'anm',
    'lpe', 'mbk', 'lz', 'bs', 'txt', 'tan'
]

gfdm_common_extensions = [
    'pak', 'fcn'
]

common_extensions += mambo_common_extensions + ddr_common_extensions + gfdm_common_extensions

ddr_common_regions = [
    'span', 'ital', 'germ', 'fren', 'engl', 'japa', 'kore'
]

ddr_common_parts = [
    'cd', 'nm', 'in', 'ta', 'th', 'bk', 'fr', '25'
]


def generate_data_paths(hash_list={}):
    pccard_filenames = [
        "a.pak",
        "ascii_size16.bin",
        "ascii_size24.bin",
        "ascii_size8.bin",
        "course_info.bin",
        "d_cautio.dat",
        "d_cautio_aa.dat",
        "d_ending.dat",
        "d_res_ns.dat",
        "d_title.dat",
        "d_title_aa.dat",
        "data/all/inst.lst",
        "data/all/inst.tex",
        "data/all/inst.tmd",
        "data/all/texbind.bin",
        "data/area/area/cobk_25.cmt",
        "data/area/area/kicbk_25.cmt",
        "data/area/area/prac_25.cmt",
        "data/area/area/titl2_25.cmt",
        "data/area/area/title.cmt",
        "data/area/area/titls_25.cmt",
        "data/area/area_ua/cobk_25.cmt",
        "data/area/area_ua/kicbk_25.cmt",
        "data/area/area_ua/prac_25.cmt",
        "data/area/area_ua/titl2_25.cmt",
        "data/area/area_ua/title.cmt",
        "data/area/area_ua/titls_25.cmt",
        "data/area/area_ja/cobk_25.cmt",
        "data/area/area_ja/kicbk_25.cmt",
        "data/area/area_ja/prac_25.cmt",
        "data/area/area_ja/titl2_25.cmt",
        "data/area/area_ja/title.cmt",
        "data/area/area_ja/titls_25.cmt",
        "data/area/area_ea/cobk_25.cmt",
        "data/area/area_ea/kicbk_25.cmt",
        "data/area/area_ea/prac_25.cmt",
        "data/area/area_ea/titl2_25.cmt",
        "data/area/area_ea/title.cmt",
        "data/area/area_ea/titls_25.cmt",
        "data/area/area_ka/cobk_25.cmt",
        "data/area/area_ka/kicbk_25.cmt",
        "data/area/area_ka/prac_25.cmt",
        "data/area/area_ka/titl2_25.cmt",
        "data/area/area_ka/title.cmt",
        "data/area/area_ka/titls_25.cmt",
        "data/back/caut/cauta_25.cmt",
        "data/back/caut/caute_25.cmt",
        "data/back/caut/cautf_25.cmt",
        "data/back/caut/cautg_25.cmt",
        "data/back/caut/cauti_25.cmt",
        "data/back/caut/cautj_25.cmt",
        "data/back/caut/cautk_25.cmt",
        "data/back/caut/cauts_25.cmt",
        "data/back/demo/unist_25.cmt",
        "data/back/game/iron_25.cmt",
        "data/chara/chara.ctx",
        "data/chara/chara.lst",
        "data/chara/chara.pos",
        "data/chara/inst/inst.ctx",
        "data/chara/inst/inst.lst",
        "data/chara/inst/inst.pos",
        "data/chara/inst/inst.tmd",
        "data/chara/inst_d/inst_d.cmt",
        "data/chara/inst_d/inst_d.lst",
        "data/chara/inst_d/inst_d.pos",
        "data/chara/inst_d/inst_d.tmd",
        "data/chara/inst_s/inst_s.cmt",
        "data/chara/inst_s/inst_s.lst",
        "data/chara/inst_s/inst_s.pos",
        "data/chara/inst_s/inst_s.tmd",
        "data/course/onimode.bin",
        "data/course/onimode.ssq",
        "data/kanji/eames.cmp",
        "data/mcard/page0e.txt",
        "data/mcard/page0j.txt",
        "data/mcard/page0k.txt",
        "data/mcard/page1e.txt",
        "data/mcard/page1j.txt",
        "data/mcard/page1k.txt",
        "data/mcard/page2e.txt",
        "data/mcard/page2j.txt",
        "data/mcard/page2k.txt",
        "data/mcard/page0.txt",
        "data/mcard/page1.txt",
        "data/mcard/page2.txt",
        "data/mdb/aa_mdb.bin",
        "data/mdb/ea_mdb.bin",
        "data/mdb/ja_mdb.bin",
        "data/mdb/ka_mdb.bin",
        "data/mdb/ua_mdb.bin",
        "data/mdb/mdb.bin",
        "data/motion/inst/inst.cmm",
        "data/motion/prac/prac.cmm",
        "data/movie/titlemv.str",
        "data/mp3/enc/M81D7HHJ.DAT",
        "data/mp3/mp3_tab.bin",
        "data/spu/system.vas",
        "data/tex/rembind.bin",
        "data/tex/subbind.bin",
        "data/tim/allcd/alcda0.cmt",
        "data/tim/allcd/alcdu0.cmt",
        "data/tim/allcd/alcde0.cmt",
        "data/tim/allcd/alcdj0.cmt",
        "data/tim/allcd/alcdk0.cmt",
        "data/tim/wfont/wfont_w.bin",
        "data/vab/ddr3.lst",
        "data/vab/ddr3.vas",
        "data/vab/ddrusa.lst",
        "data/vab/ddrusa.vas",
        "dl/n1/pathtab.bin",
        "dl/pathtab.bin",
        "pathtab.bin",
        "g_id.dat",
        "got11hlf.bin",
        "got11j0b.bin",
        "got11j1b.bin",
        "group_list.bin",
        "ir_id.bin",
        "jp_title.bin",
        "kfont8.bin",
        "music_info.bin",
        "net_id.bin",
        "sd/data/close.vab",
        "sd/data/dj_chr1.vab",
        "sd/data/dj_chr2.vab",
        "sd/data/dj_chr3.vab",
        "sd/data/dj_chr4.vab",
        "sd/data/dj_chr5.vab",
        "sd/data/dj_clr1.vab",
        "sd/data/dj_clr2.vab",
        "sd/data/dj_clr3.vab",
        "sd/data/dj_clr4.vab",
        "sd/data/dj_fail1.vab",
        "sd/data/dj_fail2.vab",
        "sd/data/dj_fail3.vab",
        "sd/data/dj_fail4.vab",
        "sd/data/dj_fail5.vab",
        "sd/data/dj_slct1.vab",
        "sd/data/dj_slct2.vab",
        "sd/data/dj_slct3.vab",
        "sd/data/dj_slct4.vab",
        "sd/data/dj_slct5.vab",
        "sd/data/dj_slct6.vab",
        "sd/data/dj_slct7.vab",
        "sd/data/dj_st_c1.vab",
        "sd/data/dj_st_c2.vab",
        "sd/data/dj_st_c3.vab",
        "sd/data/dj_st_c4.vab",
        "sd/data/dj_st_c5.vab",
        "sd/data/end.vab",
        "sd/data/game1.vab",
        "sd/data/game2.vab",
        "sd/data/in_demo.vab",
        "sd/data/jochu.vab",
        "sd/data/monitor.vab",
        "sd/data/multi.vab",
        "sd/data/out_demo.vab",
        "sd/data/scale.vab",
        "soft/s573/overlay/bin/dbugtest.olb",
        "soft/s573/overlay/bin/fpga_mp3.olb",
        "soft/s573/overlay/bin/gtest.olb",
        "soft/s573/overlay/bin/play.olb",
        "system.vas",

        "cube0.bin",
        "cube1.bin",
        "mdb.bin",
        "courseboss.bin",
        "ircourse.bin",
        "course.bin",
        "fontdb.bin",
        "arrangement_data.bin",
        "object_2d_data.bin",
        "ja_mdb.bin",
        "marathoncourse.bin",
        "font08.bin",
        "font16.bin",
        "font24.bin",
        "font32.bin",
        "font04.bin",
        "dmx2.vas",
        "dmx.vas",
    ]

    for i in range(0, 100):
        pccard_filenames.append("data/back/game/chr/%08d_25.cmt" % i)

    common_filenames = [
        'checksum', 'psx', 'main', 'config', 'fpga_mp3', 'boot', 'aout'
    ]

    common_paths = [
        '', 'boot', 's573', 'data', 'data/fpga', 'soft', 'soft/s573', 'boot/s573', 'boot/soft/s573'
    ]

    ddr_movie_filenames = [
        'cddana', 'scrob_25', 'scrbk_16', 're2424', 'acxx28', 'ccsaca', 'ccrgca', 'ccltaa',
        'ccitaa', 'ccheaa', 'ccdrga', 'ccddra', 'cccuba', 'ccclma', 'ccclca', 'title',
        'hwrlja', 'hwfroa', 'hwnora', 'hwhaja',
        'jutrah', 'jutrag', 'jutraf', 'jutrae', 'jutrad', 'jutrac', 'jutrab', 'jutraa', 'justri', 'justrh', 'justrg',
        'justrf', 'justre', 'justrd', 'justrc', 'justrb', 'justra', 'juspka', 'juspib', 'juspia', 'jusech', 'jusecg',
        'jusecf', 'jusece', 'jusecd', 'jusecc', 'jusecb', 'juseca', 'jurbab', 'jurbaa', 'junycb', 'junyca', 'juhrta',
        'juhrda', 'juhpla', 'juhmsa', 'juhmra', 'juhmma', 'juhmfa', 'juhgra', 'juhbga', 'jufdcb', 'jufdca', 'jszxca',
        'jsytra', 'jsxrpa', 'jswwwa', 'jswsxa', 'jsuioa', 'jstusa', 'jstrea', 'jstasa', 'jssssa', 'jssiba', 'jsrewa',
        'jsprza', 'jspora', 'jspaua', 'jskera', 'jskeba', 'jsjkla', 'jshjka', 'jsghja', 'jsgfda', 'jsfufa', 'jsfdsa',
        'jsewqa', 'jsenea', 'jseeee', 'jsdsaa', 'jsdima', 'jsddda', 'jsdaba', 'jsdaaa', 'jsccca', 'jsbeba', 'jsbbba',
        'jsaaaa', 'jrwird', 'jrwira', 'jruzuc', 'jruzub', 'jruzua', 'jrtryt', 'jrsupb', 'jrsupa', 'jrsumb', 'jrsuma',
        'jrssma', 'jrsmra', 'jrskya', 'jrsawa', 'jrlina', 'jrjazd', 'jrjazc', 'jrjazb', 'jrjaza', 'jrgnma', 'jrfsea',
        'jrdria', 'jrcusa', 'jrcupa', 'jrcrba', 'jrcndd', 'jrcndb', 'jrcnda', 'jrcmab', 'jrcmaa', 'jrcarb', 'jrbapa',
        'jmswrp', 'jmpaxt', 'jmparu', 'jmpahb', 'jmpaha', 'jmpabf', 'jmpaab', 'jmpaaa', 'jmlobb', 'jmloba', 'jmline',
        'jmkatb', 'jmkata', 'jmglow', 'jmflcb', 'jmflca', 'jmfilm', 'jmfcub', 'jmfcua', 'jmefil', 'jmcufb', 'jmcufa',
        'jmcubs', 'jmcubk', 'jfwrdd', 'jfwrdc', 'jfwrdb', 'jfwrda', 'jfwirc', 'jfwira', 'jfttma', 'jftrnd', 'jftrnb',
        'jftrna', 'jfsana', 'jfpiwa', 'jfpara', 'jfmjba', 'jfmecb', 'jfmeca', 'jflngb', 'jflnga', 'jflita', 'jfldac',
        'jfkoac', 'jfkkzb', 'jfinaa', 'jfhtaa', 'jffrga', 'jfctmb', 'jfctma', 'jfclib', 'jfclia', 'jfbfud', 'jfbfuc',
        'jfbfub', 'jfbfua', 'jewawa', 'jetopb', 'jetopa', 'jetono', 'jethdc', 'jethdb', 'jethda', 'jetcla', 'jestra',
        'jesnwb', 'jesnwa', 'jerain', 'jepusb', 'jepusa', 'jepmpa', 'jepina', 'jenmma', 'jeninf', 'jeninc', 'jenina',
        'jekara', 'jejete', 'jeifee', 'jeifec', 'jeifeb', 'jehnaa', 'jehgla', 'jehall', 'jegara', 'jegaku', 'jeflgb',
        'jeelea', 'jeearo', 'jedjtb', 'jedjta', 'jecupa', 'jecara', 'jeblea', 'jebkha'
    ]

    ddr_movie_paths = [
        'common', 'howto'
    ]

    ddr_anime_base_filenames = [
        'mfjc', 'mfjb', 'mfja', 'mljc', 'mljb', 'mlja', 'mrsc', 'mrsb',
        'mrsa', 'mfsc', 'mfsb', 'mfsa', 'mbsc', 'mbsb', 'mbsa', 'mlsc',
        'mlsb', 'mlsa', 'mnor'
    ]

    ddr_anime_filenames = []
    for x in ddr_anime_base_filenames:
        for i in range(0, 10):
            ddr_anime_filenames.append("%s%d" % (x, i))

    ddr_motion_filenames = [
        "abc", "abcd", "abcde", "abcdef", "abcdefg", "capoera1", "cdef", "defg",
        "defgh", "dummy", "ef", "efg", "efghi", "efghijk", "fgh", "fghi",
        "fghijk", "fghijklm", "ghi", "ghijk", "ghijklm", "hijk", "hijklm", "hiphop1",
        "hiphop2", "hopping1", "ijklm", "ijkln", "jazz1", "jazz2", "klm", "lock1",
        "mhouse1", "n31", "normal", "sino_", "soul1", "soul2", "thouse2", "thouse3",
        "wave1", "wave2", "y11", "y31",
    ]

    mambo_puppet_filenames = [
        "uhiy", "lhiy", "cygp", "cygl", "gunm", "geng", "genr", "genb",
        "brow", "sung", "spym", "uhir", "lhir", "sabo", "cong", "samr",
        "samg", "samy", "yase", "debu", "ygir", "rgir", "furc", "furb",
        "fura"
    ]

    for ext in common_extensions:
        for i in range(0, 100):
            pccard_filenames.append("data/texture/banner/banner%02d.%s" % (i, ext))

        for filename in common_filenames:
            for path in common_paths:
                pccard_filenames.append("/".join([path, "%s.%s" % (filename, ext)]))

        for part in ddr_common_parts:
            for filename in ["x"] + ["cos%02d" % x for x in range(0, 100)] + ["non%02d" % x for x in range(0, 100)]:
                pccard_filenames.append("data/course/%s_%s.%s" % (filename, part, ext))

        for region in ddr_common_regions:
            pccard_filenames.append("data/mcard/%s/pages.%s" % (region, ext))
            pccard_filenames.append("data/mcard/%s/pagel.%s" % (region, ext))

            for i in range(0, 10):
                pccard_filenames.append("data/mcard/%s/page%d.%s" % (region, i, ext))

            pccard_filenames.append("data/mcard/%s/titl2_25.%s" % (region, ext))
            pccard_filenames.append("data/mcard/%s/title.%s" % (region, ext))
            pccard_filenames.append("data/mcard/%s/titls_25.%s" % (region, ext))
            pccard_filenames.append("data/mcard/%s/unist_25.%s" % (region, ext))

        for filename in ddr_movie_filenames + ddr_motion_filenames + ddr_anime_filenames:
            pccard_filenames.append("data/anime/%s/%s.%s" % (filename, filename, ext))

        for motion in ddr_movie_filenames + ddr_motion_filenames + ddr_anime_filenames:
            pccard_filenames.append("data/motion/%s/%s.%s" % (motion, motion, ext))

        for movie_path in ddr_movie_paths:
            for filename in ddr_movie_filenames + ddr_motion_filenames + ddr_anime_filenames:
                pccard_filenames.append("data/movie/%s/%s.%s" % (movie_path, filename, ext))

        for filename in mambo_puppet_filenames:
            pccard_filenames.append("data/puppet/%s.%s" % (filename, ext))

        for x in range(0, 100):
            pccard_filenames.append("data/motion/motion%d.%s" % (x, ext))

        for filename in pccard_filenames:
            hash_list[get_filename_hash(filename)] = filename

        pccard_filenames = []

    return hash_list


def generate_ddr_song_paths(input_songlist=[], hash_list={}):
    # This is not a complete songlist. It only exists to help find songs that may not be in the game's music database
    # but are still hidden in the filesystem, which should be a rare case.
    ddr_base_songlist = [
        "have",    "that",    "kung",    "smok",    "boom",    "badg",    "lets",    "boys",
        "butt",    "puty",    "bril",    "puty2",   "bril2",   "make",    "make2",   "myfi",
        "stri",    "dubi",    "litt",    "stom",    "hero",    "getu",    "ifyo",    "ibel",
        "star",    "trip",    "para",    "sptr",    "para2",   "elri",    "tubt",    "love",
        "parh",    "ajam",    "clea",    "luvm",    "this",    "thin",    "keep",    "imth",
        "nove",    "nove2",   "inth",    "race",    "jamj",    "begi",    "doyo",    "over",
        "five",    "gamb",    "bein",    "emot",    "sogr",    "sala",    "mix",     "drlo",
        "gmdd",    "melt",    "divi",    "perf",    "rthr",    "dunk",    "deep",    "skaa",
        "spec",    "prin",    "cele",    "grad",    "luvt",    "youm",    "been",    "floj",
        "ther",    "pats",    "quee",    "into",    "inyo",    "geno",    "gent",    "ckee",
        "mach",    "cpar",    "rugg",    "cbri",    "nazo",    "sogr2",   "twen2",   "over2",
        "dunk2",   "rthr2",   "skaa2",   "spec2",   "deep2",   "grad2",   "upan",    "xana",
        "upsi",    "iton",    "soma",    "doit",    "oper",    "volf",    "rock",    "foll",
        "hbut",    "ohni",    "cans",    "mrwo",    "etup",    "hboo",    "damd",    "holi",
        "capt",    "turn",    "flas",    "wond",    "afro",    "endo",    "dyna",    "dead",
        "lase",    "sile",    "rebi",    "dluv",    "djam",    "dgra",    "dgen",    "cpar2",
        "cpar3",   "afte",    "cuti",    "theb",    "virt",    "amcs",    "theg",    "gimm",
        "bumb",    "kher",    "drop",    "stop",    "wild",    "letb",    "sprs",    "hyst",
        "pevo",    "walk",    "pink",    "musi",    "kick",    "only",    "eaty",    "adre",
        "oose",    "seve",    "shak",    "neve",    "youn",    "gotc",    "hhav",    "heat",
        "shoo",    "onet",    "nigh",    "hboy",    "sain",    "ninz",    "baby",    "clim",
        "burn",    "gher",    "naha",    "bfor",    "agai",    "hypn",    "summ",    "hify",
        "hdam",    "hher",    "talk",    "lead",    "teng",    "olic",    "eran",    "lety",
        "your",    "onts",    "getm",    "vide",    "groo",    "midn",    "orio",    "shar",
        "nana",    "kyhi",    "cafe",    "cong",    "nite",    "sexy",    "cats",    "sync",
        "onda",    "dome",    "lupi",    "rhyt",    "them",    "alla",    "ldyn",    "feal",
        "stil",    "ecst",    "abso",    "brok",    "dxyy",    "mrtt",    "tequ",    "iwas",
        "hotl",    "elec",    "peta",    "roma",    "twis",    "ones",    "lbfo",    "beto",
        "ponp",    "mats",    "reme",    "estm",    "noli",    "myge",    "cube",    "abys",
        "sana",    "moon",    "ever",    "movi",    "righ",    "trib",    "oops",    "dive",
        "gain",    "pafr",    "radi",    "inse",    "lcan",    "miam",    "samb",    "dont",
        "leth",    "wayn",    "ialv",    "toge",    "gtof",    "gtup",    "mama",    "frky",
        "lmac",    "club",    "stru",    "fore",    "aliv",    "skyh",    "oflo",    "tipi",
        "idon",    "dril",    "kiss",    "drea",    "lett",    "roov",    "heal",    "look",
        "itri",    "onth",    "styl",    "nori",    "cent",    "lovi",    "ordi",    "ghos",
        "some",    "fant",    "witc",    "oyou",    "ollo",    "offu",    "mira",    "twil",
        "cowg",    "tele",    "just",    "imin",    "etsg",    "byeb",    "then",    "wwwb",
        "maxx",    "true",    "mysw",    "frec",    "sode",    "fire",    "yozo",    "exot",
        "cand",    "ruee",    "kind",    "soin",    "long",    "maxi",    "youl",    "waka",
        "abyl",    "drte",    "esti",    "inam",    "amin",    "swee",    "snow",    "refl",
        "sofa",    "drif",    "itsr",    "stay",    "secr",    "ittl",    "rain",    "unli",
        "toth",    "tsug",    "roll",    "opti",    "noth",    "anta",    "ifee",    "andy",
        "spin",    "tran",    "atus",    "than",    "thew",    "kaku",    "afro3",   "star3",
        "bril3",   "bfor3",   "drop3",   "dyna3",   "hyst3",   "mats3",   "sexy3",   "sprs3",
        "stil3",   "wild3",   "burn3",   "tsug3",   "ecst3",   "sile3",   "nite3",   "gher3",
        "summ3",   "stro",    "didi",    "cari",    "thev",    "tryt",    "iwan",    "cott",
        "thet",    "wast",    "aaro",    "fivs",    "like",    "team",    "what",    "with",
        "anyw",    "memo",    "cras",    "yeby",    "tell",    "vani",    "tomp",    "itr2",
        "jamm",    "logi",    "loo2",    "blas",    "peac",    "imfo",    "shin",    "bom2",
        "ddyn",    "morn",    "ylea",    "dark",    "ilik",    "sand",    "mcut",    "brou",
        "keon",    "mode",    "tomo",    "suns",    "surv",    "laco",    "wewi",    "irre",
        "cart",    "spee",    "issk",    "suga",    "lamo",    "imgo",    "stin",    "thel",
        "game",    "jane",    "mobo",    "belo",    "ledl",    "radu",    "vvvv",    "aaaa",
        "wear",    "idoi",    "colo",    "tayy",    "meal",    "wite",    "froz",    "mess",
        "feel",    "daik",    "maho",    "hold",    "jetw",    "wedd",    "surv3",   "bagg",
        "lege",    "aois",    "mike",    "yncc",    "stoi",    "tars",    "ichi",    "gene",
        "xeno",    "saku",    "rose",    "heav",    "hype",    "laba",    "ddre",    "ripm",
        "airr",    "thef",    "tear",    "seno",    "acro",    "rand",    "funk",    "tryl",
        "itr3",    "loo3",    "kind3",   "frve",    "satn",    "myfa",    "yogo",    "dsmo",
        "badt",    "dsco",    "cant",    "addi",    "itta",    "iwou",    "sigh",    "lcat",
        "lcat2",   "urbo",    "oste",    "frea",    "whey",    "alit",    "stea",    "mize",
        "inee",    "cmon",    "days",    "grin",    "stal",    "getd",    "take",    "teen",
        "wann",    "stup",    "scor",    "ofec",    "allt",    "dcal",    "aven",    "foca",
        "juar",    "stbe",    "bain",    "illi",    "visi",    "dizy",    "vity",    "msic",
        "getb",    "wont",    "deux",    "maxp",    "wan2",    "canb",    "inee2",   "simp",
        "ving",    "ride",    "come",    "parb",    "fory",    "enjo",    "west",    "loco",
        "onem",    "plan",    "ofsu",    "hump",    "mick",    "free",    "stas",    "kids",
        "viva",    "ente",    "sunl",    "rela",    "ine3",    "move",    "rapp",    "shur",
        "ymca",    "supe",    "nout",    "prom",    "inda",    "beli",    "biza",    "ladi",
        "call",    "volt",    "gott",    "fami",    "lyou",    "wait",    "virg",    "rage",
        "chih",    "jama",    "good",    "okok",    "come2",   "eart",    "abs2",    "anly",
        "babx",    "bail",    "bald",    "batt",    "bt4u",    "eyes",    "fdub",    "geti",
        "gorg",    "inff",    "infi",    "ins2",    "kee2",    "kybm",    "madb",    "matj",
        "mean",    "mgs2",    "mind",    "nems",    "oute",    "put3",    "quic",    "san2",
        "swon",    "whas",    "diam",    "smap",    "odor",    "gaku",    "hone",    "kise",
        "tuff",    "chai",    "dizz",    "girl",    "mixe",    "thes",    "yous",    "kunc",
        "lady",    "oody",    "frid",    "hipt",    "midd",    "dipi",    "shou",    "geni",
        "wonn",    "asth",    "bloc",    "busy",    "mich",    "mymy",    "ilen",    "pres",
        "worl",    "opsi",    "iwsu",    "spsp",    "pump",    "fnkm",    "wona",    "craz",
        "myma",    "lose",    "polo",    "oran",    "diff",    "mari",    "tmrr",    "sedu",
        "insi",    "inje",    "pass",    "youg",    "nine",    "ridl",    "mine",    "gtwo",
        "zero",    "rout",    "luvu",    "vjar",    "rten",    "lovd",    "catc",    "voya",
        "flyt",    "hitn",    "mids",    "toej",    "monk",    "istn",    "redr",    "bais",
        "cuca",    "gyru",    "jamd",    "tenr",    "imem",    "itoy",    "remx",    "popn",
        "banz",    "brin",    "hipe",    "letd",    "stck",    "vola",    "choo",    "skrb",
        "inje2",   "doll",    "ifut",    "evrd",    "aaaa2",   "rzon",    "hpan",    "xeph",
        "hima",    "drab",    "curu",    "muge",    "nizi",    "gekk",    "kono",    "mooo",
        "thir",    "dand",    "kage",    "tika",    "unde",    "time",    "rara",    "braz",
        "taur",    "tier",    "sksk",    "okor",    "murm",    "flya",    "inno",    "myon",
        "flow",    "rbow",    "bala",    "gate",    "fold",    "long2",   "mgir",    "alov",
        "sigh2",   "daba",    "toxi",    "waww",    "laba2LA", "jerk",    "fasc",    "lare",
        "punc",    "eace",    "gold",    "glor",    "dayd",    "mond",    "cach",    "driv",
        "qmas",    "stop2",   "dyna2",   "surr",    "sedu2",   "hunt",    "daca",    "give",
        "does",    "chao",    "bred",    "colo2",   "lab3",    "illm",    "fjus",    "tlov",
        "btea",    "wowo",    "dvis",    "hana",    "flow2",   "fasc2",   "comc",    "fain",
        "meag",    "flya2",   "soul",    "gate2",   "moos",    "flow3",   "felw",    "silv",
        "trim",    "fnky",    "leff",    "shiv",    "ikno",    "sinc",    "such",    "theo",
        "onew",    "runi",    "dare",    "trno",    "doyw",    "city",    "bttw",    "sorr",
        "yoex",    "mams",    "chec",    "whyr",    "soss",    "danc",    "galv",    "numb",
        "gett",    "brkf",    "blab",    "prnc",    "sosi",    "temp",    "dscc",    "robo",
        "beau",    "btea2",   "biol",    "hood",    "godi",    "rome",    "rhrn",    "brui",
        "soni",    "onme",    "said",    "jacq",    "heyb",    "step",    "luft",    "cloc",
        "fina",    "gonn",    "hots",    "karm",    "byou",    "risa",    "sign",    "ysme",
        "fara",    "lips",    "conm",    "alie",    "fied",    "mitr",    "mala",    "rasp",
        "bloo",    "agir",    "mber",    "lefr",    "subu",    "unbe",    "prol",    "hook",
        "ofth",    "reas",    "fast",    "ange",    "csto",    "lste",    "unwr",    "dazz",
        "fway",    "alwa",    "infe",    "tlel",    "buty",    "away",    "caug",    "gyps",
        "flik",    "memi",    "unap",    "bmon",    "stim",    "tltl",    "lshi",    "bdow",
        "spar",    "cufo",    "acol",    "conf",    "leti",    "will",    "lits",    "touc",
        "ifly",    "wwlt",    "hand",    "ngon",    "higo",    "tbea",    "bins",    "mwit",
        "trea",    "samu",    "ucha",    "tigh",    "ryou",    "tobe",    "onmy",    "andt",
        "sudd",    "toky",    "orig",    "aint",    "ngoo",    "smac",    "btol",    "firr",
        "unre",    "stah",    "skan",    "hesa",    "cbac",    "sayg",    "feva",    "arou",
        "twom",    "vate",    "venu",    "blin",    "athi",    "wind",    "uber",    "arra",
        "dori",    "unti",    "trix",    "vemb",    "eter",    "dofl",    "volc",    "eday",
        "plut",    "sunr",    "pard",    "swit",    "alth",    "bbbu",    "favo",    "nomo",
        "trus",    "plur",    "lamd",    "votu",    "jupi",    "sunj",    "uran",    "mars",
        "whyn",    "shad",    "gili",    "pose",    "bris",    "amch",    "dtwf",    "dyns",
        "bfov",    "deag",    "sune",    "satu",    "tloc",    "pluf",    "bfos",    "doub",
        "smil",    "puzz",    "leav",    "timh",    "saga",    "cara",    "ontb",    "feee",
        "ghet",    "mcry",    "trac",    "waiu",    "drem",    "disn",    "fotl",    "bibb",
        "ball",    "tiki",    "circ",    "cohm",    "wish",    "spoo",    "hawa",    "heme",
        "bout",    "cmix",    "apir",    "cany",    "chim",    "evry",    "ijus",    "ltle",
        "bare",    "zadd",    "cmar",    "wabe",    "youc",    "stet",    "itsa",    "supc",
        "devi",    "haku",    "flig",    "tick",    "tajh",    "sabe",    "lovy",    "iyhr",
        "staa",    "reac",    "want",    "noma",    "crcs",    "trbu",    "here",    "wine",
        "lift",    "flou",    "taka",    "boyd",    "pute",    "myde",    "umbr",    "caom",
        "niru",    "oclo",    "allg",    "mawo",    "reda",    "feto",    "slac",    "blac",
        "cahe",    "toot",    "wasu",    "ican",    "iran",    "wego",    "youi",    "evda",
        "dane",    "thom",    "stre",    "hetr",    "mmla",    "djgo",    "icei",    "duck",
        "mcmi",    "almy",    "heit",    "happ",    "ucan",    "play",    "dace",    "slip",
        "hora",    "bust",    "dyou",    "obse",    "bigg",    "bene",    "tare",    "sare",
        "slre",    "dacr",    "jube",    "esce",    "sett",    "soyo",    "suhe",    "unit",
        "open",    "mylo",    "opee",    "soun",    "butt2",   "boys2",   "thli",    "ttlg",
        "clos",    "orig2",   "kyou",    "dmin",    "weve",    "synt",    "dubi2",   "getu2",
        "hero2",   "reup",    "weco",    "insp",    "onbo",    "trig",    "danf",    "weca",
        "raci",    "dese",    "sidr",    "thlo",    "habi",    "osak1",   "osak2",   "osak3",
        "xmix1",   "xmix2",   "xmix3",   "xmix4",   "xmix5",   "rint",    "turk",    "jung",
        "blue",    "zerr",    "purp",    "brea",    "sust",    "crgo",    "bigt",    "reso",
        "trav",    "hous",    "ours",    "crim",    "blra",    "chan",    "koko",    "parx",
        "trxs",    "parx2",   "sptx",    "rebx",    "afrx",    "pevx",    "clix",    "petx",
        "feax",    "canx",    "xmax",    "unlx",    "kakx",    "legx",    "ddrx",    "xpar",
        "geis",    "tric",    "seka",    "suki",    "tabi",    "cspa",    "cssp",    "inlo",
        "sttb",    "pori",    "less",    "geis2",   "eoti",    "tone",    "bewi",    "orig3",
        "ropp1",   "prds",    "ille",    "hott1",   "hott2",   "sabe2",   "sidr2",   "dyna4",
        "newg",    "nows",    "taki",    "dist",    "detr",    "drdr",    "imco",    "priv",
        "teme",    "frez",    "haun",    "wick",    "sosp",    "thei",    "jena",    "sacr",
        "wwcm",    "vila",    "clsr",    "iceb",    "daft",    "canu",    "rist",    "pock",
        "nver",    "hung",    "boog",    "gtim",    "vood",    "fego",    "sout",    "twau",
        "curr",    "tame",    "iair",    "ahla",    "down",    "spac",    "rnow",    "ensi",
        "bbay",    "shie",    "lvag",    "bona",    "pork",    "mypr",    "onst",    "laca",
        "ikny",    "inty",    "imag",    "nost",    "hien",    "grav",    "hest",    "tasf",
        "inzo",    "ttim",    "eine",    "kimp",    "shlo",    "dokn",    "lget",    "juda",
        "when",    "abri",    "bene2",   "yyou",    "drec",    "thni",    "geba",    "theh",
        "goda",    "sowa",    "elrt",    "ceye",    "aper",    "youa",    "seul",    "lali",
        "unen",    "letg",    "larc",    "prai",    "clju",    "crco",    "ropp",    "smoo",
        "seco",    "poss",    "huch",    "fifi",    "dada",    "allm",    "cgpr",    "whro",
        "skyi",    "shei",    "tako",    "onra",    "ifyo2",   "ezdo",    "beyo",    "sasu",
        "ropp1",   "ropp2",   "ropp3",   "ropp4",   "aftr",    "delt",    "dirt",    "dumm",
        "oarf",    "sak2",    "thr8",    "yoan",    "rezo",    "zeta",    "anti",    "batf_c",
        "capt2",   "dada2",   "damd2",   "droo",    "etny",    "goru",    "goup_c",  "hide",
        "ifut_c",  "vane",    "tens",    "sueu",    "sudr",    "shwo",    "shng",    "sday",
        "pose2",   "pier",    "nizi_c",  "newd",    "momo",    "melo_c",  "meii",    "maxl_c",
        "lvng_c",  "issk2",   "ifyo3",   "melo",    "maxl",    "lvng",    "goup",    "batf",
        "valk",    "titi",    "evti",    "pier",    "imso",    "toet",    "alst",    "amal",
        "angl",    "bere",    "cbtm",    "chro",    "cone",    "dids",    "dorm",    "dree",
        "feve",    "futu",    "fwer",    "geba",    "haun",    "hbfo",    "hevy",    "hien1",
        "hien2",   "hien3",   "hrtb",    "illf",    "ioio",    "lanj",    "litp",    "meme",
        "merm",    "mesg",    "mprd",    "neph",    "newb",    "nyev1",   "nyev2",   "nyev3",
        "pavo",    "priv",    "prog",    "rebo",    "rthm",    "ryor",    "seul",    "shiz",
        "sigs",    "snow2",   "sson",    "stra",    "sumi",    "tenj",    "toho",    "toky1",
        "toky2",   "toky3",   "trbe",    "trvo",    "twin",    "ublv",    "urlv",    "cosh",
        "koen",    "rens",    "snpr",    "revo",    "gofo",    "keyc",    "puda",    "trxa",
        "brak",    "paks",    "acwo",    "airh",    "anot",    "arms",    "bedr",    "brig",
        "burs",    "cctr",    "chew",    "chil",    "chin",    "ckpp",    "dail",    "deba",
        "dimo",    "dind",    "disp",    "doth",    "elem",    "elys",    "empa",    "engr",
        "fndw",    "furi",    "fuuf",    "gaia",    "hevy2",   "hosh",    "hyen",    "iman",
        "ixix",    "jojo",    "joke",    "kara",    "kike",    "koih",    "lanj2",   "lond",
        "magn",    "maji",    "mawa",    "meum",    "miga",    "mmme",    "mobu",    "mura",
        "nagi",    "nblw",    "negr",    "niji",    "okom",    "oren",    "oron",    "ostt",
        "pran",    "prte",    "puni",    "raki",    "revn",    "rint2",   "rola",    "rryu",
        "scho",    "seit",    "sola",    "sota",    "soth",    "sous",    "span",    "sque",
        "stel",    "sthe",    "stoa",    "stul",    "suca",    "sumf",    "swra",    "synf",
        "todo",    "tpch",    "trbl",    "tuke",    "twog",    "umum",    "vega",    "wifa",
        "wisi",    "wwve",    "yaco",    "yaky",    "yama",    "zutt",    "adul",    "akhu",
        "aozo",    "asai",    "atoz",    "awak",    "awao",    "ayak",    "bada",    "baku",
        "bamb",    "basb",    "bbme",    "bibi",    "boku",    "ccch",    "chea",    "choc",
        "cive",    "cleo",    "cody",    "czgt",    "dete",    "dkdk",    "doca",    "dong",
        "dopa",    "edmj",    "egoi",    "eltr",    "endr",    "esed",    "fiel",    "fksb",
        "foto",    "ftsy",    "fuji",    "geki",    "gens",    "gogo",    "hakt",    "hbfo2",
        "hlat",    "hlye",    "hnmr",    "home",    "idol",    "intb",    "joma",    "kaiy",
        "kawa",    "kira",    "kuro",    "llcu",    "luck",    "maam",    "mayu",    "miku",
        "mine2",   "miso",    "mrps",    "myco",    "myhr",    "nage",    "nekn",    "niko",
        "noil",    "onna",    "orrs",    "osen",    "oslv",    "otom",    "ovtp",    "papi",
        "peit",    "pooc",    "poss2",   "pran2",   "ptay",    "rair",    "raku",    "rema",
        "rusy",    "sabl",    "sakm",    "sans",    "scar",    "sedm",    "setu",    "shik",
        "ssca",    "ssst",    "stfa",    "stfa2",   "strb",    "strg",    "sumd",    "syak",
        "syun",    "tenk",    "tiho",    "tnaw",    "totu",    "tsub",    "wada",    "wech",
        "beat",    "tota",
    ]

    songlist = ddr_base_songlist if not input_songlist else input_songlist

    for song_id in songlist:
        for ext in common_extensions:
            for part in ddr_common_parts:
                filename = "data/mdb/%s/%s_%s.%s" % (song_id, song_id, part, ext)
                hash_list[get_filename_hash(filename)] = filename

            filename = "data/mdb/%s/all.%s" % (song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "data/mdb/%s/%s.%s" % (song_id, song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "data/ja/music/%s/%s.%s" % (song_id, song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "ja/music/%s/%s.%s" % (song_id, song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "music/%s/%s.%s" % (song_id, song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "%s/%s.%s" % (song_id, song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

            filename = "%s.%s" % (song_id, ext)
            hash_list[get_filename_hash(filename)] = filename

    return hash_list


# Functions used to parse DDR data
def parse_rembind_filenames(data, hash_list={}):
    entries = len(data) // 0x30

    for i in range(entries):
        filename_len = 0

        while filename_len + 0x10 < 0x30 and data[i*0x30+0x10+filename_len] != 0:
            filename_len += 1

        orig_filename = data[i*0x30+0x10:i*0x30+0x10+filename_len].decode('ascii').strip('\0')

        for ext in common_extensions:
            filename = "data/%s.%s" % (orig_filename, ext)
            hash_list[get_filename_hash(filename)] = filename

            for region in ddr_common_regions:
                for region2 in ddr_common_regions:
                    if region2 == region:
                        continue

                    needle = "%s/" % region

                    if needle not in orig_filename:
                        continue

                    filename = "data/%s.%s" % (orig_filename, ext)
                    filename = filename.replace(needle, "%s/" % region2)
                    hash_list[get_filename_hash(filename)] = filename

    return hash_list


# Functions used to parse GFDM data
def parse_group_list_filenames(data, hash_list={}):
    for i in range(len(data) // 0x30):
        filename_len = 0

        while filename_len < 0x30 and data[i*0x30+filename_len] != 0:
            filename_len += 1

        filename = data[i*0x30:i*0x30+filename_len].decode('ascii').strip('\0')

        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

        filename = os.path.splitext(filename)[0]
        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

    return hash_list


# Functions used to parse Dancemaniax data
def parse_group_list_filenames_dmx(data, hash_list={}):
    entry_size = 0x20
    cnt = int.from_bytes(data[:4], byteorder="little")
    for i in range(cnt):
        filename_len = 0

        while filename_len < entry_size and data[i*entry_size+filename_len] != 0:
            filename_len += 1

        filename = data[i*entry_size:i*entry_size+filename_len].decode('ascii').strip('\0')

        hash_list[get_filename_hash(filename)] = filename

        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

        filename = os.path.splitext(filename)[0]
        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

    data = data[0x10+0x20*cnt:]
    entry_size = 0x30
    for i in range(len(data) // entry_size):
        filename_len = 0

        while filename_len < entry_size and data[i*entry_size+filename_len] != 0:
            filename_len += 1

        filename = data[i*entry_size:i*entry_size+filename_len].decode('ascii').strip('\0')
        hash_list[get_filename_hash(filename)] = filename

        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

        filename = os.path.splitext(filename)[0]
        for ext in common_extensions:
            path = "%s.%s" % (filename, ext)
            hash_list[get_filename_hash(path)] = path

    return hash_list


# Common readers
def parse_mdb_filenames(data, entry_size, hash_list={}):
    songlist = []

    try:
        for i in range(len(data) // entry_size):
            if data[i*entry_size] == 0:
                break

            songlist.append(data[i*entry_size:i*entry_size+6].decode('ascii').strip('\0').strip())
    except:
        pass

    return generate_ddr_song_paths(songlist, hash_list)


# File table readers
def read_file_table_ddr(filename, table_offset):
    files = []

    with open(filename, "rb") as infile:
        infile.seek(table_offset, 0)

        while True:
            filename_hash = int.from_bytes(infile.read(4), byteorder="little")
            offset = int.from_bytes(infile.read(2), byteorder="little")
            flag_loc = int.from_bytes(infile.read(2), byteorder="little")
            flag_comp = int.from_bytes(infile.read(1), byteorder="little")
            flag_enc = int.from_bytes(infile.read(1), byteorder="little")
            unk = int.from_bytes(infile.read(2), byteorder="little")
            filesize = int.from_bytes(infile.read(4), byteorder="little")

            if filename_hash == 0xffffffff and offset == 0xffff:
                break

            if filesize == 0:
                continue

            files.append({
                'idx': len(files),
                'filename_hash': filename_hash,
                'offset': offset * 0x800,
                'filesize': filesize,
                'flag_loc': flag_loc,
                'flag_comp': flag_comp,
                'flag_enc': flag_enc,
                'unk': unk,
            })

    return files


def read_file_table_gfdm(filename, table_offset):
    files = []

    with open(filename, "rb") as infile:
        infile.seek(table_offset, 0)

        while True:
            filename_hash = int.from_bytes(infile.read(4), byteorder="little")
            offset = int.from_bytes(infile.read(4), byteorder="little")
            filesize = int.from_bytes(infile.read(4), byteorder="little")
            flag = int.from_bytes(infile.read(4), byteorder="little")

            if filesize == 0:
                continue

            if filename_hash == 0xffffffff and offset == 0xffffffff:
                break

            files.append({
                'idx': len(files),
                'filename_hash': filename_hash,
                'offset': offset,
                'filesize': filesize,
                'flag_loc': 0,
                'flag_comp': 0,
                'flag_enc': 0,
                'unk': 0,
                '_flag': flag,
            })

    return files


def get_file_data(input_folder, fileinfo, enckey=None):
    card_filename = None

    game_path = os.path.join(input_folder, "GAME.DAT")
    pccard_path = os.path.join(input_folder, "PCCARD.DAT")
    pccard1_path = os.path.join(input_folder, "PCCARD1.DAT")
    card_path = os.path.join(input_folder, "CARD.DAT")

    if os.path.exists(pccard_path):
        card_filename = pccard_path

    if os.path.exists(pccard1_path):
        card_filename = pccard1_path

    elif os.path.exists(card_path):
        card_filename = card_path

    game = open(game_path, "rb") if os.path.exists(game_path) else None
    card = open(card_filename, "rb") if card_filename else None

    data = None
    if fileinfo['flag_loc'] == 1:
        if card:
            card.seek(fileinfo['offset'])
            data = bytearray(card.read(fileinfo['filesize']))

    else:
        if game:
            game.seek(fileinfo['offset'])
            data = bytearray(game.read(fileinfo['filesize']))

    if data and fileinfo['flag_enc'] != 0 and enckey:
        data = decrypt_data(data, enckey)

    if data and fileinfo['flag_comp'] == 1:
        try:
            data = decode_lz(data)

        except IndexError:
            pass

    return bytearray(data)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', help='Input folder', default=None, required=True)
    parser.add_argument('--output', help='Output folder', default="output")
    parser.add_argument('--key', help='Encryption key', choices=['EXTREME', 'EURO2', 'MAX2', 'DDR5', 'MAMBO'])
    parser.add_argument('--type', help='Game Type', choices=['ddr', 'gfdm-old', 'gfdm', 'mambo', 'dmx'])
    parser.add_argument('--no-metadata', help='Do not save metadata file', default=False, action='store_true')
    parser.add_argument('--bruteforce-ddr', help='Bruteforce DDR songs using an internal database (SLOW!)',
                        default=False, action='store_true')

    args = parser.parse_args()

    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)

    hash_list = generate_data_paths()

    if args.bruteforce_ddr:
        hash_list = generate_ddr_song_paths(hash_list=hash_list)

    files = []
    if args.type in ["ddr", "mambo"]:
        files = read_file_table_ddr(os.path.join(args.input, "GAME.DAT"), 0xFE4000)

    elif args.type == "gfdm-old":
        files = read_file_table_gfdm(os.path.join(args.input, "GAME.DAT"), 0x180000)

    elif args.type == "gfdm":
        files = read_file_table_gfdm(os.path.join(args.input, "GAME.DAT"), 0x198000)

    elif args.type == "dmx":
        files = read_file_table_gfdm(os.path.join(args.input, "GAME.DAT"), 0xFF0000)

    else:
        print("Unknown format!")
        exit(1)

    for idx, fileinfo in enumerate(files):
        if fileinfo['filename_hash'] == 0x45fda52a or fileinfo['filename_hash'] in hash_list and hash_list[fileinfo['filename_hash']].endswith("config.dat"): # Just try to decrypt any config.dat
            try:
                config = decrypt_data_internal(get_file_data(args.input, fileinfo, args.key), "/s573/config.dat").decode('shift-jis')

                print("Configuration file decrypted:")
                print(config)

                for l in config.split('\n'):
                    if l.startswith("conversion "):
                        # Dumb way of doing this but I'm lazy
                        for path in l[len("conversion "):].split(':'):
                            if path.startswith('/'):
                                path = path[1:]

                            hash_list[get_filename_hash(path)] = path

            except:
                pass


        if fileinfo['filename_hash'] in hash_list:
            if args.type in ["ddr", "mambo"]:
                if hash_list[fileinfo['filename_hash']] in ["data/tex/rembind.bin", "data/all/texbind.bin"]:
                    hash_list = parse_rembind_filenames(get_file_data(args.input, fileinfo, args.key), hash_list)

            if args.type == "ddr":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x2c, hash_list)
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x30, hash_list)
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x64, hash_list)
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x6c, hash_list)
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x80, hash_list)

                elif hash_list[fileinfo['filename_hash']] in ["data/mdb/ja_mdb.bin", "data/mdb/ka_mdb.bin",
                                                              "data/mdb/aa_mdb.bin", "data/mdb/ea_mdb.bin",
                                                              "data/mdb/ua_mdb.bin"]:
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x38, hash_list)

            elif args.type == "mambo":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key), 0x2c, hash_list)

            elif args.type in ["gfdm", "gfdm-old"]:
                if hash_list[fileinfo['filename_hash']] == "group_list.bin":
                    hash_list = parse_group_list_filenames(get_file_data(args.input, fileinfo, args.key), hash_list)

            elif args.type == "dmx":
                if hash_list[fileinfo['filename_hash']] == "ja_mdb.bin":
                    hash_list = parse_mdb_filenames(get_file_data(args.input, fileinfo, args.key)[0x10:], 0x24, hash_list)

                elif hash_list[fileinfo['filename_hash']] == "arrangement_data.bin":
                    hash_list = parse_group_list_filenames_dmx(get_file_data(args.input, fileinfo, args.key), hash_list)

    used_regions = {
        0: {
            'filename': "GAME.DAT",
            'data': [0] * os.path.getsize(os.path.join(args.input, "GAME.DAT")),
        },
    }

    pccard_path = os.path.join(args.input, "PCCARD.DAT")
    pccard1_path = os.path.join(input_folder, "PCCARD1.DAT")
    card_path = os.path.join(args.input, "CARD.DAT")
    card_filename = None

    if os.path.exists(pccard_path):
        card_filename = pccard_path

    if os.path.exists(pccard1_path):
        card_filename = pccard1_path

    elif os.path.exists(card_path):
        card_filename = card_path

    if card_filename:
        used_regions[1] = {
            'filename': card_filename,
            'data': [0] * os.path.getsize(os.path.join(args.input, card_filename)),
        }

    for idx, fileinfo in enumerate(files):
        output_filename = "_output_%08x.bin" % (fileinfo['filename_hash'])

        if fileinfo['filename_hash'] in hash_list:
            output_filename = hash_list[fileinfo['filename_hash']]

            if output_filename.startswith("/"):
                output_filename = "_" + output_filename[1:]

        else:
            print("Unknown hash %08x" % fileinfo['filename_hash'], output_filename)

        files[idx]['filename'] = output_filename

        output_filename = os.path.join(args.output, output_filename)

        # Mark region as used
        region_size = fileinfo['offset'] + fileinfo['filesize']

        # if (region_size % 0x800) != 0:
        #     region_size += 0x800 - (region_size % 0x800)

        used_regions[fileinfo['flag_loc']]['data'][fileinfo['offset']:region_size] = [1] * (region_size - fileinfo['offset'])

        if os.path.exists(output_filename):
            continue

        filepath = os.path.dirname(output_filename)
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        print(fileinfo)
        print("Extracting", output_filename)
        with open(output_filename, "wb") as outfile:
            data = get_file_data(args.input, fileinfo, args.key)
            outfile.write(data)

    if not args.no_metadata:
        json.dump(files, open(os.path.join(args.output, "_metadata.json"), "w"), indent=4)


    unreferenced_path = os.path.join(args.output, "#unreferenced")
    for k in used_regions:
        data = bytearray(open(os.path.join(args.input, used_regions[k]['filename']), "rb").read())

        # Find and dump unreferenced regions with data in them
        start = 0
        while start < len(used_regions[k]['data']):
            if used_regions[k]['data'][start] == 0:
                end = start

                while end < len(used_regions[k]['data']) and used_regions[k]['data'][end] == 0:
                    end += 1

                if len([x for x in data[start:end] if x != 0]) > 0 and len([x for x in data[start:end] if x != 0xff]) > 0:
                    if not os.path.exists(unreferenced_path):
                        os.makedirs(unreferenced_path)

                    print("Found unreferenced data @ %08x - %08x" % (start, end))

                    open(os.path.join(unreferenced_path, "%d_%08x.bin" % (k, start)), "wb").write(data[start:end])

                start = end + 1

            else:
                start += 1


if __name__ == "__main__":
    main()
