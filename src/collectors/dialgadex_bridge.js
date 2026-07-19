const fs = require('fs');
const path = require('path');

// Mock UI and DOM
global.UpdateAffinityDialog = () => {};
global.UpdateLoadingBar = () => {};
global.document = { getElementById: () => ({ checked: false, value: '' }) };
global.window = global;

// Settings (Matching DialgaDex exact defaults)
global.settings_metric = "eDPS";
global.settings_default_level = [40];
global.settings_xl_budget = false;
global.settings_pve_turns = true;
global.settings_strongest_count = 25;
global.settings_compare = "budget";
global.settings_tiermethod = "jenks";
global.settings_party_size = 1;
global.settings_relobbytime = 10;
global.settings_team_size_normal = 6;
global.settings_team_size_mega = 6;
global.settings_type_affinity = true;
global.settings_theme = "darkmode";
global.settings_speculative = true;
global.settings_metric_exp = 0.225;
global.settings_newdps = true;
global.currentLocale = "en-US";

// Read DB temporarily
let raw_pkm = JSON.parse(fs.readFileSync('data/pogo_pkm.min.json', 'utf8'));
global.jb_fm = JSON.parse(fs.readFileSync('data/pogo_fm.json', 'utf8'));
global.jb_cm = JSON.parse(fs.readFileSync('data/pogo_cm.json', 'utf8'));

// Fix hidden power
global.jb_fm.find(e => e.name=="Hidden Power").type = "None";

// Load DialgaDex JS logic
const basePath = 'dialgadex/scripts/';
let code = '';
code += fs.readFileSync(basePath + 'pokemon_enums.js', 'utf8') + '\n';
code += fs.readFileSync(basePath + 'pokemon_utils.js', 'utf8') + '\n';
code += fs.readFileSync(basePath + 'calc.js', 'utf8') + '\n';
// Remove const/let so they become global in eval
code = code.replace(/const /g, 'var ').replace(/let /g, 'var ');
eval(code);

global.jb_max_id = raw_pkm[raw_pkm.length - 1].id;
global.jb_pkm = raw_pkm.filter(item => GetPokemonForms(item.id).includes(item.form));

async function generate() {
    const types = [
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
        "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
    ];
    
    let rankings = {};
    for (let t of types) {
        let search_params = {
            type: t,
            versus: false,
            mixed: true,
            offtype: true,
            suboptimal: false,
            elite: true,
            real_damage: false,
            level: 40,
            unreleased: true,
            mega: true,
            shadow: true,
            legendary: true
        };
        
        let result = await GetStrongestOfOneType(search_params);
        
        rankings[t] = result.map(r => {
            return {
                name: r.name + (r.form && r.form != "Normal" && r.form != "Purified" && !r.name.includes(r.form) ? ` (${r.form})` : ""),
                edps: r.rat.toFixed(2),
                fm: r.fm,
                cm: r.cm,
                is_mega: r.form === "Mega" || r.form === "MegaX" || r.form === "MegaY" || r.form === "Primal" || r.name.startsWith("Mega ") || r.name.startsWith("Primal "),
                is_shadow: r.shadow,
                is_native: r.fm_type === t && r.cm_type === t,
                is_released: true // All of them are considered released now
            };
        });
    }
    
    fs.writeFileSync('data/tier_list_raw.json', JSON.stringify(rankings, null, 2));
}

generate().catch(console.error);
