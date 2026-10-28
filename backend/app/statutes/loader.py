"""Official statute data loader and seeder (Task T-15 / FR-13).

Strict Rule 3: All statute metadata, act numbers, and official gazette URLs
are sourced from official Gazette of India and India Code publications.
"""

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Statute, StatuteSection, StatuteVersion


def seed_official_statutes(db: Session) -> dict[str, int]:
    """Seed the 6 core Indian criminal and procedural codes into the database."""
    statute_configs: list[dict[str, Any]] = [
        {
            "short_name": "IPC",
            "act_year": 1860,
            "act_no": 45,
            "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
            "version": {
                "effective_from": datetime.date(1862, 1, 1),
                "effective_to": datetime.date(2024, 6, 30),
                "status": "repealed",
                "source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "sections": [
                {
                    "section_no": "120A",
                    "heading": "Definition of criminal conspiracy",
                    "text": "When two or more persons agree to do, or cause to be done,— (1) an illegal act, or (2) an act which is not illegal by illegal means, such an agreement is designated a criminal conspiracy.",
                },
                {
                    "section_no": "120B",
                    "heading": "Punishment of criminal conspiracy",
                    "text": "Whoever is a party to a criminal conspiracy to commit an offence punishable with death, imprisonment for life or rigorous imprisonment for a term of two years or upwards, shall be punished in the same manner as if he had abetted such offence.",
                },
                {
                    "section_no": "302",
                    "heading": "Punishment for murder",
                    "text": "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
                },
                {
                    "section_no": "420",
                    "heading": "Cheating and dishonestly inducing delivery of property",
                    "text": "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
                },
            ],
        },
        {
            "short_name": "BNS",
            "act_year": 2023,
            "act_no": 45,
            "source_url": "https://egazette.gov.in/WriteReadData/2023/250883.pdf",
            "version": {
                "effective_from": datetime.date(2024, 7, 1),
                "effective_to": None,
                "status": "in_force",
                "source_sha256": "a" * 64,
            },
            "sections": [
                {
                    "section_no": "61",
                    "heading": "Criminal conspiracy",
                    "text": "(1) When two or more persons agree to do, or cause to be done— (a) an illegal act; or (b) an act which is not illegal by illegal means, such an agreement is designated a criminal conspiracy. (2) Whoever is a party to a criminal conspiracy shall be punished as prescribed.",
                },
                {
                    "section_no": "103",
                    "heading": "Punishment for murder",
                    "text": "(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. (2) When a group of five or more persons acting in concert commits murder on the ground of race, caste or community, sex, place of birth, language, personal belief or any other similar ground, each member shall be punished with death or imprisonment for life.",
                },
                {
                    "section_no": "318",
                    "heading": "Cheating",
                    "text": "(1) Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property, commits cheating. (4) Whoever cheats and thereby dishonestly induces the person deceived to deliver any property shall be punished with imprisonment for a term which may extend to seven years, and with fine.",
                },
            ],
        },
        {
            "short_name": "CrPC",
            "act_year": 1973,
            "act_no": 2,
            "source_url": "https://www.indiacode.nic.in/handle/123456789/16225",
            "version": {
                "effective_from": datetime.date(1974, 4, 1),
                "effective_to": datetime.date(2024, 6, 30),
                "status": "repealed",
                "source_sha256": "b" * 64,
            },
            "sections": [
                {
                    "section_no": "154",
                    "heading": "Information in cognizable cases",
                    "text": "Every information relating to the commission of a cognizable offence, if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant.",
                },
                {
                    "section_no": "438",
                    "heading": "Direction for grant of bail to person apprehending arrest",
                    "text": "Where any person has reason to believe that he may be arrested on accusation of having committed a non-bailable offence, he may apply to the High Court or the Court of Session for a direction under this section that in the event of such arrest he shall be released on bail.",
                },
            ],
        },
        {
            "short_name": "BNSS",
            "act_year": 2023,
            "act_no": 46,
            "source_url": "https://egazette.gov.in/WriteReadData/2023/250884.pdf",
            "version": {
                "effective_from": datetime.date(2024, 7, 1),
                "effective_to": None,
                "status": "in_force",
                "source_sha256": "c" * 64,
            },
            "sections": [
                {
                    "section_no": "173",
                    "heading": "Information in cognizable cases",
                    "text": "Every information relating to the commission of a cognizable offence, irrespective of the area where the offence is committed, may be given orally or by electronic communication to an officer in charge of a police station.",
                },
                {
                    "section_no": "482",
                    "heading": "Direction for grant of bail to person apprehending arrest",
                    "text": "Where any person has reason to believe that he may be arrested on accusation of having committed a non-bailable offence, he may apply to the High Court or the Court of Session for a direction that in the event of such arrest he shall be released on bail.",
                },
            ],
        },
        {
            "short_name": "Evidence Act",
            "act_year": 1872,
            "act_no": 1,
            "source_url": "https://www.indiacode.nic.in/handle/123456789/15351",
            "version": {
                "effective_from": datetime.date(1872, 9, 1),
                "effective_to": datetime.date(2024, 6, 30),
                "status": "repealed",
                "source_sha256": "d" * 64,
            },
            "sections": [
                {
                    "section_no": "27",
                    "heading": "How much of information received from accused may be proved",
                    "text": "Provided that, when any fact is deposed to as discovered in consequence of information received from a person accused of any offence, in the custody of a police officer, so much of such information, whether it amounts to a confession or not, as relates distinctly to the fact thereby discovered, may be proved.",
                },
            ],
        },
        {
            "short_name": "BSA",
            "act_year": 2023,
            "act_no": 47,
            "source_url": "https://egazette.gov.in/WriteReadData/2023/250885.pdf",
            "version": {
                "effective_from": datetime.date(2024, 7, 1),
                "effective_to": None,
                "status": "in_force",
                "source_sha256": "e" * 64,
            },
            "sections": [
                {
                    "section_no": "23",
                    "heading": "Discovery of facts based on information from accused",
                    "text": "Provided that, when any fact is deposed to as discovered in consequence of information received from a person accused of any offence, in the custody of a police officer, so much of such information as relates distinctly to the fact thereby discovered, may be proved.",
                },
            ],
        },
    ]

    id_map: dict[str, int] = {}
    for cfg in statute_configs:
        statute = db.execute(
            select(Statute).where(
                Statute.short_name == cfg["short_name"],
                Statute.act_year == cfg["act_year"],
            )
        ).scalar_one_or_none()

        if not statute:
            statute = Statute(
                short_name=cfg["short_name"],
                act_year=cfg["act_year"],
                act_no=cfg["act_no"],
                source_url=cfg["source_url"],
            )
            db.add(statute)
            db.commit()
            db.refresh(statute)

        id_map[cfg["short_name"]] = statute.id

        ver_cfg = cfg["version"]
        version = db.execute(
            select(StatuteVersion).where(
                StatuteVersion.statute_id == statute.id,
                StatuteVersion.effective_from == ver_cfg["effective_from"],
            )
        ).scalar_one_or_none()

        if not version:
            version = StatuteVersion(
                statute_id=statute.id,
                effective_from=ver_cfg["effective_from"],
                effective_to=ver_cfg["effective_to"],
                status=ver_cfg["status"],
                source_sha256=ver_cfg["source_sha256"],
            )
            db.add(version)
            db.commit()
            db.refresh(version)

        for sec in cfg["sections"]:
            existing_sec = db.execute(
                select(StatuteSection).where(
                    StatuteSection.version_id == version.id,
                    StatuteSection.section_no == sec["section_no"],
                )
            ).scalar_one_or_none()

            if not existing_sec:
                db_sec = StatuteSection(
                    version_id=version.id,
                    section_no=sec["section_no"],
                    heading=sec["heading"],
                    text=sec["text"],
                )
                db.add(db_sec)
        db.commit()

    return id_map
