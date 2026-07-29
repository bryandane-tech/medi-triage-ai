#ifndef TRIAGE_ENGINE_H
#define TRIAGE_ENGINE_H

#include <stddef.h>
#include <stdint.h>

#define MAX_MATCHES 16
#define MAX_WORD_LEN 64
#define ALPHABET_SIZE 128

typedef struct {
    size_t size;
    size_t capacity;
    uint8_t *buffer;
} Arena;

typedef struct ACNode {
    struct ACNode *children[ALPHABET_SIZE];
    struct ACNode *fail;
    int is_end;
    char keyword[MAX_WORD_LEN];
    int priority_score;
} ACNode;

typedef struct {
    char matched_symptoms[MAX_MATCHES][MAX_WORD_LEN];
    int match_count;
    int max_priority;
} TriageResult;

#ifdef __cplusplus
extern "C" {
    #endif

    Arena* create_arena(size_t capacity);
    void free_arena(Arena *arena);
    ACNode* init_aho_corasick(Arena *arena);
    void insert_keyword(Arena *arena, ACNode *root, const char *keyword, int priority);
    void build_ac_automation(Arena *arena, ACNode *root);
    void analyze_symptoms_ac(ACNode *root, const char *text, TriageResult *result);

    #ifdef __cplusplus
}
#endif

#endif // TRIAGE_ENGINE_H
