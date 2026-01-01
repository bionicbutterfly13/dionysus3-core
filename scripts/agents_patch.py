

import os

filepath = "/Volumes/Asylum/repos/smolagents/src/smolagents/agents.py"
if not os.path.exists(filepath):
    print(f"Error: {filepath} not found")
    exit(1)

with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def write_memory_to_messages(" in line:
        new_lines.append(line)
        new_lines.append("        self,\n")
        new_lines.append("        summary_mode: bool = False,\n")
        new_lines.append("    ) -> list[ChatMessage]:\n")
        new_lines.append("        # Auto-pruning for context efficiency (Dionysus Optimization)\n")
        new_lines.append("        if not summary_mode and len(self.memory.steps) > 10:\n")
        new_lines.append("            self.memory.prune_steps(keep_last_n=5, keep_task=True)\n\n")
        new_lines.append("        messages = self.memory.system_prompt.to_messages(summary_mode=summary_mode)\n")
        new_lines.append("        for memory_step in self.memory.steps:\n")
        new_lines.append("            messages.extend(memory_step.to_messages(summary_mode=summary_mode))\n")
        new_lines.append("        return messages\n")
        skip = True
        continue
    
    if skip:
        if "return messages" in line:
            skip = False
        continue
    
    new_lines.append(line)

with open(filepath, "w") as f:
    f.writelines(new_lines)
print("✅ agents.py successfully enhanced with Auto-Pruning")

