const fs = require('fs');
const csv = fs.readFileSync('survey_results_rows.csv', 'utf8').split('\n');
const header = csv[0];

// Parse CSV rows
const rows = [];
for (let i = 1; i < csv.length; i++) {
    if (!csv[i].trim()) continue;
    const line = csv[i];
    // Robust CSV parsing with quoted fields
    const fields = [];
    let current = '', inQuotes = false;
    for (let j = 0; j < line.length; j++) {
        const ch = line[j];
        if (ch === '"' && !inQuotes) { inQuotes = true; continue; }
        if (ch === '"' && inQuotes) {
            if (line[j + 1] === '"') { current += '"'; j++; continue; }
            inQuotes = false; continue;
        }
        if (ch === ',' && !inQuotes) { fields.push(current); current = ''; continue; }
        if (ch !== '\r') current += ch;
    }
    fields.push(current);
    if (fields.length < 12) continue;

    let testResults = [];
    try { testResults = JSON.parse(fields[9]); } catch(e) { continue; }
    if (!Array.isArray(testResults)) continue;

    rows.push({
        device_type: fields[2], age: fields[4], gender: fields[5],
        freq: fields[6], train: fields[7], instrument: fields[8],
        testResults, diff: fields[10], issues: fields[11]
    });
}

console.log('Real rows parsed:', rows.length);

// Group by instrument_type x audio_condition
const groups = {};
rows.forEach(r => {
    r.testResults.forEach(t => {
        const key = t.instrument_type + '|' + t.audio_condition;
        if (!groups[key]) groups[key] = { vals: [], aros: [], first_rt: [], final_rt: [] };
        if (t.valence_x != null && !isNaN(t.valence_x)) groups[key].vals.push(t.valence_x);
        if (t.arousal_y != null && !isNaN(t.arousal_y)) groups[key].aros.push(t.arousal_y);
        if (t.first_click_rt_ms != null && t.first_click_rt_ms > 0) groups[key].first_rt.push(t.first_click_rt_ms);
        if (t.final_decision_rt_ms != null && t.final_decision_rt_ms > 0) groups[key].final_rt.push(t.final_decision_rt_ms);
    });
});

// Calculate mean/std
function meanStd(arr) {
    if (arr.length === 0) return { mean: 0, std: 0.3 };
    const n = arr.length;
    const mean = arr.reduce((a,b)=>a+b,0) / n;
    const variance = arr.reduce((s,x)=>s+(x-mean)**2,0) / n;
    return { mean, std: Math.sqrt(variance) || 0.3 };
}

const stats = {};
Object.keys(groups).forEach(key => {
    const g = groups[key];
    stats[key] = {
        valence: meanStd(g.vals),
        arousal: meanStd(g.aros),
        first_rt: meanStd(g.first_rt),
        final_rt: meanStd(g.final_rt)
    };
});

console.log('Groups:', Object.keys(stats).length);
// Print a few examples
Object.entries(stats).slice(0, 3).forEach(([k,v]) => {
    console.log(k, 'V:', v.valence.mean.toFixed(2), '+/-', v.valence.std.toFixed(2),
        'A:', v.arousal.mean.toFixed(2), '+/-', v.arousal.std.toFixed(2));
});

// Normal random
function randNorm(mean, std) {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    return Math.max(-1, Math.min(1, mean + z * std));
}

// Generate 27 synthetic rows
const demoPool = rows;
const instruments = ['celeste', 'flute', 'harp', 'trumpet', 'viola'];
const conditions = ['single', 'dorian', 'major', 'minor'];

const synthRows = [];
for (let i = 0; i < 27; i++) {
    const demo = demoPool[Math.floor(Math.random() * demoPool.length)];
    const userId = 'synth_' + Math.random().toString(36).slice(2, 10);
    const ts = new Date(Date.now() - Math.floor(Math.random() * 7 * 86400000)).toISOString();

    const playlist = [];
    instruments.forEach(inst => {
        conditions.forEach(cond => {
            const key = inst + '|' + cond;
            const s = stats[key];
            playlist.push({
                audio_id: inst + '_' + cond,
                instrument_type: inst,
                audio_condition: cond,
                valence_x: parseFloat(randNorm(s.valence.mean, s.valence.std * 0.8).toFixed(2)),
                arousal_y: parseFloat(randNorm(s.arousal.mean, s.arousal.std * 0.8).toFixed(2)),
                first_click_rt_ms: Math.round(Math.max(500, randNorm(s.first_rt.mean, s.first_rt.std * 0.7))),
                final_decision_rt_ms: Math.round(Math.max(500, randNorm(s.final_rt.mean, s.final_rt.std * 0.7)))
            });
        });
    });

    synthRows.push({
        user_id: userId,
        device_type: demo.device_type,
        age: demo.age,
        gender: demo.gender,
        freq: demo.freq,
        train: demo.train,
        instrument: demo.instrument || 'none',
        test_results: playlist,
        diff: demo.diff || '',
        issues: demo.issues || '',
        timestamp: ts
    });
}

// Build output: keep original rows + add synthetic
const outLines = [];
let newId = rows.length + 1;
const existingIds = new Set();

// Copy original rows (but remove the auto-generated IDs to let Supabase handle them)
for (let i = 1; i < csv.length; i++) {
    if (!csv[i].trim()) continue;
    // Keep original rows as-is, but replace id with sequential
    const line = csv[i];
    // Skip header-like lines
    if (line.startsWith('id,')) continue;
    outLines.push(line);
}

// Add synthetic rows
synthRows.forEach(r => {
    const tr = JSON.stringify(r.test_results);
    const line = [
        newId,
        r.user_id,
        r.device_type,
        r.timestamp,
        r.age,
        r.gender,
        r.freq,
        r.train,
        r.instrument,
        '"' + tr.replace(/"/g, '""') + '"',
        r.diff,
        r.issues,
        ''
    ].join(',');
    outLines.push(line);
    newId++;
});

const output = header + '\n' + outLines.join('\n');
fs.writeFileSync('survey_results_50.csv', output);
console.log('\nDone!', synthRows.length, 'synthetic rows generated.');
console.log('Total rows:', outLines.length);
console.log('Output: survey_results_50.csv');
