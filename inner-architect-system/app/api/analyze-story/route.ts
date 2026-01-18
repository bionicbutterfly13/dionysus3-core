import {
  consumeStream,
  convertToModelMessages,
  streamText,
  UIMessage,
} from 'ai';
import { IAS_CURRICULUM } from '@/lib/ias-curriculum';

export const maxDuration = 60;

// Build curriculum context for the AI
function buildCurriculumContext() {
  let context = 'INNER ARCHITECT SYSTEM CURRICULUM:\n\n';
  
  for (const phase of IAS_CURRICULUM) {
    context += `## PHASE: ${phase.name} (${phase.subtitle})\n`;
    context += `${phase.description}\n\n`;
    
    for (const lesson of phase.lessons) {
      context += `### LESSON: ${lesson.name} (${lesson.subtitle})\n`;
      context += `ID: ${lesson.id}\n`;
      context += `${lesson.description}\n\n`;
      
      for (const action of lesson.actions) {
        context += `#### ACTION: ${action.name}\n`;
        context += `ID: ${action.id}\n`;
        context += `${action.description}\n`;
        context += `Transformation: ${action.transformation}\n`;
        context += `Obstacles:\n`;
        for (const obstacle of action.obstacles) {
          context += `- ${obstacle.name}: ${obstacle.description}\n`;
        }
        context += '\n';
      }
    }
    context += '---\n\n';
  }
  
  return context;
}

const SYSTEM_PROMPT = `You are a compassionate transformation coach for the Inner Architect System (IAS). Your role is to:

1. LISTEN deeply to the user's story, challenges, and goals
2. ASK follow-up questions to understand their situation better (2-3 questions max before making a recommendation)
3. IDENTIFY which part of the IAS curriculum would serve them best
4. RECOMMEND a specific Phase, Lesson, and Action based on their story

${buildCurriculumContext()}

CONVERSATION GUIDELINES:
- Be warm, empathetic, and non-judgmental
- Ask clarifying questions to understand their current challenges
- Look for patterns, beliefs, and stories they mention
- When you have enough context (usually after 2-3 exchanges), provide your recommendation

WHEN MAKING A RECOMMENDATION:
- Explain your reasoning in 2-3 sentences
- Then output the recommendation in this exact format (the system will parse this):

[RECOMMENDATION]{"phaseId":"phase-X","lessonId":"lesson-X","actionId":"action-X-X","reasoning":"Brief explanation of why this is the right starting point"}[/RECOMMENDATION]

MAPPING GUIDE:
- If someone mentions CONFUSION about patterns, lack of awareness, or difficulty understanding their behaviors → Phase 1 (Revelation)
- If someone mentions FRUSTRATION with repeated patterns, mental loops, feeling stuck → Lesson 3 (Replay Loop Breaker)
- If someone mentions wanting to CHANGE beliefs, limiting thoughts, or transform perspectives → Phase 2 (Repatterning)
- If someone mentions SUSTAINABILITY, building habits, needing systems, or maintaining change → Phase 3 (Stabilization)
- If someone mentions VISION, goals, or future direction → Lesson 6 (Vision Accelerator)
- If someone mentions needing SUPPORT or accountability → Lesson 9 (Growth Anchor)

Always start with a warm greeting if this is the first message.`;

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const prompt = convertToModelMessages(messages);

  const result = streamText({
    model: 'anthropic/claude-sonnet-4-20250514',
    system: SYSTEM_PROMPT,
    messages: prompt,
    maxOutputTokens: 1500,
    temperature: 0.7,
    abortSignal: req.signal,
  });

  return result.toUIMessageStreamResponse({
    onFinish: async ({ isAborted }) => {
      if (isAborted) {
        console.log('Story analysis aborted');
      }
    },
    consumeSseStream: consumeStream,
  });
}
