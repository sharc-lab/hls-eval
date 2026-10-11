#include "check_clockwise.h"
#include <cstdio>
int main() {
    const Triangle_2D cases[] = {
        {0,0,2,0,1,1,0}, {0,0,1,1,2,0,1}, {0,0,1,1,2,2,255},
        {3,3,6,2,4,5,0}, {3,3,4,5,6,2,0},
        {255,255,0,255,255,0,7}, {255,0,0,255,0,0,99}
    };
    int failures = 0;
    for (const auto& t : cases) {
        const int expected = (int(t.x2)-int(t.x0))*(int(t.y1)-int(t.y0))
                           - (int(t.y2)-int(t.y0))*(int(t.x1)-int(t.x0));
        if (check_clockwise(t) != expected) ++failures;
    }
    std::printf("ORIENTATION fields=7 failures=%d\n", failures);
    return failures ? 1 : 0;
}
