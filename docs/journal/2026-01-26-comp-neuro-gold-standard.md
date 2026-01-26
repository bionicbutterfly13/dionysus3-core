# Computational Neuroscience Gold Standard (Track 095) Complete

## Why
- Align the Dionysus cognitive architecture with gold-standard computational neuroscience principles from Anderson (2014).
- Provide theoretical grounding for attractor basins, ACT-R module mappings, and agent-based modeling.

## What Changed
- Created `AttractorBasinService` implementing Hopfield network dynamics with energy minimization and strong attractors.
- Annotated `ConsciousnessManager` with ACT-R module mappings (Observe -> Perceptual-Motor, Orient -> Declarative Memory, Decide -> Procedural Memory, Act -> Motor Module).
- Audited and annotated managed agents against ABM principles (Autonomy, Heterogeneity, Local Rules).
- Grounded `DynamicsService` in differential equations and integrate-and-fire neuron concepts.
- Linked `EFEEngine` probability and entropy calculations to random walk dynamics.
- Created comprehensive documentation structure in Quartz (Garden) with atomic concept pages for Hopfield, ACT-R, ABM, Hodgkin-Huxley, and Boolean Logic.

## Notes
- The system now has a formal mapping to established cognitive architectures.
- Attractor basin dynamics are now a first-class citizen in the service layer.
- Documentation includes specific mathematical references to Anderson (2014).
