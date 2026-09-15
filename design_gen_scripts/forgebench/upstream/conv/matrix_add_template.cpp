
void matrix_add(
    data_t in1[{C}][{H}][{W}],
    data_t in2[{C}][{H}][{W}],
    data_t out[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                out[c][i][j] = in1[c][i][j] + in2[c][i][j];
            }}
        }}
    }}
}}





