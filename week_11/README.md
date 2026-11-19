# Nand2Tetris VM Translator（網頁版）

在瀏覽器中把 Nand2Tetris 的 `.vm` 程式翻譯成 Hack 組合語言 `.asm`（Projects 7 & 8）。不需要安裝 Python 或任何套件。

## 檔案

| 檔案 | 說明 |
| --- | --- |
| `index.html` | 網頁介面 |
| `style.css` | 樣式 |
| `vm_translator.js` | VM → Hack 翻譯核心 |
| `app.js` | 上傳、貼上、複製、下載等介面邏輯 |
| `README.md` | 本說明 |

## 使用方式

直接用瀏覽器開啟 `index.html` 即可。

1. 在左側拖曳或點擊上傳 `.vm` 檔案，或直接在文字區貼上 VM 程式碼。
2. 可一次上傳多個 `.vm` 檔案；此時會自動勾選 bootstrap。
3. 視需要勾選或取消 `加入 bootstrap`。
4. 點擊 `翻譯成 .asm`。
5. 右側可複製結果或下載 `.asm` 檔。

若要使用本機伺服器（部分瀏覽器對 `file://` 較嚴格）：

```bash
python -m http.server 8000
```

然後開啟 <http://localhost:8000>。

## Bootstrap

勾選後會在 `.asm` 開頭產生：

```asm
// Bootstrap code
@256
D=A
@SP
M=D
// call Sys.init 0 ...
```

也就是 `SP = 256` 並呼叫 `Sys.init`。上傳單一檔案時預設不勾選；上傳多個檔案時預設勾選，與命令列版的資料夾行為一致。

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

## 範例

貼上：

```vm
push constant 7
push constant 8
add
```

翻譯後執行結果為堆疊頂端 `15`。

## 實作細節

- 比較運算使用遞增編號的 `CMP_TRUE_n` / `CMP_END_n` 標籤。
- 函式內的 `label` 會轉成 `functionName$label`，避免不同函式同名標籤衝突。
- 返回地址標籤格式為 `caller$ret.n`；bootstrap 的 caller 為 `BOOT`。
- `R13` 作為 `pop segment index` 的暫存位址，`R14` 作為 `return` 的返回位址。
- `static` 以檔案名稱區分，因此不同 `.vm` 檔的 `static 0` 不會互相干擾。

## 注意

此網頁只產生 `.asm`，不會組譯成 `.hack`。若要得到可執行機器碼，請再使用 Nand2Tetris 的 Assembler。
OS 函式（`Sys.*`、`Output.*`、`Math.*` 等）需自行提供對應的 `.vm` 檔案。
