const express = require('express');
const { parse } = require('csv-parse/sync');

const app = express();
const PORT = 3000;

app.use(express.static('public'));

app.get('/api/objects', (req, res) => {
    const objects = [
        { name: "Neptune", description: "The eighth planet from the Sun.", position: "8th planet from the Sun", type: "Planet" },
        { name: "Planet X", description: "A hypothetical distant planet.", position: "Beyond Neptune", type: "Unconfirmed" },
        { name: "Comet", description: "An icy celestial object.", position: "Travels around the Sun", type: "Comet" },
        { name: "Asteroid", description: "A rocky object orbiting the Sun.", position: "Asteroid belt", type: "Asteroid" },
        { name: "Brown Dwarf", description: "An object larger than a planet.", position: "Space", type: "Brown Dwarf" }
    ];
    res.json(objects);
});

// Remember the last good NASA answer for each sky position
const cache = {};

const sleep = ms => new Promise(r => setTimeout(r, ms));

app.get('/api/spherex', async (req, res) => {
    const ra = parseFloat(req.query.ra) || 127.69444;
    const dec = parseFloat(req.query.dec) || -39.17760;
    const n = parseInt(req.query.n) || 10;
    const key = `${ra}|${dec}|${n}`;

    try {
        const nasaURL = new URL('https://irsa.ipac.caltech.edu/SIA');
        nasaURL.searchParams.set('COLLECTION', 'spherex_qr3');
        nasaURL.searchParams.set('POS', `CIRCLE ${ra} ${dec} 0.01`);
        nasaURL.searchParams.set('RESPONSEFORMAT', 'CSV');
        nasaURL.searchParams.set('MAXREC', String(n));

        let response;
        for (let attempt = 1; attempt <= 4; attempt++) {
            try {
                response = await fetch(nasaURL);
                if (response.ok) break;
                console.log(`NASA attempt ${attempt} failed: ${response.status}`);
            } catch (err) {
                console.log(`NASA attempt ${attempt} failed: ${err.message}`);
                response = null;
            }
            await sleep(3000);
        }

        if (!response || !response.ok) {
            throw new Error('NASA API request failed' + (response ? ' (status ' + response.status + ')' : ''));
        }

        const csvData = await response.text();
        const records = parse(csvData, {
            columns: true,
            skip_empty_lines: true,
            relax_column_count: true,
            relax_quotes: true
        });

        records.forEach(r => delete r.cloud_access);

        const result = {
            success: true,
            source: 'NASA SPHEREx IRSA',
            total: records.length,
            images: records
        };
        cache[key] = result;
        res.json(result);

    } catch (error) {
        console.error(error.message);
        if (cache[key]) {
            console.log('Serving cached data for', key);
            return res.json({ ...cache[key], source: 'NASA SPHEREx IRSA (cached)' });
        }
        res.status(500).json({
            success: false,
            message: error.message + '. NASA may be busy, please try again in a minute.'
        });
    }
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});