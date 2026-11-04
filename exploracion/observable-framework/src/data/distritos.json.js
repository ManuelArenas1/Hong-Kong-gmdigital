// Cargador de datos: lee el MISMO archivo que usa la página publicada (public/data/demografia.json).
import {readFileSync} from "node:fs";
const d = JSON.parse(readFileSync("../../public/data/demografia.json", "utf8"));
const filas = Array.isArray(d.distritos) ? d.distritos : Object.values(d.distritos);
process.stdout.write(JSON.stringify(filas.map(({codigo, distrito_es, poblacion_2021, pct_65_mas, pct_vivienda_publica_alquiler, densidad_hab_km2}) =>
  ({codigo, distrito: distrito_es, poblacion_2021, pct_65_mas, pct_vivienda_publica_alquiler, densidad_hab_km2}))));
