import type { IResourceItem } from "@refinedev/core";
import {DashboardOutlined, GroupOutlined, UserOutlined, CalendarOutlined} from "@ant-design/icons";


export const resources: IResourceItem[] = [
    {
      name: "dashboard",
      list: "/",
      meta: {
          label: "Dashboard",
          icon: <DashboardOutlined />,
      }
    },
    {
        name: "groups",
        list: "/groups",
        create: "/groups/create",
        edit: "/groups/edit/:id",
        show: "/groups/show/:id",
        meta: {
            label: "Groups",
            canDelete: true,
            icon: <GroupOutlined />,
        }
    },
    {
        name: "persons",
        list: "/persons",
        create: "/persons/create",
        edit: "/persons/edit/:id",
        show: "/persons/show/:id",
        meta: {
            label: "Persons",
            canDelete: true,
            icon: <UserOutlined />
        }
    },
    {
        name: "instrumentsession",
        list: "/instrumentsession",
        create: "/instrumentsession/create",
        edit: "/instrumentsession/edit/:id",
        show: "/instrumentsession/show/:id",
        meta: {
            label: "Instrumentsession",
            canDelete: true,
            icon: <CalendarOutlined />
        }
    },

];