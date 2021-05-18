from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from itertools import count
from typing import List, Optional, Union

import pytest
import riscvmodel.insn
import riscvmodel.regnames

from mtkcpu.asm.asm_dump import dump_asm
from mtkcpu.cpu.cpu import MtkCpu
from mtkcpu.utils.common import START_ADDR
from mtkcpu.utils.decorators import parametrized, rename
from mtkcpu.utils.tests.memory import MemoryContents
from mtkcpu.utils.tests.registers import RegistryContents
from mtkcpu.utils.tests.sim_tests import (get_sim_memory_test,
                                          get_sim_register_test)

x0 = riscvmodel.regnames.x0
x1 = riscvmodel.regnames.x1
x2 = riscvmodel.regnames.x2
x3 = riscvmodel.regnames.x3
x4 = riscvmodel.regnames.x4
x5 = riscvmodel.regnames.x5
x6 = riscvmodel.regnames.x6
x7 = riscvmodel.regnames.x7
x8 = riscvmodel.regnames.x8
x9 = riscvmodel.regnames.x9
x10 = riscvmodel.regnames.x10
x11 = riscvmodel.regnames.x11
x12 = riscvmodel.regnames.x12
x13 = riscvmodel.regnames.x13
x14 = riscvmodel.regnames.x14
x15 = riscvmodel.regnames.x15
x16 = riscvmodel.regnames.x16
x17 = riscvmodel.regnames.x17
x18 = riscvmodel.regnames.x18
x19 = riscvmodel.regnames.x19
x20 = riscvmodel.regnames.x20
x21 = riscvmodel.regnames.x21
x22 = riscvmodel.regnames.x22
x23 = riscvmodel.regnames.x23
x24 = riscvmodel.regnames.x24
x25 = riscvmodel.regnames.x25
x26 = riscvmodel.regnames.x26
x27 = riscvmodel.regnames.x27
x28 = riscvmodel.regnames.x28
x29 = riscvmodel.regnames.x29
x30 = riscvmodel.regnames.x30
x31 = riscvmodel.regnames.x31

LUI = riscvmodel.insn.InstructionLUI
AUIPC = riscvmodel.insn.InstructionAUIPC
JAL = riscvmodel.insn.InstructionJAL
JALR = riscvmodel.insn.InstructionJALR
BEQ = riscvmodel.insn.InstructionBEQ
BNE = riscvmodel.insn.InstructionBNE
BLT = riscvmodel.insn.InstructionBLT
BGE = riscvmodel.insn.InstructionBGE
BLTU = riscvmodel.insn.InstructionBLTU
BGEU = riscvmodel.insn.InstructionBGEU
LB = riscvmodel.insn.InstructionLB
LH = riscvmodel.insn.InstructionLH
LW = riscvmodel.insn.InstructionLW
LBU = riscvmodel.insn.InstructionLBU
LHU = riscvmodel.insn.InstructionLHU
SB = riscvmodel.insn.InstructionSB
SH = riscvmodel.insn.InstructionSH
SW = riscvmodel.insn.InstructionSW
ADDI = riscvmodel.insn.InstructionADDI
SLTI = riscvmodel.insn.InstructionSLTI
SLTIU = riscvmodel.insn.InstructionSLTIU
XORI = riscvmodel.insn.InstructionXORI
ORI = riscvmodel.insn.InstructionORI
ANDI = riscvmodel.insn.InstructionANDI
SLLI = riscvmodel.insn.InstructionSLLI
SRLI = riscvmodel.insn.InstructionSRLI
SRAI = riscvmodel.insn.InstructionSRAI
ADD = riscvmodel.insn.InstructionADD
SUB = riscvmodel.insn.InstructionSUB
SLL = riscvmodel.insn.InstructionSLL
SLT = riscvmodel.insn.InstructionSLT
SLTU = riscvmodel.insn.InstructionSLTU
XOR = riscvmodel.insn.InstructionXOR
SRL = riscvmodel.insn.InstructionSRL
SRA = riscvmodel.insn.InstructionSRA
OR = riscvmodel.insn.InstructionOR
AND = riscvmodel.insn.InstructionAND
FENCE = riscvmodel.insn.InstructionFENCE
FENCEI = riscvmodel.insn.InstructionFENCEI
ECALL = riscvmodel.insn.InstructionECALL
URET = riscvmodel.insn.InstructionURET
SRET = riscvmodel.insn.InstructionSRET
HRET = riscvmodel.insn.InstructionHRET
MRET = riscvmodel.insn.InstructionMRET
WFI = riscvmodel.insn.InstructionWFI
EBREAK = riscvmodel.insn.InstructionEBREAK
CSRRW = riscvmodel.insn.InstructionCSRRW
CSRRS = riscvmodel.insn.InstructionCSRRS
CSRRC = riscvmodel.insn.InstructionCSRRC
LWU = riscvmodel.insn.InstructionLWU
LD = riscvmodel.insn.InstructionLD
SD = riscvmodel.insn.InstructionSD
NOP = riscvmodel.insn.InstructionNOP
MUL = riscvmodel.insn.InstructionMUL
MULH = riscvmodel.insn.InstructionMULH
MULHSU = riscvmodel.insn.InstructionMULHSU
MULHU = riscvmodel.insn.InstructionMULHU
DIV = riscvmodel.insn.InstructionDIV
DIVU = riscvmodel.insn.InstructionDIVU
REM = riscvmodel.insn.InstructionREM
REMU = riscvmodel.insn.InstructionREMU
CADDI = riscvmodel.insn.InstructionCADDI
CANDI = riscvmodel.insn.InstructionCANDI
CSWSP = riscvmodel.insn.InstructionCSWSP
CLI = riscvmodel.insn.InstructionCLI
CMV = riscvmodel.insn.InstructionCMV
LR = riscvmodel.insn.InstructionLR
SC = riscvmodel.insn.InstructionSC
AMOADD = riscvmodel.insn.InstructionAMOADD
AMOXOR = riscvmodel.insn.InstructionAMOXOR
AMOOR = riscvmodel.insn.InstructionAMOOR
AMOAND = riscvmodel.insn.InstructionAMOAND
AMOMIN = riscvmodel.insn.InstructionAMOMIN
AMOMAX = riscvmodel.insn.InstructionAMOMAX
AMOMINU = riscvmodel.insn.InstructionAMOMINU
AMOMAXU = riscvmodel.insn.InstructionAMOMAXU
AMOSWAP = riscvmodel.insn.InstructionAMOSWAP


@unique
class MemTestSourceType(str, Enum):
    TEXT = "text"
    RAW = "raw"
    ELF = "elf"


@dataclass(frozen=True)
class MemTestCase:
    name: str
    source: Union[
        List[riscvmodel.insn.Instruction], riscvmodel.insn.Instruction, str
    ]
    source_type: MemTestSourceType
    out_reg: Optional[int] = None
    out_val: Optional[int] = None
    mem_out: Optional[MemoryContents] = None
    timeout: Optional[int] = None
    mem_init: Optional[MemoryContents] = None
    reg_init: Optional[RegistryContents] = None

    @property
    def source_asm(self):
        if isinstance(self.source, riscvmodel.insn.Instruction):
            return f".section code\n  {str(self.source)}"
        elif isinstance(self.source, list):
            instrs = "\n  ".join([str(ins) for ins in self.source])
            return f".section code\n  {instrs}"
        return self.source


def reg_test(
    name: str,
    timeout_cycles: Optional[int],
    reg_num: int,
    expected_val: Optional[int],
    expected_mem: Optional[MemoryContents],
    reg_init: RegistryContents,
    mem_dict: Optional[MemoryContents],
    verbose: bool = False,
):
    from nmigen.back.pysim import Simulator

    cpu = MtkCpu(reg_init=reg_init.reg)
    sim = Simulator(cpu)
    sim.add_clock(1e-6)

    assert (reg_num is None and expected_val is None) or (
        reg_num is not None and expected_val is not None
    )

    sim.add_sync_process(get_sim_memory_test(cpu=cpu, mem_dict=mem_dict))
    sim.add_sync_process(
        get_sim_register_test(
            name=name,
            cpu=cpu,
            reg_num=reg_num,
            expected_val=expected_val,
            timeout_cycles=timeout_cycles,
        )
    )
    with sim.write_vcd("cpu.vcd"):
        sim.run()

    if expected_mem is not None:
        mem_dict.assert_equality(expected_mem)


def get_code_mem(case: MemTestCase) -> MemoryContents:
    if case.source_type == MemTestSourceType.TEXT:
        code = dump_asm(case.source_asm, verbose=False)
        return MemoryContents(
            memory=dict(zip(count(START_ADDR, 4), code)),
        )
    else:
        raise KeyError(
            f"Unsupported MemTestSourceType in MemTestCase: {case.source_type}"
        )


def assert_mem_test(case: MemTestCase):
    name = case.name
    reg_init = case.reg_init or RegistryContents.empty()
    mem_init = case.mem_init or MemoryContents.empty()

    program = get_code_mem(case).patch(mem_init, can_overlap=False)
    reg_test(
        name=name,
        timeout_cycles=case.timeout,
        reg_num=case.out_reg,
        expected_val=case.out_val,
        expected_mem=case.mem_out,
        reg_init=reg_init,
        mem_dict=program,
        verbose=True,
    )


@parametrized
def mem_test(f, cases: List[MemTestCase]):
    @pytest.mark.parametrize("test_case", cases)
    @rename(f.__name__)
    def aux(test_case):
        assert_mem_test(test_case)
        f(test_case)

    return aux
