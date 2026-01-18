'use client';

import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import type { Phase, Lesson, Action } from '@/lib/ias-types';

// Phase Card
interface PhaseCardProps {
  phase: Phase;
  isSelected: boolean;
  isRecommended: boolean;
  onClick: () => void;
  index: number;
}

export function PhaseCard({ phase, isSelected, isRecommended, onClick, index }: PhaseCardProps) {
  const phaseColors: Record<string, string> = {
    'phase-1': 'from-blue-500/20 to-blue-600/10 border-blue-500/30 hover:border-blue-500/60',
    'phase-2': 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 hover:border-emerald-500/60',
    'phase-3': 'from-amber-500/20 to-amber-600/10 border-amber-500/30 hover:border-amber-500/60',
  };

  const phaseAccents: Record<string, string> = {
    'phase-1': 'bg-blue-500',
    'phase-2': 'bg-emerald-500',
    'phase-3': 'bg-amber-500',
  };

  return (
    <motion.button
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ 
        opacity: 1, 
        y: 0, 
        scale: isSelected ? 1.05 : 1,
        transition: { delay: index * 0.15, duration: 0.5 }
      }}
      whileHover={{ scale: 1.02, y: -5 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative w-full p-6 rounded-2xl border bg-gradient-to-br backdrop-blur-sm transition-all duration-300 text-left group',
        phaseColors[phase.id],
        isSelected && 'ring-2 ring-accent ring-offset-2 ring-offset-background',
        isRecommended && 'animate-pulse-subtle'
      )}
    >
      {isRecommended && (
        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -top-2 -right-2 px-2 py-1 bg-accent text-accent-foreground text-xs font-medium rounded-full"
        >
          Recommended
        </motion.div>
      )}
      
      <div className={cn('w-2 h-2 rounded-full mb-4', phaseAccents[phase.id])} />
      
      <h3 className="text-xl font-semibold text-foreground mb-1">{phase.name}</h3>
      <p className="text-sm text-muted-foreground mb-3">{phase.subtitle}</p>
      <p className="text-sm text-muted-foreground/80 line-clamp-2">{phase.description}</p>
      
      <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
        <span>{phase.lessons.length} Lessons</span>
        <span className="w-1 h-1 rounded-full bg-muted-foreground/50" />
        <span>{phase.lessons.reduce((acc, l) => acc + l.actions.length, 0)} Actions</span>
      </div>
    </motion.button>
  );
}

// Lesson Card
interface LessonCardProps {
  lesson: Lesson;
  phaseId: string;
  isSelected: boolean;
  isRecommended: boolean;
  onClick: () => void;
  index: number;
}

export function LessonCard({ lesson, phaseId, isSelected, isRecommended, onClick, index }: LessonCardProps) {
  const lessonColors: Record<string, string> = {
    'phase-1': 'from-blue-500/15 to-blue-600/5 border-blue-500/25 hover:border-blue-500/50',
    'phase-2': 'from-emerald-500/15 to-emerald-600/5 border-emerald-500/25 hover:border-emerald-500/50',
    'phase-3': 'from-amber-500/15 to-amber-600/5 border-amber-500/25 hover:border-amber-500/50',
  };

  return (
    <motion.button
      initial={{ opacity: 0, x: -30 }}
      animate={{ 
        opacity: 1, 
        x: 0,
        transition: { delay: index * 0.1, duration: 0.4 }
      }}
      whileHover={{ scale: 1.01, x: 5 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className={cn(
        'relative w-full p-5 rounded-xl border bg-gradient-to-br backdrop-blur-sm transition-all duration-300 text-left',
        lessonColors[phaseId],
        isSelected && 'ring-2 ring-accent ring-offset-2 ring-offset-background'
      )}
    >
      {isRecommended && (
        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -top-2 -right-2 px-2 py-1 bg-accent text-accent-foreground text-xs font-medium rounded-full"
        >
          Start Here
        </motion.div>
      )}
      
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h4 className="text-lg font-medium text-foreground mb-1">{lesson.name}</h4>
          <p className="text-sm text-accent mb-2">{lesson.subtitle}</p>
          <p className="text-sm text-muted-foreground line-clamp-2">{lesson.description}</p>
        </div>
        <div className="text-xs text-muted-foreground bg-secondary/50 px-2 py-1 rounded-md">
          {lesson.actions.length} Actions
        </div>
      </div>
    </motion.button>
  );
}

// Action Card
interface ActionCardProps {
  action: Action;
  phaseId: string;
  isSelected: boolean;
  isRecommended: boolean;
  onClick: () => void;
  index: number;
}

export function ActionCard({ action, phaseId, isSelected, isRecommended, onClick, index }: ActionCardProps) {
  const actionColors: Record<string, string> = {
    'phase-1': 'from-blue-500/10 to-transparent border-blue-500/20 hover:border-blue-500/40',
    'phase-2': 'from-emerald-500/10 to-transparent border-emerald-500/20 hover:border-emerald-500/40',
    'phase-3': 'from-amber-500/10 to-transparent border-amber-500/20 hover:border-amber-500/40',
  };

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ 
        opacity: 1, 
        scale: 1,
        transition: { delay: index * 0.1, duration: 0.4 }
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative w-full p-5 rounded-xl border bg-gradient-to-br backdrop-blur-sm transition-all duration-300 text-left',
        actionColors[phaseId],
        isSelected && 'ring-2 ring-accent ring-offset-2 ring-offset-background'
      )}
    >
      {isRecommended && (
        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -top-2 -right-2 px-2 py-1 bg-accent text-accent-foreground text-xs font-medium rounded-full"
        >
          Your Action
        </motion.div>
      )}
      
      <h4 className="text-base font-medium text-foreground mb-2">{action.name}</h4>
      <p className="text-sm text-muted-foreground mb-3">{action.description}</p>
      
      <div className="text-xs text-muted-foreground">
        {action.obstacles.length} Obstacles to Navigate
      </div>
    </motion.button>
  );
}

// Transformation Confirmation Card
interface TransformationCardProps {
  action: Action;
  phaseId: string;
  onConfirm: (confirmed: boolean) => void;
}

export function TransformationCard({ action, phaseId, onConfirm }: TransformationCardProps) {
  const cardColors: Record<string, string> = {
    'phase-1': 'from-blue-500/20 to-blue-600/5 border-blue-500/30',
    'phase-2': 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30',
    'phase-3': 'from-amber-500/20 to-amber-600/5 border-amber-500/30',
  };

  const buttonColors: Record<string, string> = {
    'phase-1': 'bg-blue-500 hover:bg-blue-600',
    'phase-2': 'bg-emerald-500 hover:bg-emerald-600',
    'phase-3': 'bg-amber-500 hover:bg-amber-600',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'w-full max-w-lg mx-auto p-8 rounded-2xl border bg-gradient-to-br backdrop-blur-sm',
        cardColors[phaseId]
      )}
    >
      <h3 className="text-2xl font-semibold text-foreground mb-4 text-center text-balance">
        Your Transformation
      </h3>
      
      <div className="bg-card/50 rounded-xl p-6 mb-6">
        <p className="text-lg text-foreground text-center leading-relaxed text-balance">
          &ldquo;{action.transformation}&rdquo;
        </p>
      </div>
      
      <p className="text-center text-muted-foreground mb-6">
        Does this transformation resonate with what you&apos;re seeking?
      </p>
      
      <div className="flex gap-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onConfirm(true)}
          className={cn(
            'flex-1 py-3 px-6 rounded-xl text-foreground font-medium transition-colors',
            buttonColors[phaseId]
          )}
        >
          Yes, this resonates
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onConfirm(false)}
          className="flex-1 py-3 px-6 rounded-xl border border-border text-foreground font-medium hover:bg-secondary/50 transition-colors"
        >
          Show me more
        </motion.button>
      </div>
    </motion.div>
  );
}
