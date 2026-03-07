"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Users,
    MapPin,
    ShieldAlert,
    Settings,
    CalendarDays,
    Menu,
    X
} from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
    { name: 'Professors', href: '/professors', icon: Users },
    { name: 'Locations', href: '/locations', icon: MapPin },
    { name: 'Constraints', href: '/constraints', icon: ShieldAlert },
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'Roster', href: '/roster', icon: CalendarDays },
];

export default function Navigation() {
    const pathname = usePathname();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            {/* Mobile Toggle */}
            <div className="md:hidden fixed top-4 right-4 z-50">
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-2 bg-card rounded-md shadow-md text-foreground border border-border"
                >
                    {isOpen ? <X size={20} /> : <Menu size={20} />}
                </button>
            </div>

            {/* Mobile Backdrop */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 md:hidden"
                    />
                )}
            </AnimatePresence>

            <aside
                className={`fixed inset-y-0 left-0 z-40 w-64 glass-panel border-r border-border flex flex-col transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'
                    }`}
            >
                <div className="p-6">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20">
                            <CalendarDays className="text-white" size={18} />
                        </div>
                        <h1 className="text-lg font-bold tracking-tight text-foreground">
                            Faculty<span className="text-primary">Scheduler</span>
                        </h1>
                    </Link>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-6">
                    {navItems.map((item) => {
                        const isActive = pathname.startsWith(item.href);
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                onClick={() => setIsOpen(false)}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden ${isActive
                                    ? 'text-primary-foreground font-medium'
                                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                                    }`}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeNavTab"
                                        className="absolute inset-0 bg-primary/90 rounded-xl -z-10 shadow-lg shadow-primary/20"
                                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                    />
                                )}
                                <Icon size={18} className={isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'} />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-6 mt-auto">
                    <div className="p-4 rounded-xl bg-secondary/50 border border-border/50 text-xs text-muted-foreground">
                        <p>OR-Tools Powered</p>
                        <p className="mt-1">v1.0.0</p>
                    </div>
                </div>
            </aside>
        </>
    );
}
