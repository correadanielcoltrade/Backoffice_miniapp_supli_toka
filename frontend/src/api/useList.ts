import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import type { Paginated } from "./types";

/**
 * Trae TODOS los registros de un endpoint DRF, siguiendo la paginación del
 * servidor (?page_size=100 + páginas siguientes). Así el back office tiene la
 * lista completa y la pagina en el cliente (10/25/50/100). Soporta endpoints
 * paginados ({results,next}) y no paginados (arreglo plano).
 */
async function fetchAll<T>(path: string): Promise<T[]> {
  const sep = path.includes("?") ? "&" : "?";
  const acc: T[] = [];
  let page = 1;
  // Tope de seguridad para no ciclar indefinidamente ante una respuesta rara.
  for (let guard = 0; guard < 1000; guard++) {
    const { data } = await api.get<Paginated<T> | T[]>(
      `${path}${sep}page_size=100&page=${page}`
    );
    if (Array.isArray(data)) return data; // endpoint no paginado
    acc.push(...data.results);
    if (!data.next) break;
    page += 1;
  }
  return acc;
}

/** Hook para listar TODOS los registros de un recurso del backend DRF. */
export function useList<T>(path: string) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(() => {
    setLoading(true);
    setError("");
    fetchAll<T>(path)
      .then((all) => setData(all))
      .catch((e) => {
        if (e.response?.status === 403) {
          setError("No tienes permisos para ver este módulo.");
        } else {
          setError("No se pudo cargar la información.");
        }
      })
      .finally(() => setLoading(false));
  }, [path]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}
