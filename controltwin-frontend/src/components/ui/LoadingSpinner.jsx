const SIZE_CLASSES = {
  sm: "w-4 h-4",
  md: "w-8 h-8",
  lg: "w-16 h-16",
};

export function LoadingSpinner({
  size = "md",
  label,
  color = "text-ot-blue",
  fullscreen = false,
}) {
  const spinnerSize = SIZE_CLASSES[size] || SIZE_CLASSES.md;

  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <svg
        className={`${spinnerSize} ${color} animate-spin`}
        viewBox="0 0 50 50"
        role="status"
        aria-label={label || "Loading"}
      >
        <circle
          cx="25"
          cy="25"
          r="20"
          stroke="currentColor"
          strokeWidth="4"
          fill="none"
          strokeDasharray="90 150"
          strokeLinecap="round"
        />
      </svg>
      {label ? <p className="text-sm text-gray-400">{label}</p> : null}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        {content}
      </div>
    );
  }

  return <div className="flex items-center justify-center py-8">{content}</div>;
}

export default LoadingSpinner;
