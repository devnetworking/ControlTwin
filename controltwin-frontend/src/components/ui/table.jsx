import { cn } from "../../lib/utils";

export function Table({ className, ...props }) {
  return <table className={cn("w-full text-sm", className)} {...props} />;
}
export function TableHeader(props) {
  return <thead className="bg-[#0B1B36]" {...props} />;
}
export function TableBody(props) {
  return <tbody {...props} />;
}
export function TableRow({ className, ...props }) {
  return <tr className={cn("border-b border-ot-border hover:bg-white/5", className)} {...props} />;
}
export function TableHead({ className, ...props }) {
  return <th className={cn("px-3 py-2 text-left font-medium text-gray-300", className)} {...props} />;
}
export function TableCell({ className, ...props }) {
  return <td className={cn("px-3 py-2", className)} {...props} />;
}

export const THead = TableHeader;
export const TBody = TableBody;
export const TR = TableRow;
export const TH = TableHead;
export const TD = TableCell;
