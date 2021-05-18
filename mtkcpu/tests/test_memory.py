from bitstring import Bits

from mtkcpu.utils.tests.memory import MemoryContents
from mtkcpu.utils.tests.registers import RegistryContents
from mtkcpu.utils.tests.utils import (ADDI, LB, LBU, LH, LHU, LW, SB, SH, SW,
                                      MemTestCase, MemTestSourceType, mem_test,
                                      x0, x1, x5, x10, x11)

MEMORY_TESTS = [
    MemTestCase(
        name="simple 'lw'",
        source_type=MemTestSourceType.TEXT,
        source=[
            ADDI(x10, x0, -2048),
            LW(x11, x0, 0xDE),
        ],
        out_reg=11,
        out_val=0xDEADBEEF,
        timeout=10,
        mem_init=MemoryContents(memory={0xDE: 0xDEADBEEF}),
        mem_out=MemoryContents.empty(),  # empty dict means whatever (no memory checks performed)
    ),
    MemTestCase(
        name="simple 'sw'",
        source_type=MemTestSourceType.TEXT,
        source=SW(x0, x11, 0xAA),
        timeout=10,
        reg_init=RegistryContents.fill(),
        mem_out=MemoryContents(memory={0xAA: 11}),
    ),
    MemTestCase(
        name="simple 'lh'",
        source_type=MemTestSourceType.TEXT,
        source=LH(x5, x1, 0xAA),
        timeout=10,
        out_reg=5,
        out_val=Bits(
            bin=format(0b11111111_11111111_11111111_00000000, "32b")
        ).uint,  # uint because of bus unsigned..
        reg_init=RegistryContents.fill(),
        mem_init=MemoryContents(
            memory={
                0xAB: Bits(
                    bin=format(0b11111111_00000000_11111111_00000000, "32b")
                ).int
            }
        ),
    ),
    MemTestCase(
        name="simple 'lhu'",
        source_type=MemTestSourceType.TEXT,
        source=LHU(x5, x0, 0),
        timeout=10,
        out_reg=5,
        out_val=0b11111111_00000000,
        mem_init=MemoryContents(
            memory={
                0x0: Bits(
                    bin=format(0b11111111_00000000_11111111_00000000, "32b")
                ).int
            }
        ),
    ),
    MemTestCase(
        name="simple 'lb'",
        source_type=MemTestSourceType.TEXT,
        source=LB(x5, x0, 0),
        timeout=10,
        out_reg=5,
        out_val=0b11111101,  # TODO fix that unsigned bus.
        mem_init=MemoryContents(memory={0x0: -3}),
    ),
    MemTestCase(
        name="simple 'lbu'",
        source_type=MemTestSourceType.TEXT,
        source=LBU(x5, x0, 0),
        timeout=10,
        out_reg=5,
        out_val=5,
        mem_init=MemoryContents(memory={0x0: 5}),
    ),
    MemTestCase(
        name="simple 'sh'",
        source_type=MemTestSourceType.TEXT,
        source=SH(x5, x0, 0),
        timeout=10,
        reg_init=RegistryContents.fill(),
        mem_init=MemoryContents(memory={0x0: 5}),
        mem_out=MemoryContents(memory={0x0: 5}),
    ),
    MemTestCase(
        name="negative 'sh'",
        source_type=MemTestSourceType.TEXT,
        source=SH(x0, x5, 0),
        timeout=10,
        reg_init=RegistryContents.empty(value=-5),
        mem_out=MemoryContents(memory={0x0: Bits(int=-5, length=16).uint}),
    ),
    MemTestCase(
        name="simple 'sb'",
        source_type=MemTestSourceType.TEXT,
        source=SH(x5, x1, 0),
        timeout=10,
        reg_init=RegistryContents.empty(value=0xAA),
        mem_out=MemoryContents(memory={0xAA: 0xAA}),
    ),
    MemTestCase(
        name="overwrite 'sb'",
        source_type=MemTestSourceType.TEXT,
        source=SB(x1, x5, 0),
        timeout=10,
        reg_init=RegistryContents.empty(value=0xAA),
        mem_init=MemoryContents(memory={0xAA: 0xDEADBEEF}),
        mem_out=MemoryContents(memory={0xAA: 0xDEADBEAA}),
    ),
    MemTestCase(
        name="overwrite 'sh'",
        source_type=MemTestSourceType.TEXT,
        source=SH(x0, x5, 0xBB),
        timeout=10,
        reg_init=RegistryContents.empty(value=0xAAAA),
        mem_init=MemoryContents(memory={0xBB: 0xDEADBEEF}),
        mem_out=MemoryContents(memory={0xBB: 0xDEADAAAA}),
    ),
    MemTestCase(
        name="overwrite 'sw'",
        source_type=MemTestSourceType.TEXT,
        source=SW(x0, x5, 0xBB),
        timeout=10,
        reg_init=RegistryContents.empty(value=0xAAAA),
        mem_init=MemoryContents(memory={0xBB: 0xDEADBEEF}),
        mem_out=MemoryContents(memory={0xBB: 0xAAAA}),
    ),
]


@mem_test(MEMORY_TESTS)
def test_memory(_):
    pass
