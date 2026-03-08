"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Trash2, UserPlus, ArrowRight, AlertTriangle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Professor {
    id: string;
    name: string;
    code: string;
}

export default function ProfessorsPage() {
    const router = useRouter();
    const [professors, setProfessors] = useState<Professor[]>([]);
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(true);
    const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean, prof: Professor | null, isUsed: boolean }>({ isOpen: false, prof: null, isUsed: false });

    const handleDeleteClick = async (p: Professor) => {
        try {
            const res = await fetch(`${API_BASE}/api/roster`);
            const roster = await res.json();
            const isUsed = roster.some((r: any) => r.professor_id === p.id);
            setDeleteModal({ isOpen: true, prof: p, isUsed });
        } catch (err) {
            setDeleteModal({ isOpen: true, prof: p, isUsed: false });
        }
    };

    const confirmDelete = async () => {
        if (!deleteModal.prof) return;
        try {
            await fetch(`${API_BASE}/api/professors/${deleteModal.prof.id}`, { method: 'DELETE' });
            setProfessors(professors.filter(p => p.id !== deleteModal.prof!.id));
            setDeleteModal({ isOpen: false, prof: null, isUsed: false });
        } catch (err) {
            console.error("Delete error", err);
        }
    };

    // In a real app with backend connected:
    // useEffect(() => { fetch('/api/professors/')... }, []);
    // For now we will just mock state viewing if API unreachable

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name || !code) return;

        // Optimistic UI
        const newProf = { id: Math.random().toString(), name, code };
        setProfessors([...professors, newProf]);
        setName('');
        setCode('');

        try {
            await fetch(`${API_BASE}/api/professors`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, code })
            });
        } catch (err) {
            console.error("API Error", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetch(`${API_BASE}/api/professors`)
            .then(r => r.json())
            .then(data => {
                if (Array.isArray(data)) setProfessors(data);
                setLoading(false);
            })
            .catch((e) => {
                console.error(e);
                setLoading(false);
            });
    }, []);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                <h1 className="text-3xl font-bold tracking-tight">Faculty Management</h1>
                <p className="text-muted-foreground mt-2">Add and manage university professors participating in the roster.</p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel p-6 rounded-2xl"
            >
                <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-1 space-y-2 w-full">
                        <label className="text-sm font-medium text-foreground">Professor Name</label>
                        <input
                            type="text"
                            placeholder="e.g. Dr. Sharma"
                            className="input-field"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            disabled={loading}
                        />
                    </div>
                    <div className="w-full md:max-w-[150px] space-y-2">
                        <label className="text-sm font-medium text-foreground">Code</label>
                        <input
                            type="text"
                            placeholder="e.g. P1"
                            className="input-field text-center font-mono uppercase"
                            value={code}
                            onChange={e => setCode(e.target.value.toUpperCase())}
                            disabled={loading}
                        />
                    </div>
                    <button type="submit" disabled={loading} className="btn-primary flex-shrink-0 h-10 md:h-12 px-6 gap-2 w-full md:w-auto overflow-hidden group">
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                                Saving...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <UserPlus size={18} />
                                <span>Add Faculty</span>
                            </span>
                        )}
                    </button>
                </form>
            </motion.div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {loading ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground">Loading roster...</div>
                ) : professors.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground glass-panel rounded-2xl border-dashed">
                        No professors added yet.
                    </div>
                ) : (
                    professors.map((p, idx) => (
                        <motion.div
                            key={p.id}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.05 }}
                            className="glass-panel p-5 rounded-xl flex items-center justify-between group"
                        >
                            <div>
                                <p className="font-bold text-foreground">{p.name}</p>
                                <p className="text-sm text-primary font-mono bg-primary/10 inline-block px-2 py-0.5 rounded-md mt-1">{p.code}</p>
                            </div>
                            <button
                                onClick={() => handleDeleteClick(p)}
                                title="Delete Professor"
                                className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all p-2 rounded-md hover:bg-destructive/10"
                            >
                                <Trash2 size={18} />
                            </button>
                        </motion.div>
                    ))
                )}
            </div>

            <div className="flex justify-end pt-8">
                <button onClick={() => router.push('/locations')} className="btn-secondary gap-2 px-6 h-12 text-base w-full sm:w-auto">
                    Next: Locations <ArrowRight size={18} />
                </button>
            </div>

            {deleteModal.isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-card p-6 rounded-2xl shadow-xl max-w-sm w-full border border-border">
                        <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-foreground">
                            <AlertTriangle className="text-destructive" size={20} />
                            Delete Professor
                        </h3>
                        {deleteModal.isUsed ? (
                            <p className="text-sm text-muted-foreground mb-6">
                                This professor is used in a generated roster. Deleting them will remove related assignments and constraints.
                            </p>
                        ) : (
                            <p className="text-sm text-muted-foreground mb-6">
                                Are you sure you want to delete this professor? This action cannot be undone.
                            </p>
                        )}
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setDeleteModal({ isOpen: false, prof: null, isUsed: false })} className="btn-secondary h-9 px-4 text-sm">Cancel</button>
                            <button onClick={confirmDelete} className="h-9 px-4 text-sm bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-lg font-medium transition-colors">
                                Confirm Delete
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
