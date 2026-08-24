* Rohdaten-CSV → gefiltert auf Teilmenge
* Aus der Teilmenge-CSV: Teilgraph wird zuerst erzeugt (nur Prozessdaten)
* Auf Basis dieses Graphen: Profile, Normebene, Feststellungen planen
* Dokumente werden synthetisch erzeugt – mit Bezug auf konkrete Knoten im schon existierenden Teilgraphen
* Dokumente werden in denselben Graphen eingehängt (Dokument-, Chunk-, Klausel-Knoten kommen dazu)
* Der jetzt vollständige Graph (Prozess + Normen + Dokumente) wird als ein Cypher-Skript exportiert
* Dieses Skript lädt direkt in Aura – unabhängig von jeder Versionsfrage

## meine schritte
* als erstes bestimme ich zwei use cases (F1,4 oder so)
* in der Teilmenge möchte ich aber ALLE fälle für F1 und F4 plus einige, die andere sind bzw. die absolut sauber sind 
* gib mir eine Liste aller dokumente, die du vorhast zu erzeugen. ich möchte hier ggf. noch einige andere hinzufügen. 
* gib mir einen überblick über den graph den du erzeugt hast und warum du ihn so erzeugt hast

## Was nach Schritt 3 noch zu tun ist: 
* Aura Registrierung
* Load the bpic_schlank_database to aura
* Beschreibe den Use Case und die Solution 
* Bereite den Pitch vor mit einem Stichpunkt-Skript, vielleicht mit einer ppt
- Offene Punkte: 
  - Was macht Microsoft Foundry. Wozu brauche ich das? 
  - Aura MCP testen
  - Wie nutze ich das Document Indexing? Wie spielt mit dem Graphen zusammen? Welche Rolle spielt es in der Lösung? Es ist ja schliesslich GraphRAG mit Betonung auf RAG!
* Final: Sketche eine erste Lösung/Architektur und baue mit Claude Code ein erstes App Skeleton

