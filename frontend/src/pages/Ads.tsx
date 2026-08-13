import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Brand, Carousel, CarouselImage, Category, Product } from "../api/types";
import { Switch } from "../components/Switch";
import { IMAGE_RULES, checkImageDimensions, ruleHint } from "../lib/imageValidation";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api")
  .replace(/\/api\/?$/, "");

const targetSelectStyle: React.CSSProperties = {
  flex: 1,
  minWidth: 0,
  padding: "6px 8px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  fontSize: 12,
  background: "#fff",
};

const scheduleInputStyle: React.CSSProperties = {
  padding: "6px 8px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  fontSize: 12,
  background: "#fff",
};

// Convierte un ISO (UTC) al formato datetime-local (hora local) que usa el input.
function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

// Estado efectivo del carrusel (feedback inmediato en el cliente).
function scheduleStatus(
  isActive: boolean,
  from: string,
  until: string
): { label: string; badge: string } {
  if (!isActive) return { label: "Inactivo", badge: "gray" };
  const now = Date.now();
  if (from && new Date(from).getTime() > now)
    return { label: "Programado", badge: "amber" };
  if (until && new Date(until).getTime() < now)
    return { label: "Vencido", badge: "red" };
  return { label: "Activo ahora", badge: "green" };
}

// Dimensiones EXACTAS del banner (deben coincidir con BANNER_WIDTH/BANNER_HEIGHT
// del backend en apps/ads/models.py). Fuente unica en lib/imageValidation.
const BANNER_RULE = IMAGE_RULES.banner;

// Si la imagen ya es una URL absoluta (R2/Cloudflare) la usa tal cual;
// si es una ruta relativa (media local antigua) le antepone el origen del API.
function imgUrl(path: string): string {
  return path.startsWith("http") ? path : API_ORIGIN + path;
}

export default function Ads() {
  const { data, loading, error, reload } = useList<Carousel>("/carousels/");
  const { data: categories } = useList<Category>("/categories/");
  const { data: brands } = useList<Brand>("/brands/");
  const { data: products } = useList<Product>("/products/");
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
    const dimError = await checkImageDimensions(file, BANNER_RULE);
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
        `No se pudo subir el banner. Verifica que la imagen mida ${BANNER_RULE.width}×${BANNER_RULE.height} px.`
      );
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

          <CarouselSchedule carousel={c} onError={setActionError} />

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
                            {ruleHint(BANNER_RULE)}
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
                    <BannerTarget
                      image={img}
                      categories={categories}
                      brands={brands}
                      products={products}
                      onError={setActionError}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
            Máximo 4 banners por carrusel. Cada imagen debe medir exactamente{" "}
            <b>
              {BANNER_RULE.width}×{BANNER_RULE.height} px
            </b>{" "}
            o será rechazada. La función del tap se guarda sola.
          </p>
        </div>
      ))}
    </>
  );
}

/**
 * Programación de vigencia del carrusel: fecha/hora de activación y de
 * desactivación. La mini app sirve sus banners solo si está activo (interruptor)
 * Y estamos dentro de la ventana. Se guarda solo al cambiar las fechas.
 */
function CarouselSchedule({
  carousel,
  onError,
}: {
  carousel: Carousel;
  onError: (msg: string) => void;
}) {
  const [from, setFrom] = useState(toLocalInput(carousel.active_from));
  const [until, setUntil] = useState(toLocalInput(carousel.active_until));
  const [saving, setSaving] = useState(false);
  const status = scheduleStatus(carousel.is_active, from, until);

  async function save(nextFrom: string, nextUntil: string) {
    setSaving(true);
    onError("");
    try {
      await api.patch(`/carousels/${carousel.id}/`, {
        active_from: nextFrom || null,
        active_until: nextUntil || null,
      });
    } catch (err: any) {
      const detail = err.response?.data?.active_until?.[0];
      onError(detail ?? "No se pudo guardar la programación del carrusel.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 12,
        flexWrap: "wrap",
        margin: "4px 0 14px",
        padding: "10px 12px",
        background: "#f7faff",
        borderRadius: 10,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <label className="muted" style={{ fontSize: 11 }}>
          Activar desde
        </label>
        <input
          type="datetime-local"
          value={from}
          style={scheduleInputStyle}
          onChange={(e) => {
            setFrom(e.target.value);
            save(e.target.value, until);
          }}
        />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <label className="muted" style={{ fontSize: 11 }}>
          Desactivar el
        </label>
        <input
          type="datetime-local"
          value={until}
          style={scheduleInputStyle}
          onChange={(e) => {
            setUntil(e.target.value);
            save(from, e.target.value);
          }}
        />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, height: 30 }}>
        <span className={"badge " + status.badge}>{status.label}</span>
        {saving && (
          <span className="muted" style={{ fontSize: 11 }}>
            guardando…
          </span>
        )}
      </div>
      {(from || until) && (
        <button
          type="button"
          className="btn secondary"
          style={{ fontSize: 12, padding: "5px 10px" }}
          onClick={() => {
            setFrom("");
            setUntil("");
            save("", "");
          }}
        >
          Quitar programación
        </button>
      )}
    </div>
  );
}

/**
 * Función del tap del banner: a qué contenido navega la mini app al tocarlo.
 * Se elige un tipo (categoría/marca/producto) y luego la entidad. Se guarda solo
 * (PATCH) al seleccionar. "Sin función" = el banner no navega a nada.
 */
function BannerTarget({
  image,
  categories,
  brands,
  products,
  onError,
}: {
  image: CarouselImage;
  categories: Category[];
  brands: Brand[];
  products: Product[];
  onError: (msg: string) => void;
}) {
  const [type, setType] = useState(image.target_type || "");
  const [id, setId] = useState(image.target_id ? String(image.target_id) : "");
  const [saving, setSaving] = useState(false);

  // Solo se ofrecen entidades ACTIVAS como destino del tap.
  const options =
    type === "CATEGORY"
      ? categories
          .filter((c) => c.is_active)
          .map((c) => ({ id: c.id, label: c.name }))
      : type === "BRAND"
      ? brands
          .filter((b) => b.is_active)
          .map((b) => ({ id: b.id, label: b.name }))
      : type === "PRODUCT"
      ? products
          .filter((p) => p.is_active)
          .map((p) => ({ id: p.id, label: `${p.sku} · ${p.description}` }))
      : [];

  async function persist(nextType: string, nextId: string) {
    setSaving(true);
    onError("");
    try {
      await api.patch(`/carousel-images/${image.id}/`, {
        target_type: nextType,
        target_id: nextType && nextId ? Number(nextId) : null,
      });
    } catch {
      onError("No se pudo guardar la función del banner.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span className="muted" style={{ fontSize: 11 }}>
        Función del tap {saving && "· guardando…"}
      </span>
      <div style={{ display: "flex", gap: 6 }}>
        <select
          value={type}
          style={targetSelectStyle}
          onChange={(e) => {
            const t = e.target.value;
            setType(t);
            setId("");
            if (!t) persist("", ""); // sin función: guardar de una
          }}
        >
          <option value="">Sin función</option>
          <option value="CATEGORY">Categoría</option>
          <option value="BRAND">Marca</option>
          <option value="PRODUCT">Producto</option>
        </select>
        {type && (
          <select
            value={id}
            style={targetSelectStyle}
            onChange={(e) => {
              const v = e.target.value;
              setId(v);
              if (v) persist(type, v);
            }}
          >
            <option value="">Selecciona…</option>
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
