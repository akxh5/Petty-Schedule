"use client";

import { useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function BackendWaker() {
    useEffect(() => {
        // Ping health to warm up backend on initial load
        fetch(`${API_BASE}/health`).catch(() => { });
    }, []);

    return null; // This component handles side effects and renders nothing
}
