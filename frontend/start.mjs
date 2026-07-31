import { createAppServer } from "./server.mjs";

const port = Number.parseInt(process.env.PORT ?? "3000", 10);
const host = process.env.HOST ?? "0.0.0.0";
const server = createAppServer();

server.listen(port, host);
