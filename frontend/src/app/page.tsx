"use client";

import Link from 'next/link';
import { motion } from 'framer-motion';
import { CalendarDays, Users, MapPin, ShieldAlert, ArrowRight } from 'lucide-react';

const steps = [
  { title: "Manage Professors", desc: "Add or remove faculty members available for duty.", icon: Users, href: "/professors", color: "from-blue-500 to-indigo-500" },
  { title: "Define Locations", desc: "Set up the mess locations demanding monitoring.", icon: MapPin, href: "/locations", color: "from-emerald-400 to-teal-500" },
  { title: "Set Constraints", desc: "Configure unavailable days and location restrictions.", icon: ShieldAlert, href: "/constraints", color: "from-rose-400 to-red-500" },
  { title: "Generate Schedule", desc: "Run the OR-Tools CPSAT engine for fair allocation.", icon: CalendarDays, href: "/roster", color: "from-purple-500 to-fuchsia-500" }
];

export default function Home() {
  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4 pt-12"
      >
        <div className="inline-flex items-center justify-center p-4 rounded-2xl bg-gradient-to-tr from-primary/20 to-accent/20 text-primary mb-4 shadow-[0_0_30px_rgba(var(--primary),0.2)]">
          <CalendarDays size={48} />
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight">
          Automated Fair <br />
          <span className="heading-gradient">Duty Rostering</span>
        </h1>
        <p className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto">
          Discard spreadsheets. Instantly generate balanced, conflict-free faculty schedules powered by Google OR-Tools constraint satisfaction algorithms.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * idx }}
            >
              <Link href={step.href} className="block group">
                <div className="glass-panel p-6 rounded-2xl hover:border-primary/50 transition-all duration-300 h-full relative overflow-hidden">
                  <div className={`absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br ${step.color} rounded-full blur-3xl opacity-10 group-hover:opacity-20 transition-opacity`} />

                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${step.color} text-white shadow-lg`}>
                      <Icon size={24} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-foreground mb-1 flex items-center gap-2">
                        {step.title}
                        <ArrowRight size={16} className="opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-primary" />
                      </h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {step.desc}
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
