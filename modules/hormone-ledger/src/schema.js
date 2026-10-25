// User-specified strict schema: invalid source values are rejected, never clamped.
export function createSchema(z) {
  return z.object({
    角色荷尔蒙: z.record(z.string(), z.number().int().min(0).max(100)).prefault({}),
    角色活体铠甲: z.record(z.string(), z.string()).prefault({}),
  });
}
