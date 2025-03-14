import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from pprint import pp

import pandas as pd
from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.tools import VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import unwrap
from joblib import Parallel, delayed

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent

DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

EXP_DATA_DIR = DIR_CURRENT / "exp_data"

N_JOBS = 48

bench_sources = set(
    [
        "polybench",
        "machsuite",
        "rosetta",
        "chstone",
        "c2hlsc",
        "pp4fpga",
        "flowgnn",
        "gnnbuilder",
    ]
)

if __name__ == "__main__":
    all_benchmark_case_dirs = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)
    all_benchmark_cases = [
        BenchmarkCase(d, name=d.name) for d in all_benchmark_case_dirs
    ]

    # Create a list to store our benchmark data
    benchmark_data = []

    # Collect data for each benchmark
    for bc in all_benchmark_cases:
        overlap = set(bc.tags_all).intersection(bench_sources)
        if len(overlap) == 1:
            source = overlap.pop()
        else:
            raise ValueError(f"Expected 1 source, found {len(overlap)}")

        # Count kernel lines
        kernel_lines = bc.kernel_fp.read_text().splitlines()
        kernel_loc = len([line for line in kernel_lines if line.strip()])

        # Count header lines
        header_lines = bc.h_files[0].read_text().splitlines()
        header_loc = len([line for line in header_lines if line.strip()])

        # Add to our dataset
        benchmark_data.append(
            {
                "name": bc.name,
                "source": source,
                "kernel_loc": kernel_loc,
                "header_loc": header_loc,
            }
        )

    # Create dataframe
    df = pd.DataFrame(benchmark_data)

    print(df)

    # Print source counts
    source_counts = df["source"].value_counts()
    pp(source_counts.to_dict())

    # Calculate average LOC by source
    avg_stats = df.groupby("source").agg(
        {"kernel_loc": "mean", "header_loc": "mean", "name": "count"}
    )

    # Print results
    pp(avg_stats["kernel_loc"].to_dict())
    pp(avg_stats["header_loc"].to_dict())
    pp(avg_stats["name"].to_dict())

    EXP_DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(EXP_DATA_DIR / "bench_stats.csv", index=False)
    avg_stats.to_csv(EXP_DATA_DIR / "avg_stats.csv")

    order = ["polybench", "machsuite", "rosetta", "chstone", "c2hlsc"]
    display_name = {
        "polybench": "Polybench",
        "machsuite": "MachSuite",
        "rosetta": "Rosetta",
        "chstone": "CHStone",
        "c2hlsc": "C2HLSC",
    }

    # write code to eit the folling
    # \begin{tabular}{l|ccccc}
    #         \toprule
    #         \textbf{\makecell{Data\\Source}} & \textbf{\makecell{\# of Bench.\\Designs}} & \textbf{\makecell{Average\\Kernel LoC}} & \textbf{\makecell{Average HLS\\ Synthesis Runtime}} \\
    #         \midrule
    #         \textbf{Polybench \cite{polybench}} & 28 & 34 & Yes \\
    #         \textbf{MachSuite \cite{machsuite}} & 18 & 85 & Yes \\
    #         \textbf{CHStone \cite{machsuite}} & ??? & ???  & ???   \\
    #         \textbf{Rosetta \cite{rosetta}} & ???   & ???  & ???   \\
    #         \textbf{C2HLSC \cite{c2hlsc}} & ???   & ???  & ???   \\
    #         \textbf{PP4FPGA \cite{pp4fpga}} & ???   & ???  & ???   \\
    #         \textbf{GNNBuilder \cite{gn_builder}} & ???   & ???  & ???   \\
    #         \textbf{FlowGNN \cite{flow_gnn}} & ???   & ???  & ???   \\
    #         \midrule
    #         \textbf{Totals} & 85 & ??? & -   \\
    #         \bottomrule
    #     \end{tabular}

    tabular_txt = ""
    tabular_txt += "\\begin{tabular}{l|ccc}\n"
    tabular_txt += "\\toprule\n"
    tabular_txt += "\\textbf{Data\\\\Source} & \\textbf{\\# of Bench.\\\\Designs} & \\textbf{Average\\\\Kernel LoC} & \\textbf{Average HLS\\\\Synthesis Runtime} \\\\\n"
    tabular_txt += "\\midrule\n"
    for src in order:
        tabular_txt += f"\\textbf{{{display_name[src]}}}"
        tabular_txt += f" & {avg_stats['name'][src]} & {int(round(avg_stats['kernel_loc'][src]))} & - \\\\\n"
    tabular_txt += "\\midrule\n"
    tabular_txt += f"\\textbf{{Total}} & {avg_stats['name'].sum()} & - & - \\\\\n"
    tabular_txt += "\\bottomrule\n"
    tabular_txt += "\\end{tabular}\n"

    with open(EXP_DATA_DIR / "tabular.txt", "w") as f:
        f.write(tabular_txt)

    # exit()

    def measure_synth(bc: BenchmarkCase) -> float:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            benchmark_case_synth = bc.copy_to(tmp_path / "design_base")
            print(f"Running HLS synthesis in case_dir {tmp_path}")

            vitis_hls_dir = unwrap(
                auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found"
            )

            tool_hls = VitisHLSSynthTool(vitis_hls_dir)
            results = tool_hls.run(
                tmp_path,
                source_files=benchmark_case_synth.source_files,
                build_name=benchmark_case_synth.name,
                hls_top_function=benchmark_case_synth.top_fn,
            )

        assert results.data_execution.return_code == 0, results.data_execution

        return results.data_execution.execution_time

    synth_runtimes = Parallel(n_jobs=N_JOBS, backend="threading")(
        delayed(measure_synth)(bc) for bc in all_benchmark_cases
    )

    sources = [
        set(bc.tags_all).intersection(bench_sources).pop() for bc in all_benchmark_cases
    ]

    synth_data = pd.DataFrame(
        {
            "name": [bc.name for bc in all_benchmark_cases],
            "source": sources,
            "synth_runtime": synth_runtimes,
        }
    )
    avg_synth = synth_data.groupby("source").agg({"synth_runtime": "mean"})

    synth_data.to_csv(EXP_DATA_DIR / "synth_runtimes.csv", index=False)
    avg_synth.to_csv(EXP_DATA_DIR / "avg_synth_runtimes.csv")
