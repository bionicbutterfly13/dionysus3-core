import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from api.models.marketing import Product, Module, Lesson, Step, Obstacle, Solution, Avatar
import json

def build_ias_graph() -> Product:
    """
    Constructs the 3x3x3 Dependency Graph for the Inner Architect System.
    Structure: 3 Phases -> 3 Lessons/Phase -> 3 Steps/Lesson -> 3 Obstacles/Step -> 1 Solution/Obstacle
    """
    
    # --- PHASE 1: REVELATION ---
    
    # Lesson 1: Breakthrough Mapping
    # Step 1: Predictive Coding
    obs1_1_1 = Obstacle(
        name="The 'Just Me' Fallacy",
        description="Believing the pattern is your personality.",
        solution=Solution(content="Show the prediction error (it's a mechanism, not you).")
    )
    # (Leaving other obstacles as generic placeholders for now to demonstrate structure)
    step1_1 = Step(
        order=1, name="Predictive Coding", 
        instruction="Map the prediction.", 
        obstacles=[obs1_1_1, 
                   Obstacle(name="TBD 2", description="...", solution=Solution(content="...")),
                   Obstacle(name="TBD 3", description="...", solution=Solution(content="..."))]
    )
    
    # Step 2: Representational Redescription
    step1_2 = Step(
        order=2, name="Representational Redescription", 
        instruction="Make the unconscious conscious.",
        obstacles=[Obstacle(name="TBD", description="...", solution=Solution(content="..."))] * 3
    )

    # Step 3: Structural Learning
    step1_3 = Step(
        order=3, name="Structural Learning", 
        instruction="Update the deep architecture.",
        obstacles=[Obstacle(name="TBD", description="...", solution=Solution(content="..."))] * 3
    )
    
    l1 = Lesson(
        title="Breakthrough Mapping", 
        key_concept="Predictive Coding",
        action_step="Map the Sabotage Loop",
        promise="Expose the hidden loop",
        transformation="Unknowingly held back -> Crystal-clear internal map",
        steps=[step1_1, step1_2, step1_3]
    )
    
    # Lesson 2: MOSAEIC Method
    l2 = Lesson(
        title="MOSAEIC Method", 
        key_concept="Nervous System Regulation", 
        action_step="Regulate in Real-Time", 
        promise="Dissolve anxiety instantly",
        transformation="Freeze/Perform -> Calm/Command",
        steps=[Step(order=i, name=f"MOSAEIC Step {i}", instruction="...", obstacles=[Obstacle(name="TBD", description="...", solution=Solution(content="..."))]*3) for i in range(1, 4)]
    )
    
    # Lesson 3: Replay Loop Breaker
    # Known Mechanics from script: Unresolved Piece, Signal Check, Testing the Armor
    l3_step1 = Step(order=1, name="Identify Unresolved Piece", instruction="Find the question brain is asking.", 
                    obstacles=[Obstacle(name="Obs 1", description="...", solution=Solution(content="..."))]*3)
    l3_step2 = Step(order=2, name="Signal Check", instruction="Prove safety to nervous system.", 
                    obstacles=[Obstacle(name="Obs 1", description="...", solution=Solution(content="..."))]*3)
    l3_step3 = Step(order=3, name="Testing the Armor", instruction="Test letting go of the edge.", 
                    obstacles=[Obstacle(name="Obs 1", description="...", solution=Solution(content="..."))]*3)

    l3 = Lesson(
        title="Replay Loop Breaker",
        key_concept="Signal Check",
        action_step="Close the Loop",
        promise="Stop the nightly chatter",
        transformation="Mental Torture -> Complete Resolution",
        steps=[l3_step1, l3_step2, l3_step3]
    )

    p1 = Module(
        title="Phase 1: Revelation", 
        promise="Stop the Bleeding", 
        lessons=[l1, l2, l3]
    )
    
    # --- PHASE 2: REPATTERNING ---
    # Lesson 4: Conviction Gauntlet
    l4 = Lesson(title="Conviction Gauntlet", key_concept="Mismatch Experiments", action_step="Disprove Beliefs", transformation="Old Loop -> new Identity Spark", steps=[])
    # Lesson 5: Perspective Matrix
    l5 = Lesson(title="Perspective Matrix", key_concept="Dual Perspectives", action_step="Protector vs Visionary Dialogue", transformation="Paralyzed -> Strategic Advantage", steps=[])
    # Lesson 6: Vision Accelerator
    l6 = Lesson(title="Vision Accelerator", key_concept="Identity Design", action_step="Contrast & Construct", transformation="Outdated Self-Image -> Future Identity", steps=[])
    
    p2 = Module(title="Phase 2: Repatterning", promise="Recode the Loop", lessons=[l4, l5, l6])

    # --- PHASE 3: ABILIZATION ---
    # Lesson 7: Habit Harmonizer
    l7 = Lesson(title="Habit Harmonizer", key_concept="Protective Relapse", action_step="Track Feedback", transformation="Worry -> Confidence", steps=[])
    # Lesson 8: Execution Engine
    l8 = Lesson(title="Execution Engine", key_concept="Anticipatory Planning", action_step="Plan Responses", transformation="Burnout -> Sustainable Action", steps=[])
    # Lesson 9: Growth Anchor
    l9 = Lesson(title="Growth Anchor", key_concept="Ecosystem Design", action_step="Curate Support", transformation="Isolation -> Connected Evolution", steps=[])
    
    p3 = Module(title="Phase 3: Stabilization", promise="Embed the Identity", lessons=[l7, l8, l9])
    
    # --- PRODUCT ---
    avatar = Avatar(
        name="The Analytical Empath",
        pain_points=["Replay Loop", "Hollow Success"],
        desires=["Integrated Identity", "Peace"],
        obstacles=["Willpower", "Analysis Paralysis"],
        old_way="The Split Self",
        new_way="Identity Architecture"
    )

    product = Product(
        name="The Inner Architect System",
        avatar=avatar,
        promise="Rebuild internal architecture.",
        mechanism="Predictive Identity Recalibration",
        modules=[p1, p2, p3]
    )
    
    return product

if __name__ == "__main__":
    ias = build_ias_graph()
    print(f"Graph Built: {ias.name}")
    print(f"Phases: {len(ias.modules)}")
    for m in ias.modules:
        print(f"\n{m.title}")
        for l in m.lessons:
            print(f"  - {l.title} ({l.transformation})")
            if l.steps:
                for s in l.steps:
                    print(f"    * Step {s.order}: {s.name}")
                    for o in s.obstacles:
                         # Just print text for first one to keep output clean
                         pass 
                         
    print("\n[VERIFICATION] JSON Structure (Snippet):")
    # Dump first lesson fully to verify 3x3x3 structure
    print(json.dumps(ias.modules[0].lessons[0].model_dump(), indent=2))
