# Nand2Tetris VM Translator（單檔網頁版）

把 Nand2Tetris 的 `.vm` 程式翻譯成 Hack 組合語言 `.asm`（Projects 7 & 8）。

整個應用程式只有一個 `index.html`：CSS 與 JavaScript 都已內嵌，沒有外部檔案、套件或後端。任何人只要把這個檔案放到自己的伺服器即可使用。

## 部署

### 最簡單

把 `index.html` 上傳到任意靜態伺服器的網站根目錄，例如：

- Apache：`/var/www/html/index.html`
- Nginx：`/usr/share/nginx/html/index.html`
- IIS：`C:\inetpub\wwwroot\index.html`
- GitHub Pages：直接放在 repository 根目錄
- 任何物件儲存／靜態託管服務

訪客開啟 `https://你的域名/index.html` 即可。

### 本機測試

直接雙擊 `index.html`，或啟動一個臨時伺服器：

```bash
python -m http.server 8000
```

再開啟 <http://localhost:8000>。

## 使用方式

1. 拖曳或點擊上傳 `.vm` 檔案，或直接在左側貼上 VM 程式碼。
2. 可一次上傳多個 `.vm` 檔案；此時會自動勾選 bootstrap。
3. 依需求勾選或取消 `加入 bootstrap`。
4. 點擊 `翻譯成 .asm`。
5. 右側可複製結果或下載 `.asm` 檔。

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

也就是 `SP = 256` 並呼叫 `Sys.init`。上傳單一檔案時預設不勾選；上傳多個檔案時預設勾選。

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
