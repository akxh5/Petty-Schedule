"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CalendarRange, Sparkles, RefreshCcw, Printer, ArrowRight, Download, AlertTriangle, Trash2 } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RosterPage() {
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    const [assignments, setAssignments] = useState<any[]>([]);
    const [settings, setSettings] = useState<any[]>([]);
    const [professors, setProfessors] = useState<any[]>([]);
    const [locations, setLocations] = useState<any[]>([]);
    const [diagnostics, setDiagnostics] = useState<any>(null);
    const [resetLoading, setResetLoading] = useState(false);
    const [showResetModal, setShowResetModal] = useState(false);
    const router = useRouter();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [rAsg, rSett, rProf, rLoc] = await Promise.all([
                fetch(`${API_BASE}/api/roster/`),
                fetch(`${API_BASE}/api/settings/`),
                fetch(`${API_BASE}/api/professors/`),
                fetch(`${API_BASE}/api/locations/`)
            ]);
            const asgData = await rAsg.json();
            const settData = await rSett.json();

            setAssignments(asgData);
            setSettings(settData);
            setProfessors(await rProf.json());
            setLocations(await rLoc.json());

            if (settData.length > 0) {
                const latestSettingId = settData[settData.length - 1].id;
                const diagRes = await fetch(`${API_BASE}/api/roster/diagnostics?setting_id=${latestSettingId}`);
                if (diagRes.ok) {
                    setDiagnostics(await diagRes.json());
                }
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleGenerate = async () => {
        if (!settings.length) return alert("Please configure settings first.");
        const latestSettingId = settings[settings.length - 1].id;

        setLoading(true);
        setErrorMsg('');
        try {
            const res = await fetch(`${API_BASE}/api/generate-roster/?setting_id=${latestSettingId}`, {
                method: 'POST'
            });
            const data = await res.json();

            if (!res.ok) {
                if (data.detail && data.detail.error === "schedule_infeasible") {
                    setDiagnostics({ is_feasible: false, reasons: data.detail.details, warnings: [] });
                    throw new Error("Schedule cannot be generated due to impossible constraints.");
                }
                throw new Error(data.detail?.message || data.detail || "Error generating roster");
            }

            setSuccess("Successfully generated a fair duty schedule using OR-Tools!");
            setDiagnostics(null); // Clear diagnostics on success
            setTimeout(() => setSuccess(''), 5000);
            await fetchData(); // Refresh schedule view
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Group assignments by Date (Normalized to YYYY-MM-DD)
    const groupedByDate: Record<string, any[]> = {};
    const dutyCounts: Record<string, number> = {};

    assignments.forEach(a => {
        const dateKey = typeof a.date === 'string' ? a.date.split('T')[0] : a.date;
        if (!groupedByDate[dateKey]) groupedByDate[dateKey] = [];
        groupedByDate[dateKey].push(a);

        dutyCounts[a.professor_id] = (dutyCounts[a.professor_id] || 0) + 1;
    });

    const getProfessorCode = (id: string) => professors.find(p => p.id === id)?.code || "Unknown";
    const getProfessorName = (id: string) => professors.find(p => p.id === id)?.name || "Unknown";

    const handleDownload = (formatStr: 'pdf' | 'csv') => {
        window.open(`${API_BASE}/api/export/${formatStr}`, '_blank');
    };

    const handleReset = async () => {
        setResetLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/reset`, { method: 'DELETE' });
            if (!res.ok) throw new Error("Failed to reset scheduler");
            setSuccess("Scheduler cleared successfully");
            setShowResetModal(false);
            setTimeout(() => {
                router.push('/professors');
            }, 1000);
        } catch (err: any) {
            setErrorMsg(err.message);
            setShowResetModal(false);
        } finally {
            setResetLoading(false);
        }
    };

    let currentWeekDisplay: number | null = null;

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                    <h1 className="text-3xl font-bold tracking-tight">Duty Roster</h1>
                    <p className="text-muted-foreground mt-2">Generate and view the resulting scheduler mappings.</p>
                </motion.div>

                <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto mt-4 md:mt-0">
                    <button
                        onClick={() => setShowResetModal(true)}
                        className="btn-secondary text-destructive hover:bg-destructive/10 border-destructive/20 gap-2 flex-1 sm:flex-none h-12"
                    >
                        <Trash2 size={18} />
                        <span>Reset Scheduler</span>
                    </button>
                    {assignments.length > 0 && (
                        <div className="flex gap-3 w-full sm:w-auto">
                            <button onClick={() => handleDownload('csv')} className="btn-secondary gap-2 flex-1 sm:flex-none h-12">
                                <Download size={18} />
                                <span className="hidden sm:inline">Export CSV</span>
                                <span className="sm:hidden">CSV</span>
                            </button>
                            <button onClick={() => handleDownload('pdf')} className="btn-secondary gap-2 flex-1 sm:flex-none h-12">
                                <Printer size={18} />
                                <span className="hidden sm:inline">Export PDF</span>
                                <span className="sm:hidden">PDF</span>
                            </button>
                        </div>
                    )}
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="btn-primary gap-2 relative overflow-hidden group h-12 w-full sm:w-auto"
                    >
                        <span className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out" />
                        {loading ? <RefreshCcw className="animate-spin" size={18} /> : <Sparkles size={18} />}
                        <span>{loading ? 'Generating roster...' : 'Generate New Roster'}</span>
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {success && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="p-4 bg-emerald-500/10 border border-emerald-500/50 text-emerald-500 rounded-xl flex items-center gap-3"
                    >
                        <Sparkles size={20} />
                        <p className="font-medium">{success}</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {errorMsg && (
                <div className="p-4 bg-destructive/10 border border-destructive/50 text-destructive rounded-xl flex items-center gap-3">
                    <AlertTriangle size={20} />
                    <p className="font-medium">{errorMsg}</p>
                </div>
            )}

            {!diagnostics?.is_feasible && diagnostics?.reasons?.length > 0 && (
                <div className="glass-panel p-6 rounded-2xl border-destructive/50 bg-destructive/5">
                    <h3 className="font-bold text-destructive mb-4 flex items-center gap-2">
                        <AlertTriangle size={20} />
                        Schedule cannot be generated
                    </h3>
                    <div className="grid gap-4 md:grid-cols-2">
                        {diagnostics.reasons.map((r: any, idx: number) => (
                            <div key={idx} className="p-4 bg-card rounded-xl border border-destructive/20 shadow-sm">
                                {r.professor ? (
                                    <>
                                        <p className="font-semibold text-foreground mb-2">Reason: Professor {r.professor} cannot meet the required workload.</p>
                                        <ul className="text-sm space-y-1 text-muted-foreground mb-3">
                                            <li>Required duties: <span className="font-bold text-foreground">{r.required_assignments}</span></li>
                                            <li>Maximum possible duties: <span className="font-bold text-foreground">{r.max_possible_assignments}</span></li>
                                        </ul>
                                        <p className="text-sm font-medium text-destructive">Constraint causing issue: {r.constraint}</p>
                                    </>
                                ) : (
                                    <>
                                        <p className="font-semibold text-foreground mb-1">Reason: {r.error}</p>
                                        {r.details && <p className="text-sm text-muted-foreground">{r.details}</p>}
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {diagnostics?.is_feasible && diagnostics?.warnings?.length > 0 && (
                <div className="glass-panel p-4 rounded-xl border-amber-500/50 bg-amber-500/10 text-amber-500 flex items-start gap-3">
                    <AlertTriangle size={20} className="mt-0.5 flex-shrink-0" />
                    <div>
                        <p className="font-semibold">Configuration may be infeasible</p>
                        <ul className="text-sm mt-1 list-disc list-inside opacity-90">
                            {diagnostics.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                </div>
            )}

            {assignments.length === 0 ? (
                <div className="h-64 glass-panel rounded-2xl border-dashed flex flex-col items-center justify-center text-muted-foreground">
                    <CalendarRange size={48} className="mb-4 opacity-50" />
                    <p>No roster data available for the current setting.</p>
                    <p className="text-sm mt-1">Hit Generate to run the OR-Tools CPSAT solver.</p>
                </div>
            ) : (
                <motion.div className="space-y-6">
                    <div className="glass-panel p-6 rounded-2xl border-primary/20 bg-primary/5">
                        <h3 className="font-bold mb-4 flex items-center gap-2">
                            <Sparkles size={18} className="text-primary" />
                            Duty Count Summary
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                            {professors.map(p => (
                                <div key={p.id} className="p-3 bg-card rounded-xl border border-border flex items-center justify-between">
                                    <span className="font-medium text-sm">{p.name}</span>
                                    <span className="px-2 font-mono py-1 bg-primary/10 text-primary rounded-md text-xs font-bold">
                                        {dutyCounts[p.id] || 0}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="glass-panel overflow-hidden rounded-2xl shadow-xl"
                    >
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-secondary/50 border-b border-border">
                                        <th className="p-3 md:p-4 text-xs md:text-sm font-semibold text-foreground whitespace-nowrap sticky left-0 z-20 bg-secondary/90 backdrop-blur-md shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">Date / Day</th>
                                        {locations.map(loc => (
                                            <th key={loc.id} className="p-3 md:p-4 text-xs md:text-sm font-semibold text-foreground min-w-[140px] md:min-w-[150px]">
                                                {loc.name}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50">
                                    {Object.keys(groupedByDate).sort().map(dateString => {
                                        const dateInfo = parseISO(dateString);
                                        const dayAssignments = groupedByDate[dateString];
                                        const weekNum = Math.ceil(dateInfo.getDate() / 7);

                                        const isNewWeek = currentWeekDisplay !== weekNum;
                                        if (isNewWeek) currentWeekDisplay = weekNum;

                                        return (
                                            <React.Fragment key={dateString}>
                                                {isNewWeek && (
                                                    <tr className="bg-muted text-sm font-semibold text-center mt-4 border-b border-border">
                                                        <td colSpan={locations.length + 1} className="py-2 px-4 shadow-[inset_0_2px_4px_rgba(0,0,0,0.05)] text-muted-foreground tracking-widest uppercase">
                                                            Week {weekNum}
                                                        </td>
                                                    </tr>
                                                )}
                                                <tr className="hover:bg-accent/5 transition-colors">
                                                    <td className="p-3 md:p-4 whitespace-nowrap sticky left-0 z-10 bg-card/95 backdrop-blur-md shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
                                                        <div className="font-medium text-foreground text-sm md:text-base">{format(dateInfo, 'MMM dd, yyyy')}</div>
                                                        <div className="text-xs text-muted-foreground">{format(dateInfo, 'EEEE')}</div>
                                                    </td>
                                                    {locations.map(loc => {
                                                        // Find who is working here today
                                                        const asg = dayAssignments.find(a => a.location_id === loc.id);
                                                        return (
                                                            <td key={loc.id} className="p-3 md:p-4">
                                                                {asg ? (
                                                                    <div className="inline-flex items-center gap-1.5 md:gap-2 bg-primary/10 text-primary border border-primary/20 px-2 flex-wrap sm:px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium w-fit">
                                                                        <span className="w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-primary flex-shrink-0" />
                                                                        <span className="whitespace-nowrap">{getProfessorCode(asg.professor_id)}</span>
                                                                        <span className="text-[10px] md:text-xs opacity-70 hidden sm:inline whitespace-nowrap">({getProfessorName(asg.professor_id)})</span>
                                                                    </div>
                                                                ) : (
                                                                    <span className="text-muted-foreground/50 text-sm italic">—</span>
                                                                )}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            </React.Fragment>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </motion.div>
                </motion.div>
            )}

            {showResetModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-card p-6 rounded-2xl shadow-xl max-w-sm w-full border border-border">
                        <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-foreground">
                            <AlertTriangle className="text-destructive" size={20} />
                            Reset Scheduler?
                        </h3>
                        <p className="text-sm text-muted-foreground mb-6">
                            This will delete all professors, locations, constraints and roster data. System will return to a fresh state.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button disabled={resetLoading} onClick={() => setShowResetModal(false)} className="btn-secondary h-9 px-4 text-sm">Cancel</button>
                            <button disabled={resetLoading} onClick={handleReset} className="h-9 px-4 text-sm bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-lg font-medium transition-colors flex items-center gap-2">
                                {resetLoading ? <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></span> : null}
                                {resetLoading ? 'Resetting...' : 'Reset Scheduler'}
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
