// 待组装：酒馆助手角色脚本「MVU ZOD」。z 由酒馆助手提供。
import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';
const Schema = z.object({
  角色荷尔蒙: z.record(z.string(), z.number().int().min(0).max(100)).prefault({}),
  角色活体铠甲: z.record(z.string(), z.string()).prefault({}),
});
$(() => { registerMvuSchema(Schema); });
