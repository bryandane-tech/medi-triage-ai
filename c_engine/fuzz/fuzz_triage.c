#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "../include/triage_engine.h"

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    // 1. Ignore empty inputs or excessively large buffers to keep execution fast
    if (Size == 0 || Size > 4096) return 0;

    // 2. Allocate a safe, null-terminated string from the raw fuzzer bytes
    char *input_str = malloc(Size + 1);
    if (!input_str) return 0;
    memcpy(input_str, Data, Size);
    input_str[Size] = '\0';

    // 3. Initialize arena and pattern matcher
    Arena *arena = create_arena(1024 * 1024);
    if (arena) {
        ACNode *root = init_aho_corasick(arena);
        if (root) {
            insert_keyword(arena, root, "chest pain", 5);
            insert_keyword(arena, root, "shortness of breath", 4);
            insert_keyword(arena, root, "fever", 2);
            build_ac_automation(arena, root);

            TriageResult result;
            analyze_symptoms_ac(root, input_str, &result);
        }
        free_arena(arena);
    }

    free(input_str);
    return 0;
}
