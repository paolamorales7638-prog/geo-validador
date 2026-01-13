from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
import re
import pandas as pd
import tempfile

app = FastAPI()

def extraer_coords(link: str):
    patrones = [
        r"@(-?\d+\.\d+),(-?\d+\.\d+)",
        r"q=(-?\d+\.\d+),(-?\d+\.\d+)"
    ]
    for p in patrones:
        m = re.search(p, link)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None, None


@app.get("/")
def inicio():
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Validador de Links Google Maps</title>
        </head>
        <body>
            <h2>Validador de Links Google Maps</h2>
            <form method="post" action="/validar">
                <textarea name="links" rows="15" cols="120"
                    placeholder="Pegá un link por línea"></textarea><br><br>
                <button type="submit">Validar y descargar Excel</button>
            </form>
        </body>
        </html>
        """,
        status_code=200
    )


@app.post("/validar")
def validar(links: str = Form(...)):
    filas = []
    vistos = {}

    for link in links.splitlines():
        link = link.strip()
        if not link:
            continue

        lat, lon = extraer_coords(link)

        if lat is None or lon is None:
            estado = "INVALIDO"
            obs = "No se pudieron extraer coordenadas"
        elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
            estado = "INVALIDO"
            obs = "Coordenadas fuera de rango"
        else:
            key = (lat, lon)
            if key in vistos:
                estado = "REVISAR"
                obs = "Coordenadas duplicadas"
            else:
                estado = "OK"
                obs = ""
                vistos[key] = True

        filas.append({
            "LINK": link,
            "LATITUD": lat,
            "LONGITUD": lon,
            "ESTADO": estado,
            "OBSERVACION": obs
        })

    df = pd.DataFrame(filas)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(tmp.name, index=False)

    return FileResponse(
        tmp.name,
        filename="resultado_validacion_maps.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

