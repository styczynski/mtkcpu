#!/usr/bin/env python3

from itertools import count
from io import StringIO
from argparse import ArgumentParser

from asm_dump import dump_asm
from cpu import START_ADDR

from cpu import MtkCpu
from tests.reg_tests import REG_TESTS
from tests.mem_tests import MEM_TESTS
from tests.compare_tests import CMP_TESTS
from tests.upper_tests import UPPER_TESTS
from tests.branch_tests import BRANCH_TESTS
from tests.playground import PLAYGROUND_TESTS


parser = ArgumentParser(description="mtkCPU testing script.")
parser.add_argument('--reg', action='store_const', const=REG_TESTS, default=[], required=False)
parser.add_argument('--mem', action='store_const', const=MEM_TESTS, default=[], required=False)
parser.add_argument('--cmp', action='store_const', const=CMP_TESTS, default=[], required=False)
parser.add_argument('--upper', action='store_const', const=UPPER_TESTS, default=[], required=False)
parser.add_argument('--branch', action='store_const', const=BRANCH_TESTS, default=[], required=False)
parser.add_argument('--playground', action='store_const', const=PLAYGROUND_TESTS, default=[], required=False)
parser.add_argument('--verbose', action='store_const', const=True, default=False, required=False)

parser.add_argument('--elf', metavar='<ELF file path.>', type=str, required=False, help="Simulate given ELF binary.")

args = parser.parse_args()

ELF = args.elf
VERBOSE = args.verbose

ALL_TESTS = REG_TESTS + MEM_TESTS + CMP_TESTS + UPPER_TESTS + PLAYGROUND_TESTS

SELECTED_TESTS = args.mem + args.reg + args.cmp + args.upper + args.branch + args.playground
if SELECTED_TESTS == []:
    SELECTED_TESTS = ALL_TESTS



# returns memory (all PT_LOAD type segments) as dictionary.
def read_elf(elf_path, verbose=False):
    from elftools.elf.elffile import ELFFile
    handle = open(elf_path, 'rb')
    elf = ELFFile(handle)
    
    import subprocess
    p = subprocess.Popen(["riscv-none-embed-objdump", "--disassembler-options=no-aliases",  "-M",  "numeric", "-d", elf_path], stdout=subprocess.PIPE)
    out, _ = p.communicate()

    out = str(out.decode("ascii"))
    if verbose:
        print(out)
    
    from asm_dump import bytes_to_u32_arr, dump_instrs
    
    # for each segment that is being loaded into memory
    # retrieve it's data and put in 'mem' dict (both code and program data). 
    mem = {}
    for s in elf.iter_segments():
        file_offset, data_len = s.header.p_offset, s.header.p_memsz
        load_addr = s.header.p_vaddr
        handle.seek(file_offset)
        raw = handle.read(data_len)
        data = bytes_to_u32_arr(raw)
        dump_instrs(data) # for debug purposes
        segment_mem = dict(zip(count(load_addr, 4), data))
        mem.update(segment_mem)
    return mem


# checks performed: 
# * if 'expected_val' is not None: check if x<'reg_num'> == 'expected_val',
# * if 'expected_mem' is not None: check if for all k, v in 'expected_mem.items()' mem[k] == v.
def reg_test(name, timeout_cycles, reg_num, expected_val, expected_mem, reg_init, mem_dict, verbose=False):
    
    from nmigen.back.pysim import Simulator, Active, Passive, Tick, Settle

    LOG = lambda x : print(x) if verbose else True

    cpu = MtkCpu(reg_init=reg_init)
    sim = Simulator(cpu)
    sim.add_clock(1e-6)

    assert((reg_num is None and expected_val is None) or (reg_num is not None and expected_val is not None))
    check_reg = reg_num is not None
    check_mem = expected_mem is not None

    def TEST_MEM():
        yield Passive()
        # yield Tick()
        # yield Settle()
        p = .4 # .5 # probability of mem access in current cycle
        from enum import Enum
        class MemState(Enum):
            FREE = 0
            BUSY_READ = 1
            BUSY_WRITE = 2

        # TODO legacy - not used for now.
        # cursed - if we use state == MemState.FREE instead of list, 'timeout_range' generator wouldn't work.
        # param need to be passed by reference not by value, for actual binding to be visible in each loop iter.
        state = [MemState.FREE]

        arbiter = cpu.arbiter

        while(True): # that's ok, I'm passive.
            import numpy.random as random

            rdy = random.choice((0, 1), p=[1-p, p])

            ctr = yield cpu.DEBUG_CTR

            if state[0] == MemState.FREE:
                ack = yield arbiter.bus.ack
                if ack:
                    yield arbiter.bus.ack.eq(0)
                    # print(f"DEBUG_CTR: {ctr}, state: {state[0]}")
                    yield
                    continue
                cyc = yield arbiter.bus.cyc
                we  = yield arbiter.bus.we
                write = cyc and     we 
                read  = cyc and not we
                mem_addr = yield arbiter.bus.adr
                if read and write:
                    raise ValueError("ERROR (TODO handle): simultaneous 'read' and 'write' detected.")
                if read:
                    state[0] = MemState.BUSY_READ
                elif write:
                    state[0] = MemState.BUSY_WRITE
                    data = yield arbiter.bus.dat_w
            else:
                if rdy: # random indicated transaction done in current cycle
                    yield arbiter.bus.ack.eq(1)
                    sel = yield arbiter.bus.sel
                    sel = format(sel, '04b') # '1111' string for full mask
                    f = lambda x : 0xFF if int(x) == 1 else 0x00
                    g = lambda val, el: (val << 8) + el
                    from functools import reduce
                    mask = reduce(g, map(f, sel))
                    read_val = 0x0 if mem_addr not in mem_dict else mem_dict[mem_addr]
                    if state[0] == MemState.BUSY_WRITE:
                        mem_dict[mem_addr] = (read_val & ~mask) | (data & mask)
                    elif state[0] == MemState.BUSY_READ:
                        read_val &= mask
                        yield arbiter.bus.dat_r.eq(read_val)
                        # print(f"cyc {ctr}: fetched {read_val} (from {mem_dict})...")
                    state[0] = MemState.FREE
            yield
        

    def TEST_REG(timeout=25 + timeout_cycles):
        yield Active()
        yield Tick()
        yield Settle()

        for _ in range(timeout):
            en = yield cpu.reg_write_port.en
            if en == 1:
                addr = yield cpu.reg_write_port.addr
                if addr == reg_num:
                    val = yield cpu.reg_write_port.data
                    if check_reg and (val != expected_val):
                        # TODO that mechanism for now allows for only one write to reg, extend it if neccessary.
                        print(f"== ERROR: Expected data write to reg x{addr} of value {expected_val}," 
                        f" got value {val}.. \n== fail test: {name}\n")
                        print(f"{format(expected_val, '32b')} vs {format(val, '32b')}")
                        exit(1)
                    return
            yield Tick()
        
        if check_reg:
            print(f"== ERROR: Test timeouted! No register write observed. Test: {name}\n")
            exit(1)
    
    sim.add_sync_process(TEST_MEM)
    sim.add_sync_process(TEST_REG)
    with sim.write_vcd("cpu.vcd"):
        sim.run()

    if check_mem:
        print(">>> MEM CHECKING: exp. vs val:", expected_mem, mem_dict)
        for k, v in expected_mem.items():
            if not k in mem_dict:
                print(f"Error! Wrong memory state. Expected {v} value in {k} addr, got nothing here!")
                exit(1)
            if mem_dict[k] != v:
                print(f"Error! Wrong memory state. Expected {v} value in {k} addr, got {mem_dict[k]}")
                exit(1)
    


def compile_source(source_raw, output_elf_fname):
    import subprocess
    COMPILER = "riscv-none-embed-gcc"
    LINKER_SCRIPT = "../elf/linker.ld"
    p = subprocess.Popen(["which", COMPILER], stdout=subprocess.PIPE)
    _, _ = p.communicate()
    if p.returncode != 0:
        raise ValueError(f"Error! Cannot find {COMPILER} compiler in your PATH! Have you runned 'install_toolchain.sh' script?")

    import tempfile
    tmp_dir = tempfile.mkdtemp()
    asm_filename = f"{tmp_dir}/tmp.S"

    with open(asm_filename, 'w+') as asm_file:
        asm_file.write(source_raw)

    p = subprocess.Popen([COMPILER, "-nostartfiles", f"-T{LINKER_SCRIPT}", asm_filename, "-o", output_elf_fname], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise ValueError(f"Compilation error! source {source_raw}\ncouldn't get compiled! Error msg: \n{out}\n\n{err}")


if __name__ == "__main__":
    if ELF is not None:
        # for future: simulate ELF, print output memory/registers and exit.
        raise NotImplementedError("direct ELF simulating not supported for now! (However, most of architecture is already done.)")
    
    print("===== Running tests...")
    for i, t in enumerate(SELECTED_TESTS, 1):
        name     = t['name']     if 'name'     in t else f"unnamed: \n{t['source']}\n"
        reg_init = t['reg_init'] if 'reg_init' in t else [0 for _ in range(32)]
        mem_init = t['mem_init'] if 'mem_init' in t else {}
        out_reg  = t['out_reg']  if 'out_reg'  in t else None
        out_val  = t['out_val']  if 'out_val'  in t else None
        mem_out  = t['mem_out']  if 'mem_out'  in t else None

        def get_code_mem():
            assert any(['source' in t, 'source_raw' in t, 'elf' in t])
            assert 1 == len([1 for k in t if k in ['source', 'source_raw', 'elf']])
            if 'source' in t:
                source_file = StringIO(t['source'])
                code = dump_asm(source_file, verbose=False)
                code_mem = dict(zip(count(START_ADDR, 4), code))
                return code_mem
            elif 'source_raw' in t:
                tmp_fname = "tmp.elf"
                # treat 'source_raw' as content of a .S file and compile it via riscv-none-embed-gcc.
                compile_source(t['source_raw'], tmp_fname)
                return read_elf(tmp_fname, verbose=False)
            elif 'elf' in t:
                return read_elf(t['elf'], verbose=False)
            else:
                raise ValueError(f"test case must contain either 'elf', 'source' or 'source_raw' key! Not found in {t['name']}")

        mem_dict = get_code_mem()
        code_len = len(mem_dict)

        mem_dict.update(mem_init)
        if code_len + len(mem_init) != len(mem_dict):
            raise ValueError(f"ERROR: overlapping memories (instr. mem starting at {START_ADDR} ({mem_dict}) and initial {mem_init})")

        reg_test(
            name=name, 
            timeout_cycles=t['timeout'], 
            reg_num=out_reg, 
            expected_val=out_val, 
            expected_mem=mem_out, 
            reg_init=reg_init,
            mem_dict=mem_dict,
            verbose=VERBOSE)
        print(f"== Test {i}/{len(SELECTED_TESTS)}: <{name}> completed successfully..")

    # from minized import MinizedPlatform, TopWrapper
    # m = MtkCpu(32)
    # MinizedPlatform().build(TopWrapper(m), do_program=False)
