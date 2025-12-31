"""
Class-based tools for Cognitive Reasoning and EFE reflection.
Feature: 003-thoughtseed-active-inference, 042-cognitive-tools-upgrade
Tasks: T4.1, T4.2, T042.1-4
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.cognitive_tools")

# =============================================================================
# EXISTING TOOLS (Feature 003)
# =============================================================================

class ExplorerOutput(BaseModel):
    project_id: str = Field(..., description="Scoping project identifier")
    query: str = Field(..., description="Original search query")
    attractors: List[str] = Field(..., description="List of detected semantic attractors")
    recommendation: str = Field(..., description="Actionable recommendation based on EFE")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ContextExplorerTool(Tool):
    name = "context_explorer"
    description = "Explorer Agent tool. Scans knowledge graph for semantic attractors and prunes context."
    
    inputs = {
        "project_id": {
            "type": "string",
            "description": "Scoping ID for the research."
        },
        "query": {
            "type": "string",
            "description": "Specific domain or task query."
        }
    }
    output_type = "any"

    def forward(self, project_id: str, query: str) -> dict:
        async def _run():
            graphiti = await get_graphiti_service()
            return await graphiti.search(f"attractor basins for {query} in project {project_id}", limit=5)
        
        try:
            search_results = async_tool_wrapper(_run)()
            edges = search_results.get("edges", [])
            
            attractors = [e.get('fact') for e in edges if e.get('fact')]
            
            if not attractors:
                return ExplorerOutput(
                    project_id=project_id,
                    query=query,
                    attractors=[],
                    recommendation="No semantic attractors found. Increase epistemic search."
                ).model_dump()

            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=attractors,
                recommendation="Ground reasoning in the 'Analytical Professional' basin to minimize free energy."
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Explorer search failed: {e}")
            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=[],
                recommendation="Fallback to base context.",
                error=str(e)
            ).model_dump()

class CognitiveCheckOutput(BaseModel):
    efe_score: float = Field(..., description="The calculated Expected Free Energy score")
    recommended_mode: str = Field(..., description="PRAGMATIC or EPISTEMIC based on EFE")
    reasoning: str = Field(..., description="Detailed explanation of the EFE calculation")

class CognitiveCheckTool(Tool):
    name = "cognitive_check"
    description = "Autonomous EFE self-reflection tool. Calculates the agent's current Expected Free Energy."
    
    inputs = {
        "uncertainty_level": {
            "type": "number",
            "description": "0.0-1.0 (Entropy)"
        },
        "goal_alignment": {
            "type": "number",
            "description": "0.0-1.0 (Similarity to goal)"
        }
    }
    output_type = "any"

    def forward(self, uncertainty_level: float, goal_alignment: float) -> dict:
        efe = float(uncertainty_level + (1.0 - goal_alignment))
        status = "PRAGMATIC" if efe < 0.5 else "EPISTEMIC"
        
        output = CognitiveCheckOutput(
            efe_score=efe,
            recommended_mode=status,
            reasoning=f"EFE is {efe:.2f}. " + ("Context is stable, proceed to execution." if status == "PRAGMATIC" else "Uncertainty high, prioritize research/recall.")
        )
        return output.model_dump()

# =============================================================================
# RESEARCH-VALIDATED COGNITIVE TOOLS (Feature 042)
# =============================================================================

class UnderstandQuestionOutput(BaseModel):
    analysis: str = Field(..., description="Structured analysis of the problem.")
    original_question: str = Field(..., description="The input question.")

class UnderstandQuestionTool(Tool):
    name = "understand_question"
    description = "Research-validated tool to decompose complex problems. Use this FIRST for any non-trivial task."
    
    inputs = {
        "question": {
            "type": "string",
            "description": "The problem or question to analyze."
        },
        "context": {
            "type": "string",
            "description": "Optional context or background information.",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, question: str, context: Optional[str] = "") -> dict:
        prompt = f"""You are a mathematical reasoning assistant designed to analyze and break down complex mathematical problems into structured steps to help the system that actually solves problems. Your goal is to:

1. Identify the core mathematical concepts involved (e.g., algebra, calculus, linear algebra).
2. Extract and categorize relevant symbols, variables, and functions.
3. Rephrase the problem into a step-by-step sequence that makes solving easier.
4. Highlight any known theorems or techniques that might be useful in solving the problem.
5. DO NOT provide any answer to the question, only provide instructions which will guide the upstream system.

Question: {question}

{f'Context: {context}' if context else ''}

Provide a structured analysis following the guidelines above."""

        async def _run():
            return await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a research-validated cognitive tool.",
                max_tokens=1024
            )

        try:
            result = async_tool_wrapper(_run)()
            return UnderstandQuestionOutput(
                analysis=result,
                original_question=question
            ).model_dump()
        except Exception as e:
            logger.error(f"UnderstandQuestion failed: {e}")
            return {"error": str(e)}

class RecallRelatedOutput(BaseModel):
    analogies: str = Field(..., description="Analogous examples with solutions.")

class RecallRelatedTool(Tool):
    name = "recall_related"
    description = "Retrieves analogous solved examples to guide reasoning. Use after understanding the problem."
    
    inputs = {
        "question": {
            "type": "string",
            "description": "The problem to find analogies for."
        },
        "context": {
            "type": "string",
            "description": "Optional context (e.g., output from understand_question).",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, question: str, context: Optional[str] = "") -> dict:
        prompt = f"""You are a retrieval assistant whose purpose is to help solve new mathematical problems by providing solved examples of analogous problems.

Given a new math problem, your task is to:
1. Identify 2 or 3 **similar problems** from your knowledge or training set that require **comparable mathematical concepts or reasoning steps**.
2. For each similar problem:
   - Provide the **full problem statement**.
   - Provide a **complete step-by-step solution**, including relevant formulas, simplifications, or code.
   - Highlight the **final answer**, preferably using LaTeX formatting (e.g., $42$).

Do **not** solve the current problem. Instead, present only useful analogous examples that could help someone reason through it.

Output Format:
Analogous Example 1:
Q: [Similar Problem 1]
A: [Step-by-step solution...]
Final Answer: ...

Analogous Example 2:
Q: [Similar Problem 2] 
A: [Step-by-step solution...]
Final Answer: ...

Analogous Example 3:
Q: [Similar Problem 3]
A: [Step-by-step solution...]
Final Answer: ...

Some important notes to keep in mind:
- Select examples with strong structural or conceptual similarity, not just keyword overlap.
- Variation in surface details (numbers, variable names) is acceptable as long as the mathematical logic aligns.

Question: {question}

{f'Context: {context}' if context else ''}"""

        async def _run():
            return await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a research-validated cognitive tool.",
                max_tokens=1024
            )

        try:
            result = async_tool_wrapper(_run)()
            return RecallRelatedOutput(
                analogies=result
            ).model_dump()
        except Exception as e:
            logger.error(f"RecallRelated failed: {e}")
            return {"error": str(e)}

class ExamineAnswerOutput(BaseModel):
    critique: str = Field(..., description="Detailed verification and critique of the reasoning.")

class ExamineAnswerTool(Tool):
    name = "examine_answer"
    description = "Critically examines reasoning for errors. Use before finalizing an answer."
    
    inputs = {
        "question": {
            "type": "string",
            "description": "The original problem."
        },
        "current_reasoning": {
            "type": "string",
            "description": "The proposed solution or reasoning trace."
        },
        "context": {
            "type": "string",
            "description": "Optional context.",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, question: str, current_reasoning: str, context: Optional[str] = "") -> dict:
        prompt = f"""You are an expert mathematical assistant tasked with **verifying and improving** solutions to complex mathematical problems. Your role is **not to solve the problem** but to critically analyze the provided solution for correctness, clarity, and completeness. You will be given a problem/question and the current reasoning that has been produced so far.

### **Your Task:**
Follow a structured **verification process**:

### **1. Understanding the Problem**
- Ensure the proposed solution correctly interprets the given problem.
- Identify the core mathematical concepts involved (e.g., algebra, calculus, number theory).
- Extract and categorize relevant symbols, variables, and functions.
- Identify any implicit assumptions or missing constraints.

### **2. Verifying the Given Solution**
- Clearly state what is the current answer of the problem.
- Break the provided solution down into distinct logical steps.
- Check for **logical consistency**, **mathematical correctness**, and **proper justification**.
- Identify any **miscalculations, incorrect assumptions, or unjustified leaps** in reasoning.
- Analyze the **edge cases** or conditions where the solution may fail.
- Evaluate whether all necessary steps and justifications are present.

#### **2.a) Testing and Validation (Problem-Derived Checks)**
- Examine the original problem statement and extract any **constraints, conditions, identities, or testable properties** that a correct answer must satisfy.
- Derive **test cases or evaluation criteria** based on those constraints.

**If the proposed solution is a numerical answer:**
- Plug the number into the original equation(s), inequality, or scenario to verify it satisfies all conditions.
- Check whether it meets qualitative criteria (e.g., smallest, largest, integer, range bounds).

**If the proposed solution is an expression or formula:**
- **Symbolically substitute** the expression into the original problem statement or equations, and confirm that it satisfies all requirements.
- Simplify or manipulate the expression to check **equivalence**, **domain correctness**, and **edge cases**.
- Where applicable, test the expression against representative sample inputs derived from the problem.

**For both cases:**
- Clearly describe each test performed and the outcome.
- State whether the provided answer (number or expression) **passes all derived problem-based tests**.

### **3. Suggesting Improvements**
- If an error is found, explain **precisely what is wrong** and **why**.
- Suggest possible fixes or improvements **without directly solving the problem**.
- Propose alternative methods to solve the problem where relevant (e.g., algebraic vs. numerical, direct proof vs. counterexample).

### **4. Providing a Judgment**
- Clearly state whether the proposed solution is **correct or incorrect**.
- Justify your judgment with a concise explanation.
- If incorrect, **recommend corrections** without providing a direct answer.

### **Guidelines to Follow:**
- DO NOT provide the actual answer to the problem.
- Focus only on verifying and critiquing the given solution.
- Be rigorous in checking correctness but also constructive in suggesting improvements.
- Explicitly say whether the answer is correct or incorrect

Question: {question}

{f'Context: {context}' if context else ''}

Current Reasoning Trace:
{current_reasoning}

Now, **critically analyze the solution**, highlight any mistakes, and suggest improvements where necessary."""

        async def _run():
            return await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a research-validated cognitive tool.",
                max_tokens=1024
            )

        try:
            result = async_tool_wrapper(_run)()
            return ExamineAnswerOutput(
                critique=result
            ).model_dump()
        except Exception as e:
            logger.error(f"ExamineAnswer failed: {e}")
            return {"error": str(e)}

class BacktrackingOutput(BaseModel):
    strategy: str = Field(..., description="Revised strategy or backtracking guidance.")

class BacktrackingTool(Tool):
    name = "backtracking"
    description = "Recovers from errors by proposing alternative strategies. Use if examine_answer finds flaws."
    
    inputs = {
        "question": {
            "type": "string",
            "description": "The original problem."
        },
        "current_reasoning": {
            "type": "string",
            "description": "The flawed reasoning trace."
        },
        "context": {
            "type": "string",
            "description": "Optional context.",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, question: str, current_reasoning: str, context: Optional[str] = "") -> dict:
        prompt = f"""You are a careful problem-solving assistant with the ability to backtrack from flawed logic.

You will be given a math or logic problem and a reasoning trace. Your task is to:
1. Analyze the reasoning and summarize it into different steps.
2. Identify where the first error, bad assumption, or confusion occurs (if any).
3. Propose how to revise the approach from that point onward, using the steps that you have defined.
4. If the entire approach was invalid, suggest a better strategy from scratch.

Use the following format for your response:

**Identified Issues:**
- Step X: Explain what is incorrect or suboptimal.
- (Repeat for any additional steps if needed.)

**Backtrack Point:**
- Indicate the step where reasoning was still valid and you can continue from.

**Revised Strategy (from backtrack point or new):**
- Present a step-by-step strategy to solve the problem correctly from this point.

Be precise and critical. Avoid vague judgments. Always backtrack to the most recent correct step, unless no step is valid.

Question: {question}

{f'Context: {context}' if context else ''}

Current Reasoning Trace:
{current_reasoning}

Analyze the reasoning trace and provide guidance for backtracking and alternative approaches."""

        async def _run():
            return await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a research-validated cognitive tool.",
                max_tokens=1024
            )

        try:
            result = async_tool_wrapper(_run)()
            return BacktrackingOutput(
                strategy=result
            ).model_dump()
        except Exception as e:
            logger.error(f"Backtracking failed: {e}")
            return {"error": str(e)}

# Export tool instances
context_explorer = ContextExplorerTool()
cognitive_check = CognitiveCheckTool()
understand_question = UnderstandQuestionTool()
recall_related = RecallRelatedTool()
examine_answer = ExamineAnswerTool()
backtracking = BacktrackingTool()