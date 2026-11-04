"""Run Echo with Original v8 and ZeroSugar v8: same CLI, scope, budgets and artifacts as run_agent.py.

--resume is not supported for v8 workflows; it still resumes saved v7 checkpoints with v7 code.
"""

import sys

import run_agent
from agents.original_v8 import OriginalAgentV8
from agents.zero_sugar_v8 import ZeroSugarAgentV8

run_agent.OriginalAgent, run_agent.ZeroSugarAgent = OriginalAgentV8, ZeroSugarAgentV8

if __name__ == "__main__":
    sys.exit(run_agent.main())
