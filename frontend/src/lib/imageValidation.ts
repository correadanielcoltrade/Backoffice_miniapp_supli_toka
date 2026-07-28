// Validación de dimensiones de imágenes ANTES de subirlas (feedback inmediato).
// El backend vuelve a validar como fuente de verdad; esto solo mejora la UX.
//
// Las dimensiones deben coincidir con las constantes del backend:
//   - Categoría: apps/catalog/models.py  CATEGORY_ICON_*
//   - Marca:     apps/catalog/models.py  BRAND_LOGO_*
//   - Producto:  apps/catalog/models.py  PRODUCT_IMAGE_*
//   - Banner:    apps/ads/models.py      BANNER_WIDTH / BANNER_HEIGHT

export type DimensionRule =
  | { kind: "exact"; width: number; height: number; label: string }
  | { kind: "widthMaxHeight"; width: number; maxHeight: number; label: string };

/** Dimensiones exigidas por tipo de imagen (única fuente en el frontend). */
export const IMAGE_RULES = {
  categoryIcon: { kind: "exact", width: 100, height: 100, label: "El ícono de la categoría" },
  brandLogo: { kind: "widthMaxHeight", width: 320, maxHeight: 116, label: "El logo de la marca" },
  productImage: { kind: "exact", width: 1400, height: 1400, label: "La imagen del producto" },
  banner: { kind: "exact", width: 1380, height: 440, label: "El banner" },
} satisfies Record<string, DimensionRule>;

/** Texto corto de la restricción, para mostrar como pista en el input. */
export function ruleHint(rule: DimensionRule): string {
  return rule.kind === "exact"
    ? `${rule.width}×${rule.height} px`
    : `${rule.width} px de ancho · alto ≤ ${rule.maxHeight} px`;
}

/**
 * Lee el tamaño real de la imagen en el navegador y devuelve un mensaje de
 * error si NO cumple la regla, o null si es válida.
 */
export function checkImageDimensions(
  file: File,
  rule: DimensionRule
): Promise<string | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      const w = img.naturalWidth;
      const h = img.naturalHeight;
      const ok =
        rule.kind === "exact"
          ? w === rule.width && h === rule.height
          : w === rule.width && h <= rule.maxHeight;
      if (ok) {
        resolve(null);
        return;
      }
      const need =
        rule.kind === "exact"
          ? `medir exactamente ${rule.width}×${rule.height} px`
          : `medir ${rule.width} px de ancho y hasta ${rule.maxHeight} px de alto`;
      resolve(`${rule.label} debe ${need}. Esta imagen mide ${w}×${h} px.`);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve("No se pudo leer la imagen seleccionada.");
    };
    img.src = url;
  });
}
