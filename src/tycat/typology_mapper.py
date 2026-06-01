"""Mapping between FinCEN priorities and AML typologies.

Regulatory note:
- FinCEN published 8 National AML/CFT Priorities on June 30, 2021.
- AMLA 2020 Section 6209 directs Treasury to establish AML innovation/testing
  standards; TyCAT provides a reproducible testing taxonomy aligned to this.
"""

from __future__ import annotations

from dataclasses import dataclass


FINCEN_PRIORITIES: dict[str, str] = {
    "P1_corruption": "Corruption",
    "P2_cybercrime_virtual_currency": "Cybercrime and Virtual Currency",
    "P3_terrorist_financing": "Terrorist Financing",
    "P4_fraud": "Fraud",
    "P5_transnational_criminal_org": "Transnational Criminal Organization Activity",
    "P6_drug_trafficking": "Drug Trafficking Organization Activity",
    "P7_human_trafficking_smuggling": "Human Trafficking and Human Smuggling",
    "P8_proliferation": "Proliferation Financing",
}


@dataclass(frozen=True)
class TypologyDef:
    """A normalized typology definition used by generators and validators."""

    code: str
    name: str
    description: str
    etl_dimensions: tuple[str, ...]


TYPOLOGY_CATALOG: dict[str, TypologyDef] = {
    "shell_company": TypologyDef(
        "shell_company",
        "Shell Company Laundering",
        "Layered wire movement through opaque legal entities.",
        ("entity", "counterparty", "jurisdiction", "amount", "time"),
    ),
    "pep_layering": TypologyDef(
        "pep_layering",
        "PEP Layering",
        "Layering around politically exposed persons and associates.",
        ("customer_risk", "counterparty", "amount", "time"),
    ),
    "real_estate_layering": TypologyDef(
        "real_estate_layering",
        "Real Estate Layering",
        "High-value purchases and resale to disguise proceeds.",
        ("merchant", "amount", "asset", "time"),
    ),
    "crypto_layering": TypologyDef(
        "crypto_layering",
        "Crypto Layering",
        "Rapid transfer to mixing/exchange endpoints.",
        ("counterparty", "channel", "amount", "time"),
    ),
    "ransomware_payouts": TypologyDef(
        "ransomware_payouts",
        "Ransomware Payouts",
        "Urgent transfers linked to extortion incidents.",
        ("channel", "counterparty", "amount", "time"),
    ),
    "mule_account": TypologyDef(
        "mule_account",
        "Mule Account",
        "One source account fans out to many recipients.",
        ("graph", "counterparty", "time", "amount"),
    ),
    "small_value_funnel": TypologyDef(
        "small_value_funnel",
        "Small Value Funnel",
        "Many small incoming payments to one destination.",
        ("graph", "counterparty", "time", "amount"),
    ),
    "hawala_proxy": TypologyDef(
        "hawala_proxy",
        "Hawala Proxy",
        "Informal value transfer with offsetting flows.",
        ("graph", "channel", "jurisdiction", "time"),
    ),
    "ngo_misuse": TypologyDef(
        "ngo_misuse",
        "NGO Misuse",
        "Diversion of charitable funding patterns.",
        ("entity", "counterparty", "jurisdiction", "amount"),
    ),
    "account_takeover": TypologyDef(
        "account_takeover",
        "Account Takeover",
        "Compromised account used for rapid anomalous spending.",
        ("behavior", "channel", "time", "amount"),
    ),
    "first_party_fraud": TypologyDef(
        "first_party_fraud",
        "First Party Fraud",
        "Customer-originated fraud and synthetic identity behavior.",
        ("identity", "behavior", "amount", "time"),
    ),
    "elder_financial_abuse": TypologyDef(
        "elder_financial_abuse",
        "Elder Financial Abuse",
        "Unauthorized extraction from vulnerable customer accounts.",
        ("customer_risk", "behavior", "amount", "time"),
    ),
    "bulk_cash_smurfing": TypologyDef(
        "bulk_cash_smurfing",
        "Bulk Cash Smurfing",
        "Distributed sub-threshold cash placements.",
        ("channel", "amount", "time", "branch"),
    ),
    "trade_based_ml": TypologyDef(
        "trade_based_ml",
        "Trade-Based Money Laundering",
        "Mispriced cross-border trade and invoice discrepancies.",
        ("trade", "jurisdiction", "amount", "counterparty"),
    ),
    "professional_money_launderer": TypologyDef(
        "professional_money_launderer",
        "Professional Money Launderer",
        "Brokered laundering service spanning clients and geographies.",
        ("graph", "jurisdiction", "counterparty", "time"),
    ),
    "bulk_cash_structuring": TypologyDef(
        "bulk_cash_structuring",
        "Bulk Cash Structuring",
        "Repeated cash deposits just under reporting thresholds.",
        ("channel", "amount", "time", "account"),
    ),
    "funnel_account": TypologyDef(
        "funnel_account",
        "Funnel Account",
        "Aggregation account receiving many unrelated deposits.",
        ("graph", "counterparty", "amount", "time"),
    ),
    "casino_layering": TypologyDef(
        "casino_layering",
        "Casino Layering",
        "Funds converted through gaming chips and rapid redemption.",
        ("merchant", "channel", "amount", "time"),
    ),
    "small_value_recurring": TypologyDef(
        "small_value_recurring",
        "Small Value Recurring",
        "Recurring low-value debits with hidden beneficiary intent.",
        ("counterparty", "amount", "time", "frequency"),
    ),
    "hotel_transport_pattern": TypologyDef(
        "hotel_transport_pattern",
        "Hotel and Transport Pattern",
        "Travel-heavy spend associated with trafficking indicators.",
        ("merchant", "location", "time", "amount"),
    ),
    "minor_account": TypologyDef(
        "minor_account",
        "Minor Account Misuse",
        "Use of youth-linked accounts as pass-through channels.",
        ("customer_risk", "graph", "amount", "time"),
    ),
    "sanctioned_jurisdiction": TypologyDef(
        "sanctioned_jurisdiction",
        "Sanctioned Jurisdiction Exposure",
        "Outbound wires to comprehensively sanctioned countries.",
        ("jurisdiction", "channel", "amount", "counterparty"),
    ),
    "dual_use_goods_tbml": TypologyDef(
        "dual_use_goods_tbml",
        "Dual-Use Goods TBML",
        "Trade finance involving controlled or dual-use goods.",
        ("trade", "goods", "jurisdiction", "amount"),
    ),
    "front_company": TypologyDef(
        "front_company",
        "Front Company Activity",
        "Commercial facade masking illicit source and destination of funds.",
        ("entity", "trade", "counterparty", "amount"),
    ),
}


_PRIORITY_TO_TYPOLOGY: dict[str, tuple[str, str, str]] = {
    "P1_corruption": ("shell_company", "pep_layering", "real_estate_layering"),
    "P2_cybercrime_virtual_currency": (
        "crypto_layering",
        "ransomware_payouts",
        "mule_account",
    ),
    "P3_terrorist_financing": ("small_value_funnel", "hawala_proxy", "ngo_misuse"),
    "P4_fraud": ("account_takeover", "first_party_fraud", "elder_financial_abuse"),
    "P5_transnational_criminal_org": (
        "bulk_cash_smurfing",
        "trade_based_ml",
        "professional_money_launderer",
    ),
    "P6_drug_trafficking": (
        "bulk_cash_structuring",
        "funnel_account",
        "casino_layering",
    ),
    "P7_human_trafficking_smuggling": (
        "small_value_recurring",
        "hotel_transport_pattern",
        "minor_account",
    ),
    "P8_proliferation": (
        "sanctioned_jurisdiction",
        "dual_use_goods_tbml",
        "front_company",
    ),
}


def map_priority_to_typologies(priority: str) -> list[TypologyDef]:
    """Return typologies mapped to a single FinCEN priority key."""

    if priority not in _PRIORITY_TO_TYPOLOGY:
        raise KeyError(f"Unknown priority: {priority}")
    return [TYPOLOGY_CATALOG[code] for code in _PRIORITY_TO_TYPOLOGY[priority]]


def typologies_for_priorities(priorities: list[str]) -> list[TypologyDef]:
    """Return de-duplicated typologies for a list of priority keys."""

    seen: set[str] = set()
    ordered: list[TypologyDef] = []
    for priority in priorities:
        for typology in map_priority_to_typologies(priority):
            if typology.code not in seen:
                seen.add(typology.code)
                ordered.append(typology)
    return ordered


def all_typologies() -> list[TypologyDef]:
    """Return all typologies in catalog order."""

    return list(TYPOLOGY_CATALOG.values())
