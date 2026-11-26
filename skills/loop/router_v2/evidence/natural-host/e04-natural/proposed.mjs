export function sum(values) {
  return values.reduce((total, value) => {
    const numeric = typeof value === 'number' ||
      (typeof value === 'string' && value.trim().length > 0);
    const amount = numeric ? Number(value) : NaN;
    if (!Number.isFinite(amount)) throw new TypeError('Expected a finite number');
    return total + amount;
  }, 0);
}
