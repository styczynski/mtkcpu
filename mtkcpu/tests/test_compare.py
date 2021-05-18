from mtkcpu.utils.tests.registers import RegistryContents
from mtkcpu.utils.tests.utils import (LUI, SLT, SLTI, SLTIU, SLTU, MemTestCase,
                                      MemTestSourceType, mem_test, x1, x2, x3)

COMPARE_TESTS = [
    MemTestCase(
        name="simple 'sltiu'",
        source_type=MemTestSourceType.TEXT,
        source=[
            LUI(x1, 65535),
            SLTIU(x2, x1, -32),
        ],
        out_reg=2,
        out_val=1,
        timeout=10,
    ),
    MemTestCase(
        name="simple 'slti'",
        source_type=MemTestSourceType.TEXT,
        source=[
            LUI(x1, 65535),
            SLTI(x3, x1, -2048),
        ],
        out_reg=3,
        out_val=0,
        timeout=10,
    ),
    MemTestCase(
        name="simple 'sltu'",
        source_type=MemTestSourceType.TEXT,
        source=SLTU(x1, x3, x2),
        out_reg=1,
        out_val=1,
        reg_init=RegistryContents.fill(lambda i: -i),
        timeout=10,
    ),
    MemTestCase(
        name="simple 'slt'",
        source_type=MemTestSourceType.TEXT,
        source=SLT(x1, x3, x2),
        out_reg=1,
        out_val=1,
        reg_init=RegistryContents.fill(lambda i: -i),
        timeout=10,
    ),
]


@mem_test(COMPARE_TESTS)
def test_compare(_):
    pass
