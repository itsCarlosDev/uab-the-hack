# Frontend legacy data

Este folder conserva el script original (`main.py`) que genera los mapas para la demo antigua. Para usarlo necesitas copiar aqui los ficheros pesados `rookie_filtered_aps.json` y `rookie_filtered_clients.json` (saldran de `data/processed/rookie/`), y ejecutar `python main.py` para producir `mapa_health_dinamico.html`, `mapa_signal_dinamico.html` y `mapa_clientes_dinamico.html`.

Los JSON y HTML resultantes superan los 100 MB en cuanto trabajas con el dataset completo, por lo que GitHub los rechaza. Mantelos fuera del control de versiones (usa `.gitignore` + storage externo) y solo comparte los enlaces cuando el equipo los necesite.
