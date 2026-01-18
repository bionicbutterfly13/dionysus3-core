'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PhaseCard, LessonCard, ActionCard, TransformationCard } from './journey-card';
import { IAS_CURRICULUM, getPhaseForLesson, getLessonForAction } from '@/lib/ias-curriculum';
import type { Phase, Lesson, Action, JourneyState } from '@/lib/ias-types';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface JourneyNavigatorProps {
  recommendation: {
    phaseId: string;
    lessonId: string;
    actionId: string;
    reasoning: string;
  };
  onReset: () => void;
}

export function JourneyNavigator({ recommendation, onReset }: JourneyNavigatorProps) {
  const [journeyState, setJourneyState] = useState<JourneyState>({
    stage: 'phases',
  });

  // Find recommended items
  const recommendedPhase = IAS_CURRICULUM.find(p => p.id === recommendation.phaseId);
  const recommendedLesson = recommendedPhase?.lessons.find(l => l.id === recommendation.lessonId);
  const recommendedAction = recommendedLesson?.actions.find(a => a.id === recommendation.actionId);

  const handlePhaseSelect = useCallback((phase: Phase) => {
    setJourneyState({
      stage: 'lessons',
      selectedPhase: phase,
    });
  }, []);

  const handleLessonSelect = useCallback((lesson: Lesson) => {
    const phaseInfo = getPhaseForLesson(lesson.id);
    if (phaseInfo) {
      setJourneyState(prev => ({
        ...prev,
        stage: 'actions',
        selectedLesson: lesson,
      }));
    }
  }, []);

  const handleActionSelect = useCallback((action: Action) => {
    setJourneyState(prev => ({
      ...prev,
      stage: 'confirmation',
      selectedAction: action,
    }));
  }, []);

  const handleBack = useCallback(() => {
    setJourneyState(prev => {
      switch (prev.stage) {
        case 'lessons':
          return { stage: 'phases' };
        case 'actions':
          return { stage: 'lessons', selectedPhase: prev.selectedPhase };
        case 'confirmation':
          return { stage: 'actions', selectedPhase: prev.selectedPhase, selectedLesson: prev.selectedLesson };
        default:
          return prev;
      }
    });
  }, []);

  const handleConfirmation = useCallback((confirmed: boolean) => {
    if (confirmed) {
      // User confirmed - could trigger next steps here
      console.log('User confirmed transformation');
    } else {
      // User wants to see more - go back to actions
      handleBack();
    }
  }, [handleBack]);

  const getCurrentPhaseId = (): string => {
    if (journeyState.selectedPhase) return journeyState.selectedPhase.id;
    if (recommendedPhase) return recommendedPhase.id;
    return 'phase-1';
  };

  const getBreadcrumb = () => {
    const parts: string[] = [];
    if (journeyState.selectedPhase) parts.push(journeyState.selectedPhase.name);
    if (journeyState.selectedLesson) parts.push(journeyState.selectedLesson.name);
    if (journeyState.selectedAction) parts.push(journeyState.selectedAction.name);
    return parts;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with navigation */}
      <div className="border-b border-border bg-background/80 backdrop-blur-sm px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {journeyState.stage !== 'phases' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBack}
                className="h-8 w-8"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="sr-only">Go back</span>
              </Button>
            )}
            
            <div className="flex items-center gap-2 text-sm">
              {getBreadcrumb().map((part, i) => (
                <span key={part} className="flex items-center gap-2">
                  {i > 0 && <span className="text-muted-foreground">/</span>}
                  <span className={cn(
                    i === getBreadcrumb().length - 1 ? 'text-foreground' : 'text-muted-foreground'
                  )}>
                    {part}
                  </span>
                </span>
              ))}
              {getBreadcrumb().length === 0 && (
                <span className="text-foreground font-medium">Choose Your Path</span>
              )}
            </div>
          </div>
          
          <Button variant="ghost" size="sm" onClick={onReset} className="text-muted-foreground">
            <RotateCcw className="w-4 h-4 mr-2" />
            Start Over
          </Button>
        </div>
      </div>

      {/* Reasoning Banner */}
      {journeyState.stage === 'phases' && recommendation.reasoning && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card/50 border-b border-border px-4 py-4"
        >
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-muted-foreground leading-relaxed">
              <span className="font-medium text-foreground">Based on your story: </span>
              {recommendation.reasoning}
            </p>
          </div>
        </motion.div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {/* Phases Stage */}
            {journeyState.stage === 'phases' && (
              <motion.div
                key="phases"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <motion.h2 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-2xl font-semibold text-foreground text-center mb-2"
                >
                  The Three Phases
                </motion.h2>
                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1, transition: { delay: 0.1 } }}
                  className="text-muted-foreground text-center mb-8"
                >
                  Select a phase to explore, or follow the recommended path
                </motion.p>
                
                <div className="grid gap-4 md:grid-cols-3">
                  {IAS_CURRICULUM.map((phase, index) => (
                    <PhaseCard
                      key={phase.id}
                      phase={phase}
                      isSelected={journeyState.selectedPhase?.id === phase.id}
                      isRecommended={phase.id === recommendation.phaseId}
                      onClick={() => handlePhaseSelect(phase)}
                      index={index}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Lessons Stage */}
            {journeyState.stage === 'lessons' && journeyState.selectedPhase && (
              <motion.div
                key="lessons"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <motion.h2 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-2xl font-semibold text-foreground text-center mb-2"
                >
                  {journeyState.selectedPhase.name} Lessons
                </motion.h2>
                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1, transition: { delay: 0.1 } }}
                  className="text-muted-foreground text-center mb-8 max-w-lg mx-auto"
                >
                  {journeyState.selectedPhase.description}
                </motion.p>
                
                <div className="space-y-3 max-w-2xl mx-auto">
                  {journeyState.selectedPhase.lessons.map((lesson, index) => (
                    <LessonCard
                      key={lesson.id}
                      lesson={lesson}
                      phaseId={journeyState.selectedPhase!.id}
                      isSelected={journeyState.selectedLesson?.id === lesson.id}
                      isRecommended={lesson.id === recommendation.lessonId}
                      onClick={() => handleLessonSelect(lesson)}
                      index={index}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Actions Stage */}
            {journeyState.stage === 'actions' && journeyState.selectedLesson && (
              <motion.div
                key="actions"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <motion.h2 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-2xl font-semibold text-foreground text-center mb-2"
                >
                  {journeyState.selectedLesson.name}
                </motion.h2>
                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1, transition: { delay: 0.1 } }}
                  className="text-muted-foreground text-center mb-8 max-w-lg mx-auto"
                >
                  {journeyState.selectedLesson.description}
                </motion.p>
                
                <div className="grid gap-4 md:grid-cols-3 max-w-3xl mx-auto">
                  {journeyState.selectedLesson.actions.map((action, index) => (
                    <ActionCard
                      key={action.id}
                      action={action}
                      phaseId={getCurrentPhaseId()}
                      isSelected={journeyState.selectedAction?.id === action.id}
                      isRecommended={action.id === recommendation.actionId}
                      onClick={() => handleActionSelect(action)}
                      index={index}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Confirmation Stage */}
            {journeyState.stage === 'confirmation' && journeyState.selectedAction && (
              <motion.div
                key="confirmation"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.4 }}
                className="flex items-center justify-center min-h-[400px]"
              >
                <TransformationCard
                  action={journeyState.selectedAction}
                  phaseId={getCurrentPhaseId()}
                  onConfirm={handleConfirmation}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
