from importlib.metadata import PackageNotFoundError, version as _version

from schematico.generator import run_generation
from schematico.discovery import run_discovery
from schematico.models import build_batch_model, model_from_dict, model_from_json
from schematico.providers import (
    DEFAULT_MODEL,
    SchematicoModel,
    get_llm_model,
)

try:
    __version__ = _version("schematico")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    "DEFAULT_MODEL",
    "SchematicoModel",
    "build_batch_model",
    "get_llm_model",
    "model_from_dict",
    "model_from_json",
    "run_generation",
    "run_discovery",
]
