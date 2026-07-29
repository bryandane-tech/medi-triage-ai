#include "../include/triage_engine.h"
#include <stdlib.h>
#include <string.h>

Arena* create_arena(size_t capacity) {
    Arena *arena = (Arena *)malloc(sizeof(Arena));
    if (!arena) return NULL;
    arena->buffer = (uint8_t *)malloc(capacity);
    if (!arena->buffer) { free(arena); return NULL; }
    arena->capacity = capacity;
    arena->size = 0;
    return arena;
}

void free_arena(Arena *arena) {
    if (arena) {
        if (arena->buffer) free(arena->buffer);
        free(arena);
    }
}

static void* arena_alloc(Arena *arena, size_t bytes) {
    size_t aligned = (bytes + 7) & ~7; // 8-byte boundary alignment
    if (arena->size + aligned > arena->capacity) return NULL; // Prevent OOM buffer overflow
    void *ptr = &arena->buffer[arena->size];
    arena->size += aligned;
    memset(ptr, 0, aligned);
    return ptr;
}

ACNode* init_aho_corasick(Arena *arena) {
    return (ACNode *)arena_alloc(arena, sizeof(ACNode));
}

void insert_keyword(Arena *arena, ACNode *root, const char *keyword, int priority) {
    ACNode *curr = root;
    size_t len = strlen(keyword);
    for (size_t i = 0; i < len; i++) {
        uint8_t idx = (uint8_t)keyword[i];
        if (idx >= ALPHABET_SIZE) continue;
        if (!curr->children[idx]) {
            curr->children[idx] = (ACNode *)arena_alloc(arena, sizeof(ACNode));
        }
        curr = curr->children[idx];
    }
    curr->is_end = 1;
    curr->priority_score = priority;
    strncpy(curr->keyword, keyword, MAX_WORD_LEN - 1);
}

void build_ac_automation(Arena *arena, ACNode *root) {
    ACNode *queue[1024];
    int front = 0, rear = 0;

    for (int i = 0; i < ALPHABET_SIZE; i++) {
        if (root->children[i]) {
            root->children[i]->fail = root;
            queue[rear++] = root->children[i];
        } else {
            root->children[i] = root;
        }
    }

    while (front < rear) {
        ACNode *curr = queue[front++];
        for (int i = 0; i < ALPHABET_SIZE; i++) {
            if (curr->children[i] && curr->children[i] != root) {
                ACNode *fail = curr->fail;
                while (!fail->children[i]) fail = fail->fail;
                curr->children[i]->fail = fail->children[i];
                queue[rear++] = curr->children[i];
            }
        }
    }
}

void analyze_symptoms_ac(ACNode *root, const char *text, TriageResult *result) {
    if (!root || !text || !result) return;

    result->match_count = 0;
    result->max_priority = 0;

    ACNode *curr = root;
    size_t len = strlen(text);

    for (size_t i = 0; i < len; i++) {
        uint8_t idx = (uint8_t)text[i];
        if (idx >= ALPHABET_SIZE) {
            curr = root;
            continue;
        }

        while (!curr->children[idx] && curr != root) {
            curr = curr->fail;
        }

        curr = curr->children[idx] ? curr->children[idx] : root;
        ACNode *temp = curr;

        while (temp != root) {
            if (temp->is_end && result->match_count < MAX_MATCHES) {
                strncpy(result->matched_symptoms[result->match_count], temp->keyword, MAX_WORD_LEN - 1);
                result->match_count++;
                if (temp->priority_score > result->max_priority) {
                    result->max_priority = temp->priority_score;
                }
            }
            temp = temp->fail;
        }
    }
}
