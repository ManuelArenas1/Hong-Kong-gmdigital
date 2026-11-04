# Exploración: Observable Framework con los datos del lago

Segunda herramienta de visualización probada con los **mismos datos** que la página publicada (`public/data/demografia.json` y `public/data/geo.json`). No es el sistema: es evidencia de la bitácora de exploración del README raíz.

```bash
cd exploracion/observable-framework
npm install
npm run build      # genera dist/ (ignorada por git)
npm run dev        # vista previa local
```

- `src/data/*.js`: cargadores que leen los archivos del lago; el build deja instantáneas en `dist/_file/data/`.
- `src/index.md`: coropleta y barras del porcentaje de población de 65 años o más por distrito.
- Plot se instala en local (`@observablehq/plot`) para que el build no dependa de un CDN. Sin eso, el build de la prueba falló al no poder abrir `cdn.jsdelivr.net`.
- Licencias (leídas en npm, 2026-11-03): Observable Framework 1.13.4, ISC; Plot 0.6.18, ISC.
