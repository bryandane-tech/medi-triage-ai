import React, { useState } from 'react';
import { Activity, ShieldCheck, Send, RefreshCw } from 'lucide-react';

interface TriageResponse {
    triage_id: string;
    status: string;
}

export default function App() {
    const [phone, setPhone] = useState('');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<TriageResponse | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setResponse(null);

        try {
            const res = await fetch('/api/v1/triage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone, notes })
            });
            const data = await res.json();
            setResponse(data);
            setPhone('');
            setNotes('');
        } catch (err) {
            alert('Failed to connect to MediTriage Core Backend');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', fontFamily: 'system-ui, sans-serif', padding: '2rem' }}>
        <header style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2.5rem', borderBottom: '1px solid #1e293b', paddingBottom: '1rem' }}>
        <Activity color="#38bdf8" size={32} />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>MediTriage Enterprise Console</h1>
        </header>

        <main style={{ maxWidth: '800px', margin: '0 auto', display: 'grid', gap: '2rem' }}>
        <section style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
        <h2 style={{ fontSize: '1.25rem', marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <ShieldCheck color="#4ade80" size={20} /> New Patient Ingestion (AES-256 Encrypted)
        </h2>

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
        <div>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>Patient Phone</label>
        <input
        type="text"
        required
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="+201000000000"
        style={{ width: '100%', padding: '0.75rem', borderRadius: '0.375rem', border: '1px solid #475569', backgroundColor: '#0f172a', color: '#fff', boxSizing: 'border-box' }}
        />
        </div>

        <div>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>Clinical Intake Notes</label>
        <textarea
        required
        rows={4}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Patient presents with acute chest pain, sweating, and shortness of breath..."
        style={{ width: '100%', padding: '0.75rem', borderRadius: '0.375rem', border: '1px solid #475569', backgroundColor: '#0f172a', color: '#fff', boxSizing: 'border-box' }}
        />
        </div>

        <button
        type="submit"
        disabled={loading}
        style={{ padding: '0.75rem 1.5rem', borderRadius: '0.375rem', border: 'none', backgroundColor: '#0284c7', color: '#fff', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
        >
        {loading ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
        Process & Encrypt Intake
        </button>
        </form>
        </section>

        {response && (
            <div style={{ padding: '1rem', backgroundColor: '#064e3b', borderRadius: '0.5rem', border: '1px solid #059669' }}>
            <h3 style={{ margin: 0, color: '#34d399' }}>Record Ingested & Enqueued</h3>
            <p style={{ margin: '0.5rem 0 0 0', fontFamily: 'monospace', fontSize: '0.875rem' }}>ID: {response.triage_id}</p>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>Status: {response.status}</p>
            </div>
        )}
        </main>
        </div>
    );
}
