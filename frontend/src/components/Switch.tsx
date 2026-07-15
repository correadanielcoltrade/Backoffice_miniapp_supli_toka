/** Interruptor de activación reutilizable (verde = sí, gris = no). */
export function Switch({
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
