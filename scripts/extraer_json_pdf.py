"""Extrae de los PDF del MIDA (data/Documento_referencia/) un JSON por cultivo usando Gemini con LangChain.

Por cultivo se envían a Gemini la ficha de costo normativo y la página de la proyección de siembra
y cosecha; Gemini devuelve los datos en el esquema FichaCultivo (salida estructurada) y el script
los guarda con la misma forma que lee scripts/generar_datos_sinteticos.py.

Requiere GOOGLE_API_KEY (o GEMINI_API_KEY), en el archivo .env (ver .env.example) o como variable
de entorno. Modelo: GEMINI_MODEL, por defecto gemini-3.5-flash.

Ejecutar desde la raíz del repo:
    python scripts/extraer_json_pdf.py              # los tres cultivos
    python scripts/extraer_json_pdf.py cafe         # solo uno
"""
import base64
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter

# Lee GOOGLE_API_KEY y GEMINI_MODEL del archivo .env de la raíz (no pisa variables ya definidas)
load_dotenv()

PDFS = Path("data/Documento_referencia")
SALIDA = Path("data/semiestructurado/ia")
# JSON copiados a mano: si existen, se comparan con lo que extrae la IA
REFERENCIA = Path("data/semiestructurado")
PROYECCION = "Proyecciones-de-Siembra-y-Cosecha-2025-2026.pdf"
MODELO = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
GOOGLE_APY_KEY = os.environ.get("GOOGLE_API_KEY")


class Monto(BaseModel):
    nombre: str = Field(description="Nombre tal como aparece en la ficha, p. ej. 'Insumos' o 'Seguro agrícola'")
    monto: float = Field(description="Valor en balboas (B/.)")


class Region(BaseModel):
    region: str = Field(description="Nombre de la región tal como aparece en la cabecera del cuadro")
    productores: int
    ha_cosechar: float = Field(description="Fila 'Sup. a cosechar', en hectáreas")
    rendimiento_qq_ha: float = Field(description="Fila 'Rendimiento', en quintales por hectárea")


class FichaCultivo(BaseModel):
    costo_ha_total: float = Field(description="'Costo total' de producir una hectárea, en B/.")
    rubros: list[Monto] = Field(description="Subtotal de cada sección de costos (A, B, C, D), sin los porcentajes")
    recargos: list[Monto] = Field(description="Cargos porcentuales: imprevisto, asistencia técnica, seguro agrícola, intereses")
    costo_por_qq_cosechado: float = Field(description="Costo en B/. que crece por cada quintal cosechado")
    rendimiento_esperado_qq_ha: float
    precio_qq: float | None = Field(description="Precio esperado por quintal en B/.; null si el documento no lo trae")
    regiones: list[Region] = Field(description="Solo regiones con superficie a cosechar mayor que 0")


# Qué parte de cada PDF corresponde al cultivo y al sistema que usa el proyecto (páginas desde 1)
FICHAS = {
    "arroz": dict(
        cultivo="Arroz", sistema="Mecanizado en secano",
        costos="Costos-de-arroz-mecanizado-en-secano-2025-2026.pdf", pag_costos=1, pag_proyeccion=1,
        instrucciones=(
            "Ficha de costos: arroz mecanizado en secano. costo_por_qq_cosechado es el precio unitario "
            "del 'Transporte de cosecha' (B/. por QQ). rendimiento_esperado_qq_ha y precio_qq salen de la "
            "'Referencia para el Análisis Económico'. Cuadro de proyección: usa solo el bloque "
            "'Arroz mecanizado en secano Subtotal', no el 'TOTAL ARROZ' ni otros sistemas."),
    ),
    "maiz": dict(
        cultivo="Maíz", sistema="Mecanizado",
        costos="Costo-normativo-maiz-2025-026.pdf", pag_costos=1, pag_proyeccion=2,
        instrucciones=(
            "Ficha de costos: maíz mecanizado convencional. El documento no trae precio: precio_qq = null. "
            "rendimiento_esperado_qq_ha es la cantidad de quintales (coeficiente técnico) del 'Transporte "
            "cosecha', y costo_por_qq_cosechado es su precio unitario. Cuadro de proyección: usa solo el "
            "bloque 'Maíz mecanizado'; ojo, hay celdas vacías, guíate por la cabecera de cada columna."),
    ),
    "cafe": dict(
        cultivo="Café", sistema="Tecnificado (robusta, año 5)",
        costos="Costo-normativo-cafe-2025-2026.pdf", pag_costos=2, pag_proyeccion=10,
        instrucciones=(
            "Ficha de costos: café robusta convencional tecnificado, sin plátano. Usa solo la columna "
            "'V AÑO' (plantación madura). Los rubros son las secciones A a D; los recargos son las líneas "
            "de la sección E. rendimiento_esperado_qq_ha y precio_qq son los del AÑO 5 del análisis "
            "económico. costo_por_qq_cosechado = (valor de 'Cosecha café/lata' + valor de 'Transporte de "
            "cosecha' del V año) / rendimiento esperado del año 5. Cuadro de proyección: usa solo el "
            "bloque 'CAFÉ' dentro de los rubros industriales."),
    ),
}

INSTRUCCION_GENERAL = (
    "Eres un analista de datos agropecuarios. Extrae los datos del primer PDF (ficha de costo normativo "
    "por hectárea, MIDA, Panamá) y del segundo PDF (proyección de siembra y cosecha por región). "
    "Copia los números exactamente como aparecen, sin redondear ni calcular, salvo cuando se indique. "
    "Las comas son separadores de miles."
)


def pdf_base64(nombre, pagina):
    """Devuelve solo esa página del PDF, en base64, para no mandar páginas de otros cultivos."""
    escritor = PdfWriter()
    escritor.add_page(PdfReader(PDFS / nombre).pages[pagina - 1])
    buffer = io.BytesIO()
    escritor.write(buffer)
    return base64.b64encode(buffer.getvalue()).decode()


def clave(texto):
    """'B. Preparación de suelo' -> 'preparacion_de_suelo'; 'Imprevisto 5%' -> 'imprevisto'."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    texto = re.split(r"[(\d]", re.sub(r"^[a-e][.\-]\s*", "", texto))[0]
    return re.sub(r"[^a-z]+", "_", texto).strip("_")


def a_documento(f, ficha):
    """Convierte la respuesta de Gemini a la forma de data/semiestructurado/*.json."""
    rubros = {clave(m.nombre): m.monto for m in f.rubros}
    rubros["recargos"] = {clave(m.nombre): m.monto for m in f.recargos}
    return {
        "cultivo": ficha["cultivo"],
        "sistema": ficha["sistema"],
        "anio_agricola": "2025-2026",
        "moneda": "B/.",
        "fuente": {
            "costos": f"{ficha['costos']}, pág. {ficha['pag_costos']}",
            "regiones": f"{PROYECCION}, pág. {ficha['pag_proyeccion']}",
            "extraido_con": MODELO,
        },
        "costo_ha": {"total": f.costo_ha_total, "rubros": rubros, "por_qq_cosechado": f.costo_por_qq_cosechado},
        "analisis_economico": {"rendimiento_esperado_qq_ha": f.rendimiento_esperado_qq_ha, "precio_qq": f.precio_qq},
        "regiones": [r.model_dump() for r in f.regiones],
    }


def errores(doc):
    """Chequeos de calidad antes de guardar: los rubros deben sumar el total."""
    r = doc["costo_ha"]["rubros"]
    suma = sum(v for k, v in r.items() if k != "recargos") + sum(r["recargos"].values())
    total = doc["costo_ha"]["total"]
    fallas = [] if abs(suma - total) < 0.05 else [f"rubros suman {suma:,.2f} y el total es {total:,.2f}"]
    if not doc["regiones"]:
        fallas.append("no extrajo ninguna región")
    return fallas


def comparar(doc, nombre):
    """Muestra en qué difiere lo extraído por la IA del JSON copiado a mano, si existe."""
    ruta = REFERENCIA / f"{nombre}.json"
    if not ruta.exists():
        return
    ref = json.loads(ruta.read_text(encoding="utf-8"))
    pares = [
        ("costo total", ref["costo_ha"]["total"], doc["costo_ha"]["total"]),
        ("costo por qq cosechado", ref["costo_ha"]["por_qq_cosechado"], doc["costo_ha"]["por_qq_cosechado"]),
        ("rendimiento esperado", ref["analisis_economico"]["rendimiento_esperado_qq_ha"],
         doc["analisis_economico"]["rendimiento_esperado_qq_ha"]),
        ("precio por qq", ref["analisis_economico"]["precio_qq"], doc["analisis_economico"]["precio_qq"]),
    ]
    ia = {r["region"]: r for r in doc["regiones"]}
    for r in ref["regiones"]:
        otro = ia.get(r["region"], {})
        pares += [(f"{r['region']} {k}", r[k], otro.get(k)) for k in ("ha_cosechar", "rendimiento_qq_ha")]
    diferencias = [(n, a, b) for n, a, b in pares if a != b and not (a and b and abs(a - b) < 0.01)]
    sobran = sorted(set(ia) - {r["region"] for r in ref["regiones"]})
    print(f"  vs {ruta}: {len(pares) - len(diferencias)}/{len(pares)} valores coinciden")
    for n, a, b in diferencias:
        print(f"    {n}: a mano {a} | IA {b}")
    if sobran:
        print(f"    regiones que no están en el JSON a mano: {', '.join(sobran)}")


def extraer(modelo, nombre):
    ficha = FICHAS[nombre]
    mensaje = HumanMessage(content=[
        {"type": "text", "text": f"{INSTRUCCION_GENERAL}\n\n{ficha['instrucciones']}"},
        {"type": "file", "source_type": "base64", "mime_type": "application/pdf",
         "data": pdf_base64(ficha["costos"], ficha["pag_costos"])},
        {"type": "file", "source_type": "base64", "mime_type": "application/pdf",
         "data": pdf_base64(PROYECCION, ficha["pag_proyeccion"])},
    ])
    return a_documento(modelo.invoke([mensaje]), ficha)


if __name__ == "__main__":
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        sys.exit("Falta la API key: copia .env.example a .env y llena GOOGLE_API_KEY")
    pedidos = sys.argv[1:] or list(FICHAS)
    if desconocidos := set(pedidos) - set(FICHAS):
        sys.exit(f"Cultivos desconocidos: {', '.join(desconocidos)}. Opciones: {', '.join(FICHAS)}")

    modelo = ChatGoogleGenerativeAI(model=MODELO).with_structured_output(FichaCultivo)
    SALIDA.mkdir(parents=True, exist_ok=True)
    fallidos = []
    for nombre in pedidos:
        print(f"{nombre}: extrayendo con {MODELO}...")
        doc = extraer(modelo, nombre)
        if fallas := errores(doc):
            # No se guarda un JSON que no pasa los chequeos, para que no llegue al generador
            print(f"  NO guardado: {'; '.join(fallas)}")
            fallidos.append(nombre)
            continue
        (SALIDA / f"{nombre}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  guardado en {SALIDA / f'{nombre}.json'}")
        comparar(doc, nombre)
    if fallidos:
        sys.exit(f"Fallaron: {', '.join(fallidos)}")
