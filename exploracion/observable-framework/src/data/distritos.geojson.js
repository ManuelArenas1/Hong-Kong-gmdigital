// Cargador: entrega los polígonos de los 18 distritos de public/data/geo.json.
import {readFileSync} from "node:fs";
const g = JSON.parse(readFileSync("../../public/data/geo.json", "utf8"));
process.stdout.write(JSON.stringify(g.distritos));
