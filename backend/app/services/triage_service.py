import ctypes
import json
import time
import asyncpg
from app.security.envelope import MultiKeyEnvelopeEncryption
from app.security.audit import AuditLoggerService
from app.metrics.prometheus import C_ENGINE_LATENCY

class TriageResultCType(ctypes.Structure):
    _fields_ = [
        ("matched_symptoms", (ctypes.c_char * 64) * 16),
        ("match_count", ctypes.c_int),
        ("max_priority", ctypes.c_int)
    ]

class TriageEngineService:
    def __init__(self, lib_path: str, cipher: MultiKeyEnvelopeEncryption, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.cipher = cipher
        self.audit = AuditLoggerService(db_pool)

        self._c_lib = ctypes.CDLL(lib_path)
        self._c_lib.create_arena.restype = ctypes.c_void_p
        self._c_lib.create_arena.argtypes = [ctypes.c_size_t]
        self._c_lib.init_aho_corasick.restype = ctypes.c_void_p
        self._c_lib.init_aho_corasick.argtypes = [ctypes.c_void_p]
        self._c_lib.insert_keyword.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self._c_lib.build_ac_automation.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._c_lib.analyze_symptoms_ac.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(TriageResultCType)]

        self.arena = self._c_lib.create_arena(4 * 1024 * 1024)
        self.ac_root = self._c_lib.init_aho_corasick(self.arena)
        self._bootstrap_trie()

    def _bootstrap_trie(self):
        medical_dictionary = {
            "chest pain": 5,
            "shortness of breath": 4,
            "profuse bleeding": 4,
            "high fever": 2,
            "mild headache": 1
        }
        for term, priority in medical_dictionary.items():
            self._c_lib.insert_keyword(self.arena, self.ac_root, term.encode('utf-8'), priority)
        self._c_lib.build_ac_automation(self.arena, self.ac_root)

    def analyze_text(self, text: str) -> dict:
        result = TriageResultCType()
        start_time = time.perf_counter()
        self._c_lib.analyze_symptoms_ac(self.ac_root, text.encode('utf-8'), ctypes.byref(result))
        C_ENGINE_LATENCY.observe(time.perf_counter() - start_time)

        matches = [result.matched_symptoms[i].value.decode('utf-8') for i in range(result.match_count)]
        return {"matches": matches, "match_count": result.match_count, "urgency_score": result.max_priority}

    async def process_incoming_triage(self, phone_number: str, clinical_notes: str) -> tuple[str, int]:
        triage_data = self.analyze_text(clinical_notes)
        enc_phone, key_ver = self.cipher.encrypt(phone_number)
        enc_notes, _ = self.cipher.encrypt(clinical_notes)

        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO patient_triage
                        (encrypted_phone_number, encrypted_clinical_notes, key_version, ac_matched_count, urgency_score)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id;
                    """,
                    enc_phone, enc_notes, key_ver, triage_data["match_count"], triage_data["urgency_score"]
                )
                record_id = str(row['id'])

                outbox_payload = json.dumps({
                    "triage_id": record_id,
                    "urgency_score": triage_data["urgency_score"],
                    "symptoms_found": triage_data["matches"]
                })

                await conn.execute(
                    """
                    INSERT INTO transactional_outbox (aggregate_type, aggregate_id, event_type, payload)
                    VALUES ('TRIAGE_RECORD', $1, 'TRIAGE_ANALYZED', $2::jsonb);
                    """,
                    record_id, outbox_payload
                )

        return record_id, triage_data["urgency_score"]

    async def read_patient_record(self, record_id: str, actor_id: str) -> dict:
        """Decrypts a record and creates an audit entry."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, encrypted_phone_number, encrypted_clinical_notes, urgency_score FROM patient_triage WHERE id = $1;",
                record_id
            )
            if not row:
                return None

            phone, key_ver_used = self.cipher.decrypt(row['encrypted_phone_number'])
            notes, _ = self.cipher.decrypt(row['encrypted_clinical_notes'])

            # Record audit access entry
            await self.audit.log_phi_access(
                actor_id=actor_id,
                action="DECRYPT_PHI_RECORD",
                resource_id=record_id,
                key_version=key_ver_used
            )

            return {
                "triage_id": str(row['id']),
                "phone": phone,
                "notes": notes,
                "urgency_score": row['urgency_score'],
                "decrypted_with_key": key_ver_used
            }
