import { createRouter, RootRoute, Route } from "@tanstack/react-router";
import { RootLayout } from "./routes/__root";
import { Home } from "./routes/index";
import { Login } from "./routes/login";
import { Register } from "./routes/register";
import { Dashboard } from "./routes/app";

const rootRoute = new RootRoute({
  component: RootLayout,
});

const indexRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Home,
});

const loginRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "login",
  component: Login,
});

const registerRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "register",
  component: Register,
});

const appRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "app",
  component: Dashboard,
});

const routeTree = rootRoute.addChildren([indexRoute, loginRoute, registerRoute, appRoute]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
