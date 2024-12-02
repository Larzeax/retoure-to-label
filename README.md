# Label Creator für Label Printer

Ein kleines Tool, um Retourenlabels und Privatkundenlabels in das Format 105x208mm zu konvertieren und in einer Datei zusammenzufassen.

### Unterstützte Label-Arten:
- Amazon Retouren
- DHL Retouren
- DHL Privatkunden Label

---

## Getting Started

### Voraussetzungen
Nötige Software, um das Projekt lokal auszuführen:
- Python `>=3.8`

### Installation
Step-by-step:
1. Projekt downloaden oder klonen:
   ```bash
   git clone https://github.com/Larzeax/retoure-to-lable.git

2. In das Projektverzeichnis wechseln:
   ```bash
   cd retoure-to-lable

3. setup.bat ausführen:
   ```bash
   setup.bat

4. setup_context_menu.reg ausgühren (Fügt dem Kontextmenü (Rechtsklick auf Ordner) die Option "Process Labels" hinzu):
    ```bash
    setup_context_menu.reg

5. Config Datei anpassen:
    ```yaml
   webhook: Discord Webhook URL (optional) sendet die Datei als Webhook an Discord
   openFiles: True oder False (erforderlich) öffnet die erstellte PDF mit allen Labels automatisch
   ```
   
## Nutzung
- Rechtsklick auf einen Ordner und "Process Labels" auswählen um alle Labels in dem Ordner zu verarbeiten
- Rechtsklick auf eine Datei und "Process Label" auswählen um nur die ausgewählte Datei zu verarbeiten
- Rechtsklick auf mehrere Markierte Dateien > Senden an > !Label Creator um alle ausgewählten Dateien zu verarbeiten