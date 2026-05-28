export function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(value || 0);
}

export function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(value || 0);
}

export function shortId(value) {
  if (!value) return "";
  return value.replace("ACC", "A-");
}

export function tierColor(tier) {
  const colors = {
    Critical: "#e15554",
    High: "#d97706",
    Medium: "#2f80ed",
    Low: "#00a884"
  };
  return colors[tier] || "#697386";
}
