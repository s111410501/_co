import sys
from pathlib import Path

# 1. 定義 C-指令對照表
COMP_TABLE = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101",
    "!A": "0110001", "-D": "0001111", "-A": "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
    "D|M": "1010101",
}

JUMP_TABLE = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}


def assemble_lines(raw_lines: list[str]) -> list[str]:
    """將 Hack 組合語言字串列表轉譯為 16-bit 二進位字串列表"""
    # 初始化預設符號表 (R0~R15 及系統指標)
    symbols = {f"R{i}": i for i in range(16)}
    symbols.update({
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 16384, "KBD": 24576,
    })

    # 清理註解與空白字元
    cleaned_lines = []
    for line in raw_lines:
        cmd = line.split("//")[0].replace(" ", "").strip()
        if cmd:
            cleaned_lines.append(cmd)

    # Pass 1: 掃描 (LABEL) 標籤並記錄對應的 ROM 行號
    instructions = []
    for cmd in cleaned_lines:
        if cmd.startswith("(") and cmd.endswith(")"):
            label = cmd[1:-1]
            symbols[label] = len(instructions)
        else:
            instructions.append(cmd)

    # Pass 2: 翻譯 A-指令 與 C-指令，並動態配置變數
    next_var_addr = 16
    machine_code = []

    for cmd in instructions:
        if cmd.startswith("@"):
            # A-指令處理
            token = cmd[1:]
            if token.isdigit():
                addr = int(token)
            else:
                if token not in symbols:
                    symbols[token] = next_var_addr
                    next_var_addr += 1
                addr = symbols[token]
            machine_code.append(f"{addr:016b}")
        else:
            # C-指令處理: 解析 dest=comp;jump
            dest, _, rest = cmd.partition("=") if "=" in cmd else ("", "=", cmd)
            comp, _, jump = rest.partition(";")

            comp_bits = COMP_TABLE[comp]
            dest_bits = "".join("1" if reg in dest else "0" for reg in "ADM")
            jump_bits = JUMP_TABLE[jump]

            machine_code.append(f"111{comp_bits}{dest_bits}{jump_bits}")

    return machine_code


def assemble_file(filepath: str):
    """讀取 .asm 檔案並輸出 .hack 檔案"""
    path = Path(filepath)
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    hack_lines = assemble_lines(raw_lines)

    out_path = path.with_suffix(".hack")
    out_path.write_text("\n".join(hack_lines) + "\n", encoding="utf-8")
    print(f"組譯完成：{out_path} (共 {len(hack_lines)} 行機器碼)")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # 支援一次轉譯一個或多個 .asm 檔案
        for arg in sys.argv[1:]:
            assemble_file(arg)
    else:
        # 未帶參數時，執行內建測試範例 (計算 R0 = 2 + 3 並包含迴圈標籤與變數)
        sample_asm = [
            "// 測試程式：計算 2 + 3 並存入變數 sum",
            "@2",
            "D=A",
            "@3",
            "D=D+A",
            "@sum",
            "M=D",
            "(END)",
            "@END",
            "0;JMP",
        ]
        print("--- 執行內建測試範例 ---")
        result = assemble_lines(sample_asm)
        code_index = 0
        for asm in sample_asm:
            cmd = asm.split("//")[0].replace(" ", "").strip()
            if not cmd:
                continue
            if cmd.startswith("(") and cmd.endswith(")"):
                bin_code = "(標籤不佔位)"
            else:
                bin_code = result[code_index]
                code_index += 1
            print(f"{asm:<10} -> {bin_code}")
