"use client";

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Send, ArrowRight, Shield, Zap, Sparkles, ChevronRight, CheckCircle2, AlertCircle, Layers, Target } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// IAS Curriculum Data (Representative Sample based on NEO4J data)
const CURRICULUM = {
  phases: [
    {
      id: "phase-1",
      name: "Revelation",
      theme: "Predictive Self-Mapping",
      description: "Expose the hidden sabotage loop that quietly drives every setback.",
      color: "from-violet-500 to-indigo-600",
      lessons: [
        {
          id: "lesson-3",
          name: "Replay Loop Breaker",
          benefit: "Reclaim 40% of your cognitive bandwidth wasted on mental replays.",
          obstacles: [
            "Fear that naming the story will make it more real.",
            "Identity collapse if old patterns are recognized.",
            "The urge to immediately fix rather than observe."
          ],
          steps: [
            { id: "step-1", name: "Spot the Story", tagline: "Observe the prediction." },
            { id: "step-2", name: "Name the Feeling", tagline: "Anchor the affect." },
            { id: "step-3", name: "Reveal the Prediction", tagline: "Expose the brain's goal." }
          ],
          action: "Simply observe the prediction without collapsing into it."
        }
      ]
    },
    {
      id: "phase-2",
      name: "Repatterning",
      theme: "Reconsolidation Design",
      description: "Recode that loop fast—spark the new identity in real time.",
      color: "from-emerald-500 to-teal-600",
      lessons: [
        {
          id: "lesson-4",
          name: "Identity Anchor",
          benefit: "Stabilize the new self-image in high-pressure states.",
          obstacles: ["Old identity tugging back.", "Social pressure.", "Lack of immediate reward."],
          steps: [
            { id: "s1", name: "Grounding", tagline: "Locate the center." },
            { id: "s2", name: "Reframing", tagline: "Shift the lens." },
            { id: "s3", name: "Locking", tagline: "Secure the state." }
          ],
          action: "Anchor the new identity state for 60 seconds."
        }
      ]
    },
    {
      id: "phase-3",
      name: "Stabilization",
      theme: "Identity–Action Synchronization",
      description: "Embed the identity so actions, habits, and results stay congruent.",
      color: "from-blue-500 to-indigo-600",
      lessons: []
    }
  ]
};

type UIState = "idle" | "listening" | "processing" | "phase_view" | "lesson_view" | "obstacle_view" | "step_selection" | "final_action";

export default function ExperienceDashboard() {
  const [uiState, setUiState] = useState<UIState>("idle");
  const [inputValue, setInputValue] = useState("");
  const [selectedPhase, setSelectedPhase] = useState<typeof CURRICULUM.phases[0] | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [activeStep, setActiveStep] = useState<any>(null);
  const [isVoiceActive, setIsVoiceActive] = useState(false);

  // Voice Synthesis
  const speak = useCallback((text: string) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.05;
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  const handleIngest = () => {
    if (!inputValue.trim()) return;
    setUiState("processing");

    setTimeout(() => {
      const phase = CURRICULUM.phases[0];
      const lesson = phase.lessons[0];
      setSelectedPhase(phase);
      setSelectedLesson(lesson);
      setUiState("phase_view");
      speak(`Relational relevance detected in ${phase.name}. Let's enter.`);
    }, 1500);
  };

  const startVoice = () => {
    setIsVoiceActive(true);
    setUiState("listening");
    if ("webkitSpeechRecognition" in window) {
      const recognition = new (window as any).webkitSpeechRecognition();
      recognition.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        setInputValue(text);
        setIsVoiceActive(false);
        handleIngest();
      };
      recognition.onerror = () => {
        setIsVoiceActive(false);
        setUiState("idle");
      };
      recognition.start();
    } else {
      alert("Speech recognition not supported in this browser.");
      setIsVoiceActive(false);
      setUiState("idle");
    }
  };

  const handleZoomToLesson = () => {
    setUiState("lesson_view");
    speak(`The benefit of this lesson: ${selectedLesson.benefit}. Ready?`);
  };

  const handleShowObstacles = () => {
    setUiState("obstacle_view");
    speak("Observe these friction points. They are predictions, not truths.");
  };

  const handleShowSteps = () => {
    setUiState("step_selection");
    speak("Now, choose your entry point for this lesson.");
  };

  const handleZoomToStep = (step: any) => {
    setActiveStep(step);
    setUiState("final_action");
    speak(`Action Logic Primed. ${selectedLesson.action}`);
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden mesh-bg font-sans selection:bg-violet-500/30">
      {/* Texture Layer */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.02] bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] z-50" />

      {/* Lighting Ambience */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-violet-600/10 blur-[180px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-emerald-600/10 blur-[180px] rounded-full" />
      </div>

      <main className="relative z-10 flex flex-col items-center justify-center min-h-screen p-4 md:p-12 perspective-deep">

        <AnimatePresence mode="wait">
          {/* 0. IDLE / INPUT */}
          {(uiState === "idle" || uiState === "listening" || uiState === "processing") && (
            <motion.div
              key="input-state"
              initial={{ opacity: 0, scale: 0.9, rotateX: 10 }}
              animate={{ opacity: 1, scale: 1, rotateX: 0 }}
              exit={{ opacity: 0, scale: 1.5, filter: "blur(40px)", transition: { duration: 1, ease: [0.16, 1, 0.3, 1] } }}
              className="w-full max-w-3xl px-6"
            >
              <div className="space-y-16">
                <div className="space-y-6 text-center">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-center"
                  >
                    <div className="px-5 py-2 glass rounded-full flex items-center gap-3 border-white/20">
                      <Sparkles size={16} className="text-violet-400" />
                      <span className="text-[11px] font-black uppercase tracking-[0.4em] text-white/50">Core Perception Active</span>
                    </div>
                  </motion.div>
                  <motion.h1
                    className="text-7xl md:text-9xl font-black tracking-tighter text-white leading-[0.85]"
                  >
                    What's <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-emerald-400 to-indigo-400 italic">up?</span>
                  </motion.h1>
                </div>

                <div className="relative group max-w-2xl mx-auto w-full">
                  <div className="absolute -inset-2 bg-gradient-to-r from-violet-600/20 via-emerald-600/20 to-indigo-600/20 rounded-[3rem] blur-2xl opacity-50 group-hover:opacity-100 transition duration-1000"></div>
                  <div className="relative flex items-center bg-zinc-950/70 backdrop-blur-3xl border border-white/10 rounded-[3rem] p-4 pl-10 shadow-3xl">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Share your bottleneck..."
                      className="flex-1 bg-transparent border-none outline-none text-white text-2xl py-6 placeholder:text-zinc-700 font-medium"
                      onKeyDown={(e) => e.key === "Enter" && handleIngest()}
                    />
                    <div className="flex items-center gap-4 pr-2">
                      <button
                        onClick={startVoice}
                        className={cn(
                          "p-6 rounded-[2rem] transition-all active:scale-90",
                          isVoiceActive ? "bg-red-500/80 text-white shadow-[0_0_40px_rgba(239,68,68,0.4)]" : "text-zinc-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <Mic size={32} />
                      </button>
                      <button
                        onClick={handleIngest}
                        className="bg-white text-black p-6 rounded-[2rem] font-black shadow-2xl hover:bg-violet-400 transition-all active:scale-95"
                      >
                        <Send size={32} />
                      </button>
                    </div>
                  </div>
                </div>

                {uiState === "processing" && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-col items-center gap-6"
                  >
                    <div className="flex gap-2">
                      {[1, 2, 3, 4].map(i => (
                        <motion.div
                          key={i}
                          animate={{ height: [12, 32, 12], opacity: [0.3, 1, 0.3] }}
                          transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.1 }}
                          className="w-1.5 rounded-full bg-emerald-400"
                        />
                      ))}
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.5em] text-zinc-500">Mapping Attractor Basins</span>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* 1. PHASE VIEW */}
          {uiState === "phase_view" && selectedPhase && (
            <motion.div
              key="phase-state"
              initial={{ scale: 4, opacity: 0, z: -1000 }}
              animate={{ scale: 1, opacity: 1, z: 0 }}
              exit={{ scale: 0.4, opacity: 0, z: 500, transition: { duration: 0.8 } }}
              transition={{ type: "spring", damping: 25, stiffness: 60 }}
              className="w-full h-full flex flex-col items-center justify-center gap-20 preserve-3d"
            >
              <div className="text-center space-y-4">
                <span className="text-violet-400 font-black uppercase tracking-[0.5em] text-xs">Architectural Level 01</span>
                <h2 className="text-8xl font-black text-white italic tracking-tighter leading-none">The Core Phases</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-12 w-full max-w-7xl px-10">
                {CURRICULUM.phases.map((p) => (
                  <motion.div
                    key={p.id}
                    layoutId={`phase-${p.id}`}
                    whileHover={{ y: -30, scale: 1.05, rotateY: p.id === selectedPhase.id ? 0 : 8 }}
                    className={cn(
                      "group relative overflow-hidden p-12 rounded-[4rem] border transition-all duration-1000",
                      p.id === selectedPhase.id ? "bg-white/10 border-white/20 shadow-[0_0_120px_rgba(124,58,237,0.15)] scale-110 z-20" : "bg-white/5 border-white/5 opacity-20 grayscale-100 blur-[4px]"
                    )}
                  >
                    <div className={cn("absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br blur-[120px] opacity-20", p.color)} />
                    <div className="relative z-10 flex flex-col h-full min-h-[400px]">
                      <div className="p-5 bg-white/5 border border-white/10 rounded-[2rem] w-fit mb-12 text-white group-hover:bg-white group-hover:text-black transition-colors duration-700">
                        <Layers size={36} />
                      </div>
                      <h3 className="text-5xl font-black text-white mb-4 tracking-tighter uppercase">{p.name}</h3>
                      <p className="text-zinc-500 font-bold text-xl mb-10">{p.theme}</p>

                      {p.id === selectedPhase.id && (
                        <motion.button
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          onClick={handleZoomToLesson}
                          className="mt-auto group/btn flex items-center justify-between bg-white text-black pl-10 pr-4 py-4 rounded-full font-black text-xs uppercase tracking-[0.3em] hover:bg-emerald-400 transition-all active:scale-95 shadow-xl"
                        >
                          <span>Dive In</span>
                          <div className="bg-black text-white p-4 rounded-full group-hover/btn:px-8 transition-all duration-500">
                            <ArrowRight size={24} />
                          </div>
                        </motion.button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* 2. LESSON VIEW */}
          {uiState === "lesson_view" && selectedLesson && (
            <motion.div
              key="lesson-state"
              initial={{ scale: 3, opacity: 0, rotateY: -15 }}
              animate={{ scale: 1, opacity: 1, rotateY: 0 }}
              exit={{ scale: 0.6, opacity: 0, filter: "blur(20px)", transition: { duration: 0.6 } }}
              transition={{ type: "spring", damping: 20, stiffness: 70 }}
              className="w-full max-w-6xl"
            >
              <div className="glass-dark p-20 rounded-[5rem] border border-white/20 shadow-4xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-12 opacity-5">
                  <Zap size={300} strokeWidth={1} />
                </div>

                <div className="grid md:grid-cols-2 gap-20 items-center">
                  <div className="space-y-12 relative z-10">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 text-emerald-400">
                        <Target size={20} />
                        <span className="font-black uppercase tracking-[0.5em] text-xs">Transformational Unit</span>
                      </div>
                      <h2 className="text-7xl font-black text-white tracking-tighter leading-[1] uppercase">{selectedLesson.name}</h2>
                    </div>

                    <div className="p-10 bg-emerald-500/5 border border-emerald-500/10 rounded-[3rem] backdrop-blur-md">
                      <p className="text-emerald-100 italic text-3xl font-light leading-relaxed font-serif">"{selectedLesson.benefit}"</p>
                    </div>

                    <button
                      onClick={handleShowObstacles}
                      className="group flex items-center gap-8 bg-white text-black px-12 py-8 rounded-[2.5rem] font-black text-2xl hover:bg-emerald-400 transition-all active:scale-95 shadow-2xl"
                    >
                      <span>Show Impediments</span>
                      <ArrowRight className="group-hover:translate-x-4 transition-transform size-8" />
                    </button>
                  </div>

                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 60, ease: "linear" }}
                    className="hidden md:flex relative aspect-square items-center justify-center p-20"
                  >
                    <div className="absolute inset-0 border-[3px] border-dashed border-white/5 rounded-full" />
                    <div className="absolute inset-10 border border-white/10 rounded-full" />
                    <div className="absolute inset-20 border-[10px] border-white/5 rounded-full" />
                    <div className="w-80 h-80 bg-gradient-to-tr from-violet-600 to-indigo-900 rounded-[4rem] flex items-center justify-center shadow-3xl rotate-[15deg] group hover:rotate-0 transition-transform duration-1000">
                      <Zap size={120} className="text-white animate-float" />
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 3. OBSTACLE REVEAL */}
          {uiState === "obstacle_view" && selectedLesson && (
            <motion.div
              key="obstacle-state"
              initial={{ opacity: 0, scale: 1.2 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="w-full max-w-7xl px-12"
            >
              <div className="text-center space-y-8 mb-24">
                <h2 className="text-6xl font-black text-white tracking-tighter uppercase italic">Predictive Friction</h2>
                <p className="text-zinc-500 font-bold uppercase tracking-[0.8em] text-xs">The brain's plea for safety. Ignore it.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                {selectedLesson.obstacles.map((obs: string, i: number) => (
                  <motion.div
                    key={i}
                    initial={{ y: 60, opacity: 0, rotateX: 30 }}
                    animate={{ y: 0, opacity: 1, rotateX: 0 }}
                    transition={{ delay: i * 0.4, type: "spring", damping: 15 }}
                    className="relative group h-full"
                  >
                    <div className="absolute -inset-2 bg-red-600/10 rounded-[3.5rem] blur-2xl opacity-0 group-hover:opacity-100 transition duration-700" />
                    <div className="relative glass border-red-500/20 p-16 rounded-[3.5rem] h-full flex flex-col gap-8 group-hover:bg-red-950/20 transition-colors">
                      <div className="w-20 h-20 bg-red-500/10 rounded-[1.5rem] flex items-center justify-center text-red-500">
                        <AlertCircle size={40} strokeWidth={3} />
                      </div>
                      <p className="text-white/90 text-2xl font-black leading-tight tracking-tight uppercase">{obs}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="flex justify-center mt-24">
                <button
                  onClick={handleShowSteps}
                  className="group bg-zinc-900 border border-white/10 text-white px-16 py-6 rounded-full font-black uppercase tracking-[0.3em] hover:bg-white hover:text-black transition-all flex items-center gap-4 text-xs"
                >
                  <span>Proceed to Execution</span>
                  <ChevronRight size={18} />
                </button>
              </div>
            </motion.div>
          )}

          {/* 4. STEP SELECTION */}
          {uiState === "step_selection" && selectedLesson && (
            <motion.div
              key="step-selection-state"
              initial={{ scale: 5, opacity: 0, filter: "blur(100px)" }}
              animate={{ scale: 1, opacity: 1, filter: "blur(0px)" }}
              exit={{ scale: 0.2, opacity: 0, transition: { duration: 0.8 } }}
              transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-7xl px-12"
            >
              <div className="text-center mb-32">
                <span className="text-emerald-400 font-black uppercase tracking-[0.6em] text-xs">Neurological Sequence</span>
                <h2 className="text-8xl font-black text-white tracking-tighter mt-6 uppercase italic leading-none">Choose Your Path</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-16">
                {(selectedLesson.steps || []).map((step: any, i: number) => (
                  <motion.div
                    key={step.id}
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: i * 0.2 }}
                    whileHover={{ scale: 1.15, z: 100 }}
                    onClick={() => handleZoomToStep(step)}
                    className="cursor-pointer relative aspect-[4/5] glass-dark rounded-[4rem] p-16 flex flex-col justify-end border-white/5 group overflow-hidden shadow-4xl"
                  >
                    <div className="absolute top-12 right-12 opacity-5 group-hover:opacity-20 transition-opacity font-black text-[12rem] text-white leading-none">
                      {i + 1}
                    </div>
                    <div className="relative z-10 space-y-6">
                      <h3 className="text-5xl font-black text-white leading-[0.9] uppercase tracking-tighter">{step.name}</h3>
                      <p className="text-emerald-500 font-black uppercase tracking-[0.4em] text-[10px] italic">{step.tagline}</p>
                      <div className="w-16 h-2 bg-white/10 group-hover:w-full group-hover:bg-emerald-500 transition-all duration-700 ease-out" />
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* 5. FINAL ACTION */}
          {uiState === "final_action" && activeStep && (
            <motion.div
              key="action-state"
              initial={{ scale: 10, opacity: 0, z: -2000 }}
              animate={{ scale: 1, opacity: 1, z: 0 }}
              transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center justify-center text-center gap-16"
            >
              <motion.div
                animate={{
                  boxShadow: ["0 0 0px 0px rgba(16,185,129,0)", "0 0 150px 50px rgba(16,185,129,0.2)", "0 0 0px 0px rgba(16,185,129,0)"],
                  scale: [1, 1.1, 1]
                }}
                transition={{ repeat: Infinity, duration: 4 }}
                className="w-56 h-56 bg-emerald-500 rounded-full flex items-center justify-center shadow-4xl relative"
              >
                <div className="absolute inset-0 bg-white/20 rounded-full animate-ping opacity-20" />
                <CheckCircle2 size={120} className="text-white" strokeWidth={3} />
              </motion.div>

              <div className="space-y-10">
                <motion.h2
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-[12rem] md:text-[20rem] font-black text-white tracking-tighter leading-none uppercase italic opacity-90"
                >
                  READY.
                </motion.h2>
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 1 }}
                  className="glass-dark border-emerald-500/40 p-20 rounded-[5rem] max-w-5xl shadow-4xl"
                >
                  <p className="text-5xl md:text-7xl font-black text-white tracking-tighter leading-[1] uppercase">
                    {selectedLesson.action}
                  </p>
                </motion.div>
              </div>

              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 2 }}
                onClick={() => setUiState("idle")}
                className="group flex items-center gap-6 text-zinc-600 hover:text-white transition-all uppercase tracking-[0.6em] font-black text-xs px-12 py-6 glass rounded-full"
              >
                <ChevronRight size={20} className="rotate-180" />
                <span>Return to Baseline</span>
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Persistence Bar */}
      <div className="fixed bottom-12 inset-x-0 px-20 flex items-center justify-between z-50">
        <div className="glass px-8 py-4 rounded-3xl flex items-center gap-5 border-white/5 shadow-2xl">
          <div className={cn("w-3 h-3 rounded-full", uiState === "idle" ? "bg-zinc-700" : "bg-emerald-500 shadow-[0_0_15px_#10b981]")} />
          <span className="text-[11px] font-black uppercase tracking-[0.5em] text-white/50">Neural Link: {uiState.replace("_", " ").toUpperCase()}</span>
        </div>

        {selectedPhase && (
          <div className="hidden md:flex gap-6">
            <div className="glass px-8 py-4 rounded-3xl border-white/5 shadow-2xl">
              <span className="text-[11px] font-black uppercase tracking-[0.5em] text-violet-400">P-{selectedPhase.name}</span>
            </div>
            {selectedLesson && (
              <div className="glass px-8 py-4 rounded-3xl border-white/5 shadow-2xl">
                <span className="text-[11px] font-black uppercase tracking-[0.5em] text-emerald-400">L-{selectedLesson.name}</span>
              </div>
            )}
            {activeStep && (
              <div className="glass px-8 py-4 rounded-3xl border-white/5 shadow-2xl">
                <span className="text-[11px] font-black uppercase tracking-[0.5em] text-white">S-{activeStep.name}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <style jsx global>{`
        .perspective-deep {
          perspective: 3500px;
        }
        .preserve-3d {
          transform-style: preserve-3d;
        }
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0); }
          50% { transform: translateY(-40px) rotate(5deg); }
        }
        .animate-float {
          animation: float 15s ease-in-out infinite;
        }
        .glass-dark {
          background: rgba(0, 0, 0, 0.4);
          backdrop-filter: blur(80px) saturate(180%);
          border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .shadow-3xl {
          box-shadow: 0 50px 100px -20px rgba(0, 0, 0, 0.7);
        }
        .shadow-4xl {
          box-shadow: 0 80px 150px -30px rgba(0, 0, 0, 0.9);
        }
      `}</style>
    </div>
  );
}
