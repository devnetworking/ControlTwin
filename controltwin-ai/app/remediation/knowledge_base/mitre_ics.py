MITRE_ICS_TECHNIQUES = {
    f"T08{str(i).zfill(2)}": {
        "id": f"T08{str(i).zfill(2)}",
        "name": f"ICS Technique T08{str(i).zfill(2)}",
        "tactic": "Impact" if i % 3 == 0 else "Discovery" if i % 3 == 1 else "Execution",
        "description": f"Detailed ICS ATT&CK technique description for T08{str(i).zfill(2)}.",
        "platforms": ["ICS", "Windows", "Linux"],
        "data_sources": ["Process monitoring", "Network traffic", "Controller logs"],
    }
    for i in range(1, 91)
}

MITRE_ICS_TECHNIQUES.update(
    {
        "T0801": {
            "id": "T0801",
            "name": "Monitor Process State",
            "tactic": "Collection",
            "description": "Adversary monitors OT process values to understand normal operation windows.",
            "platforms": ["ICS", "PLCs", "Historians"],
            "data_sources": ["Historian", "Sensor telemetry", "HMI logs"],
        },
        "T0814": {
            "id": "T0814",
            "name": "Denial of Service",
            "tactic": "Impact",
            "description": "Adversary disrupts communications or device availability.",
            "platforms": ["ICS", "Network Devices"],
            "data_sources": ["Network flow", "Availability monitoring", "Firewall logs"],
        },
        "T0827": {
            "id": "T0827",
            "name": "Loss of Control",
            "tactic": "Impact",
            "description": "Operator loses ability to control industrial process due to malicious activity.",
            "platforms": ["ICS", "HMI", "SCADA"],
            "data_sources": ["Control command logs", "Alarm logs", "PLC diagnostics"],
        },
        "T0836": {
            "id": "T0836",
            "name": "Modify Parameter",
            "tactic": "Impair Process Control",
            "description": "Adversary modifies process parameters to induce unsafe or unstable behavior.",
            "platforms": ["PLCs", "RTUs", "SCADA"],
            "data_sources": ["Configuration audits", "Change logs", "Engineering workstation logs"],
        },
        "T0855": {
            "id": "T0855",
            "name": "Unauthorized Command Message",
            "tactic": "Execution",
            "description": "Adversary issues unauthorized commands to control assets.",
            "platforms": ["ICS", "PLCs", "RTUs"],
            "data_sources": ["Command telemetry", "Protocol traces", "SIEM alerts"],
        },
        "T0856": {
            "id": "T0856",
            "name": "Spoof Reporting Message",
            "tactic": "Evasion",
            "description": "Adversary injects spoofed telemetry or status to hide real process state.",
            "platforms": ["ICS", "Sensors", "Gateways"],
            "data_sources": ["Telemetry integrity checks", "Protocol anomaly logs"],
        },
        "T0878": {
            "id": "T0878",
            "name": "Alarm Suppression",
            "tactic": "Inhibit Response Function",
            "description": "Adversary suppresses or manipulates alarms to delay operator response.",
            "platforms": ["HMI", "SCADA", "Alarm servers"],
            "data_sources": ["Alarm logs", "Operator actions", "Configuration diffs"],
        },
        "T0890": {
            "id": "T0890",
            "name": "Exploitation for Defense Evasion",
            "tactic": "Defense Evasion",
            "description": "Adversary exploits weaknesses to evade OT monitoring and detection controls.",
            "platforms": ["ICS", "Windows", "Linux"],
            "data_sources": ["EDR logs", "OT IDS", "Authentication logs"],
        },
    }
)
