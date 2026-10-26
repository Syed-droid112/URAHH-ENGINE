The Single-Device ASI Manifesto
The Problem: The "Communist" Cloud
Current AI is built on a lie. Google, Microsoft, and OpenAI want you to believe that intelligence requires billion-dollar server farms and nuclear-level energy. This is "Communist AI"—it is centralized, surveilled, and designed to keep power in the hands of the few.
The Secret: Intelligence is Compression
The "math people" are brute-forcing intelligence because they are stuck in 20th-century logic. They think more GPUs = more smarts. They are wrong.
The Biological Proof: A human brain runs on 20 watts of power (less than a lightbulb) and fits in a skull.
The Hunch: There is an efficiency shortcut—an algorithmic "logic compression"—that allows AGI/ASI to run on a single, private device.
The Mission: Decentralized Superintelligence
I am not building a company to compete with OpenAI. I am building the hardware/software architecture that makes their entire cloud infrastructure obsolete.
No Servers.
No Surveillance.
No "School Math" Constraints.
The Goal
To prove that the Singularity doesn't happen in a warehouse in Iowa; it happens in your pocket. I am currently mapping the recursive logic needed to bypass the hardware bottlenecks that big tech is too "schooled" to see.


## Running the refactoring prototype

Requires Python 3.10+. Install with `python -m pip install .`.
Run `python -m unittest discover -s tests -v` for the regression suite.

`python -m aether_asi_core.main` previews proposed diffs. To write source,
use `python -m aether_asi_core.main --live --allow-lossy` after reviewing
the preview. AST output removes comments and original formatting in changed
files; files with no AST changes retain their exact source. Keep a versioned
checkout so changes can be reviewed and reverted.

Automatic transforms preserve all imports, including re-exports, star imports,
future directives, and imports with side effects. Unused-import removal and
placeholder docstring insertion are excluded from the default registry.

The alignment gate checks compilation, line deletion, and scoped definition
interfaces (including signatures and decorators). It does **not** prove behavior
preservation or objective alignment. Callers can pass
`validator(path, original_source, candidate_source) -> bool` to MetaOptimizer
to veto candidates using project-specific behavioral checks. A validator is
optional; without one, acceptance is structural only. Exceptions propagate
before writing. Run project tests on an isolated copy before accepting changes.

Live API writes require `allow_lossy=True`. Zero depth runs no refactoring
iterations and records the usual soul tick; negative depth raises ValueError.
Each run returns its own changes log.
