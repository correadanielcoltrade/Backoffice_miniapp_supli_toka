import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import type { Paginated } from "./types";

/** Hook simple para listar recursos paginados del backend DRF. */
export function useList<T>(path: string) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(() => {
    setLoading(true);
    setError("");
    api
      .get<Paginated<T> | T[]>(path)
      .then(({ data }) => {
        setData(Array.isArray(data) ? data : data.results);
      })
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
