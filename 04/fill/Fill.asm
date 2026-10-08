// Fill.asm
// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, the
// program clears the screen, i.e. writes "white" in every pixel.

(LOOP)
    // 1. 讀取鍵盤狀態
    @KBD
    D=M

    // 2. 判斷是否有按鍵：若 D != 0 則跳轉到 SET_BLACK，否則跳轉到 SET_WHITE
    @SET_BLACK
    D;JNE

(SET_WHITE)
    // 無按鍵：顏色填 0 (全白)
    @color
    M=0
    @DRAW
    0;JMP

(SET_BLACK)
    // 有按鍵：顏色填 -1 (全黑)
    @color
    M=-1

(DRAW)
    // 3. 初始化繪圖指標與計數器
    @SCREEN
    D=A
    @address
    M=D         // address = SCREEN (16384)

    @8192
    D=A
    @i
    M=D         // i = 8192 (螢幕總共包含 8192 個 16-bit words)

(DRAW_LOOP)
    // 檢查是否已畫完整個螢幕 (i == 0)
    @i
    D=M
    @LOOP
    D;JEQ       // 若 i == 0，畫完回到主迴圈重新檢測鍵盤

    // 將 color 寫入當前螢幕位址
    @color
    D=M
    @address
    A=M
    M=D         // *address = color

    // 更新指標與計數器
    @address
    M=M+1       // address++
    @i
    M=M-1       // i--

    @DRAW_LOOP
    0;JMP       // 繼續繪製下一個 word