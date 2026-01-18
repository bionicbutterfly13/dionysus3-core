/* eslint-disable @typescript-eslint/no-explicit-any */
// Add Window augmentation for SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '@ai-sdk/react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ArrowUp, Sparkles, Mic, Volume2, MicOff, VolumeX } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface StoryChatProps {
  onAnalysisComplete: (recommendation: {
    phaseId: string;
    lessonId: string;
    actionId: string;
    reasoning: string;
  }) => void;
}

export function StoryChat({ onAnalysisComplete }: StoryChatProps) {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true); // Auto-speak responses

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null); // SpeechRecognition type is not standard in generic TS
  const synthRef = useRef<SpeechSynthesis | null>(null);

  // Initialize Speech Recognition and Synthesis
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Speech Recognition
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true; // Real-time feedback
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event: any) => {
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            }
          }
          if (finalTranscript) {
            setInput((prev) => prev + (prev.endsWith(' ') || prev.length === 0 ? '' : ' ') + finalTranscript);
            // Optional: Auto-submit on final result? No, let user confirm.
          }
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error('Speech recognition error', event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }

      // Speech Synthesis
      if ('speechSynthesis' in window) {
        synthRef.current = window.speechSynthesis;
      }
    }
  }, []);

  const { messages, sendMessage, status } = useChat({
    // @ts-expect-error: onFinish signature mismatch fallback
    api: '/api/analyze-story',
    onFinish: (result) => {
      const content = (result.message as any).content || '';

      // Auto-speak if enabled
      if (voiceEnabled && synthRef.current) {
        // Strip recommendation block for speech
        const speechText = content.replace(/\[RECOMMENDATION\]([\s\S]*?)\[\/RECOMMENDATION\]/g, '').trim();
        if (speechText) {
          speak(speechText);
        }
      }

      try {
        const match = content.match(/\[RECOMMENDATION\]([\s\S]*?)\[\/RECOMMENDATION\]/);
        if (match) {
          const recommendation = JSON.parse(match[1]);
          onAnalysisComplete(recommendation);
        }
      } catch {
        // Not a recommendation message, continue conversation
      }
    },
  });

  const speak = (text: string) => {
    if (synthRef.current) {
      // Cancel current speech
      synthRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      // Attempt to select a nicer voice
      const voices = synthRef.current.getVoices();
      const preferredVoice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Samantha'));
      if (preferredVoice) utterance.voice = preferredVoice;

      synthRef.current.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status !== 'ready') return;
    sendMessage({ text: input });
    setInput('');
    stopSpeaking(); // Stop AI from speaking old message when user interrupts
  };

  const isLoading = status === 'streaming' || status === 'submitted';

  return (
    <div className="flex flex-col h-full">
      {/* Header controls for Voice */}
      <div className="flex justify-end px-4 py-2 border-b border-border/50">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (isSpeaking) stopSpeaking();
            setVoiceEnabled(!voiceEnabled)
          }}
          className={cn("text-xs gap-2", voiceEnabled ? "text-primary" : "text-muted-foreground")}
        >
          {isSpeaking ? (
            <span className="flex items-center gap-2"> <Volume2 className="w-4 h-4 animate-pulse" /> Speaking... (Click to Stop)</span>
          ) : (
            voiceEnabled ? <><Volume2 className="w-4 h-4" /> Auto-Read On</> : <><VolumeX className="w-4 h-4" /> Auto-Read Off</>
          )}
        </Button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center h-full text-center px-4"
          >
            <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mb-6">
              <Sparkles className="w-8 h-8 text-accent" />
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-3 text-balance">
              Share Your Story
            </h2>
            <p className="text-muted-foreground max-w-md leading-relaxed text-balance">
              Tell me about a challenge you&apos;re facing, a pattern you want to change, or a goal you&apos;re working toward. I&apos;ll help identify where to begin your transformation journey.
            </p>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-3 relative group',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border'
                )}
              >
                {/* Manual Speak Button for Assistant Messages */}
                {message.role === 'assistant' && !isSpeaking && (
                  <button
                    onClick={() => {
                      const displayText = (message as any).content.replace(/\[RECOMMENDATION\]([\s\S]*?)\[\/RECOMMENDATION\]/g, '').trim();
                      speak(displayText);
                    }}
                    className="absolute -right-8 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 text-muted-foreground hover:text-foreground"
                    aria-label="Read aloud"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                )}

                {(() => {
                  const content = (message as any).content;
                  if (!content) return null;

                  const displayText = content.replace(
                    /\[RECOMMENDATION\][\s\S]*?\[\/RECOMMENDATION\]/g,
                    ''
                  ).trim();

                  if (!displayText) return null;

                  return (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {displayText}
                    </p>
                  );
                })()}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
            <div className="bg-card border border-border rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-background/80 backdrop-blur-sm p-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className={cn(
            "relative flex items-end gap-2 bg-card border rounded-2xl p-2 transition-colors duration-300",
            isListening ? "border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]" : "border-border"
          )}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isListening ? "Listening..." : "Share what's on your mind..."}
              className="flex-1 bg-transparent border-0 resize-none text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 min-h-[44px] max-h-[200px] py-2 px-2"
              rows={1}
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />

            {/* Voice Input Button */}
            <Button
              type="button"
              size="icon"
              variant="ghost"
              onClick={toggleListening}
              disabled={isLoading}
              className={cn(
                "h-10 w-10 rounded-xl shrink-0 transition-all duration-300",
                isListening ? "text-red-500 hover:text-red-600 bg-red-500/10" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              <span className="sr-only">{isListening ? "Stop listening" : "Start listening"}</span>
            </Button>

            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="h-10 w-10 rounded-xl shrink-0"
            >
              <ArrowUp className="w-5 h-5" />
              <span className="sr-only">Send message</span>
            </Button>
          </div>
          {isListening && (
            <p className="text-xs text-red-500 mt-2 px-2 animate-pulse">
              Listening... Speak clearly.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
