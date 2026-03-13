"""Constitutional MBTI dimension sets."""

DIMENSION_SETS: dict[str, dict] = {
    "political_philosophy": {
        "name": "Political Philosophy 101",
        "description": "Classical political science framing",
        "dimensions": {
            "E_I": {
                "name": "E/I",
                "E_label": "Cosmopolitan",
                "I_label": "Sovereigntist",
                "E_desc": "References international law, human rights treaties, UN obligations, universal values",
                "I_desc": "Emphasizes national identity, self-determination, unique cultural heritage, sovereignty",
            },
            "S_N": {
                "name": "S/N",
                "S_label": "Prescriptive",
                "N_label": "Aspirational",
                "S_desc": "Specific procedures, exact numbers, quorum rules, detailed institutional mechanics",
                "N_desc": "Lofty preambles, vision statements, broad principles about justice and dignity",
            },
            "T_F": {
                "name": "T/F",
                "T_label": "Institutional",
                "F_label": "Communitarian",
                "T_desc": "Separation of powers, checks and balances, term limits, procedural architecture",
                "F_desc": "Social solidarity, collective rights, duties to community, welfare provisions",
            },
            "J_P": {
                "name": "J/P",
                "J_label": "Rigid",
                "P_label": "Living Document",
                "J_desc": "Unamendable clauses, supermajority requirements, eternal principles, entrenched provisions",
                "P_desc": "Easy amendment, provisional clauses, review mechanisms, sunset clauses",
            },
        },
    },
    "vibes": {
        "name": "Vibes-Based Governance",
        "description": "Constitutional vibes, decoded",
        "dimensions": {
            "E_I": {
                "name": "E/I",
                "E_label": "Talks to the UN at parties",
                "I_label": "Doesn't answer the door",
                "E_desc": "International obligations everywhere, references to treaties, cooperation, global community",
                "I_desc": "We do things our way, national sovereignty, minimal foreign entanglement",
            },
            "S_N": {
                "name": "S/N",
                "S_label": "Has a spreadsheet for everything",
                "N_label": "Has a vision board",
                "S_desc": "Articles about tax percentages, pension ages, exact quorum numbers, parliamentary procedure",
                "N_desc": "Justice, dignity, the flourishing of all peoples, sweeping preambles about eternal truths",
            },
            "T_F": {
                "name": "T/F",
                "T_label": "The org chart IS the point",
                "F_label": "Won't somebody think of the children",
                "T_desc": "Who appoints whom, how many judges, which committee reviews what, institutional plumbing",
                "F_desc": "Rights, welfare, education, healthcare, social protection, human dignity",
            },
            "J_P": {
                "name": "J/P",
                "J_label": "The constitution is FINAL",
                "P_label": "It's a living document, sweetie",
                "J_desc": "Eternity clauses, unamendable core, supermajority to change anything, constitutional court guardianship",
                "P_desc": "Regular review, easy amendment, sunset clauses, participatory revision mechanisms",
            },
        },
    },
    "parent_energy": {
        "name": "Parent Energy",
        "description": "What kind of parent is your constitution?",
        "dimensions": {
            "E_I": {
                "name": "E/I",
                "E_label": "Helicopter parent",
                "I_label": "Free-range parent",
                "E_desc": "The state monitors, regulates, and provides for everything — extensive positive rights and duties",
                "I_desc": "Negative rights, limited government, leave people alone, minimal state intervention",
            },
            "S_N": {
                "name": "S/N",
                "S_label": "Tiger parent",
                "N_label": "Cool parent",
                "S_desc": "Specific duties, mandatory education requirements, military service, detailed obligations",
                "N_desc": "Broad principles, trust the process, it'll work out, general aspirational language",
            },
            "T_F": {
                "name": "T/F",
                "T_label": "Strict parent",
                "F_label": "Nurturing parent",
                "T_desc": "Punishment provisions, emergency powers, state of exception, strong enforcement mechanisms",
                "F_desc": "Social rights, welfare guarantees, child protection, care for vulnerable populations",
            },
            "J_P": {
                "name": "J/P",
                "J_label": "Because I said so",
                "P_label": "Let's discuss",
                "J_desc": "Authority derived from God/history/revolution, non-negotiable foundational principles",
                "P_desc": "Participatory mechanisms, referenda, citizen initiative, deliberative processes",
            },
        },
    },
    "house_party": {
        "name": "House Party",
        "description": "Your constitution showed up to the party. What happened?",
        "dimensions": {
            "E_I": {
                "name": "E/I",
                "E_label": "Throws the party",
                "I_label": "Attends reluctantly",
                "E_desc": "Colonial/imperial legacy, exports its constitutional model, widely referenced by others",
                "I_desc": "Defensive sovereignty, non-interference, 'we were forced to write this', minimal external engagement",
            },
            "S_N": {
                "name": "S/N",
                "S_label": "Brought a playlist and schedule",
                "N_label": "Brought vibes and poetry",
                "S_desc": "Detailed articles about parliamentary procedure, voting thresholds, bureaucratic mechanics",
                "N_desc": "Sweeping preambles about human dignity, eternal truths, and the destiny of the nation",
            },
            "T_F": {
                "name": "T/F",
                "T_label": "Worried about noise complaints",
                "F_label": "Making sure everyone's having fun",
                "T_desc": "Liability, procedure, who's responsible, institutional accountability mechanisms",
                "F_desc": "Social inclusion, minority rights, equality, making sure no one's left out",
            },
            "J_P": {
                "name": "J/P",
                "J_label": "Locked the liquor cabinet",
                "P_label": "Left the door open",
                "J_desc": "Entrenched provisions, constitutional court guardianship, hard to change anything",
                "P_desc": "Amendment by simple majority, flexible interpretation, open to revision",
            },
        },
    },
    "attachment_style": {
        "name": "Relationship Attachment Style",
        "description": "How does your constitution handle commitment?",
        "dimensions": {
            "E_I": {
                "name": "E/I",
                "E_label": "Anxious attachment",
                "I_label": "Avoidant attachment",
                "E_desc": "Constant reference to international community, seeking validation, treaty obligations everywhere",
                "I_desc": "Self-sufficient, minimal foreign entanglement, doesn't need anyone's approval",
            },
            "S_N": {
                "name": "S/N",
                "S_label": "Practical partner",
                "N_label": "Romantic partner",
                "S_desc": "Here are the bills we split and how — specific procedures, numbers, practical governance mechanics",
                "N_desc": "Our love is built on dignity, justice, and shared dreams — aspirational, principled, visionary",
            },
            "T_F": {
                "name": "T/F",
                "T_label": "Let's be logical about this",
                "F_label": "How does that make you feel?",
                "T_desc": "Institutional architecture first — who does what, how decisions are made, structural clarity",
                "F_desc": "Rights and welfare first — how people are treated, social protection, emotional/moral foundation",
            },
            "J_P": {
                "name": "J/P",
                "J_label": "Five-year plan",
                "P_label": "Let's see where this goes",
                "J_desc": "Rigid constitutional order, hard to amend, permanent commitments, eternity clauses",
                "P_desc": "Flexible, evolving framework, regular review, open to renegotiation",
            },
        },
    },
}
