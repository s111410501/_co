const C_ARITHMETIC = "C_ARITHMETIC";
const C_PUSH = "C_PUSH";
const C_POP = "C_POP";
const C_LABEL = "C_LABEL";
const C_GOTO = "C_GOTO";
const C_IF = "C_IF";
const C_FUNCTION = "C_FUNCTION";
const C_RETURN = "C_RETURN";
const C_CALL = "C_CALL";

const ARITHMETIC_COMMANDS = new Set([
  "add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not",
]);

const SEGMENT_POINTERS = {
  local: "LCL",
  argument: "ARG",
  this: "THIS",
  that: "THAT",
};

class Parser {
  constructor(text) {
    this.lines = text
      .split(/\r?\n/)
      .map((line) => line.split("//", 1)[0].trim())
      .filter(Boolean);
    this.index = -1;
    this.tokens = [];
  }

  hasMoreLines() {
    return this.index + 1 < this.lines.length;
  }

  advance() {
    if (!this.hasMoreLines()) {
      throw new Error("No more lines to advance.");
    }
    this.index += 1;
    this.tokens = this.lines[this.index].split(/\s+/);
  }

  commandType() {
    const command = this.tokens[0];
    if (ARITHMETIC_COMMANDS.has(command)) return C_ARITHMETIC;
    switch (command) {
      case "push": return C_PUSH;
      case "pop": return C_POP;
      case "label": return C_LABEL;
      case "goto": return C_GOTO;
      case "if-goto": return C_IF;
      case "function": return C_FUNCTION;
      case "return": return C_RETURN;
      case "call": return C_CALL;
      default: throw new Error(`Unknown VM command: ${command}`);
    }
  }

  arg1() {
    const type = this.commandType();
    if (type === C_RETURN) {
      throw new Error("arg1() cannot be called for C_RETURN.");
    }
    if (type === C_ARITHMETIC) {
      return this.tokens[0];
    }
    if (this.tokens.length < 2) {
      throw new Error(`Missing argument for ${this.tokens[0]}`);
    }
    return this.tokens[1];
  }

  arg2() {
    const type = this.commandType();
    if (![C_PUSH, C_POP, C_FUNCTION, C_CALL].includes(type)) {
      throw new Error(`arg2() is invalid for command type ${type}.`);
    }
    const value = Number(this.tokens[2]);
    if (!Number.isInteger(value) || value < 0) {
      throw new Error(`Invalid numeric argument: ${this.tokens[2]}`);
    }
    return value;
  }
}

class CodeWriter {
  constructor({ bootstrap = false } = {}) {
    this.out = [];
    this.fileName = "";
    this.currentFunction = "";
    this.cmpCounter = 0;
    this.retCounter = 0;
    if (bootstrap) {
      this.writeInit();
    }
  }

  setFileName(name) {
    this.fileName = name.replace(/\.[^.]*$/, "");
  }

  emit(...lines) {
    this.out.push(...lines);
  }

  asm() {
    return this.out.length ? `${this.out.join("\n")}\n` : "";
  }

  pushD() {
    this.emit("@SP", "A=M", "M=D", "@SP", "M=M+1");
  }

  popToD() {
    this.emit("@SP", "AM=M-1", "D=M");
  }

  scopedLabel(label) {
    return this.currentFunction ? `${this.currentFunction}$${label}` : label;
  }

  writeInit() {
    this.emit("// Bootstrap code", "@256", "D=A", "@SP", "M=D");
    this.writeCall("Sys.init", 0);
  }

  writeArithmetic(command) {
    this.emit(`// ${command}`);
    if (command === "add") {
      this.popToD();
      this.emit("A=A-1", "M=D+M");
    } else if (command === "sub") {
      this.popToD();
      this.emit("A=A-1", "M=M-D");
    } else if (command === "and") {
      this.popToD();
      this.emit("A=A-1", "M=D&M");
    } else if (command === "or") {
      this.popToD();
      this.emit("A=A-1", "M=D|M");
    } else if (command === "neg") {
      this.emit("@SP", "A=M-1", "M=-M");
    } else if (command === "not") {
      this.emit("@SP", "A=M-1", "M=!M");
    } else if (["eq", "gt", "lt"].includes(command)) {
      const jump = { eq: "JEQ", gt: "JGT", lt: "JLT" }[command];
      const index = this.cmpCounter++;
      const trueLabel = `CMP_TRUE_${index}`;
      const endLabel = `CMP_END_${index}`;
      this.popToD();
      this.emit(
        "A=A-1",
        "D=M-D",
        `@${trueLabel}`,
        `D;${jump}`,
        "@SP",
        "A=M-1",
        "M=0",
        `@${endLabel}`,
        "0;JMP",
        `(${trueLabel})`,
        "@SP",
        "A=M-1",
        "M=-1",
        `(${endLabel})`,
      );
    } else {
      throw new Error(`Unknown arithmetic command: ${command}`);
    }
  }

  writePushPop(command, segment, index) {
    const op = command === C_PUSH ? "push" : "pop";
    this.emit(`// ${op} ${segment} ${index}`);

    if (command === C_PUSH) {
      if (segment === "constant") {
        this.emit(`@${index}`, "D=A");
      } else if (Object.prototype.hasOwnProperty.call(SEGMENT_POINTERS, segment)) {
        const base = SEGMENT_POINTERS[segment];
        this.emit(`@${base}`, "D=M", `@${index}`, "A=D+A", "D=M");
      } else if (segment === "temp") {
        this.emit(`@${5 + index}`, "D=M");
      } else if (segment === "pointer") {
        const target = index === 0 ? "THIS" : "THAT";
        this.emit(`@${target}`, "D=M");
      } else if (segment === "static") {
        this.emit(`@${this.fileName}.${index}`, "D=M");
      } else {
        throw new Error(`Unknown memory segment: ${segment}`);
      }
      this.pushD();
      return;
    }

    if (Object.prototype.hasOwnProperty.call(SEGMENT_POINTERS, segment)) {
      const base = SEGMENT_POINTERS[segment];
      this.emit(`@${base}`, "D=M", `@${index}`, "D=D+A", "@R13", "M=D");
      this.popToD();
      this.emit("@R13", "A=M", "M=D");
    } else if (segment === "temp") {
      this.popToD();
      this.emit(`@${5 + index}`, "M=D");
    } else if (segment === "pointer") {
      const target = index === 0 ? "THIS" : "THAT";
      this.popToD();
      this.emit(`@${target}`, "M=D");
    } else if (segment === "static") {
      this.popToD();
      this.emit(`@${this.fileName}.${index}`, "M=D");
    } else {
      throw new Error(`Cannot pop to segment: ${segment}`);
    }
  }

  writeLabel(label) {
    this.emit(`// label ${label}`, `(${this.scopedLabel(label)})`);
  }

  writeGoto(label) {
    this.emit(`// goto ${label}`, `@${this.scopedLabel(label)}`, "0;JMP");
  }

  writeIf(label) {
    this.emit(`// if-goto ${label}`);
    this.popToD();
    this.emit(`@${this.scopedLabel(label)}`, "D;JNE");
  }

  writeFunction(functionName, localCount) {
    this.currentFunction = functionName;
    this.emit(`// function ${functionName} ${localCount}`, `(${functionName})`);
    for (let i = 0; i < localCount; i += 1) {
      this.emit("@SP", "A=M", "M=0", "@SP", "M=M+1");
    }
  }

  writeCall(functionName, argCount) {
    const caller = this.currentFunction || "BOOT";
    const returnLabel = `${caller}$ret.${this.retCounter++}`;

    this.emit(`// call ${functionName} ${argCount}`);
    this.emit(`@${returnLabel}`, "D=A");
    this.pushD();

    for (const pointer of ["LCL", "ARG", "THIS", "THAT"]) {
      this.emit(`@${pointer}`, "D=M");
      this.pushD();
    }

    this.emit("@SP", "D=M", `@${5 + argCount}`, "D=D-A", "@ARG", "M=D");
    this.emit("@SP", "D=M", "@LCL", "M=D");
    this.emit(`@${functionName}`, "0;JMP", `(${returnLabel})`);
  }

  writeReturn() {
    this.emit("// return");
    this.emit("@LCL", "D=M", "@R13", "M=D");
    this.emit("@5", "A=D-A", "D=M", "@R14", "M=D");
    this.popToD();
    this.emit("@ARG", "A=M", "M=D");
    this.emit("@ARG", "D=M+1", "@SP", "M=D");
    for (const [offset, pointer] of [[1, "THAT"], [2, "THIS"], [3, "ARG"], [4, "LCL"]]) {
      this.emit("@R13", "D=M", `@${offset}`, "A=D-A", "D=M", `@${pointer}`, "M=D");
    }
    this.emit("@R14", "A=M", "0;JMP");
  }
}

function translateVmText(text, writer) {
  const parser = new Parser(text);
  while (parser.hasMoreLines()) {
    parser.advance();
    const type = parser.commandType();
    if (type === C_ARITHMETIC) {
      writer.writeArithmetic(parser.arg1());
    } else if (type === C_PUSH || type === C_POP) {
      writer.writePushPop(type, parser.arg1(), parser.arg2());
    } else if (type === C_LABEL) {
      writer.writeLabel(parser.arg1());
    } else if (type === C_GOTO) {
      writer.writeGoto(parser.arg1());
    } else if (type === C_IF) {
      writer.writeIf(parser.arg1());
    } else if (type === C_FUNCTION) {
      writer.writeFunction(parser.arg1(), parser.arg2());
    } else if (type === C_CALL) {
      writer.writeCall(parser.arg1(), parser.arg2());
    } else if (type === C_RETURN) {
      writer.writeReturn();
    }
  }
}

function translateFiles(files, bootstrap = false) {
  const writer = new CodeWriter({ bootstrap });
  for (const file of files) {
    writer.setFileName(file.name);
    translateVmText(file.text, writer);
  }
  return writer.asm();
}

window.VMTranslator = { translateFiles, translateVmText, CodeWriter, Parser };
