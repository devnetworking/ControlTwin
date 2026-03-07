import { Inbox } from "lucide-react";

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}) {
  const iconNode = icon || <Inbox className="w-16 h-16 text-gray-600" />;

  return (
    <div className={`flex flex-col items-center justify-center py-16 px-8 ${className}`.trim()}>
      <div className="text-gray-600">{iconNode}</div>
      <h3 className="mt-4 text-xl font-semibold text-gray-300">{title}</h3>
      {description ? (
        <p className="mt-2 max-w-sm text-center text-sm text-gray-500">{description}</p>
      ) : null}
      {action ? (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-6 rounded-lg bg-ot-blue px-4 py-2 text-white hover:bg-blue-600"
        >
          {action.label}
        </button>
      ) : null}
    </div>
  );
}

export default EmptyState;
