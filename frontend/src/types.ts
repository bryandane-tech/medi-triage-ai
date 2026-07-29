export interface TriageIngestRequest {
    phone: string;
    notes: string;
}

export interface TriageIngestResponse {
    triage_id: string;
    status: string;
}

export interface PatientRecord {
    triage_id: string;
    phone: string;
    notes: string;
    urgency_score: number;
    decrypted_with_key: string;
}
