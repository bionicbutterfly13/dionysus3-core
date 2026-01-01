import os

filepath = "/Volumes/Asylum/repos/smolagents/src/smolagents/memory.py"
if not os.path.exists(filepath):
    print(f"Error: {filepath} not found")
    exit(1)

with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "class AgentMemory:" in line:
        new_lines.append(line)
        skip = True
        
        # Insert the complete fixed class methods
        methods = [
            "    def __init__(self, system_prompt: str):",
            "        self.system_prompt: SystemPromptStep = SystemPromptStep(system_prompt=system_prompt)",
            "        self.steps: list[TaskStep | ActionStep | PlanningStep] = []",
            "        self.assets: dict[str, Any] = {}",
            "",
            "    def reset(self):",
            "        self.steps = []",
            "        self.assets = {}",
            "",
            "    def save_asset(self, name: str, value: Any) -> str:",
            "        self.assets[name] = value",
            "        return f\"{{{{asset:{name}}}}}\",",
            "",
            "    def get_asset(self, handle: str) -> Any:",
            "        if isinstance(handle, str) and handle.startswith(\"{{asset:\") and handle.endswith(\"}}\"):",
            "            name = handle[8:-2]",
            "            return self.assets.get(name)",
            "        return None",
            "",
            "    def prune_steps(self, keep_last_n: int = 5, keep_task: bool = True):",
            "        if len(self.steps) <= keep_last_n:",
            "            return",
            "        new_steps = []",
            "        if keep_task and len(self.steps) > 0:",
            "            new_steps.append(self.steps[0])",
            "        new_steps.extend(self.steps[-keep_last_n:])",
            "        self.steps = new_steps\n\n"
        ]
        for m in methods:
            new_lines.append(m + "\n")
        continue
        
    if skip:
        if "def get_succinct_steps(self) -> list[dict]:" in line:
            skip = False
            new_lines.append(line)
        continue
        
    new_lines.append(line)

with open(filepath, "w") as f:
    f.writelines(new_lines)
print("✅ memory.py successfully repaired and enhanced (List approach)")