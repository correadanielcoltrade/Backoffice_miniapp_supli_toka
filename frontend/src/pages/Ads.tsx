import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Carousel } from "../api/types";
import { Switch } from "../components/Switch";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api")
  .replace(/\/api\/?$/, "");

// Dimensiones EXACTAS que debe tener cada banner (deben coincidir con
// BANNER_WIDTH/BANNER_HEIGHT del backend en apps/ads/models.py).
const BANNER_W = 330;
const BANNER_H = 192;

// Lee el tamano real de la imagen en el navegador antes de subirla.
// Devuelve un mensaje de error si no mide BANNER_W x BANNER_H, o null si es valida.
function checkBannerDimensions(file: File): Promise<string | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      if (img.naturalWidth !== BANNER_W || img.naturalHeight !== BANNER_H) {
        resolve(
          `El banner debe medir exactamente ${BANNER_W}×${BANNER_H} px. ` +
            `Esta imagen mide ${img.naturalWidth}×${img.naturalHeight} px.`
        );
      } else {
        resolve(null);
      }
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve("No se pudo leer la imagen seleccionada.");
    };
    img.src = url;
  });
}

// Si la imagen ya es una URL absoluta (R2/Cloudflare) la usa tal cual;
// si es una ruta relativa (media local antigua) le antepone el origen del API.
function imgUrl(path: string): string {
  return path.startsWith("http") ? path : API_ORIGIN + path;
}

export default function Ads() {
  const { data, loading, error, reload } = useList<Carousel>("/carousels/");
  const [name, setName] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");

  async function createCarousel(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/carousels/", { name });
    setName("");
    reload();
  }

  async function uploadImage(carouselId: number, file: File, position: number) {
    setActionError("");
    const dimError = await checkBannerDimensions(file);
    if (dimError) {
      setActionError(dimError);
      return;
    }
    const fd = new FormData();
    fd.append("carousel", String(carouselId));
    fd.append("image", file);
    fd.append("position", String(position));
    try {
      await api.post("/carousel-images/", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      reload();
    } catch {
      setActionError(
        `No se pudo subir el banner. Verifica que la imagen mida ${BANNER_W}×${BANNER_H} px.`
      );
    }
  }

  async function updateLink(imageId: number, url: string) {
    try {
      await api.patch(`/carousel-images/${imageId}/`, { link_url: url });
    } catch {
      setActionError("No se pudo guardar el enlace del banner.");
    }
  }

  async function deleteImage(imageId: number) {
    if (!window.confirm("¿Eliminar este banner?")) return;
    await api.delete(`/carousel-images/${imageId}/`);
    reload();
  }

  async function toggleCarousel(c: Carousel) {
    setBusyId(c.id);
    setActionError("");
    try {
      await api.patch(`/carousels/${c.id}/`, { is_active: !c.is_active });
      reload();
    } catch {
      setActionError(`No se pudo cambiar el estado de "${c.name}".`);
    } finally {
      setBusyId(null);
    }
  }

  async function deleteCarousel(c: Carousel) {
    if (
      !window.confirm(
        `¿Eliminar el carrusel "${c.name}" y todos sus banners?\nEsta acción no se puede deshacer.`
      )
    )
      return;
    setBusyId(c.id);
    try {
      await api.delete(`/carousels/${c.id}/`);
      reload();
    } catch {
      setActionError(`No se pudo eliminar "${c.name}".`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-head">
          <h2>Banners · Nuevo carrusel</h2>
        </div>
        <form onSubmit={createCarousel} className="form-grid">
          <div className="field" style={{ margin: 0 }}>
            <label>Nombre</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <button className="btn">Crear</button>
        </form>
        <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          Solo los carruseles <b>activos</b> se muestran en la app. Cada banner puede
          llevar un enlace de destino.
        </p>
      </div>

      {actionError && <div className="error-text">{actionError}</div>}
      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {data.map((c) => (
        <div
          className="card"
          key={c.id}
          style={{ marginBottom: 20, opacity: c.is_active ? 1 : 0.7 }}
        >
          <div className="section-head">
            <h2 style={{ fontSize: 17 }}>
              {c.name}{" "}
              <span className="muted">
                · {c.width}×{c.height}px
              </span>
            </h2>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Switch
                  checked={c.is_active}
                  busy={busyId === c.id}
                  onChange={() => toggleCarousel(c)}
                />
                <span className="muted" style={{ fontSize: 12 }}>
                  {c.is_active ? "Activo" : "Inactivo"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => deleteCarousel(c)}
                disabled={busyId === c.id}
                style={{
                  border: "1px solid #fecaca",
                  background: "#fef2f2",
                  color: "#b91c1c",
                  borderRadius: 8,
                  padding: "6px 12px",
                  cursor: "pointer",
                  fontWeight: 500,
                  fontSize: 13,
                }}
              >
                Eliminar carrusel
              </button>
            </div>
          </div>

          <div className="slot-grid">
            {[0, 1, 2, 3].map((slot) => {
              const img = c.images.find((im) => im.position === slot) ?? c.images[slot];
              return (
                <div key={slot} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div
                    style={{
                      border: "1px dashed var(--border)",
                      borderRadius: 12,
                      aspectRatio: "1",
                      display: "grid",
                      placeItems: "center",
                      overflow: "hidden",
                      background: "#faf9ff",
                      position: "relative",
                    }}
                  >
                    {img ? (
                      <>
                        <img
                          src={imgUrl(img.image)}
                          alt=""
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                        <button
                          type="button"
                          onClick={() => deleteImage(img.id)}
                          title="Eliminar banner"
                          style={{
                            position: "absolute",
                            top: 6,
                            right: 6,
                            width: 26,
                            height: 26,
                            borderRadius: "50%",
                            border: "none",
                            background: "rgba(185,28,28,.92)",
                            color: "#fff",
                            cursor: "pointer",
                            fontWeight: 700,
                            lineHeight: 1,
                          }}
                        >
                          ✕
                        </button>
                      </>
                    ) : (
                      <label style={{ textAlign: "center", cursor: "pointer", margin: 0 }}>
                        <span className="muted">
                          + Foto {slot + 1}
                          <br />
                          <small style={{ fontSize: 11 }}>
                            {BANNER_W}×{BANNER_H} px
                          </small>
                        </span>
                        <input
                          type="file"
                          accept="image/*"
                          style={{ display: "none" }}
                          onChange={(e) =>
                            e.target.files?.[0] &&
                            uploadImage(c.id, e.target.files[0], slot)
                          }
                        />
                      </label>
                    )}
                  </div>
                  {img && (
                    <input
                      type="url"
                      placeholder="Enlace de destino (https://…)"
                      defaultValue={img.link_url}
                      onBlur={(e) => updateLink(img.id, e.target.value)}
                      style={{
                        width: "100%",
                        padding: "7px 9px",
                        borderRadius: 8,
                        border: "1px solid var(--border)",
                        fontSize: 12,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
            Máximo 4 banners por carrusel. Cada imagen debe medir exactamente{" "}
            <b>
              {BANNER_W}×{BANNER_H} px
            </b>{" "}
            o será rechazada. El enlace se guarda al salir del campo.
          </p>
        </div>
      ))}
    </>
  );
}
