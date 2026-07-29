import ctypes
import queue
from contextlib import contextmanager
from app.config import settings

class TriageResult(ctypes.Structure):
    _fields_ = [
        ("is_emergency", ctypes.c_int),
        ("urgency_score", ctypes.c_int),
        ("category", ctypes.c_char * 32)
    ]

class CEngineBindings:
    def __init__(self, pool_size: int = 10, arena_capacity: int = 1024 * 1024):
        lib_path = settings.C_LIB_PATH
        self.lib = ctypes.CDLL(lib_path)

        # C Function Signature Bindings
        self.lib.create_arena.argtypes = [ctypes.c_size_t]
        self.lib.create_arena.restype = ctypes.c_void_p

        self.lib.reset_arena.argtypes = [ctypes.c_void_p]
        self.lib.reset_arena.restype = None

        self.lib.free_arena.argtypes = [ctypes.c_void_p]
        self.lib.free_arena.restype = None

        self.lib.init_aho_corasick.argtypes = [ctypes.c_void_p]
        self.lib.init_aho_corasick.restype = ctypes.c_void_p

        self.lib.build_ac_automation.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.lib.build_ac_automation.restype = None

        self.lib.analyze_symptoms_ac.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(TriageResult)
        ]

        # Initialize global persistent trie tree using master arena
        self.master_arena = self.lib.create_arena(2 * 1024 * 1024)
        self.ac_root = self.lib.init_aho_corasick(self.master_arena)
        self.lib.build_ac_automation(self.master_arena, self.ac_root)

        # Build Thread-Safe Arena Pool for request workers
        self.pool = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            arena_ptr = self.lib.create_arena(arena_capacity)
            self.pool.put(arena_ptr)

    @contextmanager
    def _acquire_arena(self):
        # Acquire free arena pointer with 5-second timeout
        arena_ptr = self.pool.get(block=True, timeout=5.0)
        try:
            self.lib.reset_arena(arena_ptr) # O(1) Memory Reset
            yield arena_ptr
        finally:
            self.pool.put(arena_ptr) # Return to pool

    def analyze_symptoms(self, text: str) -> dict:
        result = TriageResult()
        text_bytes = text.encode('utf-8')

        with self._acquire_arena() as arena_ptr:
            self.lib.analyze_symptoms_ac(self.ac_root, text_bytes, ctypes.byref(result))

        return {
            "is_emergency": bool(result.is_emergency),
            "urgency_score": int(result.urgency_score),
            "category": result.category.decode('utf-8')
        }
