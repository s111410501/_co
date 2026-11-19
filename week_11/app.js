const fileInput = document.getElementById("file-input");
const dropZone = document.getElementById("drop-zone");
const vmText = document.getElementById("vm-text");
const fileNameInput = document.getElementById("file-name");
const bootstrapInput = document.getElementById("bootstrap");
const translateButton = document.getElementById("translate-button");
const output = document.getElementById("output");
const copyButton = document.getElementById("copy-button");
const downloadButton = document.getElementById("download-button");
const statusText = document.getElementById("status");
const errorText = document.getElementById("error");

let loadedFiles = null;
let textEdited = false;

function stem(name) {
  return (name || "Main.vm").replace(/\.[^.]*$/, "");
}

function lineCount(text) {
  return text ? text.trimEnd().split("\n").length : 0;
}

function showError(message) {
  errorText.textContent = message;
  errorText.hidden = !message;
}

function currentFiles() {
  if (loadedFiles && !textEdited) {
    return loadedFiles;
  }
  return [{ name: fileNameInput.value || "Main.vm", text: vmText.value }];
}

function outputName() {
  if (loadedFiles && !textEdited) {
    return loadedFiles.length === 1 ? `${stem(loadedFiles[0].name)}.asm` : "program.asm";
  }
  return `${stem(fileNameInput.value)}.asm`;
}

function translate() {
  showError("");
  const files = currentFiles().filter((file) => file.text.trim());
  if (!files.length) {
    output.value = "";
    statusText.textContent = "請輸入或上傳 .vm 程式";
    return;
  }
  try {
    const asm = VMTranslator.translateFiles(files, bootstrapInput.checked);
    output.value = asm;
    statusText.textContent = `產生 ${lineCount(asm)} 行 Hack assembly`;
  } catch (error) {
    output.value = "";
    statusText.textContent = "翻譯失敗";
    showError(error.message);
  }
}

async function readVmFiles(fileList) {
  const files = Array.from(fileList).filter((file) => file.name.toLowerCase().endsWith(".vm"));
  if (!files.length) {
    showError("請選擇 .vm 檔案");
    return [];
  }
  return Promise.all(
    files.map(async (file) => ({ name: file.name, text: await file.text() })),
  );
}

async function handleFiles(fileList) {
  const files = await readVmFiles(fileList);
  if (!files.length) return;
  loadedFiles = files;
  textEdited = false;
  vmText.value = files.map((file) => file.text.trimEnd()).join("\n\n");
  fileNameInput.value = files.length === 1 ? files[0].name : "program.vm";
  bootstrapInput.checked = files.length > 1;
  showError("");
  translate();
}

fileInput.addEventListener("change", () => handleFiles(fileInput.files));

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragging");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragging");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  handleFiles(event.dataTransfer.files);
});

vmText.addEventListener("input", () => {
  textEdited = true;
});

fileNameInput.addEventListener("input", () => {
  if (loadedFiles && loadedFiles.length === 1 && !textEdited) {
    loadedFiles = [{ name: fileNameInput.value || "Main.vm", text: loadedFiles[0].text }];
  }
});

translateButton.addEventListener("click", translate);

copyButton.addEventListener("click", async () => {
  if (!output.value) return;
  try {
    await navigator.clipboard.writeText(output.value);
  } catch {
    output.select();
    document.execCommand("copy");
  }
  statusText.textContent = "已複製到剪貼簿";
});

downloadButton.addEventListener("click", () => {
  if (!output.value) return;
  const blob = new Blob([output.value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = outputName();
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
});

translate();
