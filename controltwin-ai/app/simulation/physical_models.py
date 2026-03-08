from __future__ import annotations

import math
from typing import Any


class PhysicalModels:
    @staticmethod
    def load_flow_dc(nodes, edges, generation, loads) -> dict[str, Any]:
        """
        Simplified DC load flow for electrical network.
        Returns dict with voltages and flows.
        """
        theta = {n: 0.0 for n in nodes}
        slack = nodes[0] if nodes else None
        inj = {n: float(generation.get(n, 0.0) - loads.get(n, 0.0)) for n in nodes}

        # Two Newton-like iterations on linearized DC relation
        for _ in range(2):
            for n in nodes:
                if n == slack:
                    continue
                neigh = [e for e in edges if e["from"] == n or e["to"] == n]
                if not neigh:
                    continue
                num = inj[n]
                den = 0.0
                for e in neigh:
                    a, b = e["from"], e["to"]
                    x = max(float(e.get("impedance", 0.1)), 1e-4)
                    other = b if a == n else a
                    num += theta[other] / x
                    den += 1.0 / x
                theta[n] = num / den if den > 0 else theta[n]

        flows = {}
        losses = 0.0
        for i, e in enumerate(edges):
            a, b = e["from"], e["to"]
            x = max(float(e.get("impedance", 0.1)), 1e-4)
            f = (theta[a] - theta[b]) / x
            flows[f"edge_{i}_{a}_{b}"] = f
            losses += abs(f) * 0.01

        voltages = {n: 1.0 - min(0.1, abs(theta[n]) * 0.05) for n in nodes}
        return {"voltages": voltages, "flows": flows, "estimated_losses_mw": losses}

    @staticmethod
    def pipeline_pressure(
        inlet_pressure_bar,
        flow_rate_m3h,
        pipe_length_km,
        pipe_diameter_mm,
        fluid_viscosity=0.001,
        fluid_density=850,
    ) -> float:
        """
        Darcy-Weisbach equation for pressure drop (simplified).
        Returns outlet pressure in bar.
        """
        q = max(float(flow_rate_m3h) / 3600.0, 0.0)  # m3/s
        d = max(float(pipe_diameter_mm) / 1000.0, 1e-4)  # m
        l = max(float(pipe_length_km) * 1000.0, 0.0)  # m
        area = math.pi * (d ** 2) / 4.0
        v = q / area if area > 0 else 0.0
        re = (fluid_density * v * d) / max(fluid_viscosity, 1e-9)
        f = 0.3164 / (re ** 0.25) if re > 2000 else 64.0 / max(re, 1.0)
        dp_pa = f * (l / d) * (fluid_density * v * v / 2.0)
        dp_bar = dp_pa / 100000.0
        return max(0.0, float(inlet_pressure_bar) - dp_bar)

    @staticmethod
    def thermal_model(
        initial_temp_c,
        ambient_temp_c,
        heat_generation_kw,
        thermal_resistance,
        thermal_capacity,
        time_steps_minutes,
    ) -> list[float]:
        """
        RC thermal model.
        dT/dt = ( (Tamb - T)/(R*C) + P/C )
        """
        dt = 60.0  # seconds
        t = float(initial_temp_c)
        ta = float(ambient_temp_c)
        p = float(heat_generation_kw) * 1000.0  # W
        r = max(float(thermal_resistance), 1e-6)
        c = max(float(thermal_capacity), 1e-6)

        out = [t]
        for _ in range(max(int(time_steps_minutes), 0)):
            dtdt = (ta - t) / (r * c) + p / c
            t = t + dtdt * dt
            out.append(float(t))
        return out
