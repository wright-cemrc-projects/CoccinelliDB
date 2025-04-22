import {Authenticated, IResourceItem, Refine} from "@refinedev/core";
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

import { App as AntdApp } from "antd";
import dataProvider from "@refinedev/simple-rest";
import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";
import { authProvider } from "./authProvider";
import { Header } from "@/src/components";
import { ColorModeContextProvider } from "./contexts/color-mode";
import { ForgotPassword } from "./pages/forgotPassword";
// import { Login } from "./pages/login";
// import { Register } from "./pages/register";
import {filterResourcesByRoles, resources} from "@/src/config/resources";
import axios from "axios";
import { FacilityCreate, FacilityList, FacilityShow, FacilityEdit } from "./pages/facilities";
import { ProjectCreate, ProjectEdit, ProjectList, ProjectShow } from "./pages/projects";
import { GroupList, GroupEdit, GroupCreate, GroupShow } from "./pages/groups";
import { InstrumentCreate, InstrumentEdit, InstrumentList, InstrumentShow } from "./pages/instruments";
import { InstrumentSessionList, InstrumentSessionEdit, InstrumentSessionCreate, InstrumentSessionShow } from "./pages/instrumentsession";
import { PersonList, PersonEdit, PersonCreate, PersonShow } from "./pages/persons";
import { InstrumentIssueCreate, InstrumentIssueEdit, InstrumentIssueList, InstrumentIssueShow } from "./pages/instrumentissues";
import {Unauthorized} from "./pages/Unauthorized"
import { DashboardPage } from "@/src/pages/dashboard";
import { BugOutlined } from "@ant-design/icons";
import {useEffect, useState} from "react";
import { useNavigate } from "react-router-dom";
import {RoleList, RoleShow, RoleEdit, RoleCreate} from "@/src/pages/roles";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

const httpClient = axios.create();

function App() {
  const [isLogged, setIsLoggedIn] = useState(false);
  const [filteredResources, setFilteredResources] = useState<IResourceItem[]>([]);

  useEffect(() => {
      if (!isLogged) {
        authProvider.check().then((res) => {
          if (!res.authenticated) {
            authProvider.login({});
            setIsLoggedIn(true);
          }
        });
      }

    authProvider.getIdentity().then((identity: any) => {
      const roles = identity?.roles || []; // e.g. ["editor", "user"]
      const allowedResources = filterResourcesByRoles(roles);
      setFilteredResources(allowedResources);
    });
  }, []);

  return (
      <RefineKbarProvider>
        <ColorModeContextProvider>
          <AntdApp>
            <DevtoolsProvider>
              <Refine
                dataProvider={dataProvider(API_URL, httpClient)}
                notificationProvider={useNotificationProvider}
                routerProvider={routerBindings}
                authProvider={authProvider}
                resources={filteredResources}
                options={{
                  syncWithLocation: true,
                  warnWhenUnsavedChanges: true,
                  useNewQueryKeys: true,
                  projectId: "3fgJj6-lWqJLy-pmLN0C",
                  title: {
                    text: "CoccinelliDB",
                    icon: <BugOutlined />
                  }
                }}
              >
                <Routes>
                  <Route
                    element={
                      <Authenticated
                        key="authenticated-inner"
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
                    <Route index element={<DashboardPage />} />
                    <Route path="facilities">
                      <Route index element={<FacilityList/>}/>
                      <Route path="create" element={<FacilityCreate/>}/>
                      <Route path="edit/:id" element={<FacilityEdit/>}/>
                      <Route path="show/:id" element={<FacilityShow/>}/>
                    </Route>
                    <Route path="roles">
                      <Route index element={<RoleList/>}/>
                      <Route path="create" element={<RoleCreate/>}/>
                      <Route path="edit/:id" element={<RoleEdit/>}/>
                      <Route path="show/:id" element={<RoleShow/>}/>
                    </Route>
                    <Route path="/groups">
                      <Route index element={<GroupList />}/>
                      <Route path="create" element={<GroupCreate />}/>
                      <Route path="edit/:id" element={<GroupEdit />}/>
                      <Route path="show/:id" element={<GroupShow />}/>
                    </Route>
                    <Route path="persons">
                      <Route index element={<PersonList/>}/>
                      <Route path="create" element={<PersonCreate/>}/>
                      <Route path="edit/:id" element={<PersonEdit/>}/>
                      <Route path="show/:id" element={<PersonShow/>}/>
                    </Route>
                    <Route path="projects">
                      <Route index element={<ProjectList/>}/>
                      <Route path="create" element={<ProjectCreate/>}/>
                      <Route path="edit/:id" element={<ProjectEdit/>}/>
                      <Route path="show/:id" element={<ProjectShow/>}/>
                    </Route>
                    <Route path="/instruments">
                      <Route index element={<InstrumentList />}/>
                      <Route path="create" element={<InstrumentCreate />}/>
                      <Route path="edit/:id" element={<InstrumentEdit />}/>
                      <Route path="show/:id" element={<InstrumentShow />}/>
                    </Route>
                    <Route path="/instrumentsession">
                      <Route index element={<InstrumentSessionList />}/>
                      <Route path="create" element={<InstrumentSessionCreate />}/>
                      <Route path="edit/:id" element={<InstrumentSessionEdit />}/>
                      <Route path="show/:id" element={<InstrumentSessionShow />}/>
                    </Route>
                    <Route path="/instrumentissues">
                      <Route index element={<InstrumentIssueList />}/>
                      <Route path="create" element={<InstrumentIssueCreate />}/>
                      <Route path="edit/:id" element={<InstrumentIssueEdit />}/>
                      <Route path="show/:id" element={<InstrumentIssueShow />}/>
                    </Route>
                    <Route path="*" element={<ErrorComponent />} />
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
  );
}

export default App;
