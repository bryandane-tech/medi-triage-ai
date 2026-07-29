#include <stdio.h>
#include "../include/triage_engine.h"

int main(void) {
    char buffer[2048];

    // AFL++ persistent fuzzer input loop
    while (fgets(buffer, sizeof(buffer), stdin)) {
        Arena* arena = create_arena(1024 * 1024);
        if (!arena) continue;

        ACNode* root = init_aho_corasick(arena);
        if (!root) {
            free_arena(arena);
            continue;
        }

        insert_keyword(arena, root, "chest pain", 5);
        insert_keyword(arena, root, "shortness of breath", 4);
        insert_keyword(arena, root, "fever", 2);
        build_ac_automation(arena, root);

        TriageResult result;
        analyze_symptoms_ac(root, buffer, &result);

        free_arena(arena);
    }
    return 0;
}
