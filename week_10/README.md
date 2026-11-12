# Hack 組譯器（Assembler）

> 以 Python 實作的 nand2tetris 第 6 章 Hack 組譯器

| 欄位 | 內容 |
|------|------|
| 課程 | 計算機結構 |
| 學期 | 115 學年上學期 |
| 學生 | 李丞晏 |
| 學號 | 01 |
| 程式語言 | Python 3 |
| 對應章節 | nand2tetris Project 6（Assembler） |

---

## 簡介

`assembler.py` 會把 Hack 組合語言（`.asm`）轉譯成 16-bit 機器碼（`.hack`）。
Hack 平台有兩種指令：

- **A-指令**：`@value`，把 15-bit 位址載入 A 暫存器。
- **C-指令**：`dest=comp;jump`，指定運算、目的暫存器與跳躍條件。

組譯器負責把符號（標籤與變數）解析成位址，再輸出對應的二進位字串。

---

## 功能特色

- 支援 **A-指令** 與 **C-指令** 的完整轉譯。
- 內建符號表：`R0`～`R15`、`SP`、`LCL`、`ARG`、`THIS`、`THAT`、`SCREEN`、`KBD`。
- **Pass 1 / Pass 2** 兩階段組譯：
  - Pass 1 掃描 `(LABEL)` 並記錄其對應的 ROM 行號。
  - Pass 2 翻譯指令，並為新出現的變數從位址 16 開始動態配置。
- 自動忽略註解（`//`）與空白。
- 可一次組譯多個 `.asm` 檔案。
- 不帶參數執行時，會跑內建範例（計算 `2 + 3` 並存入變數 `sum`）。

---

## 使用方式

### 組譯檔案

```bash
python assembler.py <file1.asm> [file2.asm ...]
```

輸出檔會與輸入檔同名，副檔名改為 `.hack`：

```bash
python assembler.py Add.asm
# 組譯完成：Add.hack (共 6 行機器碼)
```

### 執行內建範例

```bash
python assembler.py
```

輸出：

```text
--- 執行內建測試範例 ---
@2         -> 0000000000000010
D=A        -> 1110110000010000
@3         -> 0000000000000011
D=D+A      -> 1110000010010000
@sum       -> 0000000000010000
M=D        -> 1110001100001000
(END)      -> (標籤不佔位)
@END       -> 0000000000000110
0;JMP      -> 1110101010000111
```

---

## 組譯流程

```text
讀取 .asm
   │
   ▼
清除註解與空白
   │
   ▼
Pass 1：記錄 (LABEL) 的 ROM 行號
   │
   ▼
Pass 2：翻譯 A-指令 / C-指令、配置變數位址
   │
   ▼
輸出 .hack（每行 16-bit 二進位）
```

### 指令格式

| 指令型別 | 格式 | 說明 |
|----------|------|------|
| A-指令 | `0` + 15-bit 位址 | `@value` |
| C-指令 | `111` + `comp`(7) + `dest`(3) + `jump`(3) | `dest=comp;jump` |

### C-指令範例

`D=D+A` 會被拆解為：

- `comp` = `D+A` → `0000010`
- `dest` = `D` → `001`
- `jump` = 空 → `000`

組合成 `1110000010010000`。

---

## 程式結構

| 函式 | 用途 |
|------|------|
| `assemble_lines(raw_lines)` | 將組合語言字串列表轉譯為機器碼列表 |
| `assemble_file(filepath)` | 讀取 `.asm`、輸出 `.hack` 並印出結果 |

主要資料表：

- `COMP_TABLE`：28 種 `comp` 組合對應的 7-bit 控制位元。
- `JUMP_TABLE`：8 種 `jump` 條件對應的 3-bit 控制位元。

---

## 限制

- 未處理 `dest`／`comp`／`jump` 的語法錯誤，遇到未知符號會直接拋出 `KeyError`。
- 僅支援標準 Hack 組合語言，不含巨集或額外語法。
- 變數位址從 16 開始配置，未檢查是否與既有標籤衝突。

---

## 參考資料

1. nand2tetris 官方網站：<https://www.nand2tetris.org/>
2. The Elements of Computing Systems（第 6 章：Assembler）
