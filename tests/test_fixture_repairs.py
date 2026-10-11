"""Native counterexamples for the reviewed fixture/algorithm defects.

Set VITIS_HOME and put g++ on PATH for AP header tests. This suite does not run
EDA or a model. The original kernels/testbenches come from the reviewed commit.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from hls_eval.comparison import compare_dump

ROOT = Path(__file__).resolve().parents[1]
BASE = "e373bc0a005f0a6030f77f27b3f0d71b16a35a0b"


def original(path):
    return subprocess.check_output(
        ["git", "show", f"{BASE}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT
    ).decode("utf-8")


def files(task):
    directory = ROOT / "hls_eval_data" / task
    tb = next(directory.glob("*_tb.cpp"))
    ref = next(p for p in directory.glob("*.cpp") if p != tb)
    return directory, ref, tb


@pytest.fixture
def native(tmp_path):
    compiler, sdk = shutil.which("g++"), os.environ.get("VITIS_HOME")
    if not compiler or not sdk:
        pytest.skip("Native compiler and VITIS_HOME required")
    counter = 0

    def run(task, source, tb, timeout=30):
        nonlocal counter
        directory, _, _ = files(task)
        work = tmp_path / str(counter)
        counter += 1
        work.mkdir()
        (work / "solution.cpp").write_text(source, encoding="utf-8")
        (work / "check.cpp").write_text(tb, encoding="utf-8")
        for data in directory.glob("*.data"):
            (work / data.name).write_bytes(data.read_bytes().replace(b"\r\n", b"\n"))
        exe = work / ("test.exe" if os.name == "nt" else "test")
        cmd = [
            compiler,
            "-std=c++14",
            "-O0",
            "-fno-fast-math",
            "-Wno-unknown-pragmas",
            "-I",
            str(directory),
            "-I",
            str(Path(sdk) / "include"),
            str(work / "solution.cpp"),
            str(work / "check.cpp"),
            "-o",
            str(exe),
        ]
        if os.name == "nt":
            io = work / "binary_io.cpp"
            io.write_text(
                "#include <stdlib.h>\n#include <fcntl.h>\n"
                "struct IO { IO() {_set_fmode(_O_BINARY);} }; static IO io;\n"
            )
            cmd.insert(-2, str(io))
            cmd.append("-Wl,--stack,33554432")
        compiled = subprocess.run(cmd, capture_output=True, timeout=120, check=False)
        (work / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        assert compiled.returncode == 0, compiled.stderr.decode(errors="replace")
        result = subprocess.run(
            [str(exe)], cwd=work, capture_output=True, timeout=timeout, check=False
        )
        (work / "stdout.txt").write_bytes(result.stdout)
        (work / "stderr.txt").write_bytes(result.stderr)
        return result

    return run


BAD = {
    "gnnbuilder/global_add_pool": '#include "global_add_pool.h"\nvoid global_add_pool(int,T_data[MAX_NODES][EMB_SIZE],T_data[EMB_SIZE]){}',
    "gnnbuilder/compute_neighbor_tables": '#include "compute_neighbor_tables.h"\nvoid compute_neighbor_tables(int[MAX_EDGES][2],int[MAX_NODES],int[MAX_NODES],int[MAX_NODES],int[MAX_EDGES],int,int){}',
    "gnnbuilder/gather_node_neighbors": '#include "gather_node_neighbors.h"\nvoid gather_node_neighbors(int,int,int[MAX_NODES],int[MAX_NODES],int[MAX_EDGES]){}',
    "pp4fpga/parallel_merge_sort": '#include "merge_sort_parallel.h"\nvoid merge_sort_parallel(DTYPE A[SIZE],DTYPE B[SIZE]){for(int i=0;i<SIZE;++i)B[i]=0;}',
    "polybench/nussinov": '#include "nussinov.h"\nvoid kernel_nussinov(char[60],int[60][60]){}',
    "chstone/df_float64_ge": '#include "float64_ge.h"\nflag float64_ge(float64 a,float64 b){return a>=b;}',
    "flowgnn/fgnn_linear_output_stationary": '#include "linear.h"\nvoid linear_output_stationary(FM_TYPE[DIM_IN],WT_TYPE[DIM_OUT][DIM_IN],WT_TYPE[DIM_OUT],hls::stream<std::array<FM_TYPE,PARALLEL>>&o){std::array<FM_TYPE,PARALLEL> z={};for(int i=0;i<DIM_OUT;i+=PARALLEL)o.write(z);}',
}


@pytest.mark.parametrize("task", BAD)
def test_wrong_implementations_are_rejected(native, task):
    _, _, tb = files(task)
    assert native(task, BAD[task], tb.read_text(encoding="utf-8")).returncode != 0


def test_nussinov_oracle_uses_original_input(native):
    task = "polybench/nussinov"
    _, _, tb = files(task)
    source = """#include "nussinov.h"
void kernel_nussinov(char seq[60],int table[60][60]) {
    for(int i=0;i<60;++i) {
        seq[i]='A';
        for(int j=i;j<60;++j) table[i][j]=0;
    }
}"""
    assert native(task, source, tb.read_text(encoding="utf-8")).returncode != 0


@pytest.mark.parametrize(
    "task", ["gnnbuilder/global_add_pool", "pp4fpga/parallel_merge_sort"]
)
def test_original_tb_falsely_accepts_noop(native, task):
    _, _, tb = files(task)
    assert native(task, BAD[task], original(tb)).returncode == 0


@pytest.mark.parametrize(
    "task,field",
    [
        ("machsuite/fft_strided", "real[0]"),
        ("machsuite/gemm_blocked", "prod[0]"),
        ("machsuite/md_knn", "force_x[0]"),
        ("machsuite/spmv_ellpack", "out[0]"),
        ("machsuite/md_grid", "force[0][0][0][0].x"),
    ],
)
def test_nan_was_accepted_and_is_now_rejected(native, task, field):
    directory, _, tb = files(task)
    header = next(directory.glob("*.h")).name
    for repaired in (False, True):
        text = tb.read_text(encoding="utf-8") if repaired else original(tb)
        checker = text[text.index("int check_data") : text.index("int main")]
        structure = text[
            text.index("struct bench_args_t") : text.index("int INPUT_SIZE")
        ]
        driver = (
            f'#include <cstdio>\n#include <cmath>\n#include <limits>\n#include "{header}"\n#define EPSILON 1e-6\n'
            + structure
            + checker
        )
        driver += "\nint main(){static bench_args_t a={},b={};"
        if task.endswith("md_grid") and repaired:
            driver += "fixture_n_points[0][0][0]=1;"
        driver += f"a.{field}=std::numeric_limits<double>::quiet_NaN();return check_data(&a,&b)?0:1;}}"
        assert native(task, "", driver).returncode == (1 if repaired else 0)


def test_unused_md_grid_slots_are_not_outputs(native):
    task = "machsuite/md_grid"
    _, _, tb = files(task)
    text = tb.read_text(encoding="utf-8")
    driver = '#include <cstdio>\n#include <limits>\n#include "md_grid.h"\n#define EPSILON 1e-6\n'
    driver += text[text.index("struct bench_args_t") : text.index("int INPUT_SIZE")]
    driver += text[text.index("int check_data") : text.index("int main")]
    driver += "\nint main(){static bench_args_t a={},b={};fixture_n_points[0][0][0]=1;a.force[0][0][0][1].x=std::numeric_limits<double>::quiet_NaN();return check_data(&a,&b)?0:1;}"
    assert native(task, "", driver).returncode == 0


def test_sorted_same_sum_wrong_multiset(native):
    task = "machsuite/sort_merge"
    _, _, tb = files(task)
    for repaired in (False, True):
        text = tb.read_text(encoding="utf-8") if repaired else original(tb)
        driver = '#include <cstdio>\n#include <inttypes.h>\n#include "sort_merge.h"\n'
        driver += text[text.index("struct bench_args_t") : text.index("int INPUT_SIZE")]
        driver += text[text.index("int check_data") : text.index("int main")]
        driver += "\nint main(){static bench_args_t a={},b={};a.a[0]=-1;a.a[SIZE-1]=1;return check_data(&a,&b)?0:1;}"
        assert native(task, "", driver).returncode == (1 if repaired else 0)


def test_kmp_fallback_timeout_and_return_value(native):
    task = "machsuite/kmp_kmp"
    _, ref, _ = files(task)
    driver = "#include \"kmp_kmp.h\"\nint main(){char p[4]={'A','A','A','A'},s[STRING_SIZE];int32_t next[4]={},count[1]={};for(int i=0;i<STRING_SIZE;++i)s[i]='B';s[0]=s[1]=s[2]='A';int r=kmp(p,s,next,count);return r!=0||count[0]!=0||next[3]!=3;}"
    with pytest.raises(subprocess.TimeoutExpired):
        native(task, original(ref), driver, timeout=2)
    assert native(task, ref.read_text(encoding="utf-8"), driver).returncode == 0
    once = "#include \"kmp_kmp.h\"\nint main(){char p[4]={'A','B','C','D'},s[STRING_SIZE];int32_t next[4]={},count[1]={};for(int i=0;i<STRING_SIZE;++i)s[i]='X';for(int i=0;i<4;++i)s[i]=p[i];int r=kmp(p,s,next,count);return r!=1||count[0]!=1;}"
    assert native(task, original(ref), once).returncode == 1
    assert native(task, ref.read_text(encoding="utf-8"), once).returncode == 0


@pytest.mark.parametrize(
    "task",
    ["machsuite/bfs_bulk", "rosetta/rendering_3d__projection", "polybench/nussinov"],
)
def test_original_reference_fails_repaired_contract(native, task):
    _, ref, tb = files(task)
    assert native(task, original(ref), tb.read_text(encoding="utf-8")).returncode != 0


@pytest.mark.parametrize(
    "task,signature",
    [
        (
            "polybench/heat-3d",
            "void kernel_heat_3d(double[10][10][10],double[10][10][10]){}",
        ),
        ("polybench/seidel-2d", "void kernel_seidel_2d(double[40][40]){}"),
    ],
)
def test_nonsteady_inputs_distinguish_noop(native, task, signature):
    directory, ref, tb = files(task)
    noop = f'#include "{next(directory.glob("*.h")).name}"\n{signature}'
    for repaired in (False, True):
        text = tb.read_text(encoding="utf-8") if repaired else original(tb)
        reference = native(task, ref.read_text(encoding="utf-8"), text)
        wrong = native(task, noop, text)
        assert reference.returncode == wrong.returncode == 0
        comparison = compare_dump(
            wrong.stderr.decode(), reference.stderr.decode(), kind="numeric_dump"
        )
        assert comparison["passed"] is (not repaired)


def test_clockwise_original_ap_arithmetic_is_correct(native):
    task = "rosetta/rendering_3d__check_clockwise"
    _, ref, _ = files(task)
    driver = """#include "check_clockwise.h"
int main(){unsigned state=7;for(int i=0;i<10000;++i){Triangle_2D t;unsigned c[6];for(int j=0;j<6;++j){state=1664525*state+1013904223;c[j]=state>>24;}t.x0=c[0];t.y0=c[1];t.x1=c[2];t.y1=c[3];t.x2=c[4];t.y2=c[5];t.z=0;int expected=(int(c[4])-int(c[0]))*(int(c[3])-int(c[1]))-(int(c[5])-int(c[1]))*(int(c[2])-int(c[0]));if(check_clockwise(t)!=expected)return 1;}return 0;}
"""
    assert ref.read_text(encoding="utf-8") == original(ref)
    assert native(task, ref.read_text(encoding="utf-8"), driver).returncode == 0


def test_nan_flag_accepts_any_nonzero_value(native):
    task = "chstone/df_float64_is_nan"
    _, ref, tb = files(task)
    code = ref.read_text(encoding="utf-8").replace(
        "flag float64_is_nan(", "flag original_is_nan("
    )
    code += "\nflag float64_is_nan(float64 a){return original_is_nan(a)?2:0;}\n"
    assert native(task, code, original(tb)).returncode != 0
    assert native(task, code, tb.read_text(encoding="utf-8")).returncode == 0


@pytest.mark.parametrize(
    "task,m,n,typ",
    [
        ("polybench/gramschmidt", 20, 30, "double"),
        ("hls_polybench__fixed__small/gramschmidt", 60, 80, "t_ap_fixed"),
    ],
)
def test_rank_deficient_basis_has_independent_expected_outputs(native, task, m, n, typ):
    _, ref, tb = files(task)
    driver = (
        tb.read_text(encoding="utf-8").replace(
            "    return 0;",
            f"""    for(int i=0;i<{m};++i)for(int j=0;j<{n};++j){{
        if(A[i][j]!=(j<{m}&&i==j?1:0))return 1;
        if(Q[i][j]!=(j<{m}&&i==j?1:0))return 1;
    }}
    for(int i=0;i<{n};++i)for(int j=0;j<{n};++j)
        if(R[i][j]!=(i<{m}&&j%{m}==i?1:0))return 1;
    return 0;""",
        )
        if task.startswith("polybench/")
        else tb.read_text(encoding="utf-8").replace(
            "  return 0;",
            f"""  for(int i=0;i<{m};++i)for(int j=0;j<{n};++j){{
        if(A[i][j]!=(j<{m}&&i==j?1:0))return 1;
        if(Q[i][j]!=(j<{m}&&i==j?1:0))return 1;
    }}
    for(int i=0;i<{n};++i)for(int j=0;j<{n};++j)
        if(R[i][j]!=(i<{m}&&j%{m}==i?1:0))return 1;
    return 0;""",
        )
    )
    assert driver != tb.read_text(encoding="utf-8")
    assert native(task, ref.read_text(encoding="utf-8"), driver).returncode == 0


def test_jacobi_checks_b_boundary_inside_completion_marker(native):
    task = "polybench/jacobi-2d"
    _, ref, tb = files(task)
    text = tb.read_text(encoding="utf-8")
    assert text.index("end   dump: B") < text.index("==END   DUMP_ARRAYS==")
    source = ref.read_text(encoding="utf-8").replace(
        "void kernel_jacobi_2d", "void fixture_reference"
    )
    source += "\nvoid kernel_jacobi_2d(double A[30][30],double B[30][30]){fixture_reference(A,B);B[0][0]+=1;}\n"
    reference = native(task, ref.read_text(encoding="utf-8"), text)
    wrong = native(task, source, text)
    assert wrong.returncode == 0
    assert not compare_dump(
        wrong.stderr.decode(), reference.stderr.decode(), kind="numeric_dump"
    )["passed"]


def test_outer_product_input_mutation_no_longer_changes_oracle(native):
    task = "rosetta/optical_flow__outer_product"
    _, _, tb = files(task)
    source = """#include "outer_product.h"
void outer_product(gradient_t g[MAX_HEIGHT][MAX_WIDTH],outer_t o[MAX_HEIGHT][MAX_WIDTH]){
  for(int i=0;i<MAX_HEIGHT;++i)for(int j=0;j<MAX_WIDTH;++j){
    g[i][j].x=0;g[i][j].y=0;g[i][j].z=0;
    for(int k=0;k<6;++k)o[i][j].val[k]=0;
  }
}"""
    assert native(task, source, original(tb)).returncode == 0
    assert native(task, source, tb.read_text(encoding="utf-8")).returncode != 0


@pytest.mark.parametrize("extra", [False, True])
def test_linear_token_shape(native, extra):
    task = "flowgnn/fgnn_linear_output_stationary"
    _, ref, tb = files(task)
    source = ref.read_text(encoding="utf-8").replace(
        "void linear_output_stationary", "void fixture_reference"
    )
    source += """\nvoid linear_output_stationary(FM_TYPE i[DIM_IN],WT_TYPE w[DIM_OUT][DIM_IN],
WT_TYPE b[DIM_OUT],hls::stream<std::array<FM_TYPE,PARALLEL>>&o){fixture_reference(i,w,b,o);"""
    source += (
        "std::array<FM_TYPE,PARALLEL> z={};o.write(z);}" if extra else "o.read();}"
    )
    assert native(task, source, tb.read_text(encoding="utf-8")).returncode != 0


def test_des_matches_independent_cipher_and_dump_is_checked(native, tmp_path):
    from types import SimpleNamespace

    cipher = pytest.importorskip("Crypto.Cipher.DES")
    from hls_eval.comparison import functional_passed, run_checked_csim
    from hls_eval.data import BenchmarkCase
    from hls_eval.tools import ExecutionData, ToolDataOutput

    task = "c2hlsc/des"
    directory, ref, tb = files(task)
    independent = cipher.new(
        bytes.fromhex("0123456789abcdef"), cipher.MODE_ECB
    ).encrypt(bytes.fromhex("0123456789abcde7"))
    correct = native(
        task, ref.read_text(encoding="utf-8"), tb.read_text(encoding="utf-8")
    )
    assert bytes.fromhex(correct.stdout.decode()) == independent

    def csim(build_dir, sources, **kwargs):
        implementation = next(
            p for p in sources if p.suffix == ".cpp" and not p.stem.endswith("_tb")
        )
        driver = next(p for p in sources if p.stem.endswith("_tb"))
        result = native(
            task,
            implementation.read_text(encoding="utf-8"),
            driver.read_text(encoding="utf-8"),
        )
        return (
            ToolDataOutput(ExecutionData(0, "", "", 0, 1, 1, False), None),
            ToolDataOutput(
                ExecutionData(
                    result.returncode,
                    result.stdout.decode(),
                    result.stderr.decode(),
                    0,
                    1,
                    1,
                    False,
                ),
                None,
            ),
        )

    tool = SimpleNamespace(run=csim, vitis_hls_path=Path(os.environ["VITIS_HOME"]))
    case = BenchmarkCase(directory)
    _, checked = run_checked_csim(tool, case, tmp_path / "correct", case.source_files)
    assert functional_passed(checked)
    candidate = tmp_path / "wrong.cpp"
    candidate.write_text(
        '#include "des.h"\nvoid des_crypt(des_block_t*,des_block_t*o,des_key_t*){for(int i=0;i<8;++i)(*o)[i]=0;}'
    )
    _, checked = run_checked_csim(tool, case, tmp_path / "wrong", [candidate, tb])
    assert checked.data_execution.return_code == 0
    assert not functional_passed(checked)


def test_nw_traceback_consumes_sequences_and_has_optimal_score(native):
    task = "machsuite/nw_nw"
    _, ref, _ = files(task)
    driver = """#include "nw_nw.h"
int main(){
  char a[ALEN],b[BLEN],aa[ALEN+BLEN],bb[ALEN+BLEN];
  int m[(ALEN+1)*(BLEN+1)]={};char ptr[(ALEN+1)*(BLEN+1)]={};
  int expected[BLEN+1][ALEN+1];
  for(int i=0;i<ALEN;++i)a[i]=i<ALEN/2?'A':'B';
  for(int i=0;i<BLEN;++i)b[i]=i<BLEN/2?'B':'A';
  for(int i=0;i<=ALEN;++i)expected[0][i]=-i;
  for(int j=0;j<=BLEN;++j)expected[j][0]=-j;
  for(int j=1;j<=BLEN;++j)for(int i=1;i<=ALEN;++i){
    int v=expected[j-1][i-1]+(a[i-1]==b[j-1]?1:-1);
    if(expected[j-1][i]-1>v)v=expected[j-1][i]-1;
    if(expected[j][i-1]-1>v)v=expected[j][i-1]-1;
    expected[j][i]=v;
  }
  needwun(a,b,aa,bb,m,ptr);
  int ai=ALEN-1,bi=BLEN-1,score=0,end=0;
  for(int i=0;i<ALEN+BLEN;++i){
    if(aa[i]=='_'&&bb[i]=='_'){end=i;break;}
    if(aa[i]=='-'&&bb[i]=='-')return 1;
    if(aa[i]!='-'){if(ai<0||aa[i]!=a[ai--])return 1;}
    if(bb[i]!='-'){if(bi<0||bb[i]!=b[bi--])return 1;}
    score+=aa[i]=='-'||bb[i]=='-'?-1:(aa[i]==bb[i]?1:-1);
    end=i+1;
  }
  for(int i=end;i<ALEN+BLEN;++i)if(aa[i]!='_'||bb[i]!='_')return 1;
  return ai!=-1||bi!=-1||score!=expected[BLEN][ALEN];
}"""
    assert native(task, ref.read_text(encoding="utf-8"), driver).returncode == 0
