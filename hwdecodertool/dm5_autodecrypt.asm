.psx
.open "dm5th-hack/GAME.DAT", 0x80010000 - 0x60000 - 0x800

; Skip program checksums during boot (BOOT ROM, not program)
.orga 0x00002ee3
    .byte 0x10

.org 0x80023f48
    SetFpgaKey1:

.org 0x8002425c
    SetFpgaKey2:

.org 0x80024284
    SetFpgaKey3:

.org 0x800208dc
    LoadMp3:

.org 0x80153444
    InputFileCount:

.macro draw_text_ptr,x,y
    li a0, x
    li a1, y
    jal 0x800550f8
    nop
.endmacro

.macro draw_text,x,y,text
    li a2, text
    draw_text_ptr x, y
.endmacro

.macro draw_text_printf,x,y,text
    ; Reminder: This requires a3 to be set with value to print in printf string
    li a0, x
    li a1, y
    addi a0, 30
    addi a1, 80
    li a2, text
    jal 0x800563ec
    nop
.endmacro

.macro draw_progress_text,x,y
    li a1, CurrentFileIndex
    lw a3, 0(a1)
    nop
    addi a3, 1
    draw_text_printf x, y, ProgressString

    li a0, InputFileCount
    lw a3, 0(a0)
    nop
    draw_text_printf x, y + 20, ProgressString2

.endmacro

.macro increment_file
    ; Move to the next file
    li a3, CurrentFileIndex
    lw a2, 0(a3)
    nop

    addi a2, 1
    sw a2, 0(a3)
    nop

    li a3, CurrentFilePointer
    lw a2, 0(a3)
    nop

    bnez a2, @@SkipInitializePointer
    nop

    li a2, 0x80153402

@@SkipInitializePointer:
    addi a2, 0x46
    sw a2, 0(a3)
    nop

    addi a2, 0x06
    sw a2, 8(a3)
    nop
.endmacro

; Tool version string
.org 0x800110b9
    .ascii 7, "1.0", 0

; FRE_LIST -> DEC_LIST
.org 0x80010b64
    .ascii "/DATA5/DEC_LIST.BIN", 0


; Custom code area overwriting network menu code
.org 0x800a8844
    ; Make this function return automatically (assuming it doesn't crash on return) so we can overwrite the actual code
    jr ra
    addiu sp, 0x28

DecryptionMenuString:
    .ascii "System 573 Digital Audio Decryption Tool", 0

NowDecryptingString:
    .ascii 1, "Now decrypting...", 0

FinishedDecryptingString:
    .ascii 2, "Finished decrypting!", 0

FinishedDecryptingString2:
    .ascii 2, "Please turn off the machine now.", 0, 0, 0, 0

ProgressString:
    .ascii 1, "Current: %4d", 0, 0, 0

ProgressString2:
    .ascii 1, "Total: %4d", 0, 0

DecoderStatus:
    .ascii 1, "Debug: ", 5

DecoderStatusValue:
    .ascii "%d", 0

CurrentFileIndex:
    .dd -1

DecoderStatusFlag:
    .dd 0

CurrentFilePointer:
    .dd 0 ; The address where the data should be stored

CurrentFilenamePointer:
    .dd 0 ; CurrentFilePointer + 5 to skip directly to the filename

CurrentSp:
    .dd 0

DrawOnScreenText:
    nop
    nop

    li a3, CurrentSp
    sw sp, 0(a3)

    ; Check if MP3 is already being played
    li a3, 0x80130428
    lw a3, 0(a3)
    nop

    ; If one is, reset the internal state to 0 and wait for the device to stop playing audio
    beq a3, 1, @@SkipMp3Load
    nop

    bnez a3, @@SkipMp3LoadPre
    nop

    ; Check the internal state to see if we're waiting for the decoder to start or not
    li a3, DecoderStatusFlag
    lw a3, 0(a3)
    nop

    ; If the decoder hasn't started but has been requested to start, then skip over the start code
    bnez a3, @@SkipMp3Load
    nop

    increment_file

    ; Start playing new MP3 data
    jal 0x8003FEF4
    nop

    ; This is a hacky workaround because for some reason it returns to this location twice... :\
    li a3, DecoderStatusFlag
    lw a3, 0(a3)
    nop
    bnez a3, @@SkipMp3Load
    nop

    ; Set internal state to having requested start playback
    li a3, DecoderStatusFlag
    li a2, 1
    sw a2, 0(a3)

    j @@SkipMp3Load
    nop

@@SkipMp3LoadPre:
    li a3, DecoderStatusFlag
    li a2, 0
    sw a2, 0(a3)


@@SkipMp3Load:
    ; Draw middle header
    li a0, InputFileCount
    lw a0, 0(a0)
    nop

    li a1, CurrentFileIndex
    lw a1, 0(a1)
    nop

    bne a0, a1, @@DisplayDecryptingString
    nop

    draw_text 255, 128, FinishedDecryptingString
    draw_text 255, 148, FinishedDecryptingString2

    j @@DisplayDebugStrings

@@DisplayDecryptingString:
    draw_progress_text 160, 0
    draw_text 255, 128, NowDecryptingString

    li a0, CurrentFilePointer
    lw a2, 8(a0)
    draw_text_ptr 255, 160

@@DisplayDebugStrings:
    ; Draw memory debug strings
    li a3, 0x80130420
    lw a3, 0(a3)
    nop
    draw_text_printf 160, 60, DecoderStatus

    li a3, 0x80130424
    lw a3, 0(a3)
    nop
    draw_text_printf 160, 80, DecoderStatus

    li a3, 0x80130428
    lw a3, 0(a3)
    nop
    draw_text_printf 160, 100, DecoderStatus

    li a3, CurrentSp
    lw sp, 0(a3)
    nop

    j DrawOnScreenTextReturn
    nop

CopyFilenamePointer:
    li a2, CurrentFilenamePointer
    lw a2, 0(a2)

    jal LoadMp3
    nop

    j CopyFilenamePointerReturn
    nop


HookKey1:
    li v0, CurrentFilePointer
    lw v0, 0(v0)
    nop

    beqz v0, @@NoKeyAvailable
    nop

    lhu a0, 0(v0)
    nop

@@NoKeyAvailable:
    li v0, 0x1f6400a8

    j HookKey1Return
    nop


HookKey2:
    li v0, CurrentFilePointer
    lw v0, 0(v0)
    nop

    beqz v0, @@NoKeyAvailable
    nop

    lhu a0, 2(v0)
    nop

@@NoKeyAvailable:
    li v0, 0x1F6400EA

    j HookKey2Return
    nop


HookKey3:
    li v0, CurrentFilePointer
    lw v0, 0(v0)
    nop

    beqz v0, @@NoKeyAvailable
    nop

    lbu a0, 4(v0)
    nop

@@NoKeyAvailable:
    li v0, 0x1F6400EC

    j HookKey3Return
    nop

; Change header of main menu
.org 0x8003cce4
    lui a2, 0x800b
    jal 0x8005645c
    addiu a2, a2, -0x77b4

; Replace bottom text function call with own on screen text call
.org 0x8003c97c
    nop

; Remove menu text
.org 0x8003c98c
    j DrawOnScreenText
    nop
    DrawOnScreenTextReturn:

; Disable button press menus pt1
.org 0x8003c9b4
    nop

; Disable button press menus pt2
.org 0x8003c9dc
    nop

; Disable button press menus pt3
.org 0x8003c9f4
    nop


.org 0x8003FFA8
    j CopyFilenamePointer
    nop
    nop
CopyFilenamePointerReturn:


; Key 1
.org 0x800224b4
    j HookKey1
    nop
    HookKey1Return:

; Key 2
.org 0x80022724
    j HookKey2
    nop
    HookKey2Return:

; Key 3
.org 0x8002274C
    j HookKey3
    nop
    HookKey3Return:

.close
