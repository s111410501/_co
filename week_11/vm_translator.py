#!/usr/bin/env python3
"""Nand2Tetris Virtual Machine Translator (Projects 7 & 8).

Translates .vm files (or a directory of .vm files) into Hack assembly (.asm)
following the standard VM-on-Hack mapping and symbol conventions.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional

C_ARITHMETIC = "C_ARITHMETIC"
C_PUSH = "C_PUSH"
C_POP = "C_POP"
C_LABEL = "C_LABEL"
C_GOTO = "C_GOTO"
C_IF = "C_IF"
C_FUNCTION = "C_FUNCTION"
C_RETURN = "C_RETURN"
C_CALL = "C_CALL"

ARITHMETIC_COMMANDS = frozenset({
    "add",
    "sub",
    "neg",
    "eq",
    "gt",
    "lt",
    "and",
    "or",
    "not",
})

SEGMENT_POINTERS = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}


class Parser:
    """Parses a single .vm file into VM commands and their arguments."""

    def __init__(self, vm_path: Path) -> None:
        raw_lines = vm_path.read_text(encoding="utf-8").splitlines()
        self._lines: list[str] = []
        for raw in raw_lines:
            cleaned = raw.split("//", 1)[0].strip()
            if cleaned:
                self._lines.append(cleaned)
        self._index = -1
        self._current_tokens: list[str] = []

    def has_more_lines(self) -> bool:
        return self._index + 1 < len(self._lines)

    def advance(self) -> None:
        if not self.has_more_lines():
            raise RuntimeError("No more lines to advance.")
        self._index += 1
        self._current_tokens = self._lines[self._index].split()

    def command_type(self) -> str:
        cmd = self._current_tokens[0]
        if cmd in ARITHMETIC_COMMANDS:
            return C_ARITHMETIC
        if cmd == "push":
            return C_PUSH
        if cmd == "pop":
            return C_POP
        if cmd == "label":
            return C_LABEL
        if cmd == "goto":
            return C_GOTO
        if cmd == "if-goto":
            return C_IF
        if cmd == "function":
            return C_FUNCTION
        if cmd == "return":
            return C_RETURN
        if cmd == "call":
            return C_CALL
        raise ValueError(f"Unknown VM command: {cmd!r}")

    def arg1(self) -> str:
        ctype = self.command_type()
        if ctype == C_RETURN:
            raise RuntimeError("arg1() should not be called for C_RETURN.")
        if ctype == C_ARITHMETIC:
            return self._current_tokens[0]
        return self._current_tokens[1]

    def arg2(self) -> int:
        ctype = self.command_type()
        if ctype not in (C_PUSH, C_POP, C_FUNCTION, C_CALL):
            raise RuntimeError(f"arg2() invalid for command type {ctype}.")
        return int(self._current_tokens[2])


class CodeWriter:
    """Generates Hack assembly instructions for parsed VM commands."""

    def __init__(self, output_path: Path, write_bootstrap: bool = True) -> None:
        self._out = output_path.open("w", encoding="utf-8")
        self._file_stem = output_path.stem
        self._current_function = ""
        self._cmp_counter = 0
        self._ret_counter = 0
        if write_bootstrap:
            self.write_init()

    def set_file_name(self, file_name: str) -> None:
        self._file_stem = Path(file_name).stem

    def _emit(self, *lines: str) -> None:
        for line in lines:
            self._out.write(line + "\n")

    def _push_d(self) -> None:
        self._emit("@SP", "A=M", "M=D", "@SP", "M=M+1")

    def _pop_to_d(self) -> None:
        self._emit("@SP", "AM=M-1", "D=M")

    def _scoped_label(self, label: str) -> str:
        if self._current_function:
            return f"{self._current_function}${label}"
        return label

    def write_init(self) -> None:
        """Writes bootstrap code: SP=256 and call Sys.init."""
        self._emit("// Bootstrap code", "@256", "D=A", "@SP", "M=D")
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, command: str) -> None:
        self._emit(f"// {command}")
        if command == "add":
            self._pop_to_d()
            self._emit("A=A-1", "M=D+M")
        elif command == "sub":
            self._pop_to_d()
            self._emit("A=A-1", "M=M-D")
        elif command == "and":
            self._pop_to_d()
            self._emit("A=A-1", "M=D&M")
        elif command == "or":
            self._pop_to_d()
            self._emit("A=A-1", "M=D|M")
        elif command == "neg":
            self._emit("@SP", "A=M-1", "M=-M")
        elif command == "not":
            self._emit("@SP", "A=M-1", "M=!M")
        elif command in ("eq", "gt", "lt"):
            jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
            idx = self._cmp_counter
            self._cmp_counter += 1
            true_lbl = f"CMP_TRUE_{idx}"
            end_lbl = f"CMP_END_{idx}"
            self._pop_to_d()
            self._emit(
                "A=A-1",
                "D=M-D",
                f"@{true_lbl}",
                f"D;{jump}",
                "@SP",
                "A=M-1",
                "M=0",
                f"@{end_lbl}",
                "0;JMP",
                f"({true_lbl})",
                "@SP",
                "A=M-1",
                "M=-1",
                f"({end_lbl})",
            )
        else:
            raise ValueError(f"Unknown arithmetic command: {command!r}")

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        op = "push" if command == C_PUSH else "pop"
        self._emit(f"// {op} {segment} {index}")

        if command == C_PUSH:
            if segment == "constant":
                self._emit(f"@{index}", "D=A")
            elif segment in SEGMENT_POINTERS:
                base = SEGMENT_POINTERS[segment]
                self._emit(f"@{base}", "D=M", f"@{index}", "A=D+A", "D=M")
            elif segment == "temp":
                self._emit(f"@{5 + index}", "D=M")
            elif segment == "pointer":
                target = "THIS" if index == 0 else "THAT"
                self._emit(f"@{target}", "D=M")
            elif segment == "static":
                self._emit(f"@{self._file_stem}.{index}", "D=M")
            else:
                raise ValueError(f"Unknown memory segment: {segment!r}")
            self._push_d()

        elif command == C_POP:
            if segment in SEGMENT_POINTERS:
                base = SEGMENT_POINTERS[segment]
                self._emit(f"@{base}", "D=M", f"@{index}", "D=D+A", "@R13", "M=D")
                self._pop_to_d()
                self._emit("@R13", "A=M", "M=D")
            elif segment == "temp":
                self._pop_to_d()
                self._emit(f"@{5 + index}", "M=D")
            elif segment == "pointer":
                target = "THIS" if index == 0 else "THAT"
                self._pop_to_d()
                self._emit(f"@{target}", "M=D")
            elif segment == "static":
                self._pop_to_d()
                self._emit(f"@{self._file_stem}.{index}", "M=D")
            else:
                raise ValueError(f"Cannot pop to segment: {segment!r}")

    def write_label(self, label: str) -> None:
        self._emit(f"// label {label}", f"({self._scoped_label(label)})")

    def write_goto(self, label: str) -> None:
        self._emit(f"// goto {label}", f"@{self._scoped_label(label)}", "0;JMP")

    def write_if(self, label: str) -> None:
        self._emit(f"// if-goto {label}")
        self._pop_to_d()
        self._emit(f"@{self._scoped_label(label)}", "D;JNE")

    def write_function(self, function_name: str, n_vars: int) -> None:
        self._current_function = function_name
        self._emit(f"// function {function_name} {n_vars}", f"({function_name})")
        for _ in range(n_vars):
            self._emit("@SP", "A=M", "M=0", "@SP", "M=M+1")

    def write_call(self, function_name: str, n_args: int) -> None:
        caller = self._current_function or "BOOT"
        ret_label = f"{caller}$ret.{self._ret_counter}"
        self._ret_counter += 1

        self._emit(f"// call {function_name} {n_args}")
        # Push return address
        self._emit(f"@{ret_label}", "D=A")
        self._push_d()
        # Save caller's LCL, ARG, THIS, THAT
        for ptr in ("LCL", "ARG", "THIS", "THAT"):
            self._emit(f"@{ptr}", "D=M")
            self._push_d()
        # ARG = SP - 5 - n_args
        self._emit("@SP", "D=M", f"@{5 + n_args}", "D=D-A", "@ARG", "M=D")
        # LCL = SP
        self._emit("@SP", "D=M", "@LCL", "M=D")
        # Jump to callee
        self._emit(f"@{function_name}", "0;JMP", f"({ret_label})")

    def write_return(self) -> None:
        self._emit("// return")
        # endFrame (R13) = LCL
        self._emit("@LCL", "D=M", "@R13", "M=D")
        # retAddr (R14) = *(endFrame - 5)
        self._emit("@5", "A=D-A", "D=M", "@R14", "M=D")
        # *ARG = pop()
        self._pop_to_d()
        self._emit("@ARG", "A=M", "M=D")
        # SP = ARG + 1
        self._emit("@ARG", "D=M+1", "@SP", "M=D")
        # Restore THAT, THIS, ARG, LCL
        for offset, ptr in ((1, "THAT"), (2, "THIS"), (3, "ARG"), (4, "LCL")):
            self._emit("@R13", "D=M", f"@{offset}", "A=D-A", "D=M", f"@{ptr}", "M=D")
        # goto retAddr
        self._emit("@R14", "A=M", "0;JMP")

    def close(self) -> None:
        self._out.close()


def translate_vm_file(parser: Parser, writer: CodeWriter) -> None:
    """Translates all commands in a single parsed .vm file."""
    while parser.has_more_lines():
        parser.advance()
        ctype = parser.command_type()
        if ctype == C_ARITHMETIC:
            writer.write_arithmetic(parser.arg1())
        elif ctype in (C_PUSH, C_POP):
            writer.write_push_pop(ctype, parser.arg1(), parser.arg2())
        elif ctype == C_LABEL:
            writer.write_label(parser.arg1())
        elif ctype == C_GOTO:
            writer.write_goto(parser.arg1())
        elif ctype == C_IF:
            writer.write_if(parser.arg1())
        elif ctype == C_FUNCTION:
            writer.write_function(parser.arg1(), parser.arg2())
        elif ctype == C_CALL:
            writer.write_call(parser.arg1(), parser.arg2())
        elif ctype == C_RETURN:
            writer.write_return()


def translate(source: Path, bootstrap: Optional[bool] = None) -> Path:
    """Translates a .vm file or directory of .vm files into a single .asm file."""
    if source.is_dir():
        vm_files = sorted(source.glob("*.vm"))
        if not vm_files:
            raise FileNotFoundError(f"No .vm files found in directory: {source}")
        output_path = source / f"{source.name}.asm"
        use_bootstrap = True if bootstrap is None else bootstrap
    elif source.is_file() and source.suffix == ".vm":
        vm_files = [source]
        output_path = source.with_suffix(".asm")
        use_bootstrap = False if bootstrap is None else bootstrap
    else:
        raise ValueError(f"Source must be a .vm file or directory: {source}")

    writer = CodeWriter(output_path, write_bootstrap=use_bootstrap)
    try:
        for vm_file in vm_files:
            writer.set_file_name(vm_file.name)
            parser = Parser(vm_file)
            translate_vm_file(parser, writer)
    finally:
        writer.close()

    return output_path


def main(argv: list[str] | None = None) -> int:
    arg_parser = argparse.ArgumentParser(
        description="Nand2Tetris VM Translator (.vm -> .asm)"
    )
    arg_parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=None,
        help="Input .vm file or directory (optional; prompts or uses current folder if omitted)",
    )
    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--bootstrap",
        action="store_true",
        help="Force writing bootstrap code (SP=256, call Sys.init)",
    )
    group.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Disable writing bootstrap code",
    )
    args = arg_parser.parse_args(argv)

    bootstrap_opt: Optional[bool] = None
    if args.bootstrap:
        bootstrap_opt = True
    elif args.no_bootstrap:
        bootstrap_opt = False

    source = args.source
    if source is None:
        cwd = Path.cwd()
        vm_in_cwd = sorted(cwd.glob("*.vm"))
        try:
            hint = f" (直接按 Enter 轉譯目前資料夾: {cwd})" if vm_in_cwd else ""
            user_input = input(f"請輸入 .vm 檔案或資料夾路徑{hint}: ").strip().strip('"\'')
        except EOFError:
            user_input = ""
        if user_input:
            source = Path(user_input)
        elif vm_in_cwd:
            source = cwd
        else:
            arg_parser.print_help()
            print("\n提示：未指定路徑且目前資料夾沒有 .vm 檔案，請在指令列傳入 .vm 檔案或資料夾路徑。")
            return 0

    out_path = translate(source, bootstrap=bootstrap_opt)
    print(f"Generated: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())