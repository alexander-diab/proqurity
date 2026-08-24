# WeasyPrint in einem Container statt auf dem Mac.
#
# WeasyPrint rendert die 718 Korpus-PDFs (build/korpus/generator/gen_docs.py). Es ist
# das einzige Paket im Projekt, das native Bibliotheken braucht -- Pango, Cairo,
# gdk-pixbuf, HarfBuzz. Auf macOS heisst das Homebrew plus DYLD_LIBRARY_PATH-Gefummel;
# das ist die eine Installation, die zuverlaessig eine halbe Stunde kostet.
#
# Der Korpus ist fertig (P3: 942 Dokumente, 2.127 Pflichtangaben geprueft, 0 Fehler).
# Dieses Image wird also nur gebraucht, wenn er neu erzeugt werden soll.
#
#   docker build -f docker/weasyprint.Dockerfile -t proqurity-weasyprint .
#   docker run --rm -v "$PWD:/projekt" -w /projekt/build/korpus/generator \
#     proqurity-weasyprint python3 gen_docs.py
#
# Danach unbedingt die unabhaengige Pruefung laufen lassen -- sie hat beim ersten
# Mal zwei Fehler gefunden, die die Ground Truth still mehrdeutig gemacht haetten:
#
#   docker run --rm -v "$PWD:/projekt" -w /projekt/build/korpus/generator \
#     proqurity-weasyprint python3 verify_korpus.py

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 \
      libpangoft2-1.0-0 \
      libcairo2 \
      libgdk-pixbuf-2.0-0 \
      libffi8 \
      shared-mime-info \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir weasyprint jinja2 pandas

WORKDIR /projekt
CMD ["python3", "-c", "import weasyprint; print('WeasyPrint', weasyprint.__version__, 'bereit')"]
