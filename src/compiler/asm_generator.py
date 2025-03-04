from compiler import ir, intrinsics
import dataclasses

class Locals:
    _var_to_location: dict[ir.IRVar, str]
    _stack_used: int

    def __init__(self, variables: list[ir.IRVar]) -> None:
        self._var_to_location = {}
        for i in range(len(variables)):
            self._var_to_location[variables[i]] = f'{-8 * (i + 1)}(%rbp)'
        self._stack_used = len(variables) * 8

    def get_ref(self, v: ir.IRVar) -> str:
        return self._var_to_location[v]

    def stack_used(self) -> int:
        return self._stack_used
    
def generate_asm(instructions: list[ir.Instruction]) -> str:
    lines = []
    def emit(line: str) -> None: lines.append(line)

    arg_regs = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']

    def get_all_ir_variables(instructions: list[ir.Instruction]) -> list[ir.IRVar]:
        result_set: set[ir.IRVar] = set()

        def add(v: ir.IRVar) -> None:
            if v not in result_set:
                result_set.add(v)

        for insn in instructions:
            for field in dataclasses.fields(insn):
                value = getattr(insn, field.name)
                if isinstance(value, ir.IRVar):
                    add(value)
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, ir.IRVar):
                            add(v)
        
        return list(result_set)

    locals = Locals(get_all_ir_variables(instructions))
    
    emit("""
    .extern print_int
    .extern print_bool
    .extern read_int
    .global main
    .type main, @function

    .section .text

main:
    pushq %rbp
    movq %rsp, %rbp
""") # Declarations and init
    
    emit(f'\tsubq ${locals.stack_used()}, %rsp') # Reserve space for locals

    for insn in instructions:
        emit(f'\t# {insn}')
        match insn:
            case ir.Label():
                emit('')
                emit(f'.L{insn.name}:')

            case ir.LoadIntConst():
                if -2**32 <= insn.value < 2**31:
                    emit(f'\tmovq ${insn.value}, {locals.get_ref(insn.dest)}')
                else:
                    emit(f'\tmovabsq ${insn.value}, %rax')
                    emit(f'\tmovq %rax, {locals.get_ref(insn.dest)}')

            case ir.LoadBoolConst():
                val = int(insn.value)
                emit(f'\tmovq ${val}, {locals.get_ref(insn.dest)}')

            case ir.Copy():
                source = locals.get_ref(insn.source)
                dest = locals.get_ref(insn.dest)
                emit(f'\tmovq {source}, %rax')
                emit(f'\tmovq %rax, {dest}')

            case ir.CondJump():
                emit(f'\tmovq {locals.get_ref(insn.cond)}, %rax')
                emit(f'\tcmpq $0, %rax') # 1 if %rax == 0, 0 otherwise (%rax > 0). Stored in EFLAGS (not sure what that is)
                emit(f'\tjne .L{insn.then_label.name}') # %rax != 0 -> Comparison was true
                emit(f'\tjmp .L{insn.else_label.name}') # %rax == 0 -> Comparison was false

            case ir.Jump():
                emit(f'\tjmp .L{insn.label.name}')

            case ir.Call():
                f_name = insn.fun.name
                if f_name in intrinsics.all_intrinsics:
                    intrinsics.all_intrinsics[f_name](intrinsics.IntrinsicArgs(
                        arg_refs=[locals.get_ref(arg) for arg in insn.args],
                        result_register='%rax',
                        emit=emit
                    ))
                else:
                    if len(insn.args) > 6:
                        raise Exception('Functions with more than 6 arguments are not supported')
                    for i in range(len(insn.args)):
                        emit(f'\tmovq {locals.get_ref(insn.args[i])}, {arg_regs[i]}')
                    emit(f'\ncallq {insn.fun.name}')
                emit(f'\tmovq %rax, {locals.get_ref(insn.dest)}')

    emit("""
.Lend:
    movq $0, %rax
    movq %rbp, %rsp
    popq %rbp
    ret""")

    return '\n'.join(lines)