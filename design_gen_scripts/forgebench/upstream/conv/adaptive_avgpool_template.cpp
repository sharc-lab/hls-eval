void adaptive_avgpool(
    data_t input[{C}][{H_IN}][{W_IN}],
    data_t output[{C}][{H_OUT}][{W_OUT}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int oh = 0; oh < {H_OUT}; oh++) {{
            int h_start = (int)floor(( (float)oh * {H_IN} ) / {H_OUT});
            int h_end   = (int)ceil(( (float)(oh + 1) * {H_IN} ) / {H_OUT});
            if (h_end > {H_IN}) {{
                h_end = {H_IN};
            }}
            for (int ow = 0; ow < {W_OUT}; ow++) {{
                int w_start = (int)floor(( (float)ow * {W_IN} ) / {W_OUT});
                int w_end   = (int)ceil(( (float)(ow + 1) * {W_IN} ) / {W_OUT});
                if (w_end > {W_IN}) {{
                    w_end = {W_IN};
                }}

                data_t sum = 0;
                int count = 0;
                for (int h = h_start; h < h_end; h++) {{
                    for (int w = w_start; w < w_end; w++) {{
                        sum += input[c][h][w];
                        count++;
                    }}
                }}
                if (count > 0)
                    output[c][oh][ow] = sum / (data_t)count;
                else
                    output[c][oh][ow] = 0;
            }}
        }}
    }}
}}




