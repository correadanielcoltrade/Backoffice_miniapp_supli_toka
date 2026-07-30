import { useState } from "react";

export const PAGE_SIZES = [10, 25, 50, 100] as const;

/**
 * Paginación en cliente: recibe la lista COMPLETA y devuelve la porción de la
 * página actual + los controles. Pensado para usarse junto al componente
 * <Pagination />. El tamaño de página se elige entre 10/25/50/100.
 */
export function usePagination<T>(items: T[], initialSize = 10) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSizeRaw] = useState<number>(initialSize);

  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(page, totalPages); // se autoajusta si la lista encoge
  const start = (current - 1) * pageSize;
  const pageItems = items.slice(start, start + pageSize);

  function setPageSize(size: number) {
    setPageSizeRaw(size);
    setPage(1);
  }

  return {
    pageItems,
    page: current,
    setPage,
    pageSize,
    setPageSize,
    total,
    totalPages,
    start,
    count: pageItems.length,
  };
}

export interface PaginationState {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  start: number;
  count: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
}

export function Pagination({ pg }: { pg: PaginationState }) {
  const { page, totalPages, total, pageSize, start, count } = pg;
  const onPage = pg.setPage;
  const onPageSize = pg.setPageSize;
  if (total === 0) return null;
  return (
    <div className="pagination">
      <div className="pagination-size">
        <span className="muted">Mostrar</span>
        <select
          value={pageSize}
          onChange={(e) => onPageSize(Number(e.target.value))}
          aria-label="Registros por página"
        >
          {PAGE_SIZES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <span className="muted">
          {start + 1}–{start + count} de {total}
        </span>
      </div>
      <div className="pagination-nav">
        <button
          type="button"
          className="pg-btn"
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
        >
          ‹ Anterior
        </button>
        <span className="muted" style={{ fontSize: 13 }}>
          Página {page} de {totalPages}
        </span>
        <button
          type="button"
          className="pg-btn"
          onClick={() => onPage(page + 1)}
          disabled={page >= totalPages}
        >
          Siguiente ›
        </button>
      </div>
    </div>
  );
}
