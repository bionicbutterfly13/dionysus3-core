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
        
        m1 = "    def __init__(self, system_prompt: str):\n"
        m2 = "        self.system_prompt: SystemPromptStep = SystemPromptStep(system_prompt=system_prompt)\n"
        m3 = "        self.steps: list[TaskStep | ActionStep | PlanningStep] = []\n"
        m4 = "        self.assets: dict[str, Any] = {}\n\n"
        
        m5 = "    def reset(self):\n"
        m6 = "        self.steps = []\n"
        m7 = "        self.assets = {}\n\n"
        
        m8 = "    def save_asset(self, name: str, value: Any) -> str:\n"
        m9 = "        self.assets[name] = value\n"
        m10 = "        return f\"{{{{asset:{name}}}}}\"\n\n"
        
        m11 = "    def get_asset(self, handle: str) -> Any:\n"
        m12 = "        if isinstance(handle, str) and handle.startswith(\"{{asset:\") and handle.endswith(\"}}\"):\n"
        m13 = "            name = handle[8:-2]\n"
        m14 = "            return self.assets.get(name)\n"
        m15 = "        return None\n\n"
        
        m16 = "    def prune_steps(self, keep_last_n: int = 5, keep_task: bool = True):\n"
        m17 = "        if len(self.steps) <= keep_last_n:\n"
        m18 = "            return\n"
        m19 = "        new_steps = []\n"
        m20 = "        if keep_task and len(self.steps) > 0:\n"
        m21 = "            new_steps.append(self.steps[0])\n"
        m22 = "        new_steps.extend(self.steps[-keep_last_n:])\n"
        m23 = "        self.steps = new_steps\n\n"
        
        new_lines.extend([m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15, m16, m17, m18, m19, m20, m21, m22, m23])
        continue
        
    if skip:
        if "def get_succinct_steps(self) -> list[dict]:" in line:
            skip = False
            new_lines.append(line)
        continue
        
    new_lines.append(line)

with open(filepath, "w") as f:
    f.writelines(new_lines)
print("✅ memory.py successfully repaired and enhanced")
