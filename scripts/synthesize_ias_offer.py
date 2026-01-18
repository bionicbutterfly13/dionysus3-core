import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from api.models.marketing import Product, Module, Lesson, Avatar, Offer, Bonus, KeyPhrase
import json

def create_ias_product() -> Offer:
    # 1. Avatar with Key Phrases
    avatar = Avatar(
        name="The Analytical Empath",
        pain_points=["Replay Loop", "Hollow Success", "Performing vs. Panicking"],
        desires=["Integrated Identity", "Calm Command", "Sleep in Peace"],
        obstacles=["Willpower", "Therapy that just talks", "Analysis Paralysis"],
        old_way="The Split Self (Performing on Autopilot)",
        new_way="Identity Architecture (Predictive Recalibration)",
        core_identity_statement="I am the adult in the room, but I'm suffocating.",
        key_phrases=[
            KeyPhrase(phrase="Hollow Success", category="pain", resonance_score=0.9),
            KeyPhrase(phrase="The Replay Loop", category="pain", resonance_score=1.0),
            KeyPhrase(phrase="Vigilant Sentinel", category="identity", resonance_score=0.95),
            KeyPhrase(phrase="Margin of Freedom", category="desire", resonance_score=0.85)
        ]
    )
    
    # 2. Curriculum (Phase 1)
    l1 = Lesson(title="Breakthrough Mapping", key_concept="Predictive Coding", action_step="Map the Sabotage Loop", promise="Expose the hidden loop")
    l2 = Lesson(title="MOSAEIC Method", key_concept="Nervous System Regulation", action_step="Regulate in Real-Time", promise="Dissolve anxiety instantly")
    l3 = Lesson(title="Replay Loop Breaker", key_concept="Signal Check", action_step="Close the Loop", promise="Stop the nightly chatter")
    
    p1 = Module(title="Phase 1: Revelation", promise="Stop the Bleeding", lessons=[l1, l2, l3])
    
    # 3. Product
    product = Product(
        name="The Inner Architect System",
        avatar=avatar,
        promise="Rebuild your internal architecture from the ground up.",
        mechanism="Predictive Identity Recalibration",
        modules=[p1]
    )
    
    # 4. Bonuses
    bonuses = [
        Bonus(title="Hidden Protector Style Quiz", description="Find your unique self-sabotage style", value=250.0, delivery_format="Typeform"),
        Bonus(title="60-Second Coherence Audio", description="Immediate regulation before board meetings", value=197.0, delivery_format="MP3")
    ]
    
    # 5. Offer ($97 Tripwire)
    offer = Offer(
        name="The 48-Hour Loop Breaker",
        product_ref_id=product.id,
        included_modules_ids=[p1.id],
        included_bonuses=bonuses,
        price=97.0,
        guarantee="14-Day Full Refund: If you don't feel the shift, I'll refund you.",
        upsell_hint="Face-to-Face Architecture Day ($1500)"
    )
    return offer

def synthesize_template(offer: Offer, product: Product) -> SalesTemplate:
    # Logic to map Offer -> Sales Template
    shift_text = f"From {product.avatar.old_way} -> {product.avatar.new_way}"
    
    steps = []
    # In a real scenario, we'd look up the modules by ID from the product
    # For now, we assume product.modules[0] corresponds to the offer
    for i, lesson in enumerate(product.modules[0].lessons, 1):
        steps.append({
            "step": str(i),
            "title": lesson.title,
            "desc": lesson.promise or lesson.action_step
        })
        
    modules_list = []
    for i, lesson in enumerate(product.modules[0].lessons, 1):
        modules_list.append({
            "title": f"Module {i}: {lesson.title}",
            "desc": f"Learn {lesson.key_concept} to {lesson.action_step}"
        })
        
    bonus_list = []
    for b in offer.included_bonuses:
        bonus_list.append({
            "title": f"{b.title} (Value: ${b.value})",
            "desc": b.description
        })
        
    return SalesTemplate(
        headline=f"How To Stop {product.avatar.pain_points[0]} Without {product.avatar.obstacles[0]}",
        promise=f"The {product.mechanism} method to {product.avatar.desires[2]}",
        mechanism=product.mechanism,
        program_name=offer.name,
        core_benefit="Reclaim 15+ hours/week of mental bandwidth",
        pain_points=product.avatar.pain_points,
        the_shift=shift_text,
        process_steps=steps,
        modules=modules_list,
        bonuses=bonus_list,
        price=f"${offer.price}",
        guarantee=offer.guarantee,
        upsell_hint=offer.upsell_hint
    )

if __name__ == "__main__":
    offer = create_ias_product()
    # Reconstruct product context (in real system this would be a DB lookup)
    product_context = Product(
        id=offer.product_ref_id,
        name="Inner Architect System",
        avatar=Avatar(
            name="Analytical Empath", pain_points=["Loop"], desires=["Peace"], obstacles=["Willpower"], 
            old_way="Split Self", new_way="Identity Architecture"
        ),
        promise="Rebuild", mechanism="Predictive Recalibration", modules=extract_modules_from_offer(offer) # Mock
    )
    
    # Actually we just use the creation function data for the demo
    # Redefining specifically for the template synthesis
    avatar = Avatar(
            name="The Analytical Empath",
            pain_points=["The Replay Loop", "Hollow Success", "Performing vs. Panicking"],
            desires=["Integrated Identity", "Calm Command", "Sleep in Peace"],
            obstacles=["Willpower", "Therapy that just talks", "Analysis Paralysis"],
            old_way="The Split Self (Performing on Autopilot)",
            new_way="Identity Architecture (Predictive Recalibration)"
    )
    l1 = Lesson(title="Breakthrough Mapping", key_concept="Predictive Coding", action_step="Map the Sabotage Loop", promise="Expose the hidden loop")
    l2 = Lesson(title="MOSAEIC Method", key_concept="Nervous System Regulation", action_step="Regulate in Real-Time", promise="Dissolve anxiety instantly")
    l3 = Lesson(title="Replay Loop Breaker", key_concept="Signal Check", action_step="Close the Loop", promise="Stop the nightly chatter")
    p1 = Module(title="Phase 1: Revelation", promise="Stop the Bleeding", lessons=[l1, l2, l3])
    product = Product(
        name="The Inner Architect System",
        avatar=avatar,
        promise="Rebuild your internal architecture from the ground up.",
        mechanism="Predictive Identity Recalibration",
        modules=[p1]
    )

    template = synthesize_template(offer, product)
    
    print(f"\n--- QUERY: What is the total value of the {offer.name}? ---")
    print(f"Total Value: ${offer.get_total_value()} (Price: ${offer.price})")
    
    print(f"\n--- QUERY: Give me the bonuses and their resonance ---")
    for b in offer.included_bonuses:
        print(f"- {b.title}: {b.description} (Value: ${b.value})")

    print("\n--- GENERATED SALES TEMPLATE ---\n")
    print(template.render_markdown())
