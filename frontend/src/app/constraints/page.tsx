"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ShieldAlert, Trash2, PlusCircle, ArrowRight, AlertCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Professor {
    id: string;
    name: string;
}

interface Location {
    id: string;
    name: string;
}

interface Constraint {
    id: string;
    professor_id: string;
    type: string;
    value: any;
}

export default function ConstraintsPage() {
    const router = useRouter();
    const [professors, setProfessors] = useState<Professor[]>([]);
    const [locations, setLocations] = useState<Location[]>([]);
    const [constraints, setConstraints] = useState<Constraint[]>([]);
    const [loading, setLoading] = useState(true);
    const [errorMsg, setErrorMsg] = useState("");

    const [form, setForm] = useState({
        professor_id: '',
        type: 'DAY_UNAVAILABLE',
        value_day: 'Monday',
        value_loc: '',
        value_limit: 2
    });

    useEffect(() => {
        Promise.all([
            fetch(`${API_BASE}/api/professors`).then(r => r.json()),
            fetch(`${API_BASE}/api/locations`).then(r => r.json()),
            fetch(`${API_BASE}/api/constraints`).then(r => r.json())
        ]).then(([p, l, c]) => {
            if (Array.isArray(p)) setProfessors(p);
            if (Array.isArray(l)) setLocations(l);
            if (Array.isArray(c)) setConstraints(c);
            setLoading(false);
        }).catch(e => {
            console.error(e);
            setLoading(false);
        });
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMsg("");
        if (!form.professor_id) return alert("Select a professor");

        let finalValue = {};
        if (form.type === 'DAY_UNAVAILABLE' || form.type === 'DAY_PREFERRED') {
            finalValue = { dayOfWeek: form.value_day };
        } else if (form.type === 'LOCATION_RESTRICTED') {
            if (!form.value_loc) return alert("Select a location");
            finalValue = { location_id: form.value_loc };
        } else if (form.type === 'MAX_WEEKLY') {
            finalValue = { limit: Number(form.value_limit) };
        }

        const newConstraint = {
            professor_id: form.professor_id,
            type: form.type,
            value: finalValue
        };

        try {
            const res = await fetch(`${API_BASE}/api/constraints`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConstraint)
            });
            const data = await res.json();

            if (!res.ok) {
                setErrorMsg(data.detail || "Error adding constraint");
                return;
            }

            setConstraints([...constraints, data]);
        } catch (err) {
            console.error("API Error", err);
            setErrorMsg("Network error occurred");
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Are you sure you want to delete this constraint?")) return;

        try {
            const res = await fetch(`${API_BASE}/api/constraints/${id}`, { method: 'DELETE' });
            if (res.ok) {
                setConstraints(constraints.filter(c => c.id !== id));
            }
        } catch (err) {
            console.error(err);
        }
    };

    const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    const getProfessorName = (id: string) => professors.find(p => p.id === id)?.name || id;

    const renderConstraintDesc = (c: Constraint) => {
        switch (c.type) {
            case 'DAY_UNAVAILABLE': return <span className="text-red-400">Cannot work on {c.value.dayOfWeek}s</span>;
            case 'DAY_PREFERRED': return <span className="text-emerald-400">Prefers working on {c.value.dayOfWeek}s</span>;
            case 'LOCATION_RESTRICTED':
                const ln = locations.find(l => l.id === c.value.location_id)?.name;
                return <span className="text-amber-500">Restricted from {ln || 'Location'}</span>;
            case 'MAX_WEEKLY': return <span className="text-purple-400">Max {c.value.limit} duties/week</span>;
            default: return null;
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                <h1 className="text-3xl font-bold tracking-tight">Assignment Constraints</h1>
                <p className="text-muted-foreground mt-2">Define strict rules or personal preferences for the solver engine.</p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel p-6 rounded-2xl"
            >
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2 relative">
                            <label className="text-sm font-medium">Professor</label>
                            <select className="input-field appearance-none" value={form.professor_id} onChange={e => setForm({ ...form, professor_id: e.target.value })}>
                                <option value="">Select Professor...</option>
                                {professors.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2 relative">
                            <label className="text-sm font-medium">Constraint Type</label>
                            <select className="input-field appearance-none" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                                <option value="DAY_UNAVAILABLE">Day Unavailable (Must Not Work)</option>
                                <option value="DAY_PREFERRED">Day Preferred (Soft Preference)</option>
                                <option value="LOCATION_RESTRICTED">Location Restricted</option>
                                <option value="MAX_WEEKLY">Max Duties Per Week</option>
                            </select>
                        </div>
                    </div>

                    <div className="p-4 bg-background/50 rounded-xl border border-border mt-4">
                        {(form.type === 'DAY_UNAVAILABLE' || form.type === 'DAY_PREFERRED') && (
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Select Day</label>
                                <select className="input-field" value={form.value_day} onChange={e => setForm({ ...form, value_day: e.target.value })}>
                                    {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
                                </select>
                            </div>
                        )}

                        {form.type === 'LOCATION_RESTRICTED' && (
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Restricted Location</label>
                                <select className="input-field" value={form.value_loc} onChange={e => setForm({ ...form, value_loc: e.target.value })}>
                                    <option value="">Select location they CANNOT work at...</option>
                                    {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                                </select>
                            </div>
                        )}

                        {form.type === 'MAX_WEEKLY' && (
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Max Limit</label>
                                <input type="number" min="1" max="7" className="input-field" value={form.value_limit} onChange={e => setForm({ ...form, value_limit: parseInt(e.target.value) })} />
                            </div>
                        )}
                    </div>

                    <button type="submit" className="btn-primary h-12 w-full gap-2 mt-4">
                        <PlusCircle size={18} />
                        Add Constraint
                    </button>

                    {errorMsg && (
                        <div className="p-3 bg-red-500/10 border border-red-500/50 text-red-500 rounded-lg flex items-center gap-2 mt-4 text-sm">
                            <AlertCircle size={16} />
                            {errorMsg}
                        </div>
                    )}
                </form>
            </motion.div>

            <div className="space-y-3 mt-8">
                <h3 className="font-bold text-lg mb-4">Active Constraints</h3>
                {loading ? (
                    <p className="text-muted-foreground">Loading...</p>
                ) : constraints.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground glass-panel rounded-2xl border-dashed">
                        No constraints acting on the solver. Perfect fairness rules apply by default.
                    </div>
                ) : (
                    constraints.map((c, idx) => (
                        <motion.div
                            key={c.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="glass-panel p-4 rounded-xl flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-secondary rounded-lg">
                                    <ShieldAlert size={16} className="text-foreground" />
                                </div>
                                <div>
                                    <p className="font-semibold">{getProfessorName(c.professor_id)}</p>
                                    <p className="text-sm">{renderConstraintDesc(c)}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(c.id)}
                                className="text-muted-foreground hover:text-destructive transition-colors p-2"
                            >
                                <Trash2 size={18} />
                            </button>
                        </motion.div>
                    ))
                )}
            </div>

            <div className="flex justify-end pt-8">
                <button onClick={() => router.push('/settings')} className="btn-secondary gap-2 px-6 h-12 text-base w-full sm:w-auto">
                    Next: Settings <ArrowRight size={18} />
                </button>
            </div>
        </div>
    );
}
