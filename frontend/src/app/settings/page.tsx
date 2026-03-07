"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Save, CalendarRange, ArrowRight } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SettingsPage() {
    const router = useRouter();
    const [startDa, setStartDa] = useState('');
    const [endDa, setEndDa] = useState('');
    const [countSundays, setCountSundays] = useState(true);
    const [settings, setSettings] = useState<any[]>([]);

    useEffect(() => {
        fetch(`${API_BASE}/api/settings/`)
            .then(r => r.json())
            .then(d => setSettings(d))
            .catch(e => console.error(e));
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!startDa || !endDa) return;

        try {
            const res = await fetch(`${API_BASE}/api/settings/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: startDa,
                    end_date: endDa,
                    locations_per_day: 3, // Defaults to total locations
                    count_sundays: countSundays
                })
            });
            const data = await res.json();
            setSettings([...settings, data]);
            alert("Settings Saved!");
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                <h1 className="text-3xl font-bold tracking-tight">Schedule Settings</h1>
                <p className="text-muted-foreground mt-2">Adjust the global date range for the upcoming roster generation.</p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel p-6 rounded-2xl max-w-2xl"
            >
                <form onSubmit={handleSave} className="space-y-6">
                    <div className="flex items-center gap-4 text-primary bg-primary/10 p-4 rounded-xl">
                        <CalendarRange size={24} />
                        <p className="text-sm font-medium">The schedule operates within a rigid Date framework. Set the target month or week.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Start Date</label>
                            <input
                                type="date"
                                className="input-field"
                                value={startDa}
                                onChange={e => setStartDa(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">End Date</label>
                            <input
                                type="date"
                                className="input-field"
                                value={endDa}
                                onChange={e => setEndDa(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 border border-border rounded-xl bg-background/50">
                        <input
                            type="checkbox"
                            id="countSundays"
                            className="w-5 h-5 text-primary rounded border-border focus:ring-primary"
                            checked={countSundays}
                            onChange={(e) => setCountSundays(e.target.checked)}
                        />
                        <label htmlFor="countSundays" className="font-medium cursor-pointer">
                            Count Sundays in Schedule
                            <p className="text-xs text-muted-foreground font-normal">If unchecked, the solver will skip assigning any duties on Sundays.</p>
                        </label>
                    </div>

                    <button type="submit" className="btn-primary w-full h-12 gap-2 transition-all">
                        <Save size={18} />
                        Save Configuration
                    </button>
                </form>
            </motion.div>

            {settings.length > 0 && (
                <div className="mt-8 space-y-4">
                    <h3 className="font-bold text-lg">History</h3>
                    {settings.slice().reverse().map((s, idx) => (
                        <div key={idx} className="p-4 glass-panel rounded-xl flex items-center justify-between">
                            <div>
                                <p className="font-medium text-foreground">Range: {new Date(s.start_date).toLocaleDateString()} — {new Date(s.end_date).toLocaleDateString()}</p>
                                <p className="text-xs text-muted-foreground mt-1">Sundays included: {s.count_sundays ? 'Yes' : 'No'} | ID: {s.id}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex justify-end pt-8">
                <button onClick={() => router.push('/roster')} className="btn-secondary gap-2 px-6 h-12 text-base w-full sm:w-auto">
                    Next: Generate Roster <ArrowRight size={18} />
                </button>
            </div>
        </div>
    );
}
