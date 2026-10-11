#include "block.h"
#include <cmath>
#include <limits>
int main() {
    int epsilon_test[N * M];
    for (int case_id=0; case_id<4; ++case_id) {
        for (int i=0; i<N*M; ++i) {
            epsilon_test[i] = case_id==0 ? (i*73%7==0) : case_id==1 ? 0 : case_id==2 ? 1 : ((i*11+i/M)%5<2);
        }
        double result = std::numeric_limits<double>::quiet_NaN();
        BlockFrequency(&result, epsilon_test);
        if (!std::isfinite(result)) return 1;
        printf("case %d result %.17g\n",case_id,result);
    }
    return 0;
}
