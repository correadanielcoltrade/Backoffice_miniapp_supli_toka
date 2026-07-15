import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Brand, Category, Product, ProductSpec } from "../api/types";

const EMPTY = {
  description: "",
  long_description: "",
  sku: "",
  category: "",
  brand: "",
  sale_price: "",
  is_active: true,
  is_featured: false,
  is_on_offer: false,
  show_stock: true,
  featuresText: "",
  specsText: "",
};

// ---- helpers de conversión lista <-> texto ----
const featuresToText = (arr?: string[]) => (arr ?? []).join("\n");
const parseFeatures = (t: string) =>
  t.split("\n").map((s) => s.trim()).filter(Boolean);
const specsToText = (arr?: ProductSpec[]) =>
  (arr ?? []).map((s) => `${s?.key ?? ""}: ${s?.value ?? ""}`).join("\n");
const parseSpecs = (t: string): ProductSpec[] =>
  t
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      const i = line.indexOf(":");
      return i === -1
        ? { key: line, value: "" }
        : { key: line.slice(0, i).trim(), value: line.slice(i + 1).trim() };
    });

/** Switch de activación (verde = sí, gris = no). */
function Switch({
  checked,
  onChange,
  busy,
}: {
  checked: boolean;
  onChange: () => void;
  busy?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onChange}
      disabled={busy}
      role="switch"
      aria-checked={checked}
      style={{
        width: 46,
        height: 26,
        borderRadius: 999,
        border: "none",
        padding: 0,
        cursor: busy ? "wait" : "pointer",
        background: checked ? "#16a34a" : "#cbd5e1",
        position: "relative",
        transition: "background .15s ease",
        opacity: busy ? 0.6 : 1,
        flex: "0 0 auto",
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 3,
          left: checked ? 23 : 3,
          width: 20,
          height: 20,
          borderRadius: "50%",
          background: "#fff",
          transition: "left .15s ease",
          boxShadow: "0 1px 2px rgba(0,0,0,.25)",
        }}
      />
    </button>
  );
}

function LabeledSwitch({
  label,
  hint,
  checked,
  onChange,
}: {
  label: string;
  hint?: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <Switch checked={checked} onChange={onChange} />
      <span style={{ fontWeight: 500 }}>{label}</span>
      {hint && (
        <span className="muted" style={{ fontSize: 12 }}>
          {hint}
        </span>
      )}
    </div>
  );
}

function Chip({ text, color }: { text: string; color: string }) {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        padding: "2px 8px",
        borderRadius: 999,
        background: `${color}1a`,
        color,
        border: `1px solid ${color}40`,
      }}
    >
      {text}
    </span>
  );
}

export default function Catalog() {
  const { data: products, loading, error, reload } = useList<Product>("/products/");
  const { data: categories } = useList<Category>("/categories/");
  const { data: brands, reload: reloadBrands } = useList<Brand>("/brands/");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [images, setImages] = useState<(File | null)[]>([null, null, null, null]);
  const [currentImages, setCurrentImages] = useState<string[]>([]);

  function setImage(i: number, file: File | null) {
    const next = [...images];
    next[i] = file;
    setImages(next);
  }

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY);
    setImages([null, null, null, null]);
    setCurrentImages([]);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(p: Product) {
    setEditingId(p.id);
    setForm({
      description: p.description,
      long_description: p.long_description ?? "",
      sku: p.sku,
      category: String(p.category),
      brand: p.brand != null ? String(p.brand) : "",
      sale_price: String(p.sale_price),
      is_active: p.is_active,
      is_featured: p.is_featured,
      is_on_offer: p.is_on_offer,
      show_stock: p.show_stock,
      featuresText: featuresToText(p.features),
      specsText: specsToText(p.specifications),
    });
    setImages([null, null, null, null]);
    setCurrentImages(p.images ?? []);
    setFormError("");
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function addBrand() {
    const name = window.prompt("Nombre de la nueva marca:");
    if (!name) return;
    try {
      const { data } = await api.post("/brands/", { name });
      await reloadBrands();
      setForm((f) => ({ ...f, brand: String(data.id) }));
    } catch (err: any) {
      setFormError(
        "No se pudo crear la marca: " +
          JSON.stringify(err.response?.data ?? "error")
      );
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      // FormData para soportar imagenes. Los booleanos y el JSON se envian
      // SIEMPRE explicitos (en multipart, un booleano ausente = False).
      const fd = new FormData();
      fd.append("description", form.description);
      fd.append("long_description", form.long_description);
      fd.append("sku", form.sku);
      fd.append("category", form.category);
      fd.append("brand", form.brand); // "" = sin marca (el backend lo vuelve null)
      fd.append("sale_price", form.sale_price);
      fd.append("is_active", form.is_active ? "true" : "false");
      fd.append("is_featured", form.is_featured ? "true" : "false");
      fd.append("is_on_offer", form.is_on_offer ? "true" : "false");
      fd.append("show_stock", form.show_stock ? "true" : "false");
      fd.append("features", JSON.stringify(parseFeatures(form.featuresText)));
      fd.append("specifications", JSON.stringify(parseSpecs(form.specsText)));
      images.forEach((file, i) => {
        if (file) fd.append(`image${i + 1}`, file);
      });
      const cfg = { headers: { "Content-Type": "multipart/form-data" } };
      if (editingId) {
        await api.patch(`/products/${editingId}/`, fd, cfg);
      } else {
        await api.post("/products/", fd, cfg);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY);
      setImages([null, null, null, null]);
      reload();
    } catch (err: any) {
      setFormError(JSON.stringify(err.response?.data ?? "Error"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(p: Product) {
    setBusyId(p.id);
    setActionError("");
    try {
      await api.patch(`/products/${p.id}/`, { is_active: !p.is_active });
      reload();
    } catch {
      setActionError(`No se pudo cambiar el estado de "${p.description}".`);
    } finally {
      setBusyId(null);
    }
  }

  async function remove(p: Product) {
    if (
      !window.confirm(
        `¿Eliminar "${p.description}" del catálogo?\nEsta acción no se puede deshacer.`
      )
    )
      return;
    setBusyId(p.id);
    setActionError("");
    try {
      await api.delete(`/products/${p.id}/`);
      reload();
    } catch (err: any) {
      const st = err.response?.status;
      if (st === 400 || st === 409 || st === 500) {
        setActionError(
          `No se puede eliminar "${p.description}" porque está asociado a pedidos. Desactívalo con el switch en su lugar.`
        );
      } else {
        setActionError(`No se pudo eliminar "${p.description}".`);
      }
    } finally {
      setBusyId(null);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    minHeight: 80,
    resize: "vertical",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid var(--border)",
    fontFamily: "inherit",
    fontSize: 14,
  };

  return (
    <div className="card">
      <div className="section-head">
        <h2>Gestión de Catálogo</h2>
        {showForm ? (
          <button className="btn" onClick={() => setShowForm(false)}>
            Cerrar
          </button>
        ) : (
          <button className="btn" onClick={openCreate}>
            + Nuevo producto
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={save} style={{ marginBottom: 24 }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 14,
            }}
          >
            <div className="field">
              <label>Nombre / descripción corta</label>
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="field">
              <label>SKU</label>
              <input
                value={form.sku}
                onChange={(e) => setForm({ ...form, sku: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Categoría</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                <option value="">Selecciona…</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>
                Marca{" "}
                <button
                  type="button"
                  onClick={addBrand}
                  style={{
                    border: "none",
                    background: "none",
                    color: "var(--primary, #4f46e5)",
                    cursor: "pointer",
                    fontSize: 12,
                    fontWeight: 600,
                    padding: 0,
                  }}
                >
                  ＋ nueva
                </button>
              </label>
              <select
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
              >
                <option value="">Sin marca</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Precio de venta</label>
              <input
                type="number"
                step="0.01"
                value={form.sale_price}
                onChange={(e) => setForm({ ...form, sale_price: e.target.value })}
              />
            </div>
          </div>

          <div className="field" style={{ marginTop: 14 }}>
            <label>Descripción larga (ficha del producto)</label>
            <textarea
              style={inputStyle}
              value={form.long_description}
              onChange={(e) =>
                setForm({ ...form, long_description: e.target.value })
              }
            />
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 14,
              marginTop: 4,
            }}
          >
            <div className="field">
              <label>
                Características{" "}
                <span className="muted" style={{ fontWeight: 400 }}>
                  — una por línea
                </span>
              </label>
              <textarea
                style={inputStyle}
                placeholder={"600 ml\nNo retornable"}
                value={form.featuresText}
                onChange={(e) =>
                  setForm({ ...form, featuresText: e.target.value })
                }
              />
            </div>
            <div className="field">
              <label>
                Especificaciones{" "}
                <span className="muted" style={{ fontWeight: 400 }}>
                  — formato «Clave: Valor», una por línea
                </span>
              </label>
              <textarea
                style={inputStyle}
                placeholder={"Sabor: Cola\nContenido: 600 ml"}
                value={form.specsText}
                onChange={(e) => setForm({ ...form, specsText: e.target.value })}
              />
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "14px 28px",
              margin: "18px 0 8px",
              padding: "14px 16px",
              background: "#faf9ff",
              borderRadius: 12,
              border: "1px solid var(--border)",
            }}
          >
            <LabeledSwitch
              label={form.is_active ? "Activo" : "Inactivo"}
              hint="visible en la app"
              checked={form.is_active}
              onChange={() => setForm({ ...form, is_active: !form.is_active })}
            />
            <LabeledSwitch
              label="Destacado"
              hint="featured"
              checked={form.is_featured}
              onChange={() => setForm({ ...form, is_featured: !form.is_featured })}
            />
            <LabeledSwitch
              label="En oferta"
              hint="offer"
              checked={form.is_on_offer}
              onChange={() => setForm({ ...form, is_on_offer: !form.is_on_offer })}
            />
            <LabeledSwitch
              label="Mostrar stock"
              hint="showStock"
              checked={form.show_stock}
              onChange={() => setForm({ ...form, show_stock: !form.show_stock })}
            />
          </div>

          <label style={{ marginTop: 6 }}>
            Imágenes del producto (hasta 4)
            {editingId && (
              <span className="muted" style={{ fontWeight: 400 }}>
                {" "}
                — deja una casilla vacía para conservar la imagen actual
              </span>
            )}
          </label>
          <div className="slot-grid" style={{ marginBottom: 16 }}>
            {[0, 1, 2, 3].map((i) => {
              const preview = images[i]
                ? URL.createObjectURL(images[i]!)
                : currentImages[i] ?? null;
              return (
                <label
                  key={i}
                  style={{
                    border: "1px dashed var(--border)",
                    borderRadius: 12,
                    aspectRatio: "1",
                    display: "grid",
                    placeItems: "center",
                    cursor: "pointer",
                    overflow: "hidden",
                    background: "#faf9ff",
                    margin: 0,
                    fontWeight: 500,
                  }}
                >
                  {preview ? (
                    <img
                      src={preview}
                      alt=""
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  ) : (
                    <span className="muted">+ Foto {i + 1}</span>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={(e) => setImage(i, e.target.files?.[0] ?? null)}
                  />
                </label>
              );
            })}
          </div>

          <button className="btn" disabled={saving}>
            {saving
              ? "Guardando…"
              : editingId
              ? "Guardar cambios"
              : "Crear producto"}
          </button>
          {formError && <div className="error-text">{formError}</div>}
        </form>
      )}

      {actionError && <div className="error-text">{actionError}</div>}
      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Imagen</th>
                <th>SKU</th>
                <th>Producto</th>
                <th>Categoría</th>
                <th>Precio</th>
                <th>Stock</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} style={{ opacity: p.is_active ? 1 : 0.55 }}>
                  <td>
                    {p.images.length > 0 ? (
                      <img
                        src={p.images[0]}
                        alt=""
                        style={{
                          width: 40,
                          height: 40,
                          objectFit: "cover",
                          borderRadius: 8,
                        }}
                      />
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td>{p.sku}</td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{p.description}</div>
                    <div className="muted" style={{ fontSize: 12 }}>
                      {p.brand_name || "Sin marca"}
                    </div>
                    {(p.is_featured || p.is_on_offer) && (
                      <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                        {p.is_featured && (
                          <Chip text="Destacado" color="#7c3aed" />
                        )}
                        {p.is_on_offer && <Chip text="Oferta" color="#ea580c" />}
                      </div>
                    )}
                  </td>
                  <td>{p.category_name}</td>
                  <td>${Number(p.sale_price).toLocaleString("es-MX")}</td>
                  <td>{p.units_in_stock ?? 0}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Switch
                        checked={p.is_active}
                        busy={busyId === p.id}
                        onChange={() => toggleActive(p)}
                      />
                      <span
                        className="muted"
                        style={{ fontSize: 12, minWidth: 54 }}
                      >
                        {p.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        type="button"
                        onClick={() => openEdit(p)}
                        disabled={busyId === p.id}
                        style={{
                          border: "1px solid var(--border)",
                          background: "#fff",
                          borderRadius: 8,
                          padding: "6px 12px",
                          cursor: "pointer",
                          fontWeight: 500,
                          fontSize: 13,
                        }}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => remove(p)}
                        disabled={busyId === p.id}
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
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
