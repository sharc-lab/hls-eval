# ForgeBench base-config validation

Upstream: feature/correctness-harness at 7f9cbd777e02c8fb050e71720673300b29b1b742.

All kernels use ap_fixed<16,5>. Testbenches compare every declared output element
against independent float64 goldens with abs(actual - golden) <= 1e-3 and no relative allowance.

Designs: **50**. **4 arithmetic_error**; **14 mismatch**; **32 pass**.

Native C simulation uses installed Vitis fixed-point/math headers and libraries,
with GCC array-bounds instrumentation. These results do not include synthesis or RTL cosimulation.

| Design | Result | Mismatches / compared | Maximum absolute error |
|---|---|---:|---:|
| attention_op_p1 | arithmetic_error | 0 / 0 | not reached |
| attention_op_p2 | mismatch | 503 / 512 | 0.0030260364 |
| attention_op_p3 | mismatch | 507 / 512 | 0.003051547 |
| config_CIN16_HIN28_WIN28_COUT16_K1_IPF1_KPF11_KPF21_BPF1_OPF1_UFCIN1_UFCOU1_ap_fixed_16_5_ | pass | 0 / 14400 | 7.4218193e-07 |
| conv_A | pass | 0 / 12544 | 0 |
| conv_B | pass | 0 / 6272 | 0 |
| conv_C | pass | 0 / 25088 | 0 |
| conv_D | pass | 0 / 25088 | 0 |
| conv_E | pass | 0 / 3136 | 0 |
| conv_F | pass | 0 / 12544 | 0 |
| conv_G | pass | 0 / 9216 | 0 |
| conv_H | pass | 0 / 3136 | 0 |
| conv_I | pass | 0 / 10816 | 0 |
| conv_template | pass | 0 / 12544 | 1.0644451e-06 |
| diff_dims_p1 | pass | 0 / 12288 | 0 |
| diff_dims_p2 | pass | 0 / 8192 | 0 |
| diff_dims_p3 | pass | 0 / 49152 | 0 |
| diff_orders_p1 | pass | 0 / 4096 | 0 |
| diff_orders_p2 | pass | 0 / 1024 | 0 |
| diff_orders_p3 | pass | 0 / 8192 | 0 |
| gpt_transformer_p1 | mismatch | 256 / 256 | 1.3236193 |
| llama_transformer_p2 | arithmetic_error | 0 / 0 | not reached |
| mlp | pass | 0 / 4096 | 0.0006676795 |
| mult_op_p1 | pass | 0 / 512 | 0 |
| mult_op_p2 | pass | 0 / 16 | 0 |
| mult_op_p3 | pass | 0 / 1 | 0 |
| resnet18_block1 | mismatch | 33545 / 200704 | 0.0027771597 |
| resnet18_block2 | mismatch | 15340 / 100352 | 0.0027466473 |
| resnet18_block2_downsample | mismatch | 4168 / 100352 | 0.0026245294 |
| resnet18_block3 | mismatch | 8357 / 50176 | 0.0028381015 |
| resnet18_block3_downsample | mismatch | 7207 / 50176 | 0.0025024261 |
| resnet18_block4 | mismatch | 2859 / 25088 | 0.0026245294 |
| resnet18_block4_downsample | mismatch | 3158 / 25088 | 0.0026855249 |
| resnet50_block1 | pass | 0 / 802816 | 0.0008182293 |
| resnet50_block2 | pass | 0 / 401408 | 0.00087160985 |
| resnet50_block2_downsample | pass | 0 / 401408 | 0.00087257801 |
| resnet50_block3 | pass | 0 / 200704 | 0.00085825495 |
| resnet50_block3_downsample | pass | 0 / 200704 | 0.00079724848 |
| resnet50_block4 | pass | 0 / 100352 | 0.00083539488 |
| resnet50_block4_downsample | pass | 0 / 100352 | 0.0008163168 |
| testing_impl | pass | 0 / 513 | 0 |
| testing_unroll | pass | 0 / 513 | 0 |
| tiled_attn_p1 | arithmetic_error | 0 / 0 | not reached |
| tiled_attn_p2 | arithmetic_error | 0 / 0 | not reached |
| vec_mtx_p1 | pass | 0 / 16 | 0 |
| vec_mtx_p2 | pass | 0 / 16 | 0 |
| vgg19_block1 | mismatch | 174641 / 401408 | 0.0037841797 |
| vgg19_block2 | mismatch | 45534 / 200704 | 0.0068974495 |
| vgg19_block3 | mismatch | 22031 / 100352 | 0.0060358047 |
| vgg19_block4 | mismatch | 5112 / 25088 | 0.0084209442 |

## Float control

**50/50 temporary float kernels pass** against the same float64 goldens
and the same absolute 1e-3 threshold. The configs use the same dimensions and
operations as the fixed-point dataset. Input/golden file hashes were checked
for equality. The saved dataset remains fixed-point.

See float_control_results.json for per-output errors.


## Config repairs

Untouched originals are included as upstream_config.json in every design.
The effective config.json contains the fixed-point datatype and these documented data-path repairs:

- resnet50_block3_downsample: Match final residual-add, activation, and store channels to the declared full output shape [1024, 14, 14]; upstream only processed half the channels.
- resnet50_block4_downsample: Match final residual-add, activation, and store channels to the declared full output shape [2048, 7, 7]; upstream only processed half the channels.
- testing_impl: Wire DRAM_12 to dot(DRAM_5[:16], DRAM_10[:16]) + DRAM_11[0] using existing ports; add missing loads, compute/store where absent.
- testing_unroll: Wire DRAM_12 to dot(DRAM_5[:16], DRAM_10[:16]) + DRAM_11[0] using existing ports; add missing loads, compute/store where absent.
- vec_mtx_p2: Load all 64 vector elements required by the 64x16 vector-matrix product; upstream loaded only 16.

## Exclusions

- conv/test_case_configs/conv_variable.json: Symbolic, non-JSON template: Expecting value: line 3 column 47 (char 63)

## Execution diagnostics

### attention_op_p1

~~~text
Process terminated by SIGFPE

[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib64/libthread_db.so.1".

Program received signal SIGFPE, Arithmetic exception.
0x0000000000406f92 in ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::RType<16, 5, true>::div ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::operator/<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>(ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0> const&) const ()
#0  0x0000000000406f92 in ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::RType<16, 5, true>::div ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::operator/<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>(ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0> const&) const ()
#1  0x0000000000406176 in grouped_multihead_attention_8_256_16_16_ap_fixed_16_5_(ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], int) ()
#2  0x0000000000406d64 in top(ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [256]) ()
#3  0x000000000040dc75 in main ()
~~~

### llama_transformer_p2

~~~text
Process terminated by SIGFPE

[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib64/libthread_db.so.1".

Program received signal SIGFPE, Arithmetic exception.
0x0000000000407598 in ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::RType<16, 5, true>::div ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::operator/<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>(ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0> const&) const ()
#0  0x0000000000407598 in ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::RType<16, 5, true>::div ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>::operator/<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0>(ap_fixed_base<16, 5, true, (ap_q_mode)5, (ap_o_mode)3, 0> const&) const ()
#1  0x00000000004061ca in rms_norm_8_32_ap_fixed_16_5_(ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0>*, ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32]) ()
#2  0x00000000004071e8 in top(ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [128], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32], ap_fixed<16, 5, (ap_q_mode)5, (ap_o_mode)3, 0> (*) [32]) ()
#3  0x0000000000413130 in main ()
~~~

### tiled_attn_p1

~~~text
Process terminated by SIGFPE
~~~

### tiled_attn_p2

~~~text
Process terminated by SIGFPE
~~~


## Limits

Each design has one deterministic input case. Inputs contain signed values and convolution
weights use two selected input channels per output with varied spatial taps.
This exercises the configured full-size output; it does not exhaust the input space.
Numerical mismatches can reflect quantization, overflow, or remaining kernel defects.
They are not automatically classified as harmless fixed-point error.

Full commands, logs, executables, and actual output dumps: /tmp/forgebench-base-validation.
