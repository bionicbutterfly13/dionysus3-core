'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { StoryChat } from '@/components/story-chat';
import { JourneyNavigator } from '@/components/journey-navigator';

interface Recommendation {
  phaseId: string;
  lessonId: string;
  actionId: string;
  reasoning: string;
}

export default function InnerArchitectPage() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [stage, setStage] = useState<'chat' | 'journey'>('chat');

  const handleAnalysisComplete = (rec: Recommendation) => {
    setRecommendation(rec);
    // Small delay before transitioning to let the final message render
    setTimeout(() => {
      setStage('journey');
    }, 1500);
  };

  const handleReset = () => {
    setRecommendation(null);
    setStage('chat');
  };

  return (
    <main className="min-h-screen bg-background">
      {/* Ambient Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-phase-revelation/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-phase-repatterning/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-phase-stabilization/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
              <div className="w-4 h-4 rounded-sm bg-accent" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Inner Architect</h1>
              <p className="text-xs text-muted-foreground">Transformation System</p>
            </div>
          </div>
          
          {stage === 'chat' && (
            <div className="text-sm text-muted-foreground">
              Share your story to begin
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 h-[calc(100vh-73px)]">
        <AnimatePresence mode="wait">
          {stage === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.4 }}
              className="h-full"
            >
              <StoryChat onAnalysisComplete={handleAnalysisComplete} />
            </motion.div>
          )}

          {stage === 'journey' && recommendation && (
            <motion.div
              key="journey"
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="h-full"
            >
              <JourneyNavigator 
                recommendation={recommendation} 
                onReset={handleReset}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
