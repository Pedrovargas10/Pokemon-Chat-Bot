import httpx
import logging
from typing import List, Dict, Any
from pathlib import Path
from .base import BaseCollector

logger = logging.getLogger(__name__)

class DialgadexCollector(BaseCollector):
    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.pkm_url = "https://raw.githubusercontent.com/mgrann03/pokemon-resources/main/pogo_pkm.min.json"
        self.fm_url = "https://raw.githubusercontent.com/mgrann03/pokemon-resources/main/pogo_fm.json"
        self.cm_url = "https://raw.githubusercontent.com/mgrann03/pokemon-resources/main/pogo_cm.json"

    async def collect(self) -> list[dict]:
        logger.info("Downloading DialgaDex database (Pokemon, Fast Moves, Charge Moves)...")
        async with httpx.AsyncClient() as client:
            pkm_res = await client.get(self.pkm_url)
            fm_res = await client.get(self.fm_url)
            cm_res = await client.get(self.cm_url)

        pkm_data = pkm_res.json()
        fm_data = {m['name']: m for m in fm_res.json()}
        cm_data = {m['name']: m for m in cm_res.json()}

        types = [
            "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
            "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
            "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
        ]
        
        rankings = {t: [] for t in types}

        for p in pkm_data:
            if not p.get("released", False):
                continue
                
            base_attack = p["stats"]["baseAttack"]
            pkm_types = p["types"]
            fms = p.get("fm", [])
            cms = p.get("cm", [])
            is_mega = "Mega " in p["name"] or "Primal" in p["name"]

            forms_to_check = [(p["name"], 1.0)]
            if p.get("shadow", False) and not is_mega:
                forms_to_check.append((f"Shadow {p['name']}", 1.2))

            for form_name, damage_multiplier in forms_to_check:
                best_by_type = {}

                for fm_name in fms:
                    if fm_name not in fm_data: continue
                    fm = fm_data[fm_name]
                    if fm['duration'] == 0: continue
                    
                    for cm_name in cms:
                        if cm_name not in cm_data: continue
                        cm = cm_data[cm_name]
                        if cm['duration'] == 0: continue
                        
                        fm_stab = 1.2 if fm['type'] in pkm_types else 1.0
                        cm_stab = 1.2 if cm['type'] in pkm_types else 1.0
                        
                        f_p = fm['power'] * fm_stab
                        f_d = fm['duration'] / 1000.0
                        f_e = fm['energy_delta']
                        
                        c_p = cm['power'] * cm_stab
                        c_d = cm['duration'] / 1000.0
                        c_e = abs(cm['energy_delta'])
                        
                        if f_d <= 0 or c_d <= 0 or f_e <= 0 or c_e <= 0:
                            continue
                            
                        fdps = f_p / f_d
                        feps = f_e / f_d
                        cdps = c_p / c_d
                        ceps = c_e / c_d
                        
                        cycle_dps = (fdps * ceps + cdps * feps) / (ceps + feps)
                        
                        tdm = (base_attack + 15) * cycle_dps * damage_multiplier
                        
                        atk_type = cm['type']
                        if atk_type not in best_by_type or tdm > best_by_type[atk_type][0]:
                            best_by_type[atk_type] = (tdm, fm_name, cm_name)
                            
                for atk_type, (tdm, fm_name, cm_name) in best_by_type.items():
                    if atk_type in rankings:
                        display_name = form_name
                        if p.get("form") and p["form"] not in ["Normal", "Purified"] and "Mega" not in p["name"] and "Primal" not in p["name"]:
                            display_name += f" ({p['form']})"
                            
                        rankings[atk_type].append({
                            "name": display_name,
                            "tdm": tdm,
                            "fm": fm_name,
                            "cm": cm_name
                        })

        lines = ["# Melhores Atacantes PvE (Tier List Atualizada)", ""]
        lines.append("> Baseado em cálculos matemáticos reais de DPS usando a database do jogo.\n")
        
        # We will format it exactly like the default save_markdown would, or just write custom markdown.
        # Since we bypass save_markdown to write a completely custom formatted document:
        for atk_type in types:
            rankings[atk_type] = sorted(rankings[atk_type], key=lambda x: x["tdm"], reverse=True)
            
            seen = set()
            filtered = []
            for r in rankings[atk_type]:
                if r["name"] not in seen:
                    seen.add(r["name"])
                    filtered.append(r)
            
            top_10 = filtered[:10]
            if top_10:
                lines.append(f"## Top Atacantes Tipo {atk_type}")
                for i, r in enumerate(top_10):
                    lines.append(f"{i+1}. **{r['name']}** ({r['fm']} + {r['cm']})")
                lines.append("")
                    
        md_content = "\n".join(lines)
        path = self.data_dir / "tier_list.md"
        path.write_text(md_content, encoding="utf-8")
        logger.info("Saved custom tier_list.md to %s", path)
        
        # Return a dummy list so the scheduler prints 'returned 1 items'
        return [{"status": "success"}]
