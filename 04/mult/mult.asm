// Mult.asm
// Computes R0 * R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

    // 1. 初始化 R2 = 0 (用於累積結果)
    @R2
    M=0

    // 2. 初始化計數器 i = R1
    @R1
    D=M
    @i
    M=D

(LOOP)
    // 3. 檢查計數器是否為 0 (i == 0)
    @i
    D=M
    @END
    D;JEQ       // 若 i == 0，結束計算

    // 4. 將 R0 累加至 R2 (R2 = R2 + R0)
    @R0
    D=M
    @R2
    M=M+D

    // 5. 計數器減 1 (i = i - 1)
    @i
    M=M-1

    // 6. 繼續下一輪迴圈
    @LOOP
    0;JMP

(END)
    // 7. 無限迴圈終止程式 (Hack 組合語言的最佳實踐標準)
    @END
    0;JMP