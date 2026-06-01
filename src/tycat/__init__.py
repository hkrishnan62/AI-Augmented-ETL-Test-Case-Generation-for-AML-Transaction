"""TyCAT public API.

TyCAT (Typology-Conditioned AI Testing) generates AML ETL test cases aligned to
FinCEN's AML/CFT National Priorities (June 30, 2021), AMLA 2020 Section 6209,
and modern AI/model risk guidance (NIST AI RMF 1.0, NIST AI 600-1, and April 2026
interagency MRM guidance).
"""

from .llm_generator import (
    AnthropicBackend,
    LLMBackend,
    MockBackend,
    OpenAIBackend,
    TestSpec,
    generate_test_spec,
)
from .metrics import Mutant, fp_reduction_estimate, mutation_score, priority_coverage, typology_coverage
from .oracles import Oracle, OracleAssertion, OracleTemplate, get_oracle_template
from .synthetic_data import generate_demo, write_demo
from .typology_mapper import (
    FINCEN_PRIORITIES,
    TYPOLOGY_CATALOG,
    TypologyDef,
    all_typologies,
    map_priority_to_typologies,
    typologies_for_priorities,
)
from .validators import to_ge_suite, to_pandera_schema

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "AnthropicBackend",
    "FINCEN_PRIORITIES",
    "LLMBackend",
    "MockBackend",
    "Mutant",
    "OpenAIBackend",
    "Oracle",
    "OracleAssertion",
    "OracleTemplate",
    "TYPOLOGY_CATALOG",
    "TestSpec",
    "TypologyDef",
    "all_typologies",
    "fp_reduction_estimate",
    "generate_demo",
    "generate_test_spec",
    "get_oracle_template",
    "map_priority_to_typologies",
    "mutation_score",
    "priority_coverage",
    "to_ge_suite",
    "to_pandera_schema",
    "typologies_for_priorities",
    "typology_coverage",
    "write_demo",
]
