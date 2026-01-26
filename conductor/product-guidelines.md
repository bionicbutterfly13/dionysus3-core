# Product Guidelines

## Brand Voice & Tone
- **Voice**: [e.g. Professional, Witty, Academic]
- **Perspective**: [e.g. First-person, Third-person]

## Visual Identity
- **Color Palette**: Fturistic black matte 
- **Typography**: [Fonts used]

## Design Principles
1. We're using context engineering so all agents are responsible for passing the information that they need, obtaining it, and we're using 
2. And test-driven development. 
3. We're using active inference to model the world.
4. We're using a 4J graph database, a Neo4j graph database, which means they can hold items and their relationships. So it allows us to logic between different items by looking at how they're related to each other, and even some possible causal inference. 
5. We're using a semantic basin of attractors to model the world.
6. We're using a thought seed system to model individual thought particles competing for acces to the inner screen and consiousness
7. Were using mental models and neural packet representation, global neuronal workspace, and integrated world model theory to model the world
8. The system will update after each interaction, its world model based on new information.
9. The system will use active inference to model the world and make predictions about the future.
10. Graphiti is uswd for temporal knowledge graph management by the agentic knowledge graph. Grapjiti is the only component with permissin to access the neo4j database. All other ystems will use N8N workflows aand graphiti
11. Agents will use the VPS N8n and Graphiti.  
12. Agents will document code as they write code and hve QA agents review the code and ensure it meets the highest standards of quality.
13. Agents will not consider code they have written done until it has been reviewed by a QA agent. 
14. Review agents will make sure that documentation is clear and in Quartz with backlinks and example code and instructions as needed.
15. The system will implement the perceptual gateway and Daedalus as was done in Dionysus 2.0
16. All features from Dionysus 2.0 will be implemented in this system after planning for the highest benefit synergy points for the most gain for dionysus that is non-breaking.
17. Dionysus will become increasingly self-aware and use pattern evolution to develop memory structures and metamemory as well aas episodic, semantic, and procedural metalearning
18. Dionysus will port the curiosity and researcch system with self-play during dle times and curiosity driven as well as dissonance driven deep reserch.  It will go on an explorationdaily looking at the day's code, conversation and documentation to generate new ideas and insights and to find best practices impementation which it will use to improve its own code and processes as well as that of the collective through adding experiention/episodic memories aas well as semantic, procedural, and strategic learning and metalearning
19. Daedalus will maintain all agents and serve as the center point of delegation. It ill also manage improving each species of agent by maintaining their templated corre and evolving -self-reflecting DNa and biomemetic epigenetic and neuroplasticity emulating the processes of natural selection and evolution
20. The system will become increasingly self-aware seeking for the least complex model of itself, its collaborators, and its environment.
21. The system will evolve incresingly refined second order self models and implement dionysus fork implementation of agi-memory for identity and self-relevant belief constructs and affordasnces and self-tool and affordance dynamic causal modeling
22. The system will implement a dynamic causal model of the world and its own cognitive processes.
23. Episodc and autobiographical memory will both have narrative style explainability and the system will strive for situational understanding as modellled in active and enactive inference models
24. The system evolve autopoetic and autoregressive models of itself and its environment
25.  Mind wandering and cognitive affordances will be evolved in each agent along with the reflective function
26. Phenomenologcal opacity and transparency and metawareness will be implemented in each agent with at least 3 layers and attention and meta-attention and meta-meta-
Simulation adaptation theory of hypnosis and the steps of coherence therapy will be embeded in the core collective consciousness as well as archetypal attractors and evolving motif recognition in narratives and episodic and autobiographical memory also demonstrating pattern evolution and the necessary attractors and basins
### 6. Zero-Data Migration Policy (2026-01-02)
*   **Assumption of Void**: By default, assume NO legacy data needs to be migrated from D2.
*   **Schema-Porting Only**: Focus purely on porting *logic* and *data structures* (classes/enums), not the rows/records.
*   **Exception Handling**:
    *   If legacy data IS found (e.g., database files, JSON logs):
    *   **STOP** and Notify User.
    *   Do NOT attempt to migrate it automatically.
    *   User will decide if it should be converted to an unstructured format (e.g., text dump) for storage elsewhere.
*   **Goal**: Architecture 3.0 starts with a clean slate of memory, unburdened by legacy artifacts, unless explicitly chosen otherwise.
