import argparse
import ctypes
import json
import os
import string
import struct

def get_filename_hash(filename):
    hash = 0

    for cidx, c in enumerate(filename):
        for i in range(6):
            hash = ctypes.c_int(((hash >> 31) & 0x4c11db7) ^ ((hash << 1) | ((ord(c) >> i) & 1))).value

    return hash & 0xffffffff

def decrypt_data(data, input_key):
    def calculate_key(input):
        key = 0

        for c in input.upper():
            if c in string.ascii_uppercase:
                key -= 0x37

            elif c in string.ascii_lowercase:
                key -= 0x57

            elif c in string.digits:
                key -= 0x30

            key += ord(c)

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
    # Based on decompression code from IIDX GOLD CS
    input_data = bytearray(input_data)
    idx = 0

    output = bytearray()

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


pccard_filenames = [
    # General
    "boot/checksum.dat",
    "checksum.dat",
    "boot/psx.bin",
    "boot/main.exe",
    "data/main.exe",
    "psx.bin",
    "main.exe",
    "config.dat",

    # Files from DDR
    "data/fpga/fpga_mp3.bin",
    "data/mp3/mp3_tab.bin",
    "data/tim/wfont/wfont_w.bin",
    "data/mdb/mdb.bin",
    "data/mdb/ja_mdb.bin",
    "data/tex/rembind.bin",
    "data/tex/subbind.bin",
    "data/chara/inst_s/inst_s.cmt",
    "data/chara/inst_d/inst_d.cmt",
    "data/course/onimode.bin",
    "data/course/onimode.ssq",
    "data/mp3/enc/M81D7HHJ.DAT", # Dance Dance Revolution from Extreme is stored in the card data, unlike every other song in the game
    "data/chara/inst/inst.ctx",
    "data/motion/inst/inst.cmm",
    "data/chara/chara.pos",
    "data/chara/inst_s/inst_s.pos",
    "data/chara/inst_d/inst_d.pos",
    "data/chara/chara.lst",
    "data/chara/inst/inst.tmd",
    "data/chara/inst/inst.lst",
    "data/chara/inst_s/inst_s.tmd",
    "data/chara/inst_s/inst_s.lst",
    "data/chara/inst_d/inst_d.tmd",
    "data/chara/inst_d/inst_d.lst",
    "data/mcard/engl/pages.bin",
    "data/mcard/japa/pages.bin",
    "data/mcard/engl/pagel.bin",
    "data/mcard/japa/pagel.bin",

    # From GFDM
    "fpga_mp3.bin",
    "ir_id.bin",
    "net_id.bin",
    "kfont8.bin",
    "ascii_size8.bin",
    "ascii_size16.bin",
    "ascii_size24.bin",
    "music_info.bin",
    "course_info.bin",
    "group_list.bin",
    "jp_title.bin",
    "got11j1b.bin",
    "got11j0b.bin",
    "got11hlf.bin",
    "d_res_ns.dat",
    "d_ending.dat",
    "d_title.dat",
    "d_cautio.dat",
    "g_id.dat",
    "d_title_aa.dat",
    "d_cautio_aa.dat",
    "a.pak",
    "system.vas",

    # Mambo a Gogo
    "dl/n1/pathtab.bin",
    "data/kanji/eames.cmp",
    "data/spu/system.vas",
    "soft/s573/overlay/bin/dbugtest.olb",
    "soft/s573/overlay/bin/gtest.olb",
    "soft/s573/overlay/bin/play.olb",
    #"data/mp3/sample/",
    # "soft/s573/overlay/bin/fpga_mp3.olb", # There's a fpga_mp3_new.bin somewhere in here but I have no idea what filename it's using
]

# start DDR data
for filename in ['cddana', 'scrob_25', 'scrbk_16', 're2424', 'acxx28', 'ccsaca', 'ccrgca', 'ccltaa', 'ccitaa', 'ccheaa', 'ccdrga', 'ccddra', 'cccuba', 'ccclma', 'ccclca', 'title']:
    pccard_filenames.append("data/movie/common/%s.sbs" % filename)

for filename in ['hwrlja', 'hwfroa', 'hwnora', 'hwhaja']:
    pccard_filenames.append("data/movie/howto/%s.sbs" % filename)

for filename in ["x"] + ["cos%02d" % x for x in range(0, 100)] + ["non%02d" % x for x in range(0, 100)]:
    for part in ['nm', 'in', 'ta', 'th', 'bk']:
        for ext in ['cmt', 'tim']:
            pccard_filenames.append("data/course/%s_%s.%s" % (filename, part, ext))

song_table = [
    "have", "that", "kung", "smok", "boom", "badg", "lets", "boys", "butt", "puty", "bril", "puty2", "bril2", "make", "make2", "myfi",
    "stri", "dubi", "litt", "stom", "hero", "getu", "ifyo", "ibel", "star", "trip", "para", "sptr", "para2", "elri", "tubt", "love",
    "parh", "ajam", "clea", "luvm", "this", "thin", "keep", "imth", "nove", "nove2", "inth", "race", "jamj", "begi", "doyo", "over",
    "five", "gamb", "bein", "emot", "sogr", "sala", "mix", "drlo", "gmdd", "melt", "divi", "perf", "rthr", "dunk", "deep", "skaa",
    "spec", "prin", "cele", "grad", "luvt", "youm", "been", "floj", "ther", "pats", "quee", "into", "inyo", "geno", "gent", "ckee",
    "mach", "cpar", "rugg", "cbri", "nazo", "sogr2", "twen2", "over2", "dunk2", "rthr2", "skaa2", "spec2", "deep2", "grad2", "upan", "xana",
    "upsi", "iton", "soma", "doit", "oper", "volf", "rock", "foll", "hbut", "ohni", "cans", "mrwo", "etup", "hboo", "damd", "holi",
    "capt", "turn", "flas", "wond", "afro", "endo", "dyna", "dead", "lase", "sile", "rebi", "dluv", "djam", "dgra", "dgen", "cpar2",
    "cpar3", "afte", "cuti", "theb", "virt", "amcs", "theg", "gimm", "bumb", "kher", "drop", "stop", "wild", "letb", "sprs", "hyst",
    "pevo", "walk", "pink", "musi", "kick", "only", "eaty", "adre", "oose", "seve", "shak", "neve", "youn", "gotc", "hhav", "heat",
    "shoo", "onet", "nigh", "hboy", "sain", "ninz", "baby", "clim", "burn", "gher", "naha", "bfor", "agai", "hypn", "summ", "hify",
    "hdam", "hher", "talk", "lead", "teng", "olic", "eran", "lety", "your", "onts", "getm", "vide", "groo", "midn", "orio", "shar",
    "nana", "kyhi", "cafe", "cong", "nite", "sexy", "cats", "sync", "onda", "dome", "lupi", "rhyt", "them", "alla", "ldyn", "feal",
    "stil", "ecst", "abso", "brok", "dxyy", "mrtt", "tequ", "iwas", "hotl", "elec", "peta", "roma", "twis", "ones", "lbfo", "beto",
    "ponp", "mats", "reme", "estm", "noli", "myge", "cube", "abys", "sana", "moon", "ever", "movi", "righ", "trib", "oops", "dive",
    "gain", "pafr", "radi", "inse", "lcan", "miam", "samb", "dont", "leth", "wayn", "ialv", "toge", "gtof", "gtup", "mama", "frky",
    "lmac", "club", "stru", "fore", "aliv", "skyh", "oflo", "tipi", "idon", "dril", "kiss", "drea", "lett", "roov", "heal", "look",
    "itri", "onth", "styl", "nori", "cent", "lovi", "ordi", "ghos", "some", "fant", "witc", "oyou", "ollo", "offu", "mira", "twil",
    "cowg", "tele", "just", "imin", "etsg", "byeb", "then", "wwwb", "maxx", "true", "mysw", "frec", "sode", "fire", "yozo", "exot",
    "cand", "ruee", "kind", "soin", "long", "maxi", "youl", "waka", "abyl", "drte", "esti", "inam", "amin", "swee", "snow", "refl",
    "sofa", "drif", "itsr", "stay", "secr", "ittl", "rain", "unli", "toth", "tsug", "roll", "opti", "noth", "anta", "ifee", "andy",
    "spin", "tran", "atus", "than", "thew", "kaku", "afro3", "star3", "bril3", "bfor3", "drop3", "dyna3", "hyst3", "mats3", "sexy3", "sprs3",
    "stil3", "wild3", "burn3", "tsug3", "ecst3", "sile3", "nite3", "gher3", "summ3", "stro", "didi", "cari", "thev", "tryt", "iwan", "cott",
    "thet", "wast", "aaro", "fivs", "like", "team", "what", "with", "anyw", "memo", "cras", "yeby", "tell", "vani", "tomp", "itr2",
    "jamm", "logi", "loo2", "blas", "peac", "imfo", "shin", "bom2", "ddyn", "morn", "ylea", "dark", "ilik", "sand", "mcut", "brou",
    "keon", "mode", "tomo", "suns", "surv", "laco", "wewi", "irre", "cart", "spee", "issk", "suga", "lamo", "imgo", "stin", "thel",
    "game", "jane", "mobo", "belo", "ledl", "radu", "vvvv", "aaaa", "wear", "idoi", "colo", "tayy", "meal", "wite", "froz", "mess",
    "feel", "daik", "maho", "hold", "jetw", "wedd", "surv3", "bagg", "lege", "aois", "mike", "yncc", "stoi", "tars", "ichi", "gene",
    "xeno", "saku", "rose", "heav", "hype", "laba", "ddre", "ripm", "airr", "thef", "tear", "seno", "acro", "rand", "funk", "tryl",
    "itr3", "loo3", "kind3", "frve", "satn", "myfa", "yogo", "dsmo", "badt", "dsco", "cant", "addi", "itta", "iwou", "sigh", "lcat",
    "lcat2", "urbo", "oste", "frea", "whey", "alit", "stea", "mize", "inee", "cmon", "days", "grin", "stal", "getd", "take", "teen",
    "wann", "stup", "scor", "ofec", "allt", "dcal", "aven", "foca", "juar", "stbe", "bain", "illi", "visi", "dizy", "vity", "msic",
    "getb", "wont", "deux", "maxp", "wan2", "canb", "inee2", "simp", "ving", "ride", "come", "parb", "fory", "enjo", "west", "loco",
    "onem", "plan", "ofsu", "hump", "mick", "free", "stas", "kids", "viva", "ente", "sunl", "rela", "ine3", "move", "rapp", "shur",
    "ymca", "supe", "nout", "prom", "inda", "beli", "biza", "ladi", "call", "volt", "gott", "fami", "lyou", "wait", "virg", "rage",
    "chih", "jama", "good", "okok", "come2", "eart", "abs2", "anly", "babx", "bail", "bald", "batt", "bt4u", "eyes", "fdub", "geti",
    "gorg", "inff", "infi", "ins2", "kee2", "kybm", "madb", "matj", "mean", "mgs2", "mind", "nems", "oute", "put3", "quic", "san2",
    "swon", "whas", "diam", "smap", "odor", "gaku", "hone", "kise", "tuff", "chai", "dizz", "girl", "mixe", "thes", "yous", "kunc",
    "lady", "oody", "frid", "hipt", "midd", "dipi", "shou", "geni", "wonn", "asth", "bloc", "busy", "mich", "mymy", "ilen", "pres",
    "worl", "opsi", "iwsu", "spsp", "pump", "fnkm", "wona", "craz", "myma", "lose", "polo", "oran", "diff", "mari", "tmrr", "sedu",
    "insi", "inje", "pass", "youg", "nine", "ridl", "mine", "gtwo", "zero", "rout", "luvu", "vjar", "rten", "lovd", "catc", "voya",
    "flyt", "hitn", "mids", "toej", "monk", "istn", "redr", "bais", "cuca", "gyru", "jamd", "tenr", "imem", "itoy", "remx", "popn",
    "banz", "brin", "hipe", "letd", "stck", "vola", "choo", "skrb", "inje2", "doll", "ifut", "evrd", "aaaa2", "rzon", "hpan", "xeph",
    "hima", "drab", "curu", "muge", "nizi", "gekk", "kono", "mooo", "thir", "dand", "kage", "tika", "unde", "time", "rara", "braz",
    "taur", "tier", "sksk", "okor", "murm", "flya", "inno", "myon", "flow", "rbow", "bala", "gate", "fold", "long2", "mgir", "alov",
    "sigh2", "daba", "toxi", "waww", "laba2LA", "jerk", "fasc", "lare", "punc", "eace", "gold", "glor", "dayd", "mond", "cach", "driv",
    "qmas", "stop2", "dyna2", "surr", "sedu2", "hunt", "daca", "give", "does", "chao", "bred", "colo2", "lab3", "illm", "fjus", "tlov",
    "btea", "wowo", "dvis", "hana", "flow2", "fasc2", "comc", "fain", "meag", "flya2", "soul", "gate2", "moos", "flow3", "felw", "silv",
    "trim", "fnky", "leff", "shiv", "ikno", "sinc", "such", "theo", "onew", "runi", "dare", "trno", "doyw", "city", "bttw", "sorr",
    "yoex", "mams", "chec", "whyr", "soss", "danc", "galv", "numb", "gett", "brkf", "blab", "prnc", "sosi", "temp", "dscc", "robo",
    "beau", "btea2", "biol", "hood", "godi", "rome", "rhrn", "brui", "soni", "onme", "said", "jacq", "heyb", "step", "luft", "cloc",
    "fina", "gonn", "hots", "karm", "byou", "risa", "sign", "ysme", "fara", "lips", "conm", "alie", "fied", "mitr", "mala", "rasp",
    "bloo", "agir", "mber", "lefr", "subu", "unbe", "prol", "hook", "ofth", "reas", "fast", "ange", "csto", "lste", "unwr", "dazz",
    "fway", "alwa", "infe", "tlel", "buty", "away", "caug", "gyps", "flik", "memi", "unap", "bmon", "stim", "tltl", "lshi", "bdow",
    "spar", "cufo", "acol", "conf", "leti", "will", "lits", "touc", "ifly", "wwlt", "hand", "ngon", "higo", "tbea", "bins", "mwit",
    "trea", "samu", "ucha", "tigh", "ryou", "tobe", "onmy", "andt", "sudd", "toky", "orig", "aint", "ngoo", "smac", "btol", "firr",
    "unre", "stah", "skan", "hesa", "cbac", "sayg", "feva", "arou", "twom", "vate", "venu", "blin", "athi", "wind", "uber", "arra",
    "dori", "unti", "trix", "vemb", "eter", "dofl", "volc", "eday", "plut", "sunr", "pard", "swit", "alth", "bbbu", "favo", "nomo",
    "trus", "plur", "lamd", "votu", "jupi", "sunj", "uran", "mars", "whyn", "shad", "gili", "pose", "bris", "amch", "dtwf", "dyns",
    "bfov", "deag", "sune", "satu", "tloc", "pluf", "bfos", "doub", "smil", "puzz", "leav", "timh", "saga", "cara", "ontb", "feee",
    "ghet", "mcry", "trac", "waiu", "drem", "disn", "fotl", "bibb", "ball", "tiki", "circ", "cohm", "wish", "spoo", "hawa", "heme",
    "bout", "cmix", "apir", "cany", "chim", "evry", "ijus", "ltle", "bare", "zadd", "cmar", "wabe", "youc", "stet", "itsa", "supc",
    "devi", "haku", "flig", "tick", "tajh", "sabe", "lovy", "iyhr", "staa", "reac", "want", "noma", "crcs", "trbu", "here", "wine",
    "lift", "flou", "taka", "boyd", "pute", "myde", "umbr", "caom", "niru", "oclo", "allg", "mawo", "reda", "feto", "slac", "blac",
    "cahe", "toot", "wasu", "ican", "iran", "wego", "youi", "evda", "dane", "thom", "stre", "hetr", "mmla", "djgo", "icei", "duck",
    "mcmi", "almy", "heit", "happ", "ucan", "play", "dace", "slip", "hora", "bust", "dyou", "obse", "bigg", "bene", "tare", "sare",
    "slre", "dacr", "jube", "esce", "sett", "soyo", "suhe", "unit", "open", "mylo", "opee", "soun", "butt2", "boys2", "thli", "ttlg",
    "clos", "orig2", "kyou", "dmin", "weve", "synt", "dubi2", "getu2", "hero2", "reup", "weco", "insp", "onbo", "trig", "danf", "weca",
    "raci", "dese", "sidr", "thlo", "habi", "osak1", "osak2", "osak3", "xmix1", "xmix2", "xmix3", "xmix4", "xmix5", "rint", "turk", "jung",
    "blue", "zerr", "purp", "brea", "sust", "crgo", "bigt", "reso", "trav", "hous", "ours", "crim", "blra", "chan", "koko", "parx",
    "trxs", "parx2", "sptx", "rebx", "afrx", "pevx", "clix", "petx", "feax", "canx", "xmax", "unlx", "kakx", "legx", "ddrx", "xpar",
    "geis", "tric", "seka", "suki", "tabi", "cspa", "cssp", "inlo", "sttb", "pori", "less", "geis2", "eoti", "tone", "bewi", "orig3",
    "ropp1", "prds", "ille", "hott1", "hott2", "sabe2", "sidr2", "dyna4", "newg", "nows", "taki", "dist", "detr", "drdr", "imco", "priv",
    "teme", "frez", "haun", "wick", "sosp", "thei", "jena", "sacr", "wwcm", "vila", "clsr", "iceb", "daft", "canu", "rist", "pock",
    "nver", "hung", "boog", "gtim", "vood", "fego", "sout", "twau", "curr", "tame", "iair", "ahla", "down", "spac", "rnow", "ensi",
    "bbay", "shie", "lvag", "bona", "pork", "mypr", "onst", "laca", "ikny", "inty", "imag", "nost", "hien", "grav", "hest", "tasf",
    "inzo", "ttim", "eine", "kimp", "shlo", "dokn", "lget", "juda", "when", "abri", "bene2", "yyou", "drec", "thni", "geba", "theh",
    "goda", "sowa", "elrt", "ceye", "aper", "youa", "seul", "lali", "unen", "letg", "larc", "prai", "clju", "crco", "ropp", "smoo",
    "seco", "poss", "huch", "fifi", "dada", "allm", "cgpr", "whro", "skyi", "shei", "tako", "onra", "ifyo2", "ezdo", "beyo", "sasu",
    "ropp1", "ropp2", "ropp3", "ropp4", "aftr", "delt", "dirt", "dumm", "oarf", "sak2", "thr8", "yoan", "rezo", "zeta", "anti", "batf_c",
    "capt2", "dada2", "damd2", "droo", "etny", "goru", "goup_c", "hide", "ifut_c", "vane", "tens", "sueu", "sudr", "shwo", "shng", "sday",
    "pose2", "pier", "nizi_c", "newd", "momo", "melo_c", "meii", "maxl_c", "lvng_c", "issk2", "ifyo3", "melo", "maxl", "lvng", "goup", "batf",
    "valk", "titi", "evti", "pier", "imso", "toet", "alst", "amal", "angl", "bere", "cbtm", "chro", "cone", "dids", "dorm", "dree",
    "feve", "futu", "fwer", "geba", "haun", "hbfo", "hevy", "hien1", "hien2", "hien3", "hrtb", "illf", "ioio", "lanj", "litp", "meme",
    "merm", "mesg", "mprd", "neph", "newb", "nyev1", "nyev2", "nyev3", "pavo", "priv", "prog", "rebo", "rthm", "ryor", "seul", "shiz",
    "sigs", "snow2", "sson", "stra", "sumi", "tenj", "toho", "toky1", "toky2", "toky3", "trbe", "trvo", "twin", "ublv", "urlv", "cosh",
    "koen", "rens", "snpr", "revo", "gofo", "keyc", "puda", "trxa", "brak", "paks", "acwo", "airh", "anot", "arms", "bedr", "brig",
    "burs", "cctr", "chew", "chil", "chin", "ckpp", "dail", "deba", "dimo", "dind", "disp", "doth", "elem", "elys", "empa", "engr",
    "fndw", "furi", "fuuf", "gaia", "hevy2", "hosh", "hyen", "iman", "ixix", "jojo", "joke", "kara", "kike", "koih", "lanj2", "lond",
    "magn", "maji", "mawa", "meum", "miga", "mmme", "mobu", "mura", "nagi", "nblw", "negr", "niji", "okom", "oren", "oron", "ostt",
    "pran", "prte", "puni", "raki", "revn", "rint2", "rola", "rryu", "scho", "seit", "sola", "sota", "soth", "sous", "span", "sque",
    "stel", "sthe", "stoa", "stul", "suca", "sumf", "swra", "synf", "todo", "tpch", "trbl", "tuke", "twog", "umum", "vega", "wifa",
    "wisi", "wwve", "yaco", "yaky", "yama", "zutt", "adul", "akhu", "aozo", "asai", "atoz", "awak", "awao", "ayak", "bada", "baku",
    "bamb", "basb", "bbme", "bibi", "boku", "ccch", "chea", "choc", "cive", "cleo", "cody", "czgt", "dete", "dkdk", "doca", "dong",
    "dopa", "edmj", "egoi", "eltr", "endr", "esed", "fiel", "fksb", "foto", "ftsy", "fuji", "geki", "gens", "gogo", "hakt", "hbfo2",
    "hlat", "hlye", "hnmr", "home", "idol", "intb", "joma", "kaiy", "kawa", "kira", "kuro", "llcu", "luck", "maam", "mayu", "miku",
    "mine2", "miso", "mrps", "myco", "myhr", "nage", "nekn", "niko", "noil", "onna", "orrs", "osen", "oslv", "otom", "ovtp", "papi",
    "peit", "pooc", "poss2", "pran2", "ptay", "rair", "raku", "rema", "rusy", "sabl", "sakm", "sans", "scar", "sedm", "setu", "shik",
    "ssca", "ssst", "stfa", "stfa2", "strb", "strg", "sumd", "syak", "syun", "tenk", "tiho", "tnaw", "totu", "tsub", "wada", "wech",
    "xmas", "yaoy", "aeth", "waa1", "tel3", "bud4", "bye5", "fac6", "sen7", "bak8", "kor7", "kor8", "kor2", "korc", "kor9", "kora",
    "twen", "inst", "name", "rank", "scal", "selc", "sele", "stae", "staf",
]

for filename in song_table:
    pccard_filenames.append("data/mdb/%s/all.csq" % filename)
    pccard_filenames.append("data/mdb/%s/all.ssq" % filename)

    for part in ['nm', 'in', 'ta', 'th', 'bk']:
        for ext in ['cmt', 'tim']:
            pccard_filenames.append("data/mdb/%s/%s_%s.%s" % (filename, filename, part, ext))

anim_table = ['mfjc1', 'mfjb1', 'mfja1', 'mljc1', 'mljb1', 'mlja1', 'mrsc1', 'mrsb1', 'mrsa1', 'mfsc1', 'mfsb1', 'mfsa1', 'mbsc1', 'mbsb1', 'mbsa1', 'mlsc1', 'mlsb1', 'mlsa1', 'mnor1']
for filename in anim_table:
    pccard_filenames.append("data/anime/%s/%s.can" % (filename, filename))
    pccard_filenames.append("data/anime/%s/%s.anm" % (filename, filename))

def parse_rembind_filenames(data):
    hash_list_add = {}
    entries = len(data) // 0x30

    for i in range(entries):
        for region in ['span', 'ital', 'germ', 'fren', 'engl', 'japa']:
            filename = data[i*0x30+0x10:i*0x30+0x28].decode('ascii').strip('\0')
            filename = "data/%s.cmt" % filename
            filename = filename.replace("japa/", "%s/" % region)
            hash_list_add[get_filename_hash(filename)] = filename

    return hash_list_add


def parse_mdb_filenames(data):
    hash_list_add = {}

    for i in range(len(data) // 0x80):
        if data[i*0x80] == 0:
            break

        filename = data[i*0x80:i*0x80+6].decode('ascii').strip('\0').strip()

        if filename in song_table:
            continue

        print(filename)

        path = "data/mdb/%s/all.csq" % filename
        hash_list_add[get_filename_hash(path)] = path

        path = "data/mdb/%s/all.ssq" % filename
        hash_list_add[get_filename_hash(path)] = path

        for part in ['nm', 'in', 'ta', 'th', 'bk']:
            for ext in ['cmt', 'tim']:
                path = "data/mdb/%s/%s_%s.%s" % (filename, filename, part, ext)
                hash_list_add[get_filename_hash(path)] = path

    return hash_list_add
# end DDR data


# start GFDM data
def parse_group_list_filenames(data):
    hash_list_add = {}

    for i in range(len(data) // 0x20):
        filename = data[i*0x20:(i+1)*0x20].decode('ascii').strip('\0')

        path = "%s.fcn" % (filename)
        hash_list_add[get_filename_hash(path)] = path

    return hash_list_add

# end GFDM data

# start Mambo a Gogo data
for filename in ["'uhiy", "lhiy", "cygp", "cygl", "gunm", "geng", "genr", "genb", "brow", "sung", "spym", "uhir", "lhir", "sabo", "cong", "samr", "samg", "samy", "yase", "debu", "ygir", "rgir", "furc", "furb", "fura"]:
    pccard_filenames.append("data/puppet/%s.pup" % filename)

for x in range(0, 100):
    pccard_filenames.append("data/motion/motion%d.bin" % x)

def parse_mdb_mambo_filenames(data):
    hash_list_add = {}

    for i in range(len(data) // 0x2c):
        if data[i*0x2c] == 0:
            break

        filename = data[i*0x2c:i*0x2c+6].decode('ascii').strip('\0').strip()

        if filename in song_table:
            continue

        print(filename)

        path = "data/mdb/%s/all.csq" % filename
        hash_list_add[get_filename_hash(path)] = path

        path = "data/mdb/%s/all.ssq" % filename
        hash_list_add[get_filename_hash(path)] = path

        for part in ['nm', 'in', 'ta', 'th', 'bk']:
            for ext in ['cmt', 'tim']:
                path = "data/mdb/%s/%s_%s.%s" % (filename, filename, part, ext)
                hash_list_add[get_filename_hash(path)] = path

    return hash_list_add
# end Mambo a Gogo data


def read_file_table(filename, table_offset):
    files = []

    with open(filename, "rb") as infile:
        infile.seek(table_offset, 0)

        while True:
            filename_hash, offset, flag_loc, flag_comp, flag_enc, unk, filesize = struct.unpack("<IHHBBHI", infile.read(0x10))

            if offset == 0xffffffff or filename_hash == 0:
                break

            files.append({
                'idx': len(files),
                'filename_hash': filename_hash,
                'offset': offset * 0x800,
                'filesize': filesize,
                'flag_loc': flag_loc,
                'flag_comp': flag_comp,
                'flag_enc': flag_enc,
            })


    return files

def read_file_table_mambo(filename, table_offset):
    files = []

    with open(filename, "rb") as infile:
        infile.seek(table_offset, 0)

        while True:
            filename_hash, offset, flag_loc, flag_comp, flag_enc, unk, filesize = struct.unpack("<IHHBBHI", infile.read(0x10))

            if offset == 0xffffffff or filename_hash == 0:
                break

            files.append({
                'idx': len(files),
                'filename_hash': filename_hash,
                'offset': offset * 0x800,
                'filesize': filesize,
                'flag_loc': flag_loc,
                'flag_comp': flag_comp,
                'flag_enc': flag_enc,
            })


    return files

def read_file_table_gfdm(filename, table_offset):
    files = []

    with open(filename, "rb") as infile:
        infile.seek(table_offset, 0)

        while True:
            filename_hash, offset, filesize, flag = struct.unpack("<IIII", infile.read(0x10))

            if offset == 0xffffffff or filename_hash == 0:
                break

            files.append({
                'idx': len(files),
                'filename_hash': filename_hash,
                'offset': offset,
                'filesize': filesize,
                'flag_loc': 0,
                'flag_comp': 0,
                'flag_enc': 0,
            })

    return files


def get_file_data(fileinfo, enckey=None):
    card_filename = None

    if os.path.exists("PCCARD.DAT"):
        card_filename = "PCCARD.DAT"

    elif os.path.exists("CARD.DAT"):
        card_filename = "CARD.DAT"

    game = open("GAME.DAT", "rb") if os.path.exists("GAME.DAT") else None
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
        data = decode_lz(data)

    return bytearray(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', help='Input folder', default=None, required=True)
    parser.add_argument('--output', help='Output folder', default="output")
    parser.add_argument('--key', help='Encryption key', choices=['EXTREME', 'EURO2', 'MAX2', 'DDR5', 'MAMBO'])
    parser.add_argument('--type', help='Game Type', choices=['ddr', 'gfdm-old', 'gfdm', 'mambo'])
    parser.add_argument('--no-metadata', help='Do not save metadata file', default=False, action='store_true')

    args = parser.parse_args()

    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)

    if args.type == "ddr":
        files = read_file_table(os.path.join(args.input, "GAME.DAT"), 0xFE4000)

    elif args.type == "gfdm-old":
        files = read_file_table_gfdm(os.path.join(args.input, "GAME.DAT"), 0x180000)

    elif args.type == "gfdm":
        files = read_file_table_gfdm(os.path.join(args.input, "GAME.DAT"), 0x198000)

    elif args.type == "mambo":
        files = read_file_table_mambo(os.path.join(args.input, "GAME.DAT"), 0xFE4000)

    else:
        print("Unknown format!")
        exit(1)

    hash_list = {}
    for filename in pccard_filenames:
        hash_list[get_filename_hash(filename)] = filename

    for idx, fileinfo in enumerate(files):
        if fileinfo['filename_hash'] in hash_list:
            if args.type in ["ddr", "mambo"]:
                if hash_list[fileinfo['filename_hash']] == "data/tex/rembind.bin":
                    hash_list.update(parse_rembind_filenames(get_file_data(fileinfo, args.key)))

            if args.type == "ddr":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list.update(parse_mdb_filenames(get_file_data(fileinfo, args.key)))

            elif args.type == "mambo":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list.update(parse_mdb_mambo_filenames(get_file_data(fileinfo, args.key)))

            elif args.type in ["gfdm", "gfdm-old"]:
                if hash_list[fileinfo['filename_hash']] == "group_list.bin":
                    hash_list.update(parse_group_list_filenames(get_file_data(fileinfo, args.key)))

    for idx, fileinfo in enumerate(files):
        if fileinfo['filename_hash'] in hash_list:
            if args.type in ["ddr", "mambo"]:
                if hash_list[fileinfo['filename_hash']] == "data/tex/rembind.bin":
                    hash_list.update(parse_rembind_filenames(get_file_data(fileinfo, args.key)))

            if args.type == "ddr":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list.update(parse_mdb_filenames(get_file_data(fileinfo, args.key)))

            elif args.type == "mambo":
                if hash_list[fileinfo['filename_hash']] == "data/mdb/mdb.bin":
                    hash_list.update(parse_mdb_mambo_filenames(get_file_data(fileinfo, args.key)))

    for idx, fileinfo in enumerate(files):
        output_filename = "_output_%08x.bin" % (fileinfo['filename_hash'])

        if fileinfo['offset'] == 0x7c0000:
            print("%08x" % fileinfo['offset'], fileinfo)

        if fileinfo['filename_hash'] in hash_list:
            output_filename = hash_list[fileinfo['filename_hash']]

            if output_filename.startswith("/"):
                output_filename = "_" + output_filename[1:]

        else:
            print("Unknown hash %08x" % fileinfo['filename_hash'], output_filename)

        files[idx]['filename'] = output_filename

        output_filename = os.path.join(args.output, output_filename)

        if os.path.exists(output_filename):
            continue

        filepath = os.path.dirname(output_filename)
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        print(fileinfo)
        print("Extracting", output_filename)
        with open(output_filename, "wb") as outfile:
            data = get_file_data(fileinfo, args.key)
            outfile.write(data)

    if not args.no_metadata:
        json.dump(files, open(os.path.join(args.output, "_metadata.json"), "w"), indent=4)
