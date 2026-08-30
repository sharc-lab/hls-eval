import argparse
import json
import random
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from scipy.stats import kendalltau, spearmanr

DIR_CURRENT = Path(__file__).resolve().parent
DIR_FIGURES = DIR_CURRENT / "figures"

DEFAULT_OUTPUT_DATA_DIR = DIR_CURRENT / "output_data"
DEFAULT_TAU_AT_K_PLOT_PATH = DIR_FIGURES / "kernel_latency_tau_at_k.png"
DEFAULT_RHO_AT_K_PLOT_PATH = DIR_FIGURES / "kernel_latency_rho_at_k.png"

MODELS_TO_PLOT = ["deepseek/deepseek-v4-flash", "openai/gpt-oss-120b"]

# Monte Carlo trials per k. A pilot run measured the per-k standard deviation
# of rho/tau under resampling (largest at k=1, shrinking as k grows toward
# the max sample count) and solved trials = (sigma / target_se)^2 for a
# target standard error of 0.005; the largest requirement observed was ~153
# trials at k=1. This is cheap CPU-only resampling of already-collected LLM
# estimates (no new LLM calls), so we use a generous fixed trial count well
# above that minimum rather than tuning it per k.
MONTE_CARLO_TRIALS = 2000

AGGREGATORS = {
    "median": statistics.median,
    "mean": statistics.mean,
}


def load_kernel_samples(
    output_data_dir: Path,
    model_name: str,
) -> list[tuple[str, float, list[float]]]:
    """Return (kernel_name, true_latency, valid_estimates) for each kernel.

    Kernels with zero valid (non-null) estimates are excluded entirely, since
    there is no sample to draw from at any k.
    """
    kernels = []

    for results_path in sorted(output_data_dir.glob("*/all_eval_data.json")):
        all_results = json.loads(results_path.read_text())
        model_results = [
            sample
            for sample in all_results.values()
            if sample.get("model_name") == model_name
        ]
        if not model_results:
            continue

        kernel_name = model_results[0]["benchmark_case_name"]
        true_latency = model_results[0].get("target_actual_latency_cycles")
        estimated_latencies = [
            sample["estimated_latency_cycles"]
            for sample in model_results
            if sample.get("estimated_latency_cycles") is not None
        ]

        if true_latency is None or not estimated_latencies:
            continue

        kernels.append((kernel_name, true_latency, estimated_latencies))

    return kernels


def draw_k_samples(
    estimates: list[float], k: int, rng: random.Random
) -> list[float]:
    """Draw k samples for one kernel, matching pass@k-style resampling.

    Sampled without replacement when the kernel has at least k valid
    estimates (an ordinary random subset, as in pass@k). When a kernel has
    fewer than k valid estimates, without-replacement sampling of k values is
    impossible, so we fall back to sampling with replacement from whatever
    valid estimates that kernel does have.
    """
    if len(estimates) >= k:
        return rng.sample(estimates, k)
    return [rng.choice(estimates) for _ in range(k)]


def run_monte_carlo_trials(
    kernels: list[tuple[str, float, list[float]]],
    k: int,
    aggregator_name: str,
    n_trials: int,
    rng: random.Random,
) -> tuple[list[float], list[float]]:
    """Run n_trials joint resampling trials at a given k.

    Each trial independently draws k samples per kernel (see draw_k_samples),
    aggregates them into one predicted latency per kernel, and computes
    Spearman rho and Kendall tau between the resulting predicted-latency
    ranking and the gold ranking. Both statistics are computed from the same
    draws so they share one Monte Carlo sampling loop.

    Returns (rho_trials, tau_trials): the per-trial statistic values, from
    which the mean (rho@k / tau@k) and standard error can be computed.
    """
    aggregate = AGGREGATORS[aggregator_name]
    true_values = [true_latency for _, true_latency, _ in kernels]

    rho_trials = []
    tau_trials = []

    for _ in range(n_trials):
        predicted_values = [
            aggregate(draw_k_samples(estimates, k, rng))
            for _, _, estimates in kernels
        ]

        rho, _ = spearmanr(true_values, predicted_values)
        tau, _ = kendalltau(true_values, predicted_values)
        rho_trials.append(rho)
        tau_trials.append(tau)

    return rho_trials, tau_trials


def compute_stat_at_k(
    kernels: list[tuple[str, float, list[float]]],
    aggregator_name: str,
    n_trials: int,
    seed: int,
) -> dict[int, dict[str, tuple[float, float]]]:
    """Compute rho@k and tau@k (mean and standard error) for k=1..max_n.

    max_n is the largest number of valid samples held by any included
    kernel. Returns {k: {"rho": (mean, se), "tau": (mean, se)}}.
    """
    max_n = max(len(estimates) for _, _, estimates in kernels)
    rng = random.Random(seed)

    results = {}
    for k in range(1, max_n + 1):
        rho_trials, tau_trials = run_monte_carlo_trials(
            kernels, k, aggregator_name, n_trials, rng
        )
        rho_mean = statistics.mean(rho_trials)
        rho_se = statistics.pstdev(rho_trials) / (n_trials**0.5)
        tau_mean = statistics.mean(tau_trials)
        tau_se = statistics.pstdev(tau_trials) / (n_trials**0.5)
        results[k] = {
            "rho": (rho_mean, rho_se),
            "tau": (tau_mean, tau_se),
        }

    return results


MODEL_COLORS = {
    "deepseek/deepseek-v4-flash": "tab:blue",
    "openai/gpt-oss-120b": "tab:orange",
}


def plot_stat_at_k(
    stat_at_k_by_model: dict[str, dict[int, dict[str, tuple[float, float]]]],
    stat_key: str,
    stat_label: str,
    plot_path: Path,
    aggregator: str,
) -> None:
    if not stat_at_k_by_model:
        raise ValueError("No valid model results were found")

    figure, axis = plt.subplots(figsize=(7.5, 5.5))

    all_k_values: set[int] = set()
    for model_name, stat_at_k in stat_at_k_by_model.items():
        k_values = sorted(stat_at_k)
        all_k_values.update(k_values)
        means = [stat_at_k[k][stat_key][0] for k in k_values]
        standard_errors = [stat_at_k[k][stat_key][1] for k in k_values]
        color = MODEL_COLORS.get(model_name)

        lower_band = [mean - 3 * se for mean, se in zip(means, standard_errors)]
        upper_band = [mean + 3 * se for mean, se in zip(means, standard_errors)]
        axis.fill_between(k_values, lower_band, upper_band, color=color, alpha=0.2)

        axis.plot(
            k_values,
            means,
            color=color,
            linewidth=1.6,
            marker="o",
            markersize=5,
            label=model_name,
        )

    axis.set_xticks(sorted(all_k_values))
    axis.set_xlim(min(all_k_values), max(all_k_values))
    figure.suptitle(
        f"HLS Kernel Ranking {stat_label}@k ({aggregator})", fontsize=13, y=0.99
    )
    axis.set_title(
        "Shaded band: ±3 SE of the Monte Carlo estimate of the mean\n"
        "(sampling precision only, not ranking uncertainty)",
        fontsize=8.5,
        color="dimgray",
    )
    axis.set_xlabel("k (samples aggregated per kernel)")
    axis.set_ylabel(f"Monte Carlo Estimate of Expected {stat_label} vs. Gold Ranking")
    axis.grid(linestyle="--", alpha=0.35)
    axis.set_axisbelow(True)
    axis.legend(loc="lower right", fontsize=8, framealpha=0.85)

    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def aggregator_plot_path(base_path: Path, aggregator: str) -> Path:
    return base_path.with_name(f"{base_path.stem}__{aggregator}{base_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot expected Kendall tau@k and Spearman rho@k between "
        "the LLM-predicted and gold HLS kernel latency rankings, as a "
        "function of how many samples per kernel are aggregated."
    )
    parser.add_argument(
        "--output-data-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DATA_DIR,
        help="Directory containing per-kernel evaluation result directories",
    )
    parser.add_argument(
        "--tau-at-k-output",
        type=Path,
        default=DEFAULT_TAU_AT_K_PLOT_PATH,
        help="Path for the generated tau@k PNG plot",
    )
    parser.add_argument(
        "--rho-at-k-output",
        type=Path,
        default=DEFAULT_RHO_AT_K_PLOT_PATH,
        help="Path for the generated rho@k PNG plot",
    )
    parser.add_argument(
        "--aggregator",
        choices=sorted(AGGREGATORS),
        default="median",
        help="How to combine the k sampled estimates per kernel",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=MONTE_CARLO_TRIALS,
        help="Monte Carlo trials per k",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for Monte Carlo sampling",
    )
    args = parser.parse_args()

    args.tau_at_k_output.parent.mkdir(parents=True, exist_ok=True)
    args.rho_at_k_output.parent.mkdir(parents=True, exist_ok=True)

    stat_at_k_by_model = {}
    for model_name in MODELS_TO_PLOT:
        kernels = load_kernel_samples(args.output_data_dir, model_name)
        if not kernels:
            print(f"Skipping {model_name}: no valid model results")
            continue

        stat_at_k = compute_stat_at_k(
            kernels, args.aggregator, args.trials, args.seed
        )
        stat_at_k_by_model[model_name] = stat_at_k
        for k in sorted(stat_at_k):
            rho_mean, _ = stat_at_k[k]["rho"]
            tau_mean, _ = stat_at_k[k]["tau"]
            print(
                f"{model_name} k={k}: rho@k={rho_mean:.4f} tau@k={tau_mean:.4f}"
            )

    if not stat_at_k_by_model:
        return

    tau_plot_path = aggregator_plot_path(args.tau_at_k_output, args.aggregator)
    plot_stat_at_k(
        stat_at_k_by_model, "tau", "Kendall τ", tau_plot_path, args.aggregator
    )
    print(f"Saved tau@k plot to {tau_plot_path}")

    rho_plot_path = aggregator_plot_path(args.rho_at_k_output, args.aggregator)
    plot_stat_at_k(
        stat_at_k_by_model, "rho", "Spearman ρ", rho_plot_path, args.aggregator
    )
    print(f"Saved rho@k plot to {rho_plot_path}")


if __name__ == "__main__":
    main()
