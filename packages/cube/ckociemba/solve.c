#include <stdio.h>
#include <stdlib.h>
#include "search.h"

int main(int argc, char **argv)
{
    if (argc > 2) {
        char patternized[64];
        char* facelets = argv[2];
        if (argc > 3) {
            patternize(facelets, argv[3], patternized);
            facelets = patternized;
        }
        char *sol = solution(
            facelets,
            24,
            1000,
            0,
            argv[1]
        );
        if (sol == NULL) {
            puts("Unsolvable cube!");
            return 2;
        }
        puts(sol);
        free(sol);
        return 0;
    } else {
        return 1;
    }
}
