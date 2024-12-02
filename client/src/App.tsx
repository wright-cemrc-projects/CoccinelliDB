import { Authenticated, GitHubBanner, Refine } from "@refinedev/core";
import { DevtoolsPanel, DevtoolsProvider } from "@refinedev/devtools";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";

import {
  ErrorComponent,
  ThemedLayoutV2,
  ThemedSiderV2,
  useNotificationProvider,
} from "@refinedev/antd";
import "@refinedev/antd/dist/reset.css";

import routerBindings, {
  CatchAllNavigate,
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
// import { dataProvider } from "./providers/data-providers";
import { App as AntdApp } from "antd";
import dataProvider from "@refinedev/simple-rest";
import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";
import { authProvider } from "./authProvider";
import { Header } from "./components/header";
import { ColorModeContextProvider } from "./contexts/color-mode";
import { ForgotPassword } from "./pages/forgotPassword";
import { Login } from "./pages/login";
import { Register } from "./pages/register";

import axios from "axios";
import {GroupList, GroupEdit, GroupCreate, GroupShow} from "./pages/groups";
import {InstrumentSessionList, InstrumentSessionEdit, InstrumentSessionCreate, InstrumentSessionShow} from "./pages/instrumentsession";
import {PersonList, PersonEdit, PersonCreate, PersonShow} from "./pages/persons";

const httpClient = axios.create();

function App() {
  return (
    <BrowserRouter>
      <GitHubBanner />
      <RefineKbarProvider>
        <ColorModeContextProvider>
          <AntdApp>
            <DevtoolsProvider>
              <Refine
                // dataProvider={dataProvider("https://api.fake-rest.refine.dev", httpClient)}
                  dataProvider={dataProvider("http://127.0.0.1:8080", httpClient)}
                notificationProvider={useNotificationProvider}
                routerProvider={routerBindings}
                authProvider={authProvider}
                resources={[
                  {
                    name: "groups",
                    list: "/groups",
                    create: "/groups/create",
                    edit: "/groups/edit/:id",
                    show: "/groups/show/:id",
                    meta: {
                      canDelete: true,
                    }
                  },
                  {
                    name: "instrumentsession",
                    list: "/instrumentsession",
                    create: "/instrumentsession/create",
                    edit: "/instrumentsession/edit/:id",
                    show: "/instrumentsession/show/:id",
                    meta: {
                        canDelete: true,
                    }
                  },
                  {
                    name: "persons",
                    list: "/persons",
                    create: "/persons/create",
                    edit: "/persons/edit/:id",
                    show: "/persons/show/:id",
                    meta: {
                      canDelete: true,
                    }
                  }
                ]}
                options={{
                  syncWithLocation: true,
                  warnWhenUnsavedChanges: true,
                  useNewQueryKeys: true,
                  projectId: "3fgJj6-lWqJLy-pmLN0C",
                }}
              >
                <Routes>
                  <Route
                    element={
                      <Authenticated
                        key="authenticated-inner"
                        fallback={<CatchAllNavigate to="/login" />}
                      >
                        <ThemedLayoutV2
                          Header={Header}
                          Sider={(props) => <ThemedSiderV2 {...props} fixed />}
                        >
                          <Outlet />
                        </ThemedLayoutV2>
                      </Authenticated>
                    }
                  >
                    <Route path="/groups">
                      <Route index element={<GroupList />}/>
                      <Route path="create" element={<GroupCreate />}/>
                      <Route path="edit/:id" element={<GroupEdit />}/>
                      <Route path="show/:id" element={<GroupShow />}/>
                    </Route>
                    <Route path="/instrumentsession">
                      <Route index element={<InstrumentSessionList />}/>
                      <Route path="create" element={<InstrumentSessionCreate />}/>
                      <Route path="edit/:id" element={<InstrumentSessionEdit />}/>
                      <Route path="show/:id" element={<InstrumentSessionShow />}/>
                    </Route>
                    <Route path="persons">
                      <Route index element={<PersonList/>}/>
                      <Route path="create" element={<PersonCreate/>}/>
                      <Route path="edit/:id" element={<PersonEdit/>}/>
                      <Route path="show/:id" element={<PersonShow/>}/>
                    </Route>
                    <Route path="*" element={<ErrorComponent />} />
                  </Route>
                  <Route
                    element={
                      <Authenticated
                        key="authenticated-outer"
                        fallback={<Outlet />}
                      >
                        <NavigateToResource />
                      </Authenticated>
                    }
                  >
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route
                      path="/forgot-password"
                      element={<ForgotPassword />}
                    />
                  </Route>
                </Routes>

                <RefineKbar />
                <UnsavedChangesNotifier />
                <DocumentTitleHandler />
              </Refine>
              <DevtoolsPanel />
            </DevtoolsProvider>
          </AntdApp>
        </ColorModeContextProvider>
      </RefineKbarProvider>
    </BrowserRouter>
  );
}

export default App;