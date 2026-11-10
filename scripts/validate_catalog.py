#!/usr/bin/env python3
"""Validação estrutural do catálogo sem dependências externas além de PyYAML."""
from pathlib import Path
from datetime import date
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "company", "product", "category", "benefit", "eligibility", "links", "verification"}
BENEFIT_FIELDS = {"type", "description", "discount_percent", "credit_amount", "currency", "duration", "base_price"}
ELIGIBILITY_FIELDS = {"education_levels", "country_status", "verification", "restrictions"}
VERIFICATION_FIELDS = {"status", "checked_on", "brazil_eligibility_confirmed"}
ALLOWED_STATUS = {"confirmed_official", "pending", "expired", "discontinued"}

def validate(path):
    errors = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{path}: erro ao carregar YAML: {exc}"], None
    if not isinstance(data, dict):
        return [f"{path}: raiz deve ser um mapa"], None
    for field in sorted(REQUIRED - data.keys()):
        errors.append(f"{path}: campo ausente: {field}")
    for section, fields in [("benefit", BENEFIT_FIELDS), ("eligibility", ELIGIBILITY_FIELDS), ("verification", VERIFICATION_FIELDS)]:
        value = data.get(section)
        if not isinstance(value, dict):
            errors.append(f"{path}: {section} deve ser mapa")
            continue
        for field in sorted(fields - value.keys()):
            errors.append(f"{path}: {section}.{field} ausente")
    benefit = data.get("benefit", {})
    if isinstance(benefit, dict):
        pct = benefit.get("discount_percent")
        if pct is not None and (isinstance(pct, bool) or not isinstance(pct, (int, float)) or not 0 < pct <= 100):
            errors.append(f"{path}: discount_percent inválido")
        if benefit.get("type") == "credit" and benefit.get("credit_amount") is None:
            errors.append(f"{path}: crédito sem valor")
    links = data.get("links")
    if not isinstance(links, dict) or not isinstance(links.get("official"), str) or not links["official"].startswith("https://"):
        errors.append(f"{path}: links.official deve ser URL HTTPS")
    verification = data.get("verification", {})
    if isinstance(verification, dict):
        if verification.get("status") not in ALLOWED_STATUS:
            errors.append(f"{path}: verification.status inválido")
        if not isinstance(verification.get("brazil_eligibility_confirmed"), bool):
            errors.append(f"{path}: brazil_eligibility_confirmed deve ser booleano")
        checked = verification.get("checked_on")
        if not isinstance(checked, (date, str)):
            errors.append(f"{path}: checked_on deve ser data ISO")
        else:
            try:
                date.fromisoformat(str(checked))
            except ValueError:
                errors.append(f"{path}: checked_on inválida")
    return errors, data.get("id")

def main():
    paths = sorted((ROOT / "data" / "benefits").glob("*.yaml"))
    if not paths:
        print("ERRO: nenhum benefício encontrado", file=sys.stderr)
        return 1
    errors, ids = [], set()
    for path in paths:
        issues, identifier = validate(path)
        errors.extend(issues)
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{path}: id inválido")
        elif identifier in ids:
            errors.append(f"{path}: id duplicado: {identifier}")
        else:
            ids.add(identifier)
    for error in errors:
        print("ERRO:", error, file=sys.stderr)
    print(f"{len(paths)} registros verificados; {len(errors)} erros")
    return int(bool(errors))

if __name__ == "__main__":
    raise SystemExit(main())
