from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .pipeline import PartnerIntegrationPipeline


def load_payload(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Feed mock payloads through the partner integration pipeline.")
    parser.add_argument("--partner", required=True, help="Partner code (e.g., hhru, habr, generic)")
    parser.add_argument("--external-id", required=True, help="External vacancy identifier")
    parser.add_argument("--file", type=Path, required=True, help="Path to mock JSON payload")
    parser.add_argument("--request-id", help="Optional request identifier")
    parser.add_argument("--endpoint", help="Optional endpoint description")
    args = parser.parse_args()

    payload = load_payload(args.file)

    pipeline = PartnerIntegrationPipeline()
    endpoint = args.endpoint or f"mock:{args.file.stem}"
    result = pipeline.process(
        partner_code=args.partner,
        external_id=args.external_id,
        payload=payload,
        request_id=args.request_id,
        endpoint=endpoint,
    )

    print(
        json.dumps(
            {
                "status": result.status,
                "issues": [
                    {"field": issue.field, "code": issue.code, "message": issue.message}
                    for issue in (result.validation.issues if result.validation else [])
                ],
                "storage": getattr(result.storage, "reason", None),
                "core_snapshot": pipeline.storage_gateway.core_records,
                "staging_snapshot": pipeline.storage_gateway.staging_records,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
