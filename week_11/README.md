# Nand2Tetris VM Translator

將 Nand2Tetris 的 `.vm` 程式翻譯成 Hack 組合語言 `.asm`（Projects 7 & 8）。


## 需求

- Python 3.10 以上
- 不需要額外套件

## 用法

```bash
# 翻譯單一 .vm 檔（預設不產生 bootstrap）
python vm_translator.py Simple.vm

# 翻譯資料夾內所有 .vm 檔（預設產生 bootstrap）
python vm_translator.py ProjectFolder/

# 強制／停用 bootstrap
python vm_translator.py ProjectFolder/ --bootstrap
python vm_translator.py Simple.vm --no-bootstrap

# 不給路徑時，會提示輸入；若目前資料夾有 .vm 檔，直接按 Enter 即可
python vm_translator.py
```

輸出位置：

- 單一檔案：`Simple.vm` → `Simple.asm`
- 資料夾：`ProjectFolder/` → `ProjectFolder/ProjectFolder.asm`

## 支援的 VM 指令

| 類別 | 指令 |
| --- | --- |
| 算術 | `add` `sub` `neg` `eq` `gt` `lt` `and` `or` `not` |
| 記憶體 | `push` `pop`：constant、local、argument、this、that、temp、pointer、static |
| 流程控制 | `label` `goto` `if-goto` |
| 函式 | `function` `call` `return` |

## 記憶體區段對應

| 區段 | Hack 實作 |
| --- | --- |
| `constant` | 立即數 `A` |
| `local` | `LCL + index` |
| `argument` | `ARG + index` |
| `this` | `THIS + index` |
| `that` | `THAT + index` |
| `temp` | `R5`～`R10` |
| `pointer 0/1` | `THIS` / `THAT` |
| `static index` | `檔案名稱.index`，由 assembler 配置到 RAM 16～255 |

## Bootstrap

資料夾模式預設會在 `.asm` 開頭產生：

```asm
@256
D=A
@SP
M=D
// call Sys.init 0 ...
```

也就是 `SP = 256` 並呼叫 `Sys.init`。若只是測試單一 `.vm` 檔，可用 `--no-bootstrap`。

## 實作細節

- 比較運算使用遞增編號的 `CMP_TRUE_n` / `CMP_END_n` 標籤。
- 函式內的 `label` 會轉成 `functionName$label`，避免不同函式同名標籤衝突。
- 返回地址標籤格式為 `caller$ret.n`；bootstrap 的 caller 為 `BOOT`。
- `R13` 作為 `pop segment index` 的暫存位址，`R14` 作為 `return` 的返回位址。
- `static` 以來源檔案名稱區分，因此不同 `.vm` 檔的 `static 0` 不會互相干擾。

## 範例

`Simple.vm`：

```vm
push constant 7
push constant 8
add
```

```bash
python vm_translator.py Simple.vm
```

會產生 `Simple.asm`，執行結果為堆疊頂端 `15`。

## 注意

此程式只產生 `.asm`，不會組譯成 `.hack`。若要得到可執行機器碼，請再使用 Nand2Tetris 的 Assembler。
OS 函式（`Sys.*`、`Output.*`、`Math.*` 等）需自行提供對應的 `.vm` 檔案。
