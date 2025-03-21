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
    
def generate_asm(modules: dict[str, list[ir.Instruction]]) -> str:
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
    
    emit('.extern print_int')
    emit('.extern print_bool')
    emit('.extern read_int')
    emit('.section .text') # Declarations and init

    def parse_module(instructions: list[ir.Instruction]) -> None:
        local_vars = get_all_ir_variables(instructions)
        locals = Locals(local_vars)
        emit(f'# Stack used: {locals.stack_used()}')
        for v in local_vars:
            emit(f'# {v} in {locals.get_ref(v)}')
        # emit(f'{module}:')
        emit('pushq %rbp')
        # emit('movq %rsp, %rbp')
        # emit(f'subq ${locals.stack_used()}, %rsp') # Reserve space for locals

        for insn in instructions:
            emit(f'# {insn}')
            match insn:
                case ir.Fun():
                    emit(f'.global {insn.name}')
                    emit(f'.type {insn.name}, @function')
                    emit(f'{insn.name}:')
                    
                    emit('pushq %rbp')
                    emit('movq %rsp, %rbp')
                    
                    if insn.params:
                        for i in range(len(insn.params)):
                            if i >= 6:
                                break # Only the first 6 parameters need to be moved from registers
                            p = insn.params[i]
                            if p in local_vars: # Only copy the parameter if it's used in the function
                                emit(f'movq {arg_regs[i]}, {locals.get_ref(p)}')
                            
                    
                    emit(f'subq ${locals.stack_used()}, %rsp') # Reserve space for locals
                    

                case ir.Label():
                    emit('')
                    emit(f'.L{insn.name}:')

                case ir.LoadIntConst():
                    if -2**32 <= insn.value < 2**31:
                        emit(f'movq ${insn.value}, {locals.get_ref(insn.dest)}')
                    else:
                        emit(f'movabsq ${insn.value}, %rax')
                        emit(f'movq %rax, {locals.get_ref(insn.dest)}')

                case ir.LoadBoolConst():
                    val = int(insn.value)
                    emit(f'movq ${val}, {locals.get_ref(insn.dest)}')

                case ir.Copy():
                    source = locals.get_ref(insn.source)
                    dest = locals.get_ref(insn.dest)
                    emit(f'movq {source}, %rax')
                    emit(f'movq %rax, {dest}')

                case ir.CondJump():
                    emit(f'movq {locals.get_ref(insn.cond)}, %rax')
                    emit(f'cmpq $0, %rax') # 1 if %rax == 0, 0 otherwise (%rax > 0). Stored in EFLAGS (not sure what that is)
                    emit(f'jne .L{insn.then_label.name}') # %rax != 0 -> Comparison was true
                    emit(f'jmp .L{insn.else_label.name}') # %rax == 0 -> Comparison was false

                case ir.Jump():
                    emit(f'jmp .L{insn.label.name}')

                case ir.Call():
                    f_name = insn.fun.name
                    arg_offset = 0 if len(insn.args) < 6 else 8 * (len(insn.args) - 6)
                    offset = (locals.stack_used() + arg_offset) % 16
                    if f_name in intrinsics.all_intrinsics:
                        offset = 0
                        intrinsics.all_intrinsics[f_name](intrinsics.IntrinsicArgs(
                            arg_refs=[locals.get_ref(arg) for arg in insn.args],
                            result_register='%rax',
                            emit=emit
                        ))
                    else:
                        if offset > 0:
                            emit(f'subq ${offset}, %rsp')
                        for i in range(len(insn.args)):
                            if i < 6:
                                emit(f'movq {locals.get_ref(insn.args[i])}, {arg_regs[i]}')
                            else:
                                emit(f'pushq {locals.get_ref(insn.args[i])}')
                        emit(f'callq {f_name}')
                    emit(f'movq %rax, {locals.get_ref(insn.dest)}')
                    offset += arg_offset
                    if offset > 0:
                        emit(f'add ${offset}, %rsp')

                case ir.Return():
                    if insn.var:
                        emit(f'movq {locals.get_ref(insn.var)}, %rax')
                    else:
                        emit('movq $0, %rax')
                    emit('movq %rbp, %rsp')
                    emit('popq %rbp')
                    emit('ret')

    for instructions in modules.values():
        parse_module(instructions)

#     emit("""
# .Lend:
# movq $0, %rax
# movq %rbp, %rsp
# popq %rbp
# ret""")

    return '\n'.join(lines)