"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Trash2, MapPinPlus, ArrowRight, AlertTriangle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Location {
    id: string;
    name: string;
}

export default function LocationsPage() {
    const router = useRouter();
    const [locations, setLocations] = useState<Location[]>([]);
    const [name, setName] = useState('');
    const [loading, setLoading] = useState(true);
    const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean, loc: Location | null, isUsed: boolean }>({ isOpen: false, loc: null, isUsed: false });

    const handleDeleteClick = async (l: Location) => {
        try {
            const res = await fetch(`${API_BASE}/api/roster`);
            const roster = await res.json();
            const isUsed = roster.some((r: any) => r.location_id === l.id);
            setDeleteModal({ isOpen: true, loc: l, isUsed });
        } catch (err) {
            setDeleteModal({ isOpen: true, loc: l, isUsed: false });
        }
    };

    const confirmDelete = async () => {
        if (!deleteModal.loc) return;
        try {
            await fetch(`${API_BASE}/api/locations/${deleteModal.loc.id}`, { method: 'DELETE' });
            setLocations(locations.filter(l => l.id !== deleteModal.loc!.id));
            setDeleteModal({ isOpen: false, loc: null, isUsed: false });
        } catch (err) {
            console.error("Delete error", err);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name) return;

        // Optimistic UI
        const newLoc = { id: Math.random().toString(), name };
        setLocations([...locations, newLoc]);
        setName('');
        setLoading(true);

        try {
            await fetch(`${API_BASE}/api/locations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
        } catch (err) {
            console.error("API Error", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetch(`${API_BASE}/api/locations`)
            .then(r => r.json())
            .then(data => {
                if (Array.isArray(data)) setLocations(data);
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
                <h1 className="text-3xl font-bold tracking-tight">Duty Locations</h1>
                <p className="text-muted-foreground mt-2">Define areas or floors requiring faculty monitoring.</p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel p-6 rounded-2xl"
            >
                <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-1 space-y-2 w-full">
                        <label className="text-sm font-medium text-foreground">Location Name</label>
                        <input
                            type="text"
                            placeholder="e.g. Ground Floor Mess"
                            className="input-field"
                            value={name}
                            onChange={e => setName(e.target.value)}
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
                                <MapPinPlus size={18} />
                                <span>Add Location</span>
                            </span>
                        )}
                    </button>
                </form>
            </motion.div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {loading ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground">Loading locations...</div>
                ) : locations.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground glass-panel rounded-2xl border-dashed">
                        No locations added yet.
                    </div>
                ) : (
                    locations.map((loc, idx) => (
                        <motion.div
                            key={loc.id}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.05 }}
                            className="glass-panel p-5 rounded-xl flex items-center justify-between group"
                        >
                            <div>
                                <p className="font-bold text-foreground">{loc.name}</p>
                            </div>
                            <button
                                onClick={() => handleDeleteClick(loc)}
                                title="Delete Location"
                                className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all p-2 rounded-md hover:bg-destructive/10"
                            >
                                <Trash2 size={18} />
                            </button>
                        </motion.div>
                    ))
                )}
            </div>
            <div className="flex justify-end pt-8">
                <button onClick={() => router.push('/constraints')} className="btn-secondary gap-2 px-6 h-12 text-base w-full sm:w-auto">
                    Next: Constraints <ArrowRight size={18} />
                </button>
            </div>

            {deleteModal.isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-card p-6 rounded-2xl shadow-xl max-w-sm w-full border border-border">
                        <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-foreground">
                            <AlertTriangle className="text-destructive" size={20} />
                            Delete Location
                        </h3>
                        {deleteModal.isUsed ? (
                            <p className="text-sm text-muted-foreground mb-6">
                                This location is used in a generated roster. Deleting it will remove related assignments.
                            </p>
                        ) : (
                            <p className="text-sm text-muted-foreground mb-6">
                                Are you sure you want to delete this location? This action cannot be undone.
                            </p>
                        )}
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setDeleteModal({ isOpen: false, loc: null, isUsed: false })} className="btn-secondary h-9 px-4 text-sm">Cancel</button>
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
