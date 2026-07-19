import httpx
import logging
import json
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

    def get_edps(self, dps: float, tdo: float, is_mega: bool) -> float:
        """DialgaDex exact eDPS formula port"""
        if tdo <= 0 or dps <= 0: return 0
        party_size = 5 if is_mega else 6
        hp = 1000000000.0
        tof = tdo / dps
        lives = hp / tdo
        deaths = lives - 0.5
        relobbies = (deaths / party_size) - 0.5
        # 1 sec respawn, 15 sec relobby
        ttw = (lives * tof) + (deaths - relobbies) * 1.0 + 15.0 * relobbies
        return hp / ttw

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
            base_attack = p["stats"]["baseAttack"]
            base_defense = p["stats"].get("baseDefense", 100)
            base_stamina = p["stats"].get("baseStamina", 100)
            pkm_types = p["types"]
            fms = p.get("fm", [])
            cms = p.get("cm", [])
            is_mega = "Mega " in p["name"] or "Primal " in p["name"]
            is_released = p.get("released", False)
            is_legendary = p.get("class", "") in ["Legendary", "Mythical", "Ultra Beast"]

            forms_to_check = [(p["name"], 1.0, False)]
            if p.get("shadow", False) and not is_mega:
                forms_to_check.append((f"Shadow {p['name']}", 1.2, True))

            for form_name, dmg_mult, is_shadow in forms_to_check:
                best_by_type = {}

                atk_stat = (base_attack + 15) * dmg_mult
                def_stat = (base_defense + 15) / dmg_mult  # Shadows take 20% more dmg
                sta_stat = (base_stamina + 15)

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
                        
                        # Simplified GamePress DPS math
                        f_p = fm['power'] * fm_stab * atk_stat / 180.0  # assume 180 enemy def
                        f_d = fm['duration'] / 1000.0
                        f_e = fm['energy_delta']
                        
                        c_p = cm['power'] * cm_stab * atk_stat / 180.0
                        c_d = cm['duration'] / 1000.0
                        c_e = abs(cm['energy_delta'])
                        
                        if f_d <= 0 or c_d <= 0 or f_e <= 0 or c_e <= 0:
                            continue
                            
                        fdps = f_p / f_d
                        feps = f_e / f_d
                        cdps = c_p / c_d
                        ceps = c_e / c_d
                        
                        # Cycle DPS
                        cycle_dps = (fdps * ceps + cdps * feps) / (ceps + feps)
                        
                        # DialgaDex TDO formula: DPS * (HP * DEF / 1340)
                        tdo = cycle_dps * (sta_stat * def_stat) / 1340.0
                        
                        # DialgaDex eDPS
                        edps = self.get_edps(cycle_dps, tdo, is_mega)
                        
                        atk_type = cm['type']
                        if atk_type not in best_by_type or edps > best_by_type[atk_type]["edps"]:
                            best_by_type[atk_type] = {
                                "edps": edps,
                                "fm": fm_name,
                                "cm": cm_name,
                                "fm_type": fm["type"]
                            }
                            
                for atk_type, data in best_by_type.items():
                    if atk_type in rankings:
                        display_name = form_name
                        if p.get("form") and p["form"] not in ["Normal", "Purified"] and "Mega" not in p["name"] and "Primal" not in p["name"]:
                            display_name += f" ({p['form']})"
                            
                        rankings[atk_type].append({
                            "name": display_name,
                            "edps": round(data["edps"] * 10, 2), # Scale up for readability (matches DialgaDex ~20-30 scale)
                            "fm": data["fm"],
                            "cm": data["cm"],
                            "is_mega": is_mega,
                            "is_shadow": is_shadow,
                            "is_released": is_released,
                            "is_legendary": is_legendary,
                            "is_native": (data["fm_type"] == atk_type) and (atk_type in pkm_types)
                        })

        # Sort and save JSON
        for atk_type in types:
            rankings[atk_type] = sorted(rankings[atk_type], key=lambda x: x["edps"], reverse=True)
            
            # Remove dupes
            seen = set()
            filtered = []
            for r in rankings[atk_type]:
                if r["name"] not in seen:
                    seen.add(r["name"])
                    filtered.append(r)
            rankings[atk_type] = filtered

        json_path = self.data_dir / "tier_list_raw.json"
        json_path.write_text(json.dumps(rankings, indent=2), encoding="utf-8")
        logger.info("Saved custom tier_list_raw.json to %s", json_path)
        
        # Save a minified Markdown for the AI so it still has context
        lines = ["# Melhores Atacantes PvE (Tier List Atualizada)"]
        for atk_type in types:
            # AI sees top 5 of all pokemon (released flag ignored since user said everything is released)
            valid = rankings[atk_type]
            if valid:
                lines.append(f"\n## {atk_type}")
                for i, r in enumerate(valid[:5]):
                    lines.append(f"{i+1}. {r['name']} ({r['fm']} + {r['cm']}) - eDPS: {r['edps']}")
                    
        md_path = self.data_dir / "tier_list.md"
        md_path.write_text("\n".join(lines), encoding="utf-8")
        
        return [{"status": "success"}]
