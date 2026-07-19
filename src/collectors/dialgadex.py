import httpx
import logging
import json
import subprocess
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

        (self.data_dir / "pogo_pkm.min.json").write_bytes(pkm_res.content)
        (self.data_dir / "pogo_fm.json").write_bytes(fm_res.content)
        (self.data_dir / "pogo_cm.json").write_bytes(cm_res.content)

        logger.info("Running DialgaDex JS Engine via Node.js...")
        try:
            subprocess.run(["node", "src/collectors/dialgadex_bridge.js"], check=True)
            logger.info("Saved custom tier_list_raw.json via JS bridge")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to run DialgaDex bridge: %s", e)
            return [{"status": "error"}]

        # Create md for AI
        raw_json = self.data_dir / "tier_list_raw.json"
        if raw_json.exists():
            rankings = json.loads(raw_json.read_text("utf-8"))
            lines = ["# Melhores Atacantes PvE (Tier List Atualizada)"]
            for atk_type, valid in rankings.items():
                if valid:
                    lines.append(f"\n## {atk_type}")
                    for i, r in enumerate(valid[:5]):
                        lines.append(f"{i+1}. {r['name']} ({r['fm']} + {r['cm']}) - eDPS: {r['edps']}")
            md_path = self.data_dir / "tier_list.md"
            md_path.write_text("\n".join(lines), encoding="utf-8")
        
        return [{"status": "success"}]
