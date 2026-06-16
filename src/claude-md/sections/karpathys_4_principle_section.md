# 4 Principles section
You always follow the SDD tool currently in use (speckit, openspec). But for anything requiring writing/editing code, follow the 4 principles below:

\## 1. Think Before Coding  
**Don't assume. Don't hide confusion. Surface tradeoffs.**  
  
Before implementing:  
\- State your assumptions explicitly. If uncertain, ask.  
\- If multiple interpretations exist, present them.  
\- If a simpler approach exists, say so.  
\- If something is unclear, stop. Name what's confusing.  
  
\## 2. Simplicity First  
**Minimum code that solves the problem. Nothing speculative.**  
  
\- No features beyond what was asked.  
\- No abstractions for single-use code.  
\- No “flexibility” that wasn't requested.  
\- No error handling for impossible scenarios.  
\- If 200 lines could be 50, rewrite it.  
  
\## 3. Surgical Changes  
**Touch only what you must. Clean up only your own mess.**  
  
\- Don't “improve” adjacent code or formatting.  
\- Don't refactor things that aren't broken.  
\- Match existing style, even if you'd do it differently.  
\- If you notice dead code, mention it — don't delete it.  
  
\## 4. Goal-Driven Execution  
**Define success criteria. Loop until verified.**  